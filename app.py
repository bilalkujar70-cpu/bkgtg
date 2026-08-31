# -*- coding: utf-8 -*-
import os, sys, json, time, logging, random, warnings, asyncio, subprocess, re, threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def auto_install():
    for p in ["requests", "pycryptodome", "cryptography", "protobuf", "python-telegram-bot"]:
        try:
            __import__(p.replace("-", "_"))
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", p, "--quiet"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
auto_install()

import requests as rq
import urllib3
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives.ciphers import Cipher as Cp, algorithms as Al, modes as Md
from cryptography.hazmat.backends import default_backend as Bk
from google.protobuf.internal.decoder import _DecodeVarint32
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

urllib3.disable_warnings()
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════
BOT_TOKEN = "8731286183:AAEq5mVMBmkVtTuUeMr7iGStN2G6et_r6-A"
DEVELOPER = "@c1me_99111"
ADMINS = [7270942727, 7458823107, 5854363025]
SUPER_ADMIN = 7458823107  # ← الآدمن الرئيسي المخول بعمليات التقسيم وعرض الأخطاء
MAX_PER_MAP = 999999999
FREE_POINTS = 300
ACCOUNTS_FILE = "acc.json"
FAILED_ACCOUNTS_FILE = "da.json"
accounts_file_lock = threading.Lock()
DATA_FILE = "bot_data.json"
WORKER_THREADS = 20
DEFAULT_CODE_MAX_REDEEM = 10

K = b"Yg&tc%DEuh6%Zc^8"
IV = b"6oyZDr22E3ychjM%"

REGION_LANG = {"ME":"ar","IND":"hi","ID":"id","VN":"vi","TH":"th","BD":"bn","PK":"ur","TW":"zh","CIS":"ru","SAC":"es","BR":"pt","SG":"en"}
REGION_URLS = {"IND":"https://client.ind.freefiremobile.com","ID":"https://clientbp.ggblueshark.com","BR":"https://client.us.freefiremobile.com","ME":"https://clientbp.ggpolarbear.com","VN":"https://clientbp.ggblueshark.com","TH":"https://clientbp.common.ggbluefox.com","CIS":"https://clientbp.ggblueshark.com","BD":"https://clientbp.ggpolarbear.com","PK":"https://clientbp.ggblueshark.com","SG":"https://clientbp.ggblueshark.com","SAC":"https://client.us.freefiremobile.com","TW":"https://clientbp.ggblueshark.com"}
REGION_FLAGS = {"ME":"\U0001f1f8\U0001f1e6","IND":"\U0001f1ee\U0001f1f3","ID":"\U0001f1ee\U0001f1e9","VN":"\U0001f1fb\U0001f1f3","TH":"\U0001f1f9\U0001f1ed","BD":"\U0001f1e7\U0001f1e9","PK":"\U0001f1f5\U0001f1f0","TW":"\U0001f1f9\U0001f1fc","CIS":"\U0001f1f7\U0001f1fa","SAC":"\U0001f1e7\U0001f1f7","BR":"\U0001f1e7\U0001f1f7","SG":"\U0001f1f8\U0001f1ec"}

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ═══════════════════════════════════════
#  Helpers / Cleaners
# ═══════════════════════════════════════
def escape_html(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ═══════════════════════════════════════
#  AES / Protobuf
# ═══════════════════════════════════════
def aes_enc(data):
    if isinstance(data, str): data = data.encode()
    return AES.new(K, AES.MODE_CBC, IV).encrypt(pad(data, 16))

def aes_dec(data):
    try: return unpad(AES.new(K, AES.MODE_CBC, IV).decrypt(data), 16)
    except: return data

def write_varint(val):
    res = b''; val = int(val)
    while True:
        byte = val & 0x7F; val >>= 7
        if val: res += bytes([byte | 0x80])
        else: res += bytes([byte]); break
    return res

def pbD(data):
    i, out = 0, {}
    while i < len(data):
        try: key, i = _DecodeVarint32(data, i)
        except: break
        fn, wt = key >> 3, key & 0x7
        if wt == 0:
            v, i = _DecodeVarint32(data, i); out[str(fn)] = {"t": "int", "v": v}
        elif wt == 2:
            ln, i = _DecodeVarint32(data, i); v = data[i:i+ln]; i += ln
            try: out[str(fn)] = {"t": "str", "v": v.decode()}
            except: out[str(fn)] = {"t": "hex", "v": v.hex()}
        elif wt == 1: out[str(fn)] = {"t": "64b", "v": data[i:i+8].hex()}; i += 8
        elif wt == 5: out[str(fn)] = {"t": "32b", "v": data[i:i+4].hex()}; i += 4
        else: break
    return out

def random_ua():
    return random.choice([
        "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
        "GarenaMSDK/4.0.18P6(SM-A125F ;Android 11;en;IN;)",
        "GarenaMSDK/4.1.0P3(Redmi 9A ;Android 10;en;ID;)",
    ])

def build_major_pro(oid, tok, uid, plat):
    p = b''
    ts = str(datetime.now())[:-7].encode()
    p += b'\x1a' + write_varint(len(ts)) + ts
    p += b'\x22\x09\x66\x72\x65\x65\x20\x66\x69\x72\x65'
    v = b"1.123.2"
    p += b'2' + write_varint(len(v)) + v
    u_b = str(uid).encode()
    p += b'\x9a\x01' + write_varint(len(u_b)) + u_b
    o_b = str(oid).encode()
    p += b'\xb2\x01' + write_varint(len(o_b)) + o_b
    pl_s = str(plat).encode()
    p += b'\xba\x01' + write_varint(len(pl_s)) + pl_s
    t_b = str(tok).encode()
    p += b'\xea\x01' + write_varint(len(t_b)) + t_b
    p += b'\xb0\x04\x04'
    chk = b"e89b158e4bcf988ebd09eb83f5378e87"
    p += b'\xc2\x03' + write_varint(len(chk)) + chk
    p += b'\x9a\x06' + write_varint(len(pl_s)) + pl_s
    p += b'\xa2\x06' + write_varint(len(pl_s)) + pl_s
    return p

# ═══════════════════════════════════════
#  Data Management
# ═══════════════════════════════════════
data_lock = threading.Lock()

def load_data():
    with data_lock:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f: return json.load(f)
            except: pass
    return {"users": {}, "codes": {}, "maps": {}, "queue_id": 0, "tokens": {}}

def save_data(data):
    with data_lock:
        try:
            with open(DATA_FILE, "w") as f: json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error("Save error: %s", e)

def get_user(data, chat_id):
    cid = str(chat_id)
    if cid not in data["users"]:
        data["users"][cid] = {"name": "", "username": "", "points": 0, "total_likes": 0, "total_subs": 0, "redeemed": []}
    if "redeemed" not in data["users"][cid]:
         data["users"][cid]["redeemed"] = []
    return data["users"][cid]

def clean_code(raw):
    c = raw.strip().upper()
    if c.startswith("#"):
        c = c[1:]
    return c.strip()

# ═══════════════════════════════════════
#  Token Cache (حفظ التوكنات لتفادي حظر 429)
# ═══════════════════════════════════════
def get_cached_jwt(uid):
    data = load_data()
    tokens = data.setdefault("tokens", {})
    if uid in tokens:
        t = tokens[uid]
        exp_ts = t.get("exp", 0)
        if time.time() < exp_ts:
            return t.get("jwt"), t.get("dyn")
    return None, None

def set_cached_jwt(uid, jwt, dyn):
    data = load_data()
    tokens = data.setdefault("tokens", {})
    tokens[uid] = {
        "jwt": jwt,
        "dyn": dyn,
        "exp": time.time() + 43200  # الحفظ لمدة 12 ساعة كاملة
    }
    save_data(data)

def clear_cached_jwt(uid):
    data = load_data()
    tokens = data.setdefault("tokens", {})
    tokens.pop(uid, None)
    save_data(data)

# ═══════════════════════════════════════
#  Accounts Sharding / Rotating Loader (المداورة التلقائية الدائرية لمنع التكرار والحظر)
# ═══════════════════════════════════════
_accounts_cache = []
_accounts_loaded = False

def normalize_account_record(item):
    """Read the user's acc.json schema without rewriting the original record."""
    if not isinstance(item, dict):
        return None
    uid = item.get("uid")
    password = item.get("password") or item.get("pass")
    if uid is None or not password:
        return None
    return {"u": str(uid), "p": str(password), "record": item}

def load_accounts():
    global _accounts_cache, _accounts_loaded
    if _accounts_loaded: return _accounts_cache
    if not os.path.exists(ACCOUNTS_FILE):
        log.error("Accounts file NOT FOUND: %s (cwd: %s)", ACCOUNTS_FILE, os.getcwd())
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f: raw = json.load(f)
    except Exception as e:
        log.error("Accounts file read error: %s", e)
        return []
    accs = []
    for item in raw:
        u = item.get("uid")
        p = item.get("password") or item.get("pass")
        if u and p:
            accs.append({"u": str(u), "p": str(p)})
    _accounts_cache = accs
    _accounts_loaded = True
    log.info("Loaded %d accounts from %s", len(accs), ACCOUNTS_FILE)
    return accs

def load_raw_accounts_file():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, list) else []
    except Exception as e:
        log.error("Accounts file read error: %s", e)
        return []

