"""POMP NET compatibility bridge for MHSanaei 3X-UI v3.11.0.

Staging-only HTTP adapter for the existing dashboard's core endpoints.
No legacy database is modified. Public /sub tokens are intentionally NOT
rewritten until a verified legacy-token -> 3X-UI subId migration exists.
"""
import base64, hashlib, hmac, http.cookiejar, json, os, re, threading, time
import urllib.error, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE = os.getenv("XUI_BASE_URL", "").rstrip("/")
USER = os.getenv("XUI_USERNAME", "")
PASSWORD = os.getenv("XUI_PASSWORD", "")
API_TOKEN = os.getenv("XUI_API_TOKEN", "")
SECRET = os.getenv("POMPNET_ADAPTER_SECRET", "")
PORT = int(os.getenv("POMPNET_3XUI_BRIDGE_PORT", "8091"))
INBOUND_TAGS = {
    "vless": os.getenv("XUI_VLESS_INBOUND_TAG", "VLESS WS"),
    "vmess": os.getenv("XUI_VMESS_INBOUND_TAG", "VMESS WS"),
    "trojan": os.getenv("XUI_TROJAN_INBOUND_TAG", "TROJAN WS"),
}
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
csrf = ""
lock = threading.RLock()

class BridgeError(Exception): pass

def request(method, path, payload=None, form=False):
    global csrf
    if not BASE:
        raise BridgeError("XUI_BASE_URL is not configured")
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        if form:
            data = urllib.parse.urlencode(payload).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(payload, separators=(",", ":")).encode()
            headers["Content-Type"] = "application/json"
    if API_TOKEN:
        headers["Authorization"] = "Bearer " + API_TOKEN
    elif csrf:
        headers["X-CSRF-Token"] = csrf
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with opener.open(req, timeout=18) as res:
            raw = res.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise BridgeError("3X-UI HTTP %s: %s" % (e.code, e.read().decode("utf-8","replace")[:240]))
    except Exception as e:
        raise BridgeError("3X-UI connection failed: " + str(e)[:180])
    try: result = json.loads(raw) if raw else {}
    except Exception: raise BridgeError("3X-UI returned invalid JSON")
    if isinstance(result, dict) and result.get("success") is False:
        raise BridgeError(str(result.get("msg") or "3X-UI API rejected request"))
    return result.get("obj", result) if isinstance(result, dict) else result

def login_xui(username, password):
    global csrf
    if API_TOKEN:
        return
    if not USER or not PASSWORD or not hmac.compare_digest(username, USER) or not hmac.compare_digest(password, PASSWORD):
        raise BridgeError("نام کاربری یا رمز عبور نادرست است")
    with lock:
        try:
            c = request("GET", "/panel/csrf-token")
            if isinstance(c, dict): csrf = str(c.get("token") or c.get("csrfToken") or "")
        except BridgeError:
            csrf = ""
        # 3X-UI login endpoint accepts form-encoded credentials.
        request("POST", "/login", {"username": USER, "password": PASSWORD}, form=True)
        try:
            c = request("GET", "/panel/csrf-token")
            if isinstance(c, dict): csrf = str(c.get("token") or c.get("csrfToken") or "")
        except BridgeError:
            pass

def token_make(username):
    payload = json.dumps({"u": username, "exp": int(time.time()) + 12*3600}, separators=(",",":")).encode()
    body = base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig

def token_check(header):
    if not SECRET: raise BridgeError("POMPNET_ADAPTER_SECRET is not configured")
    if not header.startswith("Bearer "): raise BridgeError("login_required")
    try:
        body, sig = header[7:].split(".", 1)
        expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(body + "="*((4-len(body)%4)%4)))
        if int(data["exp"]) < time.time(): raise ValueError()
        return data["u"]
    except Exception: raise BridgeError("invalid_or_expired_token")

def obj(response):
    return response.get("obj", response) if isinstance(response, dict) else response

def inbound_index():
    rows = obj(request("GET", "/panel/api/inbounds/list"))
    if not isinstance(rows, list): raise BridgeError("3X-UI inbound list is not an array")
    return {str(x.get("tag")): x for x in rows if isinstance(x, dict) and x.get("tag")}

def normalize(client, inbound_map):
    traffic = client.get("traffic") or {}
    up, down = int(traffic.get("up", 0) or 0), int(traffic.get("down", 0) or 0)
    total = int(client.get("totalGB", 0) or 0)
    expiry_ms = int(client.get("expiryTime", 0) or 0)
    proto_map = {}
    for iid in client.get("inboundIds", []) or []:
        for inbound in inbound_map.values():
            if int(inbound.get("id", -1)) == int(iid):
                proto = str(inbound.get("protocol", "")).lower()
                if proto in ("vless","vmess","trojan"):
                    proto_map.setdefault(proto, []).append(str(inbound.get("tag","")))
    proxies = {}
    inbounds = {}
    for proto, tags in proto_map.items():
        proxies[proto] = {}
        inbounds[proto] = tags
    return {
        "username": client.get("email", ""),
        "status": "active" if client.get("enable", True) else "disabled",
        "used_traffic": up + down,
        "data_limit": total or None,
        "expire": int(expiry_ms/1000) if expiry_ms else None,
        "online_at": None,
        "proxies": proxies,
        "inbounds": inbounds,
        "sub_url": ("/sub/" + str(client.get("subId"))) if client.get("subId") else None,
        "admin": {"is_sudo": False},
    }

