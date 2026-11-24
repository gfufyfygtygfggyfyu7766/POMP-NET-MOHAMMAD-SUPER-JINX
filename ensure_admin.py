# Super JinX admin manager (runs on every start)
# Owner credentials are explicit deployment secrets; never generate an owner password.
# The internal support-bot account remains separately randomized.
import json, os, secrets, sys
from datetime import datetime, timezone
sys.path.insert(0, "/code")
ADMIN = "ADMIN_tanel9990"
DEFAULT_PW = os.environ.get("ADMIN_PASSWORD", "").strip()
ALLOW_INSECURE = os.environ.get("ALLOW_INSECURE_ADMIN_PASSWORD", "").strip().lower() in ("1", "true", "yes", "on")
if not DEFAULT_PW:
    print("[admin] FATAL: set ADMIN_PASSWORD in the deployment's private Variables/Secrets; owner passwords are never generated automatically.", flush=True)
    sys.exit(1)
if len(DEFAULT_PW) < 14 and not ALLOW_INSECURE:
    print("[admin] FATAL: ADMIN_PASSWORD must contain at least 14 characters.", flush=True)
    sys.exit(1)
FIRST_LOGIN_FILE = "/var/lib/marzban/.pompnet-first-login"
RESET_PASSWORD_FILE = "/var/lib/marzban/.pompnet-admin-reset-password"
DEFAULT_ADMIN_APPLIED = "/var/lib/marzban/.pompnet-default-admin-applied"
ADMIN_RECOVERY_MARKER = "/var/lib/marzban/.pompnet-admin-admin-recovery-v3"
SYSTEM = "jinx-system"
CRED = "/run/jinx/system.json"
RESET = (os.environ.get("RESET_ADMIN_PASSWORD", "").strip().lower() in ("1", "true", "yes", "on")
         or not os.path.exists(DEFAULT_ADMIN_APPLIED))

from passlib.context import CryptContext
from app.db import GetDB
from app.db.models import Admin
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def set_pw(a, password):
    a.hashed_password = pwd.hash(password)
    a.is_sudo = True
    if hasattr(a, "password_reset_at"):
        a.password_reset_at = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)

RESELLERS = set()
STORE_BROKEN = False
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
    owners = [a for a in panel_admins if a.username not in RESELLERS]
    sudo = [a for a in owners if a.is_sudo]
    if STORE_BROKEN:
        msg = "[admin] WARNING: reseller data unreadable -> admin roles left exactly as they are this start"
    elif not owners:
        if db.query(Admin).filter(Admin.username == ADMIN).first() is None:
            db.add(Admin(username=ADMIN, hashed_password=pwd.hash(DEFAULT_PW), is_sudo=True))
            try:
                fd = os.open(ADMIN_RECOVERY_MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as _f:
                    _f.write("completed\n")
                    _f.flush()
                    os.fsync(_f.fileno())
            except FileExistsError:
                pass
            msg = f"[admin] first install: explicit admin credentials configured for {ADMIN}"
        else:
            msg = "[admin] WARNING: only reseller admins exist and one is named 'admin'; rename it to recover"
    elif not os.path.exists(ADMIN_RECOVERY_MARKER):
        taken_by_reseller = any(x.username == ADMIN for x in panel_admins if x.username in RESELLERS)
        if taken_by_reseller:
            print("[admin] FATAL: username ADMIN_tanel9990 belongs to a reseller; rename that reseller before recovery", flush=True)
            sys.exit(1)
        a = next((x for x in owners if x.username == ADMIN), None) or (sudo or owners)[0]
        a.username = ADMIN
        set_pw(a, DEFAULT_PW)
        try:
            fd = os.open(ADMIN_RECOVERY_MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as _f:
                _f.write("completed\n")
                _f.flush()
                os.fsync(_f.fileno())
        except FileExistsError:
            pass
        msg = f"[admin] one-time recovery applied for {ADMIN}"
    elif RESET:
        a = next((x for x in owners if x.username == ADMIN), None) or (sudo or owners)[0]
        taken = any(x.username == ADMIN and x is not a for x in panel_admins)
        if not taken:
            a.username = ADMIN
        set_pw(a, DEFAULT_PW)
        msg = f"[admin] credentials rotated for {a.username}; remove RESET_ADMIN_PASSWORD after successful login"
    else:
        if not sudo:
            owners[0].is_sudo = True
        msg = "[admin] owner username/password preserved; set RESET_ADMIN_PASSWORD=1 for a one-time credential reset"
    sys_pw = secrets.token_urlsafe(24)
    s = db.query(Admin).filter(Admin.username == SYSTEM).first()
    if s is None:
        db.add(Admin(username=SYSTEM, hashed_password=pwd.hash(sys_pw), is_sudo=True))
    else:
        set_pw(s, sys_pw)
    db.commit()
    if not STORE_BROKEN:
        try:
            fd = os.open(DEFAULT_ADMIN_APPLIED, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as _f:
                _f.write(ADMIN + "\n")
                _f.flush()
                os.fsync(_f.fileno())
        except OSError as e:
            print(f"[admin] WARNING: could not save default-admin marker: {e}", flush=True)
    print(msg, flush=True)

os.makedirs("/run/jinx", exist_ok=True)
_tmp = CRED + ".tmp"
with open(_tmp, "w") as f:
    json.dump({"username": SYSTEM, "password": sys_pw}, f)
    f.flush()
    os.fsync(f.fileno())
os.chmod(_tmp, 0o600)
os.replace(_tmp, CRED)
print("[admin] support bots credentials ready", flush=True)