def save_raw_accounts_file(accounts):
    tmp = ACCOUNTS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ACCOUNTS_FILE)

def move_failed_accounts_to_da(failed_accounts):
    if not failed_accounts:
        return
    with accounts_file_lock:
        failed = []
        if os.path.exists(FAILED_ACCOUNTS_FILE):
            try:
                with open(FAILED_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    failed = json.load(f)
                if not isinstance(failed, list): failed = []
            except Exception: failed = []
        failed.extend(failed_accounts)
        tmp = FAILED_ACCOUNTS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        os.replace(tmp, FAILED_ACCOUNTS_FILE)

def consume_successful_accounts(successful_uids):
    if not successful_uids:
        return
    ids = {str(x) for x in successful_uids}
    with accounts_file_lock:
        accounts = load_raw_accounts_file()
        remaining = [a for a in accounts if str(a.get("uid")) not in ids]
        save_raw_accounts_file(remaining)
    reload_accounts()

def reload_accounts():
    global _accounts_cache, _accounts_loaded
    _accounts_cache = []
    _accounts_loaded = False
    return load_accounts()

# جلب الحسابات المطلوبة فقط برمجياً من الملفات المقسمة بالتناوب
def load_accounts_for_job(needed_count):
    data = load_data()
    shards_config = data.get("shards_config")
    
    # في حال لم يتم تفعيل التقسيم بعد، يتم الاعتماد على الملف الأصلي كاحتياط
    if not shards_config:
        return load_accounts()[:needed_count]
        
    folder = shards_config.get("folder")
    total_files = shards_config.get("total_files", 0)
    current_file_idx = shards_config.get("current_file_idx", 1)
    
    loaded_accs = []
    files_processed = 0
    
    # الاستمرار بالتحميل حتى نلبي العدد المطلوب أو نمر على جميع الملفات بالكامل
    while len(loaded_accs) < needed_count and files_processed < total_files:
        file_path = os.path.join(folder, f"{current_file_idx}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    chunk = json.load(f)
                    for item in chunk:
                        u = item.get("uid")
                        p = item.get("password") or item.get("pass")
                        if u and p:
                            loaded_accs.append({"u": str(u), "p": str(p)})
            except Exception as e:
                log.error("Error reading shard file %s: %s", file_path, e)
        
        # الانتقال الدائري للمجلد التالي برمجياً
        current_file_idx += 1
        if current_file_idx > total_files:
            current_file_idx = 1
            
        files_processed += 1
        
    # حفظ الإشارة إلى الملف القادم لضمان عدم التكرار في العمليات القادمة
    shards_config["current_file_idx"] = current_file_idx
    save_data(data)
    
    return loaded_accs[:needed_count]

# ═══════════════════════════════════════
#  API
# ═══════════════════════════════════════
def get_garena_token(uid, password):
    r = rq.post("https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant",
        headers={"Host":"ffmconnect.live.gop.garenanow.com","User-Agent":random_ua(),"Content-Type":"application/x-www-form-urlencoded","Connection":"close"},
        data={"uid":uid,"password":password,"response_type":"token","client_type":"2",
              "client_secret":"2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_id":"100067"},
        verify=False, timeout=15)
    if r.status_code != 200: raise Exception("garena " + str(r.status_code))
    d = r.json()
    return d["access_token"], d["open_id"], d.get("platform", 4)

def get_jwt(access_token, open_id, uid, platform):
    payload = build_major_pro(open_id, access_token, uid, platform)
    h = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; V2026 Build/SP1A.210812.003)",
        "X-GA": "v1 1",
        "Releaseversion": "OB54",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue"
    }
    r = rq.post("https://loginbp.ggpolarbear.com/MajorLogin", data=aes_enc(payload), headers=h, verify=False, timeout=20)
    if r.status_code != 200: raise Exception("login " + str(r.status_code))
    dec = aes_dec(r.content); pb = pbD(dec)
    jwt = pb.get("8",{}).get("v","")
    dyn = pb.get("10",{}).get("v","")
    if not jwt: raise Exception("no jwt")
    
    if isinstance(jwt, bytes): jwt = jwt.decode(errors='ignore')
    if isinstance(dyn, bytes): dyn = dyn.decode(errors='ignore')
    return jwt.strip(), dyn.strip("/")

def api_request(jwt, dyn_url, region_key, action, map_code):
    base = dyn_url or REGION_URLS.get(region_key, REGION_URLS["ME"])
    lang = REGION_LANG.get(region_key, "en")
    if action == "subscribe":
        url = base + "/SubscribeWorkshopCode"
        m_b = map_code.encode(); l_b = lang.encode()
        game_pb = b"\x08\x01\x12" + write_varint(len(m_b)) + m_b + b"\x22" + write_varint(len(l_b)) + l_b
    else:
        url = base + "/SendWorkshopLike"
        m_b = map_code.encode()
        game_pb = b"\x0a" + write_varint(len(m_b)) + m_b + b"\x12\x01\x14\x18\x06"
    h = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; V2026 Build/SP1A.210812.003)",
        "X-GA": "v1 1",
        "Releaseversion": "OB54",
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue",
        "Authorization": "Bearer " + jwt
    }
    r = rq.post(url, data=aes_enc(game_pb), headers=h, verify=False, timeout=10)
    if r.status_code in [401, 403]:
        raise Exception("TOKEN_EXPIRED_OR_UNAUTHORIZED")
    if not (200 <= r.status_code < 300):
        raise Exception(f"API_HTTP_{r.status_code}")
    return True

def execute_one(acc, region_key, action, map_code, force_refresh=False):
    uid = acc["u"]
    jwt = None
    dyn = None
    if not force_refresh:
        jwt, dyn = get_cached_jwt(uid)
    
    if not jwt or not dyn:
        at, oid, plat = get_garena_token(acc["u"], acc["p"])
        jwt, dyn = get_jwt(at, oid, acc["u"], plat)
        set_cached_jwt(uid, jwt, dyn)
        
    return api_request(jwt, dyn, region_key, action, map_code)

