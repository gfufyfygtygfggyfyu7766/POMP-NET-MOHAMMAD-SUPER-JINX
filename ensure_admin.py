# Super JinX admin manager (runs on every start)
#  - first install: creates admin as admin; ADMIN_PASSWORD overrides the built-in first-deploy default
#  - generated first-login credentials are saved privately on the persistent data volume and printed once to deploy logs
#  - existing panel admins and passwords are preserved on normal restarts
#  - explicit reset: set RESET_ADMIN_PASSWORD=1 with new ADMIN_USERNAME and ADMIN_PASSWORD
#  - creates a hidden internal admin for the support bots (random password, rotated every start)
import json, os, secrets, sys
from datetime import datetime, timezone
sys.path.insert(0, "/code")
ADMIN = os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin"
DEFAULT_PW = os.environ.get("ADMIN_PASSWORD", "PnJ!7vQ#4mR@9xL2zK8$wT6c")
FIRST_LOGIN_FILE = "/var/lib/marzban/.pompnet-first-login"
SYSTEM = "jinx-system"
CRED = "/run/jinx/system.json"
RESET = os.environ.get("RESET_ADMIN_PASSWORD", "").strip().lower() in ("1", "true", "yes", "on")

from passlib.context import CryptContext
from app.db import GetDB
from app.db.models import Admin
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def set_pw(a, password):
    a.hashed_password = pwd.hash(password)
    a.is_sudo = True
    if hasattr(a, "password_reset_at"):
        a.password_reset_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)  # whole second: tokens issued right after stay valid

RESELLERS = set()                                   # reseller panels are never promoted / reset
STORE_BROKEN = False                                # reseller file exists but can't be read -> touch no roles at all
_seen = False
for _p in ("/var/lib/marzban/jinx_resellers.json", "/var/lib/marzban/jinx_resellers.json.bak"):
    if not os.path.exists(_p):
        continue
    _seen = True
    try:
        with open(_p, encoding="utf-8") as _f:
            _d = json.load(_f)
        if not isinstance(_d, dict):
            raise ValueError("bad format")
        RESELLERS = set(_d)
        break
    except Exception:
        continue
else:
    STORE_BROKEN = _seen

with GetDB() as db:
    panel_admins = [a for a in db.query(Admin).all() if a.username != SYSTEM]
    owners = [a for a in panel_admins if a.username not in RESELLERS]      # reseller panels are never promoted
    sudo = [a for a in owners if a.is_sudo]
    if STORE_BROKEN:
        msg = "[admin] WARNING: reseller data unreadable -> admin roles left exactly as they are this start"
    elif not owners:
        if len(ADMIN) < 3:
            print("[admin] FATAL: ADMIN_USERNAME must contain at least 3 characters", flush=True)
            sys.exit(1)
        # Generate a one-time password when the deployer has not supplied one.
        # Keep it on the persistent data volume so a database recovery can reuse it.
        generated = False
        if not DEFAULT_PW:
            try:
                with open(FIRST_LOGIN_FILE, encoding="utf-8") as _f:
                    DEFAULT_PW = _f.read().strip()
            except OSError:
                DEFAULT_PW = secrets.token_urlsafe(32)
                generated = True
        if len(DEFAULT_PW) < 14:
            print("[admin] FATAL: ADMIN_PASSWORD must contain at least 14 characters", flush=True)
            sys.exit(1)
        if db.query(Admin).filter(Admin.username == ADMIN).first() is None:
            db.add(Admin(username=ADMIN, hashed_password=pwd.hash(DEFAULT_PW), is_sudo=True))
            msg = f"[admin] first install: secure admin created for {ADMIN}"
            if generated:
                try:
                    fd = os.open(FIRST_LOGIN_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "w", encoding="utf-8") as _f:
                        _f.write(DEFAULT_PW)
                        _f.flush()
                        os.fsync(_f.fileno())
                except FileExistsError:
                    pass
                print(f"[admin] ONE-TIME LOGIN -> username: {ADMIN} | password: {DEFAULT_PW}", flush=True)
            elif not os.path.exists(FIRST_LOGIN_FILE):
                fd = os.open(FIRST_LOGIN_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as _f:
                    _f.write(DEFAULT_PW)
                    _f.flush()
                    os.fsync(_f.fileno())
        else:                                                                  # 'admin' is a reseller's name
            msg = "[admin] WARNING: only reseller admins exist and one is named 'admin'; rename it to recover"
    elif RESET:
        if len(ADMIN) < 3 or len(DEFAULT_PW) < 14:
            print("[admin] FATAL: password reset requires ADMIN_USERNAME (3+ chars) and ADMIN_PASSWORD (14+ chars)", flush=True)
            sys.exit(1)
        a = next((x for x in owners if x.username == ADMIN), None) or (sudo or owners)[0]
        taken = any(x.username == ADMIN and x is not a for x in panel_admins)   # 'admin' used by a reseller
        if not taken:
            a.username = ADMIN
        set_pw(a, DEFAULT_PW)
        msg = (f"[admin] RESET_ADMIN_PASSWORD -> credentials rotated for {a.username} (remove reset variable now)")
    else:
        if not sudo:
            owners[0].is_sudo = True
        msg = "[admin] your admin username/password kept (change them any time from the panel menu)"
    sys_pw = secrets.token_urlsafe(24)
    s = db.query(Admin).filter(Admin.username == SYSTEM).first()
    if s is None:
        db.add(Admin(username=SYSTEM, hashed_password=pwd.hash(sys_pw), is_sudo=True))
    else:
        set_pw(s, sys_pw)
    db.commit()
    print(msg, flush=True)

os.makedirs("/run/jinx", exist_ok=True)
_tmp = CRED + ".tmp"
with open(_tmp, "w") as f:
    json.dump({"username": SYSTEM, "password": sys_pw}, f); f.flush(); os.fsync(f.fileno())
os.chmod(_tmp, 0o600)
os.replace(_tmp, CRED)
print("[admin] support bots credentials ready", flush=True)
