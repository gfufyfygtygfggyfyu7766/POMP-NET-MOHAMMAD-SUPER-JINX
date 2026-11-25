#!/usr/bin/env python3
"""Explicit, idempotent Marzban -> 3X-UI v3.11.0 importer.

Dry-run is the default. Use --apply only after checking the source export and
inbound mapping. This script never edits the Marzban database.
"""
import argparse, json, os, re, sqlite3, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

def api(base, token, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept":"application/json", "Authorization":"Bearer "+token}
    if data is not None: headers["Content-Type"]="application/json"
    req=urllib.request.Request(base.rstrip("/") + path, data=data, headers=headers,
                               method="GET" if data is None else "POST")
    with urllib.request.urlopen(req, timeout=25) as res:
        raw=res.read().decode("utf-8")
    obj=json.loads(raw) if raw else {}
    if isinstance(obj,dict) and obj.get("success") is False:
        raise RuntimeError(str(obj.get("msg") or "3X-UI API rejected request"))
    return obj.get("obj",obj) if isinstance(obj,dict) else obj

def user_uuid(row):
    found=set()
    value=row.get("uuid")
    if isinstance(value,str) and value.strip(): found.add(value.strip())
    proxies=row.get("proxies") or {}
    if isinstance(proxies,dict):
        for config in proxies.values():
            if isinstance(config,dict):
                for key in ("id","uuid"):
                    v=config.get(key)
                    if isinstance(v,str) and v.strip(): found.add(v.strip())
    if len(found)!=1:
        raise ValueError("UUID missing or conflicting across protocols; refusing user: "+str(row.get("username")))
    return next(iter(found))

def enabled(row):
    status=str(row.get("status","active")).lower()
    return status not in ("disabled","inactive","limited","expired","on_hold","false","0")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--export",required=True,help="Read-only JSON export from the existing Marzban container")
    p.add_argument("--inbound-map",required=True,help='JSON object, e.g. {"vless":1,"vmess":2}')
    p.add_argument("--base-url",default=os.getenv("XUI_BASE_URL",""))
    p.add_argument("--api-token",default=os.getenv("XUI_API_TOKEN",""))
    p.add_argument("--map-db",default=os.getenv("POMPNET_SUB_MAP_DB","/var/lib/marzban/pompnet-sub-map.sqlite3"))
    p.add_argument("--apply",action="store_true",help="Actually create users and write token mappings; default is dry-run")
    args=p.parse_args()
    if not args.base_url or not args.api_token:
        p.error("Set --base-url and --api-token (or XUI_BASE_URL and XUI_API_TOKEN).")
    export=json.loads(Path(args.export).read_text(encoding="utf-8"))
    if export.get("format")!="pompnet-marzban-export-v1" or not isinstance(export.get("users"),list):
        raise SystemExit("Unsupported export format; no changes made.")
    inbound_map={str(k).lower():int(v) for k,v in json.loads(args.inbound_map).items()}
    existing=api(args.base_url,args.api_token,"/panel/api/clients/list") or []
    by_email={str(x.get("email","")):x for x in existing if isinstance(x,dict)}
    prepared=[]
    errors=[]
    for row in export["users"]:
        try:
            username=str(row.get("username","")).strip()
            token=str(row.get("token") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9_.@-]{2,64}",username): raise ValueError("invalid username")
            if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}",token): raise ValueError("legacy subscription token missing/invalid")
            proto_data=row.get("proxies") or {}
            protocols={str(k).lower() for k in proto_data} if isinstance(proto_data,dict) else set()
            protocols &= {"vless","vmess","trojan"}
            if not protocols: raise ValueError("no supported VLESS/VMess/Trojan proxy in export")
            missing=protocols-set(inbound_map)
            if missing: raise ValueError("missing inbound IDs for: "+",".join(sorted(missing)))
            uuid=user_uuid(row)
            expire=row.get("expire")
            if isinstance(expire,str):
                # Marzban exports ISO timestamps in some schema versions.
                from datetime import datetime
                expire=int(datetime.fromisoformat(expire.replace("Z","+00:00")).timestamp())
            expire_ms=int(expire or 0)*1000
            quota=int(row.get("data_limit") or 0)
            if quota<0: raise ValueError("negative data limit")
            ids=sorted({inbound_map[x] for x in protocols})
            client={"id":uuid,"email":username,"subId":token,"totalGB":quota,
                    "expiryTime":expire_ms,"enable":enabled(row),"tgId":0,
                    "limitIp":0,"limitHwid":0}
            old=by_email.get(username)
            if old:
                if str(old.get("id",""))!=uuid or str(old.get("subId",""))!=token:
                    raise ValueError("email already exists in 3X-UI with a different UUID/subId; manual review required")
                action="already-present"
            else: action="create"
            prepared.append((row,client,ids,action,token,username))
        except Exception as exc: errors.append({"username":row.get("username"),"error":str(exc)})
    print(json.dumps({"source_users":len(export["users"]),"prepared":len(prepared),
                      "errors":errors,"mode":"APPLY" if args.apply else "DRY-RUN",
                      "note":"Historical used_traffic is not imported by the 3X-UI client-add API; this tool does not fake it."},
                     ensure_ascii=False,indent=2))
    if errors: raise SystemExit("Preflight failed: no writes performed.")
    if not args.apply:
        print("Dry-run only. Re-run with --apply after reviewing the report.")
        return
    Path(args.map_db).parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(args.map_db,timeout=20)
    db.execute("CREATE TABLE IF NOT EXISTS legacy_sub_map (legacy_token TEXT PRIMARY KEY, xui_sub_id TEXT NOT NULL UNIQUE, username TEXT NOT NULL, migrated_at INTEGER NOT NULL)")
    try:
        for row,client,ids,action,token,username in prepared:
            if action=="create":
                api(args.base_url,args.api_token,"/panel/api/clients/add",{"client":client,"inboundIds":ids})
            db.execute("INSERT INTO legacy_sub_map(legacy_token,xui_sub_id,username,migrated_at) VALUES(?,?,?,?) ON CONFLICT(legacy_token) DO UPDATE SET xui_sub_id=excluded.xui_sub_id,username=excluded.username,migrated_at=excluded.migrated_at",
                       (token,token,username,int(time.time())))
            db.commit()
            print("MIGRATED",username,action,flush=True)
    finally: db.close()
    print("Import finished. Old Marzban users were not deleted or modified.")

if __name__=="__main__": main()