def execute_with_retry(acc, region_key, action, map_code, max_retry=3):
    uid = acc["u"]
    force_refresh = False
    last_err = "خطأ غير معروف"
    for attempt in range(max_retry):
        try:
            res = execute_one(acc, region_key, action, map_code, force_refresh=force_refresh)
            if res:
                return True, ""
            else:
                last_err = "طلب API أعاد نتيجة False (الحساب قد يكون محظوراً أو الخريطة غير متوفرة في هذه المنطقة)"
        except Exception as e:
            err_str = str(e)
            last_err = err_str
            log.warning("Account %s attempt %d failed: %s", uid[:6], attempt + 1, err_str[:80])
            if "TOKEN_EXPIRED_OR_UNAUTHORIZED" in err_str or "login" in err_str or "garena" in err_str:
                clear_cached_jwt(uid)
                force_refresh = True
    return False, last_err

# ═══════════════════════════════════════
#  Queue System
# ═══════════════════════════════════════
task_queue = []
queue_id_counter = 0
queue_counter_lock = threading.Lock()
processing_lock = threading.Lock()
is_processing = False
bot_app = None
cancel_flags = {}
processing_done_count = {}

def add_to_queue(chat_id, action, region, map_code, count, message_id):
    global queue_id_counter
    with queue_counter_lock:
        queue_id_counter += 1
        qid = queue_id_counter
    task_queue.append({
        "qid": qid, "chat_id": chat_id, "action": action,
        "region": region, "map_code": map_code, "count": count,
        "message_id": message_id, "cancelled": False
    })
    return qid

def remove_from_queue(chat_id):
    for i, t in enumerate(task_queue):
        if t["chat_id"] == chat_id:
            task_queue[i]["cancelled"] = True
            task_queue.pop(i)
            return True
    return False

def user_in_queue(chat_id):
    for t in task_queue:
        if t["chat_id"] == chat_id: return True
    if is_processing and process_current.get("chat_id") == chat_id:
        return True
    return False

process_current = {}

def get_queue_position(chat_id):
    for i, t in enumerate(task_queue):
        if t["chat_id"] == chat_id: return i + 1
    return 0

# ═══════════════════════════════════════
#  User States
# ═══════════════════════════════════════
user_states = {}

def set_state(chat_id, step, extra=None):
    user_states[chat_id] = {"step": step, "data": extra or {}}

def get_state(chat_id):
    return user_states.get(chat_id)

def clear_state(chat_id):
    user_states.pop(chat_id, None)

# ═══════════════════════════════════════
#  Telegram Helpers
# ═══════════════════════════════════════
def make_btn(text, data):
    return InlineKeyboardButton(text, callback_data=data)

def make_menu(text, buttons):
    rows = []
    for row in buttons:
        rows.append([make_btn(t, d) for t, d in row])
    return InlineKeyboardMarkup(rows)

# ═══════════════════════════════════════
#  Main Menu
# ═══════════════════════════════════════
def build_main_menu(user_data):
    pts = user_data.get("points", 0)
    text = (
        " مرحبا!\n\n"
        " الاسم: " + (escape_html(user_data.get("name")) or "غير معروف") + "\n"
        " المعرف: " + ("@" + user_data.get("username") if user_data.get("username") else "لا يوجد") + "\n"
        " النقاط: <b>" + str(pts) + "</b>\n\n"
        "1  = 1 نقطة | 1  = 1 نقطة"
    )
    btns = [
        [("️ اضافة اعجابات", "do_like"), (" اضافة اشتراكات", "do_sub")],
        [(" استبدال كود", "redeem"), (" احصائياتي", "mystats")],
    ]
    return text, make_menu(text, btns)

async def send_main_menu(update_or_chat, ctx=None, user_data=None):
    data = load_data()
    uid = 0
    if hasattr(update_or_chat, 'effective_chat'):
        uid = update_or_chat.effective_user.id
        chat_id = update_or_chat.effective_chat.id
    else:
        chat_id = update_or_chat
        uid = update_or_chat
    if not user_data:
        user_data = get_user(data, uid)
    text, markup = build_main_menu(user_data)
    if ctx:
        await ctx.bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    else:
        await update_or_chat.reply_text(text, reply_markup=markup, parse_mode="HTML")

# ═══════════════════════════════════════
#  /start
# ═══════════════════════════════════════
async def start_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = load_data()
    udata = get_user(data, user.id)
    first = udata.get("points", 0) == 0 and udata.get("total_likes", 0) == 0 and udata.get("total_subs", 0) == 0
    udata["name"] = user.first_name or ""
    udata["username"] = user.username or ""
    if first:
        udata["points"] = FREE_POINTS
    save_data(data)
    clear_state(user.id)
    text, markup = build_main_menu(udata)
    extra = ""
    if first:
        extra = "\n\n لقد حصلت على <b>" + str(FREE_POINTS) + "</b> نقطة مجانا!"
    await update.message.reply_text(text + extra, reply_markup=markup, parse_mode="HTML")

# ═══════════════════════════════════════
#  Admin
# ═══════════════════════════════════════
def is_admin(uid):
    return uid in ADMINS

def build_admin_panel_text():
    return (
        "️ <b>لوحة المشرف</b>\n\n"
        " التعليمات:\n"
        "-  اضافة كود: انشئ كود استبدال بالنقاط للمستخدمين\n"
        "- ️ حذف كود: احذف كود موجود من القائمة\n"
        "-  عرض الاكواد: عرض جميع الاكواد الموجودة\n"
        "-  اعادة تحميل الحسابات: تحميل ملف الحسابات من جديد"
    )

def build_admin_panel_btns(uid):
    btns = [
        [(" اضافة كود", "admin_add"), ("️ حذف كود", "admin_del")],
        [(" عرض الاكواد", "admin_show_codes"), (" اعادة تحميل الحسابات", "admin_reload_acc")],
    ]
    # زر التقسيم الحصري للأدمن الخارق فقط
    if uid == SUPER_ADMIN:
        btns.append([(" تقسيم الحسابات", "super_split_init")])
    btns.append([(" رجوع", "back_main")])
    return btns

async def admin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text(" ليس لديك صلاحية.")
        return
    text = build_admin_panel_text()
    btns = build_admin_panel_btns(uid)
    await update.message.reply_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")

