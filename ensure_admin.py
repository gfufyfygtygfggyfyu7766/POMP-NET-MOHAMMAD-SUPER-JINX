# Super JinX admin manager (runs on every start)
#  - first install: uses ADMIN_PASSWORD or generates a strong one-time password
#  - generated first-login credentials are saved privately on the persistent data volume and printed once to deploy logs
#  - existing installations are migrated once, then preserve later password changes
#  - a marker on the persistent data volume prevents password changes on later restarts
#  - creates a hidden internal admin for the support bots (random password, rotated every start)
import json, os, secrets, sys
from datetime import datetime, timezone
sys.path.insert(0, "/code")
# Fixed owner login name: every fresh install and one-time recovery uses "admin".
# ADMIN_USERNAME is intentionally ignored so the panel username remains admin.
ADMIN = "admin"
# An explicit ADMIN_PASSWORD is honored; otherwise a strong one-time password is generated.
DEFAULT_PW = os.environ.get("ADMIN_PASSWORD", "").strip()
# Weak passwords are rejected unless the operator explicitly opts in for a controlled test or recovery.
ALLOW_INSECURE = os.environ.get("ALLOW_INSECURE_ADMIN_PASSWORD", "").strip().lower() in ("1", "true", "yes", "on")
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
        if len(DEFAULT_PW) < 14 and not ALLOW_INSECURE:
            print("[admin] FATAL: ADMIN_PASSWORD must contain at least 14 characters; set ALLOW_INSECURE_ADMIN_PASSWORD=1 only if you explicitly accept a weak password", flush=True)
            sys.exit(1)
        if db.query(Admin).filter(Admin.username == ADMIN).first() is None:
            db.add(Admin(username=ADMIN, hashed_password=pwd.hash(DEFAULT_PW), is_sudo=True))
            # Mark fresh installs as migrated immediately. Otherwise the next
            # restart would run legacy recovery and overwrite the owner's password.
            try:
                fd = os.open(ADMIN_RECOVERY_MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as _f:
                    _f.write("completed" + chr(10))
                    _f.flush()
                    os.fsync(_f.fileno())
            except FileExistsError:
                pass
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
            # Explicit ADMIN_PASSWORD values are not copied into a plaintext recovery file.
        else:                                                                  # 'admin' is a reseller's name
            msg = "[admin] WARNING: only reseller admins exist and one is named 'admin'; rename it to recover"
    elif not os.path.exists(ADMIN_RECOVERY_MARKER):
        # One-time recovery for existing installations. The marker prevents
        # normal restarts from overwriting a password changed by the owner.
        if len(ADMIN) < 3:
            print("[admin] FATAL: ADMIN_USERNAME must contain at least 3 characters", flush=True)
            sys.exit(1)
        taken_by_reseller = any(x.username == ADMIN for x in panel_admins if x.username in RESELLERS)
        if taken_by_reseller:
            print("[admin] FATAL: username admin belongs to a reseller; rename that reseller before recovery", flush=True)
            sys.exit(1)
        recovery_pw = DEFAULT_PW
        generated = False
        if not recovery_pw:
            try:
                with open(RESET_PASSWORD_FILE, encoding="utf-8") as _f:
                    recovery_pw = _f.read().strip()
            except OSError:
                recovery_pw = secrets.token_urlsafe(32)
                generated = True
                fd = os.open(RESET_PASSWORD_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as _f:
                    _f.write(recovery_pw)
                    _f.flush()
                    os.fsync(_f.fileno())
        if len(recovery_pw) < 14 and not ALLOW_INSECURE:
            print("[admin] FATAL: weak ADMIN_PASSWORD rejected; set ALLOW_INSECURE_ADMIN_PASSWORD=1 only if you explicitly accept this risk", flush=True)
            sys.exit(1)
        a = next((x for x in owners if x.username == ADMIN), None) or (sudo or owners)[0]
        a.username = ADMIN
        set_pw(a, recovery_pw)
        if generated:
            print(f"[admin] ONE-TIME LOGIN -> username: {ADMIN} | password: {recovery_pw}", flush=True)
        try:
            fd = os.open(ADMIN_RECOVERY_MARKER, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as _f:
                _f.write("completed" + chr(10))
                _f.flush()
                os.fsync(_f.fileno())
        except FileExistsError:
            pass
        msg = f"[admin] one-time recovery applied for {ADMIN}; remove RESET_ADMIN_PASSWORD after successful login if it was set"
    elif RESET:
        if len(ADMIN) < 3:
            print("[admin] FATAL: ADMIN_USERNAME must contain at least 3 characters", flush=True)
            sys.exit(1)
        # Set RESET_ADMIN_PASSWORD=1 to recover an existing owner account.
        # An explicit ADMIN_PASSWORD is honored; without one, a strong one-time
        # password is generated, persisted on the volume, and printed once.
        generated = False
        if not DEFAULT_PW:
            try:
                with open(RESET_PASSWORD_FILE, encoding="utf-8") as _f:
                    DEFAULT_PW = _f.read().strip()
            except OSError:
                DEFAULT_PW = secrets.token_urlsafe(32)
                generated = True
                os.makedirs(os.path.dirname(RESET_PASSWORD_FILE), exist_ok=True)
                try:
                    fd = os.open(RESET_PASSWORD_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(fd, "w", encoding="utf-8") as _f:
                        _f.write(DEFAULT_PW)
                        _f.flush()
                        os.fsync(_f.fileno())
                except FileExistsError:
                    with open(RESET_PASSWORD_FILE, encoding="utf-8") as _f:
                        DEFAULT_PW = _f.read().strip()
                    generated = False
        if len(DEFAULT_PW) < 14 and not ALLOW_INSECURE:
            print("[admin] FATAL: ADMIN_PASSWORD must contain at least 14 characters; set ALLOW_INSECURE_ADMIN_PASSWORD=1 only if you explicitly accept a weak password", flush=True)
            sys.exit(1)
        a = next((x for x in owners if x.username == ADMIN), None) or (sudo or owners)[0]
        taken = any(x.username == ADMIN and x is not a for x in panel_admins)   # 'admin' used by a reseller
        if not taken:
            a.username = ADMIN
        set_pw(a, DEFAULT_PW)
        if generated:
            print(f"[admin] ONE-TIME LOGIN -> username: {a.username} | password: {DEFAULT_PW}", flush=True)
        msg = (f"[admin] credentials rotated for {a.username}; remove RESET_ADMIN_PASSWORD after successful login")
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
    # Apply the repository default to an existing installation only once. The marker
    # lives beside the database, so normal restarts preserve any later password change.
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
    json.dump({"username": SYSTEM, "password": sys_pw}, f); f.flush(); os.fsync(f.fileno())
os.chmod(_tmp, 0o600)
os.replace(_tmp, CRED)
print("[admin] support bots credentials ready", flush=True)