def json_body(handler, limit=65536):
    n = int(handler.headers.get("Content-Length") or 0)
    if n < 1 or n > limit: raise BridgeError("invalid_request_body")
    data = json.loads(handler.rfile.read(n).decode("utf-8"))
    if not isinstance(data, dict): raise BridgeError("invalid_request_body")
    return data

class Handler(BaseHTTPRequestHandler):
    server_version = "POMP-NET-3XUI-Bridge/1.0"
    def sendj(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Cache-Control","no-store"); self.send_header("Content-Length",str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
    def log_message(self, fmt, *args):
        print("[3xui-bridge] " + (fmt % args), flush=True)
    def do_POST(self):
        try:
            if self.path == "/api/admin/token":
                if not SECRET: raise BridgeError("POMPNET_ADAPTER_SECRET is not configured")
                ctype = self.headers.get("Content-Type","")
                if "application/x-www-form-urlencoded" in ctype:
                    raw = int(self.headers.get("Content-Length") or 0)
                    form = urllib.parse.parse_qs(self.rfile.read(min(raw,8192)).decode())
                    username = form.get("username",[""])[0]; password = form.get("password",[""])[0]
                else:
                    body = json_body(self,8192); username=body.get("username",""); password=body.get("password","")
                login_xui(str(username), str(password))
                return self.sendj(200, {"access_token":token_make(str(username)), "token_type":"bearer"})
            if self.path == "/api/user":
                token_check(self.headers.get("Authorization",""))
                body = json_body(self)
                username = str(body.get("username","")).strip()
                if not re.fullmatch(r"[A-Za-z0-9_.@-]{2,64}", username): raise BridgeError("invalid_username")
                requested = body.get("inbounds") or {}
                tags = sorted({str(t) for values in requested.values() if isinstance(values,list) for t in values})
                if not tags: raise BridgeError("select_at_least_one_inbound")
                imap = inbound_index()
                ids=[]
                for tag in tags:
                    inbound=imap.get(tag)
                    if not inbound: raise BridgeError("inbound_not_found: "+tag)
                    proto=str(inbound.get("protocol","")).lower()
                    if proto not in ("vless","vmess","trojan"): raise BridgeError("unsupported_protocol: "+proto)
                    ids.append(int(inbound["id"]))
                expiry=int(body.get("expire") or 0)*1000
                quota=int(body.get("data_limit") or 0)
                client={"email":username,"totalGB":quota,"expiryTime":expiry,"enable":True,"tgId":0,"limitIp":0,"limitHwid":0}
                created=obj(request("POST","/panel/api/clients/add",{"client":client,"inboundIds":ids}))
                return self.sendj(200, {"username":username,"status":"active","result":created})
            raise BridgeError("not_found")
        except BridgeError as e:
            msg=str(e); status=401 if "login" in msg or "رمز" in msg or "token" in msg else 400
            self.sendj(status,{"detail":msg})
        except Exception as e: self.sendj(400,{"detail":str(e)[:300]})
    def do_GET(self):
        try:
            if self.path == "/health": return self.sendj(200,{"ok":True,"engine":"3x-ui-v3.11.0"})
            token_check(self.headers.get("Authorization",""))
            if self.path == "/api/users":
                imap=inbound_index()
                rows=obj(request("GET","/panel/api/clients/list"))
                return self.sendj(200,[normalize(x,imap) for x in (rows or [])])
            if self.path == "/api/system":
                imap=inbound_index()
                rows=obj(request("GET","/panel/api/clients/list")) or []
                return self.sendj(200,{"engine":"3X-UI v3.11.0","inbounds":len(imap),"total_users":len(rows),"active_users":sum(1 for x in rows if x.get("enable")),"online_users":None,"traffic_up":sum(int((x.get("traffic") or {}).get("up",0) or 0) for x in rows),"traffic_down":sum(int((x.get("traffic") or {}).get("down",0) or 0) for x in rows)})
            raise BridgeError("not_found")
        except BridgeError as e:
            msg=str(e); self.sendj(401 if "token" in msg or "login" in msg else 502,{"detail":msg})
        except Exception as e: self.sendj(502,{"detail":str(e)[:300]})
    def do_DELETE(self):
        try:
            token_check(self.headers.get("Authorization",""))
            m=re.fullmatch(r"/api/user/([^/]+)",urllib.parse.urlsplit(self.path).path)
            if not m: raise BridgeError("not_found")
            email=urllib.parse.unquote(m.group(1))
            result=obj(request("POST","/panel/api/clients/del/"+urllib.parse.quote(email,safe="")))
            return self.sendj(200,{"detail":"User deleted","result":result})
        except BridgeError as e: self.sendj(401 if "token" in str(e) else 502,{"detail":str(e)})
        except Exception as e: self.sendj(502,{"detail":str(e)[:300]})

if __name__ == "__main__":
    if os.getenv("POMPNET_3XUI_BRIDGE","0") == "1":
        if not BASE or not SECRET or (not USER or not PASSWORD):
            raise SystemExit("[3xui-bridge] FATAL: set XUI_BASE_URL, POMPNET_ADAPTER_SECRET and XUI_API_TOKEN or XUI_USERNAME/XUI_PASSWORD")
        print("[3xui-bridge] staging compatibility API listening on 127.0.0.1:%d" % PORT, flush=True)
        ThreadingHTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
    else:
        print("[3xui-bridge] disabled; set POMPNET_3XUI_BRIDGE=1 to enable",flush=True)