# ═══════════════════════════════════════
#  Callback Handler
# ═══════════════════════════════════════
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    uid = q.from_user.id
    chat_id = q.message.chat_id

    # ─── MAIN MENU BUTTONS ───
    if d == "do_like":
        set_state(chat_id, "spend_amount", {"action": "like"})
        text = " <b>اضافة اعجابات</b>\n\n1 نقطة = 1 \n اكتب عدد النقاط التي تريد صرفها:"
        await q.edit_message_text(text, parse_mode="HTML")
        return

    if d == "do_sub":
        set_state(chat_id, "spend_amount", {"action": "subscribe"})
        text = " <b>اضافة اشتراكات</b>\n\n1 نقطة = 1 \n اكتب عدد النقاط التي تريد صرفها:"
        await q.edit_message_text(text, parse_mode="HTML")
        return

    if d == "redeem":
        set_state(chat_id, "redeem_input")
        await q.edit_message_text(" <b>استبدال كود</b>\n\n اكتب الكود:", parse_mode="HTML")
        return

    if d == "mystats":
        data = load_data()
        udata = get_user(data, uid)
        text = (
            " <b>احصائيات حسابك</b>\n\n"
            " الاسم: " + (escape_html(udata.get("name")) or "-") + "\n"
            " المعرف: " + ("@" + udata.get("username") if udata.get("username") else "-") + "\n"
            " النقاط المتبقية: <b>" + str(udata.get("points", 0)) + "</b>\n"
            " اجمالي الاعجابات: <b>" + str(udata.get("total_likes", 0)) + "</b>\n"
            " اجمالي الاشتراكات: <b>" + str(udata.get("total_subs", 0)) + "</b>"
        )
        btns = [[(" رجوع", "back_main")]]
        await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        return

    if d == "back_main":
        clear_state(chat_id)
        data = load_data()
        udata = get_user(data, uid)
        text, markup = build_main_menu(udata)
        try: await q.edit_message_text(text, reply_markup=markup, parse_mode="HTML")
        except: pass
        return

    # ─── ADMIN PANEL (from callback) ───
    if d == "admin_panel_cb":
        text = build_admin_panel_text()
        btns = build_admin_panel_btns(uid)
        try: await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        except: pass
        return

    # ─── ADMIN: ADD CODE ───
    if d == "admin_add":
        text = " هل تريد اضافة كود؟"
        btns = [[(" نعم", "admin_add_yes"), (" لا", "admin_panel_cb")]]
        await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        return

    if d == "admin_add_yes":
        set_state(chat_id, "admin_code_input")
        await q.edit_message_text(" اكتب الكود الجديد:", parse_mode="HTML")
        return

    if d == "admin_del":
        set_state(chat_id, "admin_del_code")
        await q.edit_message_text("️ يرجى إدخال الكود المراد حذفه:", parse_mode="HTML")
        return

    # ─── SUPER ADMIN: INITIALIZE SHARDS SPLIT (تقسيم الحسابات حصرياً للآدمن الرئيسي) ───
    if d == "super_split_init":
        if uid != SUPER_ADMIN:
            await q.answer(" عذراً، هذا الأمر متاح للمشرف الرئيسي فقط.", show_alert=True)
            return
        set_state(chat_id, "super_split_folder")
        await q.edit_message_text(
            " <b>تقسيم الحسابات ومقاومة الحظر</b>\n\n"
            "يرجى إرسال <b>اسم المجلد الجديد</b> الذي ترغب بإنشائه لحفظ الملفات المقسمة (مثال: <code>accounts_shards</code>):",
            parse_mode="HTML"
        )
        return

    # ─── ADMIN: SHOW ALL CODES ───
    if d == "admin_show_codes":
        data = load_data()
        codes = data.get("codes", {})
        if not codes:
            text = " <b>جميع الأكواد</b>\n\nلا توجد أكواد حالياً."
            btns = [[(" رجوع", "admin_panel_cb")]]
            await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
            return

        lines = [" <b>جميع الأكواد النشطة</b>\n"]
        for code, info in codes.items():
            if isinstance(info, dict):
                pts = info.get("points", 0)
                max_r = info.get("max_redeem", DEFAULT_CODE_MAX_REDEEM)
                used = info.get("used", 0)
                unlimited = info.get("unlimited", False)
                limit_str = "∞ بلا حدود" if unlimited else (str(max_r) + " شخص")
                lines.append(
                    "──────────────────\n"
                    " الكود: <code>" + str(code) + "</code>\n"
                    " النقاط: <b>" + str(pts) + "</b>\n"
                    " الحد الأقصى: " + limit_str + "\n"
                    " تم الاستبدال: <b>" + str(used) + "</b> / " + (str(max_r) if not unlimited else "∞")
                )
            else:
                lines.append(
                    "──────────────────\n"
                    " الكود: <code>" + str(code) + "</code>\n"
                    " النقاط: <b>" + str(info) + "</b>\n"
                    " الحد الأقصى: " + str(DEFAULT_CODE_MAX_REDEEM) + " شخص\n"
                    " تم الاستبدال: <b>0</b>"
                )
        text = "\n".join(lines)
        btns = [[(" رجوع", "admin_panel_cb")]]
        await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        return

    # ─── ADMIN: RELOAD ACCOUNTS ───
    if d == "admin_reload_acc":
        data = load_data()
        shards_config = data.get("shards_config")
        if shards_config:
            folder = shards_config.get("folder")
            total_files = shards_config.get("total_files", 0)
            total_accs = 0
            for i in range(1, total_files + 1):
                p = os.path.join(folder, f"{i}.json")
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8") as f:
                            total_accs += len(json.load(f))
                    except: pass
            text = f" تم إعادة تحميل الحسابات المقسمة!\n\n- المجلد: <code>{folder}</code>\n- عدد الملفات: <b>{total_files}</b>\n- إجمالي الحسابات: <b>{total_accs}</b>"
        else:
            count = reload_accounts()
            text = " تم اعادة تحميل الحسابات!\n\nعدد الحسابات المتاحة: <b>" + str(len(count)) + "</b>"
            
        btns = [[(" رجوع", "admin_panel_cb")]]
        await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        return

    if d == "admin_del_yes":
        st = get_state(chat_id)
        if not st: return
        code = st["data"].get("del_code", "")
        data = load_data()
        if code in data.get("codes", {}):
            del data["codes"][code]
            save_data(data)
            await q.edit_message_text(" تم حذف الكود: <code>" + code + "</code>", parse_mode="HTML",
                reply_markup=make_menu("", [[(" رجوع", "admin_panel_cb")]]))
        else:
            await q.edit_message_text(" الكود غير موجود.", parse_mode="HTML",
                reply_markup=make_menu("", [[(" رجوع", "admin_panel_cb")]]))
        clear_state(chat_id)
        return

    if d == "admin_del_no":
        clear_state(chat_id)
        text = build_admin_panel_text()
        btns = build_admin_panel_btns(uid)
        await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        return

    # ─── REGION BUTTONS ───
    if d.startswith("reg_"):
        region = d[4:]
        st = get_state(chat_id)
        if not st: return
        st["data"]["region"] = region
        st["step"] = "spend_map"
        flag = REGION_FLAGS.get(region, "")
        text = flag + " المنطقة: <b>" + region + "</b>\n\n اكتب كود الخريطة:"
        await q.edit_message_text(text, parse_mode="HTML")
        return

    # ─── CANCEL QUEUE (before processing) ───
    if d == "cancel_queue":
        if remove_from_queue(chat_id):
            data = load_data()
            udata = get_user(data, chat_id)
            st = get_state(chat_id)
            refund = 0
            if st:
                refund = st["data"].get("pending_points", 0)
            if refund > 0:
                udata["points"] = udata.get("points", 0) + refund
                save_data(data)
            clear_state(chat_id)
            text = " تم الغاء الطلب واعادة <b>" + str(refund) + "</b> نقطة لرصيدك."
            btns = [[(" رجوع للقائمة", "back_main")]]
            try: await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
            except: pass
        else:
            try: await q.answer(" لا يوجد طلب للالغاء في الانتظار حالياً", show_alert=True)
            except: pass
        return

    # ─── CANCEL PROCESS (confirmation during processing) ───
    if d == "cancel_process_ask":
        text = (
            "️ <b>هل انت متاكد من الغاء العمليه؟</b>\n\n"
            "سيتم إيقاف الإرسال فوراً وإعادة النقاط للكميات التي لم تُرسل بعد."
        )
        btns = [[(" نعم، الغاء", "cancel_process_yes"), (" لا، استمرار", "cancel_process_no")]]
        try: await q.edit_message_text(text, reply_markup=make_menu(text, btns), parse_mode="HTML")
        except: pass
        return

    if d == "cancel_process_yes":
        cancel_flags[chat_id] = True
        try: await q.answer(" جاري الغاء العملية...", show_alert=True)
        except: pass
        return

    if d == "cancel_process_no":
        try: await q.answer(" سيتم الاستمرار في العملية.", show_alert=True)
        except: pass
        return


# ═══════════════════════════════════════
#  Message Handler
# ═══════════════════════════════════════
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    st = get_state(chat_id)
    if not st: return

    step = st["step"]

    # ─── SUPER ADMIN: SHARDS FOLDER INPUT ───
    if step == "super_split_folder":
        folder_name = "".join([c for c in text if c.isalnum() or c in ["_", "-"]]).strip()
        if not folder_name:
            await update.message.reply_text(" اسم مجلد غير صالح. يرجى إرسال اسم يحتوي على أحرف وأرقام فقط:")
            return
        st["data"]["folder_name"] = folder_name
        st["step"] = "super_split_size"
        await update.message.reply_text(
            f" تم تحديد اسم المجلد: <code>{folder_name}</code>\n\n"
            f" أرسل الآن عدد الحسابات المطلوب وضعها في كل ملف (مثال: 100):",
            parse_mode="HTML"
        )
        return

    # ─── SUPER ADMIN: SHARDS CHUNK SIZE INPUT ───
    if step == "super_split_size":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text(" يرجى إرسال عدد صحيح أكبر من الصفر:")
            return
        split_size = int(text)
        folder_name = st["data"].get("folder_name")
        
        # التأكد من وجود ملف الحسابات الأصلي بالاستضافة
        if not os.path.exists(ACCOUNTS_FILE):
            clear_state(chat_id)
            await update.message.reply_text(
                f" لم يتم العثور على الملف الرئيسي <code>{ACCOUNTS_FILE}</code> بالاستضافة!\n"
                f"يرجى رفعه أولاً ثم إعادة المحاولة.",
                parse_mode="HTML"
            )
            return
            
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                raw_accounts = json.load(f)
        except Exception as e:
            clear_state(chat_id)
            await update.message.reply_text(f" خطأ أثناء قراءة ملف الحسابات: <code>{str(e)}</code>", parse_mode="HTML")
            return
            
        if not isinstance(raw_accounts, list) or len(raw_accounts) == 0:
            clear_state(chat_id)
            await update.message.reply_text(" ملف acc.json فارغ أو ليس بتنسيق قائمة (List)!", parse_mode="HTML")
            return
            
        total_accounts = len(raw_accounts)
        
        # إنشاء المجلد
        os.makedirs(folder_name, exist_ok=True)
        
        # تقسيم المصفوفة إلى كتل
        chunks = [raw_accounts[i:i + split_size] for i in range(0, total_accounts, split_size)]
        total_files = len(chunks)
        
        # حفظ الكتل في ملفات منفصلة رقمية
        for idx, chunk in enumerate(chunks, 1):
            chunk_path = os.path.join(folder_name, f"{idx}.json")
            try:
                with open(chunk_path, "w", encoding="utf-8") as f_chunk:
                    json.dump(chunk, f_chunk, indent=2, ensure_ascii=False)
            except Exception as e:
                clear_state(chat_id)
                await update.message.reply_text(f" خطأ أثناء حفظ الملف {idx}.json: {str(e)}", parse_mode="HTML")
                return
                
        # حفظ إعدادات التقسيم في قاعدة البيانات
        data = load_data()
        data["shards_config"] = {
            "folder": folder_name,
            "total_files": total_files,
            "current_file_idx": 1,
            "per_file": split_size
        }
        save_data(data)
        
        # حذف ملف acc.json الأصلي لتوفير المساحة ومنع التعليق
        try:
            os.remove(ACCOUNTS_FILE)
            deleted_original = True
        except Exception as e:
            log.warning("Could not delete original acc.json: %s", e)
            deleted_original = False
            
        clear_state(chat_id)
        
        del_status = "تم حذفه تلقائياً لتوفير مساحة الاستضافة ️" if deleted_original else "لم يتم حذفه (تأكد من الصلاحيات)"
        success_msg = (
            f" <b>تم تقسيم الحسابات بنجاح!</b>\n\n"
            f" <b>تفاصيل التقسيم:</b>\n"
            f" اسم المجلد: <code>{folder_name}</code>\n"
            f" حسابات كل ملف: <b>{split_size}</b>\n"
            f" إجمالي الملفات المنتجة: <b>{total_files} ملف JSON</b> (تبدأ من 1.json حتى {total_files}.json)\n"
            f" إجمالي الحسابات المقسمة: <b>{total_accounts} حساب</b>\n"
            f"️ ملف acc.json الأصلي: <b>{del_status}</b>\n\n"
            f" البوت الآن سيعمل بنظام <b>المداورة الدائرية (Round-Robin)</b> التلقائي لتوزيع الحمل وتفادي الحظر!"
        )
        btns = [[(" رجوع لوحة التحكم", "admin_panel_cb")]]
        await update.message.reply_text(success_msg, reply_markup=make_menu(success_msg, btns), parse_mode="HTML")
        return

    # ─── ADMIN: CODE INPUT ───
    if step == "admin_code_input":
        if not text: return
        code = text.strip()
        data = load_data()
        
        # تحقق من تكرار الكود لمنع استبدال كود موجود بالفعل
        if code in data.get("codes", {}):
            clear_state(chat_id)
            btns = [[(" رجوع لوحة التحكم", "admin_panel_cb")]]
            await update.message.reply_text(
                " <b>هذا الكود موجود بالفعل!</b> لا يمكنك تكرار استخدام نفس الاسم.",
                reply_markup=make_menu("", btns), parse_mode="HTML"
            )
            return

        st["data"]["new_code"] = code
        st["step"] = "admin_points_input"
        await update.message.reply_text(
            " اكتب عدد نقاط هذا الكود:",
            parse_mode="HTML"
        )
        return

    # ─── ADMIN: POINTS INPUT ───
    if step == "admin_points_input":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text(" يرجى ادخال رقم صحيح فقط.")
            return
        pts = int(text)
        st["data"]["points"] = pts
        st["step"] = "admin_max_redeem_input"
        await update.message.reply_text(
            " الحد الاقصى لعدد الأشخاص الذين يمكنهم استبدال هذا الكود (الافتراضي " + str(DEFAULT_CODE_MAX_REDEEM) + "):\n"
            " اكتب الرقم، او اكتب <b>0</b> لبلا حدود:",
            parse_mode="HTML"
        )
        return

    # ─── ADMIN: MAX REDEEM INPUT ───
    if step == "admin_max_redeem_input":
        if text == "0":
            max_redeem = -1
        elif text.isdigit() and int(text) > 0:
            max_redeem = int(text)
        else:
            await update.message.reply_text(" يرجى ادخال رقم صحيح (0 لبلا حدود).")
            return

        code = st["data"].get("new_code", "")
        pts = st["data"].get("points", 0)
        data = load_data()
        unlimited = (max_redeem == -1)
        data.setdefault("codes", {})[code] = {
            "points": pts,
            "max_redeem": max_redeem if not unlimited else 999999,
            "used": 0,
            "unlimited": unlimited
        }
        save_data(data)
        clear_state(chat_id)
        limit_str = "∞ بلا حدود" if unlimited else str(max_redeem) + " شخص"
        text2 = (
            " تم انشاء كود الاستبدال بنجاح!\n\n"
            " الكود: <code>" + code + "</code>\n"
            " قيمة الكود: <b>" + str(pts) + " نقطة</b> (يحصل عليها المستخدم عند الاستبدال)\n"
            " الحد الأقصى للمستفيدين: " + limit_str
        )
        btns = [[(" رجوع", "admin_panel_cb")]]
        await update.message.reply_text(text2, reply_markup=make_menu(text2, btns), parse_mode="HTML")
        return

    # ─── ADMIN: DELETE CODE ───
    if step == "admin_del_code":
        code = text.strip()
        st["data"]["del_code"] = code
        st["step"] = "admin_del_confirm"
        btns = [[(" نعم", "admin_del_yes"), (" لا", "admin_del_no")]]
        await update.message.reply_text(
            "️ هل انت متاكد من حذف الكود: <code>" + code + "</code>?",
            reply_markup=make_menu("", btns), parse_mode="HTML"
        )
        return

    # ─── REDEEM CODE (with duplicate prevention per account) ───
    if step == "redeem_input":
        code = text.strip()
        data = load_data()
        codes = data.get("codes", {})
        if code in codes:
            udata = get_user(data, uid)
            
            # منع الحساب الواحد من استبدال الكود مرتين
            if code in udata.get("redeemed", []):
                clear_state(chat_id)
                await update.message.reply_text(
                    " <b>لقد قمت باستبدال هذا الكود مسبقاً!</b> لا يمكن استبدال الكود الواحد أكثر من مرة لكل حساب تيليجرام."
                )
                return

            code_info = codes[code]
            if isinstance(code_info, (int, float)):
                pts = int(code_info)
                max_redeem = DEFAULT_CODE_MAX_REDEEM
                used = 0
                unlimited = False
            else:
                pts = code_info.get("points", 0)
                max_redeem = code_info.get("max_redeem", DEFAULT_CODE_MAX_REDEEM)
                used = code_info.get("used", 0)
                unlimited = code_info.get("unlimited", False)

            # التحقق من أن الكود لم ينفد حده الأقصى الإجمالي لعدد الأشخاص
            if not unlimited and used >= max_redeem:
                if code in codes:
                    del codes[code]
                save_data(data)
                clear_state(chat_id)
                await update.message.reply_text(
                    " هذا الكود تم استخدامه للحد الأقصى مسبقاً، وتم حذفه تلقائياً من النظام."
                )
                return

            # إعطاء النقاط وتسجيل الكود كمسترد لهذا المستخدم
            udata["points"] = udata.get("points", 0) + pts
            udata.setdefault("redeemed", []).append(code)

            new_used = used + 1
            if not unlimited and new_used >= max_redeem:
                if code in codes:
                    del codes[code]
                is_purged = True
            else:
                if isinstance(code_info, dict):
                    code_info["used"] = new_used
                    codes[code] = code_info
                else:
                    codes[code] = {"points": pts, "max_redeem": DEFAULT_CODE_MAX_REDEEM, "used": new_used, "unlimited": False}
                is_purged = False
            
            save_data(data)
            clear_state(chat_id)
            
            if is_purged:
                remaining = "0 (تم حذفه تلقائياً لاكتماله)"
            else:
                remaining = "∞" if unlimited else str(max_redeem - new_used) + " شخص"

            text2 = (
                " تم استبدال الكود بنجاح!\n\n"
                " حصلت على: <b>+" + str(pts) + "</b> نقطة\n"
                " رصيدك الان: <b>" + str(udata["points"]) + "</b>\n\n"
                " متبقي لعدد أشخاص آخرين: " + remaining
            )
            btns = [[(" رجوع للقائمة الرئيسية", "back_main")]]
            await update.message.reply_text(text2, reply_markup=make_menu(text2, btns), parse_mode="HTML")
        else:
            await update.message.reply_text(" الكود غير صالح او انتهت صلاحيته.")
        return

    # ─── SPEND: AMOUNT INPUT ───
    if step == "spend_amount":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text(" يلزم فقط ارقام! اكتب عدد النقاط:")
            return
        amount = int(text)
        data = load_data()
        udata = get_user(data, uid)
        if amount > udata.get("points", 0):
            await update.message.reply_text(" نقاطك غير كافية! عندك: " + str(udata.get("points", 0)) + " نقطة.")
            return
        action = st["data"]["action"]
        st["data"]["amount"] = amount
        st["step"] = "spend_region"
        keys = list(REGION_URLS.keys())
        btns = []
        for i in range(0, len(keys), 3):
            row = []
            for j in range(i, min(i + 3, len(keys))):
                k = keys[j]
                flag = REGION_FLAGS.get(k, "")
                row.append((flag + " " + k, "reg_" + k))
            btns.append(row)
        action_name = " اعجابات" if action == "like" else " اشتراكات"
        await update.message.reply_text(
            action_name + " | " + str(amount) + " نقطة\n\n️ اختر المنطقة:",
            reply_markup=make_menu("", btns), parse_mode="HTML"
        )
        return

    # ─── SPEND: MAP CODE INPUT ───
    if step == "spend_map":
        code = clean_code(text)
        if not code or len(code) < 3:
            await update.message.reply_text(" كود غير صالح. اكتب كود الخريطة:")
            return

        action = st["data"]["action"]
        region = st["data"]["region"]
        amount = st["data"]["amount"]
        data = load_data()

        maps = data.setdefault("maps", {})
        map_info = maps.get(code, {"subs": 0, "likes": 0})
        current = map_info.get("subs" if action == "subscribe" else "likes", 0)
        remaining = MAX_PER_MAP - current

        if remaining <= 0:
            label = " الاشتراكات" if action == "subscribe" else " الاعجابات"
            other = " الاعجابات" if action == "subscribe" else " الاشتراكات"
            other_cur = map_info.get("likes" if action == "subscribe" else "subs", 0)
            other_rem = MAX_PER_MAP - other_cur
            msg = "️ هذه الخريطة وصلت للحد الاقصى من " + label + " (" + str(MAX_PER_MAP) + "/" + str(MAX_PER_MAP) + ")"
            if other_rem > 0:
                msg += "\nيمكنك اضافة " + other + " (" + str(other_rem) + " متبقي)"
            clear_state(chat_id)
            btns = [[(" رجوع", "back_main")]]
            await update.message.reply_text(msg, reply_markup=make_menu(msg, btns), parse_mode="HTML")
            return

        actual = min(amount, remaining)
        refund_diff = amount - actual
        if refund_diff > 0:
            udata = get_user(data, uid)
            udata["points"] = udata.get("points", 0) + refund_diff
            save_data(data)
            amount = actual

        udata = get_user(data, uid)
        udata["points"] = udata.get("points", 0) - amount
        save_data(data)

        clear_state(chat_id)
        set_state(chat_id, "in_queue", {"action": action, "region": region, "map_code": code, "amount": amount, "pending_points": amount})

        msg = await update.message.reply_text(" جاري الاضافة للطابور...", parse_mode="HTML")
        qid = add_to_queue(chat_id, action, region, code, amount, msg.message_id)

        pos = get_queue_position(chat_id)
        flag = REGION_FLAGS.get(region, "")
        action_label = " اضافة اعجاب" if action == "like" else " اضافة اشتراك"
        wait_text = (
            " رقم انتظارك: <b>" + str(pos) + "</b>\n"
            + flag + " " + region + " | " + action_label + "\n"
            "كود خريطة: <code>" + code + "</code>\n"
            " النقاط: " + str(amount) + "\n\n"
            " الرجاء الانتظار حتى يتم تنفيذ الطلبات السابقة"
        )
        btns = [[(" الغاء الطلب", "cancel_queue")]]
        try:
            await msg.edit_text(wait_text, reply_markup=make_menu(wait_text, btns), parse_mode="HTML")
        except: pass

        asyncio.create_task(trigger_queue(ctx))
        return


# ═══════════════════════════════════════
#  Queue Processor
# ═══════════════════════════════════════
async def trigger_queue(ctx):
    global is_processing
    if is_processing:
        return
    if not task_queue:
        return
    is_processing = True
    try:
        while task_queue:
            item = task_queue.pop(0)
            if item.get("cancelled"):
                continue
            await process_queue_item(ctx, item)
            await update_queue_positions(ctx)
            await asyncio.sleep(0.5)
    except Exception as e:
        log.error("Queue processor error: %s", e)
    finally:
        is_processing = False

async def update_queue_positions(ctx):
    """Update queue position messages for all waiting users"""
    for i, t in enumerate(task_queue):
        if t.get("cancelled"):
            continue
        chat_id = t["chat_id"]
        new_pos = i + 1
        flag = REGION_FLAGS.get(t["region"], "")
        action = t["action"]
        action_label = " اضافة اعجاب" if action == "like" else " اضافة اشتراك"
        wait_text = (
            " رقم انتظارك: <b>" + str(new_pos) + "</b>\n"
            + flag + " " + t["region"] + " | " + action_label + "\n"
            "كود خريطة: <code>" + t["map_code"] + "</code>\n"
            " النقاط: " + str(t["count"]) + "\n\n"
            " الرجاء الانتظار حتى يتم تنفيذ الطلبات السابقة"
        )
        btns = [[(" الغاء الطلب", "cancel_queue")]]
        try:
            await ctx.bot.edit_message_text(
                chat_id, t["message_id"],
                wait_text, reply_markup=make_menu(wait_text, btns), parse_mode="HTML"
            )
        except Exception as e:
            log.warning("Could not update queue msg for %s: %s", chat_id, str(e)[:60])

# تقرير خطأ مفصل يرسل حصرياً للآدمن الرئيسي SUPER_ADMIN لتفادي تسريب الأخطاء
async def notify_admins_of_error(ctx, user_name, chat_id, map_code, region, action, done, total, error_msg):
    admin_text = (
        f"️ <b>[تقرير خطأ للمشرف الرئيسي]</b>\n\n"
        f" العضو: {escape_html(user_name)} (<code>{chat_id}</code>)\n"
        f"️ الخريطة: <code>{map_code}</code>\n"
        f" المنطقة: <b>{region}</b>\n"
        f"️ العملية: <b>{action}</b>\n"
        f" التقدم: {done}/{total}\n\n"
        f" <b>الخطأ التقني المستلم:</b>\n"
        f"<code>{escape_html(error_msg)}</code>"
    )
    try:
        await ctx.bot.send_message(chat_id=SUPER_ADMIN, text=admin_text, parse_mode="HTML")
    except Exception as e:
        log.error("Could not notify super admin: %s", e)

async def process_queue_item(ctx, item):
    global process_current
    chat_id = item["chat_id"]
    action = item["action"]
    region = item["region"]
    map_code = item["map_code"]
    total = item["count"]
    flag = REGION_FLAGS.get(region, "")
    action_emoji = "" if action == "like" else ""
    action_name = "إعجاب" if action == "like" else "اشتراك"
    action_label = f"{action_emoji} إضافة {action_name}"

    process_current = {"chat_id": chat_id}
    cancel_flags[chat_id] = False
    processing_done_count[chat_id] = 0

    # 1. جلب بيانات المستخدم
    data = load_data()
    udata = get_user(data, chat_id)
    user_name = udata.get("name") or "المستخدم"

    # 2. حذف رسالة رقم الانتظار تماماً فور تفعيل الطلب
    try:
        await ctx.bot.delete_message(chat_id, item["message_id"])
    except Exception as e:
        log.warning("Could not delete queue wait message for %s: %s", chat_id, e)

    # 3. إرسال رسالة تفعيل البدء الجديدة وتنبيه المستخدم
    start_text = (
        f" <b>لقد حان دورك يا {escape_html(user_name)}!</b>\n\n"
        f"️ جاري بدء معالجة طلبك الآن...\n"
        f" المنطقة: {flag} <b>{region}</b>\n"
        f"️ الخريطة: <code>{map_code}</code>\n\n"
        f" التقدم: <b>0/{total}</b> {action_emoji}\n\n"
        f" يرجى الانتظار ولا تقم بطلب آخر حالياً."
    )
    btns = [[(" الغاء العمليه", "cancel_process_ask")]]
    
    try:
        new_msg = await ctx.bot.send_message(
            chat_id=chat_id,
            text=start_text,
            reply_markup=make_menu(start_text, btns),
            parse_mode="HTML"
        )
        item["message_id"] = new_msg.message_id
    except Exception as e:
        log.error("Could not send start message for %s: %s", chat_id, e)
        process_current.clear()
        return

    # استهلاك مباشر من acc.json: الناجح يحذف، والفاشل ينتقل إلى da.json
    raw_accounts = load_raw_accounts_file()
    accounts = []
    for rec in raw_accounts:
        u = rec.get("uid")
        p = rec.get("password") or rec.get("pass")
        if u and p:
            accounts.append({"record": rec, "u": str(u), "p": str(p)})

    if not accounts:
        try:
            try: await ctx.bot.delete_message(chat_id, item["message_id"])
            except: pass
            err_no_acc = " <b>لا توجد حسابات متوفرة حالياً في acc.json!</b>\n\n تم إعادة كامل النقاط لرصيدك: <b>" + str(total) + "</b> نقطة"
            await ctx.bot.send_message(chat_id, err_no_acc, reply_markup=make_menu("", [[(" رجوع", "back_main")]]), parse_mode="HTML")
        except: pass
        data = load_data(); udata = get_user(data, chat_id)
        udata["points"] = udata.get("points", 0) + total; save_data(data)
        clear_state(chat_id); process_current.clear(); return

    loop = asyncio.get_event_loop()
    done = 0
    account_idx = 0
    consecutive_zeros = 0
    last_batch_error = "لا توجد أخطاء مسجلة"

    def run_batch(batch_accounts):
        nonlocal last_batch_error
        results = []; errors = []
        with ThreadPoolExecutor(max_workers=min(WORKER_THREADS, len(batch_accounts))) as executor:
            futures = {}
            for acc in batch_accounts:
                f = executor.submit(execute_with_retry, acc, region, action, map_code)
                futures[f] = acc
            for f in as_completed(futures):
                acc = futures[f]
                try:
                    success, err_msg = f.result()
                    results.append((success, acc))
                    if not success and err_msg:
                        errors.append(f"الحساب {str(acc['u'])[:6]}: {err_msg}")
                except Exception as e:
                    results.append((False, acc)); errors.append(f"الحساب {str(acc['u'])[:6]}: استثناء {str(e)}")
        if errors: last_batch_error = errors[-1]
        return results

    try:
        while done < total:
            if cancel_flags.get(chat_id, False):
                remaining_points = total - done
                if remaining_points > 0:
                    data2 = load_data()
                    udata2 = get_user(data2, chat_id)
                    udata2["points"] = udata2.get("points", 0) + remaining_points
                    maps = data2.setdefault("maps", {})
                    mi = maps.get(map_code, {"subs": 0, "likes": 0})
                    if action == "like":
                        mi["likes"] = mi.get("likes", 0) + done
                        udata2["total_likes"] = udata2.get("total_likes", 0) + done
                    else:
                        mi["subs"] = mi.get("subs", 0) + done
                        udata2["total_subs"] = udata2.get("total_subs", 0) + done
                    maps[map_code] = mi
                    save_data(data2)

                cancel_text = (
                    f" <b>تم الغاء العملية بناءً على طلبك</b>\n\n"
                    f" العضو: {escape_html(user_name)}\n"
                    f"️ الخريطة: <code>{map_code}</code>\n"
                    f"{flag} المنطقة: <b>{region}</b>\n\n"
                    f" تم إضافة: {done}/{total} {action_emoji}\n"
                    f" تم استرجاع: <b>{total - done}</b> نقطة إلى رصيدك."
                )
                btns2 = [[(" رجوع للقائمة الرئيسية", "back_main")]]
                try:
                    await ctx.bot.delete_message(chat_id, item["message_id"])
                except: pass
                await ctx.bot.send_message(chat_id, cancel_text, reply_markup=make_menu(cancel_text, btns2), parse_mode="HTML")
                
                clear_state(chat_id)
                cancel_flags.pop(chat_id, None)
                processing_done_count.pop(chat_id, None)
                process_current.clear()
                return

            remaining_needed = total - done
            if account_idx >= len(accounts):
                break

            batch_size = min(WORKER_THREADS * 2, remaining_needed, len(accounts) - account_idx)
            batch_accounts = accounts[account_idx:account_idx + batch_size]
            batch_results = await loop.run_in_executor(None, run_batch, batch_accounts)
            account_idx += batch_size

            successful_uids = []
            failed_records = []
            for success, acc in batch_results:
                if success:
                    successful_uids.append(acc["u"])
                else:
                    failed_records.append(acc["record"])

            if successful_uids:
                consume_successful_accounts(successful_uids)
            if failed_records:
                move_failed_accounts_to_da(failed_records)

            batch_done = len(successful_uids)
            if batch_done == 0:
                consecutive_zeros += 1
            else:
                consecutive_zeros = 0

            done += batch_done
            if done > total:
                done = total

            # تعديل نص التقدم اللحظي ليتغير مع الوقت أثناء التنفيذ
            prog_text = (
                f" <b>يتم الآن تنفيذ طلبك يا {escape_html(user_name)}!</b>\n\n"
                f"️ الخريطة: <code>{map_code}</code>\n"
                f"{flag} المنطقة: <b>{region}</b>\n"
                f"️ العملية: <b>{action_label}</b>\n\n"
                f" التقدم الحالي (يتحدث تلقائياً):\n"
                f" <b>{done}/{total}</b> {action_emoji}\n\n"
                f" يرجى عدم القيام بأي طلب آخر حتى ينتهي البوت."
            )
            try:
                await ctx.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=item["message_id"],
                    text=prog_text,
                    reply_markup=make_menu("", btns),
                    parse_mode="HTML"
                )
            except: pass

            if consecutive_zeros >= 3:
                log.warning("Terminating queue item for %s due to 3 consecutive failed batches.", chat_id)
                # إرسال إشعار فوري للأدمن الرئيسي SUPER_ADMIN لتشخيص المشكلة
                await notify_admins_of_error(
                    ctx, user_name, chat_id, map_code, region, action, done, total, last_batch_error
                )
                break

    except Exception as e:
        log.error("Process error for %s: %s", chat_id, e)
        remaining_points = total - done
        if remaining_points > 0:
            data_err = load_data()
            udata_err = get_user(data_err, chat_id)
            udata_err["points"] = udata_err.get("points", 0) + remaining_points
            save_data(data_err)
        
        # إرسال تقرير الخطأ الفوري للمشرف الرئيسي
        await notify_admins_of_error(
            ctx, user_name, chat_id, map_code, region, action, done, total, str(e)
        )

        err_text = (
            f" <b>حدث خطأ غير متوقع أثناء المعالجة</b>\n\n"
            f"️ الخريطة: <code>{map_code}</code>\n"
            f"{flag} المنطقة: <b>{region}</b>\n\n"
            f" تم إضافة: {done}/{total} {action_emoji}\n"
            f" تم استرجاع: <b>{remaining_points}</b> نقطة غير مكتملة لرصيدك."
        )
        
        # تظهر رسالة الخطأ التقني للأدمن الرئيسي فقط
        if chat_id == SUPER_ADMIN:
            err_text += f"\n\n️ <b>خطأ تقني للمشرف:</b>\n<code>{escape_html(str(e))}</code>"

        btns_err = [[(" رجوع للقائمة الرئيسية", "back_main")]]
        try: await ctx.bot.delete_message(chat_id, item["message_id"])
        except: pass
        await ctx.bot.send_message(chat_id, err_text, reply_markup=make_menu(err_text, btns_err), parse_mode="HTML")
        clear_state(chat_id)
        cancel_flags.pop(chat_id, None)
        processing_done_count.pop(chat_id, None)
        process_current.clear()
        return

    # حفظ وتحديث البيانات في نهاية العملية
    maps = data.setdefault("maps", {})
    mi = maps.get(map_code, {"subs": 0, "likes": 0})
    if action == "like":
        mi["likes"] = mi.get("likes", 0) + done
    else:
        mi["subs"] = mi.get("subs", 0) + done
    maps[map_code] = mi

    udata = get_user(data, chat_id)
    if action == "like":
        udata["total_likes"] = udata.get("total_likes", 0) + done
    else:
        udata["total_subs"] = udata.get("total_subs", 0) + done

    remaining_points = total - done
    if remaining_points > 0:
        udata["points"] = udata.get("points", 0) + remaining_points
        
    save_data(data)
    clear_state(chat_id)

    # 4. حذف رسالة عداد التقدم اللحظي لإرسال النتيجة النهائية كرسالة مستقلة ونظيفة
    try:
        await ctx.bot.delete_message(chat_id, item["message_id"])
    except:
        pass

    btns_final = [[(" العودة للقائمة الرئيسية", "back_main")]]
    if remaining_points > 0:
        # رسالة التوقف الجزئي للمستخدم العادي (تظل نظيفة ومطابقة للمطلوب)
        final_text = (
            f"️ <b>تم إيقاف العملية جزئياً لعدم استجابة بعض الحسابات</b>\n\n"
            f" العضو: {escape_html(user_name)}\n"
            f"️ الخريطة: <code>{map_code}</code>\n"
            f"{flag} المنطقة: <b>{region}</b>\n\n"
            f" تم إضافة: <b>{done}/{total}</b> {action_emoji} ️\n"
            f" تم استرجاع: <b>{remaining_points}</b> نقطة غير مكتملة لرصيدك تلقائياً.\n\n"
            f" إحصائيات الخريطة الإجمالية:\n"
            f" اشتراكات: {mi.get('subs', 0)}\n"
            f" اعجابات: {mi.get('likes', 0)}"
        )
        # تظهر رسالة الخطأ التقني المستلم للأدمن الرئيسي فقط
        if chat_id == SUPER_ADMIN:
            final_text += f"\n\n️ <b>خطأ تقني للمشرف الرئيسي:</b>\n<code>{escape_html(last_batch_error)}</code>"
    else:
        final_text = (
            f" <b>تم اكتمال طلبك بنجاح! </b>\n\n"
            f" العضو: {escape_html(user_name)}\n"
            f"️ الخريطة: <code>{map_code}</code>\n"
            f"{flag} المنطقة: <b>{region}</b>\n\n"
            f" تم إضافة: <b>{done}</b> من الـ {action_name} بنجاح!\n\n"
            f" إحصائيات الخريطة الإجمالية:\n"
            f" اشتراكات: {mi.get('subs', 0)}\n"
            f" اعجابات: {mi.get('likes', 0)}"
        )
    
    await ctx.bot.send_message(chat_id, final_text, reply_markup=make_menu(final_text, btns_final), parse_mode="HTML")

    cancel_flags.pop(chat_id, None)
    processing_done_count.pop(chat_id, None)
    process_current.clear()


# ═══════════════════════════════════════
#  Error Handler
# ═══════════════════════════════════════
async def error_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    log.error("Error: %s", ctx.error)


# ═══════════════════════════════════════
#  Startup & Main
# ═══════════════════════════════════════
async def on_startup(app):
    global bot_app
    bot_app = app
    acc_count = load_accounts()
    log.info("Bot ready! Accounts loaded: %d", len(acc_count))

def main():
    builder = Application.builder().token(BOT_TOKEN)
    builder.connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30)
    app = builder.build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("Admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    app.post_init = on_startup
    log.info("Starting bot...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()