import html

import os, json, re, html, shutil, tempfile, logging, zipfile, hashlib, struct, asyncio, random, string, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import requests as rq
from pathlib import Path
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, text_format
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, LabeledPrice
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, PreCheckoutQueryHandler, filters
import app as stars_core
import main_N6 as long_sub_core

BASE=Path(__file__).resolve().parent
METADATA=json.load(open(BASE/"metadata.json",encoding="utf-8"))

CATEGORY_MAPPING = {'قواعد اللعبة': ['GamePrepareTimeS', 'MultiRoundsEnabled', 'RoundCount', 'RoundTime', 'RoundPreparingTime', 'TeamNum', 'TeamMemberNum', 'MinNumOfMatchStart', 'AllowHangUpTime', 'EnableFreeQuit', 'DisableReconnect'], 'اللاعب والخصائص': ['MaxHP', 'MaxEP', 'StartEP', 'Damage', 'Damaged', 'MoveSpeed', 'JumpHeight', 'AutoHealing', 'UnlimitedBullet', 'UnlimitedGloowall', 'UnlimitedThrowables', 'EnableInventoryDrop'], 'نظام الإنعاش': ['HumanCanRevive', 'BotCanRevive', 'ReviveCDTime', 'ReviveRule', 'ReviveSwitch'], 'إعدادات المشاهدة': ['EnableDeathObserve', 'ObserverModeEnable', 'ObserverMode', 'UGCObserverCameraMode'], 'الاقتصاد': ['EnableTotalToken', 'EcoRoundMoney', 'EcoKillMoney', 'EcoWinMoney', 'CoinHudShow', 'EnableUGCToken'], 'المنطقة الآمنة (الزون)': ['SafeZoneEnabled', 'SafeZoneSize', 'SafeZoneStartTime', 'SafeZoneDamage', 'SafeZoneShrinkTime'], 'إعدادات الكاميرا': ['CameraType', 'CameraFov', 'CameraPitch', 'CameraYaw', 'CameraDistance', 'CameraOffset', 'CameraProjectionMode', 'CameraBlockMode', 'TwoDimensionCamEnableZAxis', 'CameraViewingAngleRestrictionType'], 'المهارات والسكنات': ['EnableActiveSkill', 'EnablePassiveSkill', 'PetEnable', 'PetSkillEnable', 'EnableWeaponSkinProperty', 'EnableWeaponSkillProperty', 'EnablePveWeaponSkinProperty'], 'قواعد المباراة': ['RecommendStartGameNumber', 'EnableQuickStartMatch', 'GameStartTimeS', 'EnableHalfwayJoin', 'HalfwayJoinNumberLimit', 'HalfwayJoinNumber', 'EnableHalfwayJoinEffectTime', 'HalfwayJoinEffectTime'], 'إعدادات متقدمة': ['EnableMiniMapV2', 'DisableDepthMap', 'EnableRuntimeDynamicNavMesh', 'EnableEnergySavingMode', 'IsDownFPPResource', 'UGCIsShowSocialChooseBox', 'EnableInternalWorkflowLogic', 'EnableAOIFilter', 'IsHoudiniUsed', 'DisableEnemyFootstepVibrate', 'IsAIGenUsed', 'MorphModeDisableTemplate']}
TRANSLATIONS = {
    'GamePrepareTimeS':'وقت تجهيز المباراة (ثانية)', 'MultiRoundsEnabled':'تفعيل تعدد الجولات', 'RoundCount':'عدد الجولات', 'RoundTime':'وقت الجولة', 'RoundPreparingTime':'وقت تجهيز الجولة', 'TeamNum':'عدد الفرق', 'TeamMemberNum':'عدد أعضاء الفريق', 'MinNumOfMatchStart':'الحد الأدنى لبدء المباراة', 'AllowHangUpTime':'وقت السماح بالتعليق', 'EnableFreeQuit':'السماح بالخروج الحر', 'DisableReconnect':'تعطيل إعادة الاتصال',
    'MaxHP':'الصحة القصوى', 'MaxEP':'الطاقة القصوى (EP)', 'StartEP':'الطاقة عند البداية', 'Damage':'قوة الضرر', 'Damaged':'الضرر المستلم', 'MoveSpeed':'سرعة الحركة', 'JumpHeight':'ارتفاع القفز', 'AutoHealing':'الشفاء التلقائي', 'UnlimitedBullet':'ذخيرة لا نهائية', 'UnlimitedGloowall':'جدار ثلجي لا نهائي', 'UnlimitedThrowables':'رميات لا نهائية', 'EnableInventoryDrop':'تفعيل إسقاط الحقيبة',
    'HumanCanRevive':'السماح للاعب بالإنعاش', 'BotCanRevive':'السماح للبوت بالإنعاش', 'ReviveCDTime':'وقت انتظار الإنعاش', 'ReviveRule':'قواعد الإنعاش', 'ReviveSwitch':'تفعيل نظام الإنعاش',
    'EnableDeathObserve':'تفعيل مشاهدة الموت', 'ObserverModeEnable':'تفعيل وضع المشاهدة', 'ObserverMode':'وضع المشاهدة', 'UGCObserverCameraMode':'وضع كاميرا المشاهدة',
    'EnableTotalToken':'تفعيل إجمالي العملات', 'EcoRoundMoney':'عملات الجولة', 'EcoKillMoney':'عملات القتل', 'EcoWinMoney':'عملات الفوز', 'CoinHudShow':'إظهار العملات على الشاشة', 'EnableUGCToken':'تفعيل عملات UGC',
    'SafeZoneEnabled':'تفعيل المنطقة الآمنة', 'SafeZoneSize':'حجم المنطقة الآمنة', 'SafeZoneStartTime':'وقت بدء المنطقة الآمنة', 'SafeZoneDamage':'ضرر المنطقة الآمنة', 'SafeZoneShrinkTime':'وقت انكماش المنطقة الآمنة',
    'CameraType':'نوع الكاميرا', 'CameraFov':'زاوية رؤية الكاميرا', 'CameraPitch':'ميل الكاميرا', 'CameraYaw':'دوران الكاميرا', 'CameraDistance':'مسافة الكاميرا', 'CameraOffset':'إزاحة الكاميرا', 'CameraProjectionMode':'وضع إسقاط الكاميرا', 'CameraBlockMode':'وضع حجب الكاميرا', 'TwoDimensionCamEnableZAxis':'تفعيل محور Z للكاميرا ثنائية الأبعاد', 'CameraViewingAngleRestrictionType':'نوع تقييد زاوية الرؤية',
    'EnableActiveSkill':'تفعيل المهارات النشطة', 'EnablePassiveSkill':'تفعيل المهارات السلبية', 'PetEnable':'تفعيل الحيوانات الأليفة', 'PetSkillEnable':'تفعيل مهارات الحيوانات الأليفة', 'EnableWeaponSkinProperty':'تفعيل خصائص سكن السلاح', 'EnableWeaponSkillProperty':'تفعيل مهارات السلاح', 'EnablePveWeaponSkinProperty':'تفعيل خصائص سكن سلاح PVE',
    'RecommendStartGameNumber':'رقم بدء المباراة المقترح', 'EnableQuickStartMatch':'تفعيل بدء المباراة السريع', 'GameStartTimeS':'وقت بدء المباراة (ثانية)', 'EnableHalfwayJoin':'تفعيل الانضمام أثناء المباراة', 'HalfwayJoinNumberLimit':'حد عدد المنضمين أثناء المباراة', 'HalfwayJoinNumber':'عدد المنضمين أثناء المباراة', 'EnableHalfwayJoinEffectTime':'تفعيل مدة تأثير الانضمام', 'HalfwayJoinEffectTime':'مدة تأثير الانضمام',
    'EnableMiniMapV2':'تفعيل الخريطة المصغرة', 'DisableDepthMap':'تعطيل خريطة العمق', 'EnableRuntimeDynamicNavMesh':'تفعيل الملاحة الديناميكية', 'EnableEnergySavingMode':'تفعيل وضع توفير الطاقة', 'IsDownFPPResource':'تحميل موارد منظور الشخص الأول', 'UGCIsShowSocialChooseBox':'إظهار مربع الاختيار الاجتماعي', 'EnableInternalWorkflowLogic':'تفعيل منطق سير العمل الداخلي', 'EnableAOIFilter':'تفعيل فلتر AOI', 'IsHoudiniUsed':'تفعيل Houdini', 'DisableEnemyFootstepVibrate':'تعطيل اهتزاز خطوات العدو', 'IsAIGenUsed':'تفعيل توليد الذكاء الاصطناعي', 'MorphModeDisableTemplate':'تعطيل قالب وضع التحول'
}

def build_proto():
    from google.protobuf import descriptor_pb2, descriptor_pool, message_factory
    fd = descriptor_pb2.FileDescriptorProto()
    fd.name = "ugc.proto"
    fd.syntax = "proto3"

    def msg(name, fields):
        m = fd.message_type.add()
        m.name = name
        for num, fname, ftype, label, type_name in fields:
            f = m.field.add()
            f.number = num
            f.name = fname
            f.type = ftype
            f.label = label
            if type_name:
                f.type_name = type_name
        return m

    L_OPT = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    T_BYTES = descriptor_pb2.FieldDescriptorProto.TYPE_BYTES
    T_UINT64 = descriptor_pb2.FieldDescriptorProto.TYPE_UINT64
    T_INT32 = descriptor_pb2.FieldDescriptorProto.TYPE_INT32
    T_BOOL = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL
    T_FLOAT = descriptor_pb2.FieldDescriptorProto.TYPE_FLOAT
    T_MSG = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    L_REP = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED

    msg("Settings", [
        (1,"id",T_INT32,L_OPT,None),
        (2,"enable",T_BOOL,L_OPT,None),
        (3,"value",T_INT32,L_OPT,None),
        (4,"ratio",T_FLOAT,L_OPT,None),
    ])
    msg("SettingsWrapper", [
        (1,"settings",T_MSG,L_REP,".Settings"),
    ])
    msg("Root", [
        (1,"settings",T_MSG,L_REP,".SettingsWrapper"),
        (3,"version",T_INT32,L_OPT,None),
    ])
    msg("UGCProjectData", [
        (1,"graph_editor_project",T_BYTES,L_OPT,None),
        (2,"workflow_editor_project",T_BYTES,L_OPT,None),
        (3,"entity_editor_project",T_BYTES,L_OPT,None),
        (4,"hud_editor_project",T_BYTES,L_OPT,None),
        (5,"map_editor_project",T_BYTES,L_OPT,None),
        (6,"ShahGCreator",T_MSG,L_OPT,".Root"),
        (7,"author_uid",T_UINT64,L_OPT,None),
        (8,"custom_resources_package",T_BYTES,L_OPT,None),
        (9,"timeline_editor_project",T_BYTES,L_OPT,None),
        (10,"user_custom_event_editor_project",T_BYTES,L_OPT,None),
        (999,"compatible_version",T_INT32,L_OPT,None),
        (1000,"public_version",T_INT32,L_OPT,None),
    ])
    pool=descriptor_pool.DescriptorPool()
    pool.Add(fd)
    descriptor = pool.FindMessageTypeByName("UGCProjectData")

    # Compatible with old and new protobuf releases used by hosting platforms.
    # Newer protobuf exposes the module-level GetMessageClass(), while older
    # releases expose GetPrototype() through MessageFactory.
    get_message_class = getattr(message_factory, "GetMessageClass", None)
    if get_message_class is not None:
        return get_message_class(descriptor)

    factory = message_factory.MessageFactory(pool)
    get_prototype = getattr(factory, "GetPrototype", None)
    if get_prototype is not None:
        return get_prototype(descriptor)

    # Final compatibility path for releases exposing GetMessageClass on the
    # MessageFactory instance.
    factory_get_message_class = getattr(factory, "GetMessageClass", None)
    if factory_get_message_class is not None:
        return factory_get_message_class(descriptor)

    raise RuntimeError(
        "Unsupported protobuf version: no compatible dynamic message factory was found."
    )

UGC=build_proto()

SESSIONS={}
REPORTS={}
ADMIN_ID=7270942727

# ---------- Independent 5-minute feature cooldowns ----------
FEATURE_COOLDOWN_SECONDS = 5 * 60
FEATURE_COOLDOWNS = {}

def cooldown_remaining(user_id, feature):
    now = asyncio.get_running_loop().time()
    last = FEATURE_COOLDOWNS.get((int(user_id), feature), 0)
    return max(0, int(FEATURE_COOLDOWN_SECONDS - (now - last)))

def set_feature_cooldown(user_id, feature):
    FEATURE_COOLDOWNS[(int(user_id), feature)] = asyncio.get_running_loop().time()

def cooldown_text(user_id, feature):
    remaining = cooldown_remaining(user_id, feature)
    if remaining <= 0:
        return None
    m, sec = divmod(remaining, 60)
    return f"⏳ انتظر <b>{m} دقيقة و{sec} ثانية</b> قبل استخدام هذه الميزة مرة أخرى."

def feature_description(feature):
    return {
        "settings": "⚙️ <b>تعديل إعدادات الخريطة</b>\n\nأرسل ملف المشروع بصيغة <code>.bytes</code>، وبعدها اختر القسم والإعداد الذي تريد تعديله.",
        "skins": "👕 <b>السكنات</b>\n\nارفع ملف ZIP يحتوي الملفات المطلوبة، وسيقوم البوت بفحصها وتجهيزها.",
        "map_info": "🗺️ <b>معلومات الخريطة</b>\n\nأرسل رمز الخريطة، وسيعرض لك البوت المعلومات المتوفرة عنها.",
        "uid": "🆔 <b>إزالة UID</b>\n\nأرسل ملف <code>.bytes</code>، وسيحاول البوت إزالة UID ثم يرسل الملف المعدل.",
        "stars": " <b>إضافة نجوم</b>\n\nاستخدم نقاطك لإضافة الإعجابات أو الاشتراكات، أو استبدل كودًا لإضافة نقاط إلى رصيدك.",
    }.get(feature, "")

VIDEO_FILE = BASE / "help_video.json"
REPORTS_FILE = BASE / "reports.json"
BLOCK_FILE = BASE / "block_file.json"
HELP_VIDEOS_FILE = BASE / "help_videos.json"
try:
    SAVED_BLOCK = json.loads(BLOCK_FILE.read_text(encoding="utf-8")) if BLOCK_FILE.exists() else {}
except Exception:
    SAVED_BLOCK = {}
try:
    SAVED_HELP_VIDEOS = json.loads(HELP_VIDEOS_FILE.read_text(encoding="utf-8")) if HELP_VIDEOS_FILE.exists() else {}
except Exception:
    SAVED_HELP_VIDEOS = {}

def save_block():
    BLOCK_FILE.write_text(json.dumps(SAVED_BLOCK, ensure_ascii=False, indent=2), encoding="utf-8")

def save_help_videos():
    HELP_VIDEOS_FILE.write_text(json.dumps(SAVED_HELP_VIDEOS, ensure_ascii=False, indent=2), encoding="utf-8")
try:
    SAVED_HELP_VIDEO = json.loads(VIDEO_FILE.read_text(encoding="utf-8")) if VIDEO_FILE.exists() else {}
except Exception:
    SAVED_HELP_VIDEO = {}
try:
    REPORTS = json.loads(REPORTS_FILE.read_text(encoding="utf-8")) if REPORTS_FILE.exists() else {}
except Exception:
    REPORTS = {}
def save_help_video():
    VIDEO_FILE.write_text(json.dumps(SAVED_HELP_VIDEO, ensure_ascii=False, indent=2), encoding="utf-8")
def save_reports():
    REPORTS_FILE.write_text(json.dumps(REPORTS, ensure_ascii=False, indent=2), encoding="utf-8")

WELCOME_FILE = BASE / "welcome_config.json"
DEFAULT_WELCOME = (
    '<tg-emoji emoji-id="5465196621161606098">✨</tg-emoji> <b>اهـلاً بك في بوت عبودي التوب - Aboudi TOP</b>\n'
    '<tg-emoji emoji-id="5404666019266467874">🛠️</tg-emoji> <b>البوت مختص لتعديل اعدادات الخريطة وتفعيل سكنات</b>\n'
    '<tg-emoji emoji-id="5465166573570401247">⚡</tg-emoji> <b>سارع بتجربة أسرع</b>\n'
    '<tg-emoji emoji-id="5465423515693914416">🆔</tg-emoji> | <b>ايديك :</b> <code>{user_id}</code>'
)
try:
    WELCOME_TEXT = json.loads(WELCOME_FILE.read_text(encoding="utf-8")).get("text", DEFAULT_WELCOME) if WELCOME_FILE.exists() else DEFAULT_WELCOME
except Exception:
    WELCOME_TEXT = DEFAULT_WELCOME

def save_welcome():
    WELCOME_FILE.write_text(json.dumps({"text": WELCOME_TEXT}, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- EXTRA TOOLS: UID remover + map information ----------
ALL_REGIONS = ["ME", "IND", "ID", "BR", "VN", "TH", "CIS", "BD", "PK", "SG", "SAC", "TW"]
MAP_STATES = {}

def remove_uid_pattern(data: bytes):
    buffer = bytearray(data)
    index = -1
    for i in range(len(buffer) - 7, -1, -1):
        if buffer[i] == 0x38 and buffer[i + 6] == 0x42:
            index = i
            break
    if index == -1:
        return data, False
    new_buf = bytearray(len(buffer) - 4)
    new_buf[:index] = buffer[:index]
    new_buf[index:index + 3] = bytes([0x38, 0x00, 0x42])
    new_buf[index + 3:] = buffer[index + 7:]
    return bytes(new_buf), True

def is_valid_map_data(workshop):
    name = workshop.get("workshop_name", "")
    if not name or name == "غير معروف" or len(name) < 2:
        return False
    return True

def get_map_info(map_code):
    device_id = "4e93e5106b39e1902e24d1ba2f17c709"
    for region in ALL_REGIONS:
        try:
            url = f"https://mapshare.freefiremobile.com/api/info?lang=en&region={region}&map_code=%23{map_code}&device_id={device_id}"
            response = rq.get(url, timeout=10, verify=False)
            if response.status_code != 200: continue
            data = response.json()
            if data.get("code") != 0 or not data.get("data"): continue
            workshop = data["data"].get("workshop_code_info", {})
            if not is_valid_map_data(workshop): continue
            tag_mapping = {4:"سولو",5:"دو",6:"تريو",7:"سكواد",8:"فرق 5",9:"فرق 6",10:"ذخيرة غير محدودة",11:"تحويل EP سريع",12:"انكماش سريع",13:"انكماش متأخر",14:"منطقة صغيرة",18:"مهارات غير محدودة",19:"فريق واحد",20:"وضع البقاء",21:"العدوى",23:"اختبئ وابحث",24:"متعدد المستويات",26:"جدران جلو غير محدودة",27:"قنابل غير محدودة",28:"الجميع للجميع",29:"معركة أسلحة",30:"ملك الأسلحة",31:"إعادة النشر",32:"قناص",33:"بقاء",34:"فردي",35:"رعب",36:"عادي",37:"سهل",38:"متوسط",39:"صعب",40:"تحدي عالي",41:"هروب",42:"VIP",43:"مصادر مخصصة",44:"ألغاز",45:"سباقات",46:"موسيقى",47:"MOBA",48:"مغامرة",49:"صيد الزومبي",50:"PvP",51:"لعبة حفلات",52:"معركة فرق",53:"دفاع بالأبراج",54:"تدريب"}
            tags = ", ".join(tag_mapping[t] for t in workshop.get("tags", []) if t in tag_mapping) or "لا يوجد تصنيف"
            state_text = {0:"غير منشور",1:"منشور",2:"قيد المراجعة",3:"مرفوض"}.get(workshop.get("state",0),"غير معروف")
            mode = {0:"مخصص",1:"Wipe Out",2:"Points Grab",3:"Parkour",4:"Wipe Out",5:"Points Grab",6:"Parkour",7:"Rush",8:"Endurance",10:"اختبئ وابحث",11:"Contest Canvas",12:"Clash Squad",13:"الجميع للجميع",14:"First-Person",15:"Mini Parkour"}.get(workshop.get("mode_template_id",0),"غير معروف")
            return {"name":workshop.get("workshop_name","غير معروف"),"desc":workshop.get("workshop_desc","لا يوجد وصف"),"image":workshop.get("map_cover_url",""),"likes":workshop.get("like_count",0),"subs":workshop.get("subscribe_count",0),"creator_level":workshop.get("creator_level",0),"team_count":workshop.get("team_count",0),"round_count":workshop.get("round_count",0),"min_time":workshop.get("min_est_play_time",0),"max_time":workshop.get("max_est_play_time",0),"state_text":state_text,"mode":mode,"tags":tags,"region":region}, None
        except Exception:
            continue
    return None, "❌ رمز الخريطة غير صحيح، تأكد من الكود وأعد المحاولة"

def format_map_info(info):
    return (f"<b>🗺️ معلومات الخريطة</b>\n{'─'*30}\n\n"
            f"<b> الاسم:</b> {info['name']}\n<b> مستوى المنشئ:</b> {info['creator_level']}\n"
            f"<b>📝 الوصف:</b> {info['desc'][:150]}{'...' if len(info['desc']) > 150 else ''}\n\n"
            f"<b>❤️ الإعجابات:</b> {info['likes']}\n<b>📥 الاشتراكات:</b> {info['subs']}\n"
            f"<b>🏷️ التصنيفات:</b> {info['tags']}\n\n<b>👥 عدد الفرق:</b> {info['team_count']}\n"
            f"<b>🎮 نمط اللعبة:</b> {info['mode']}\n<b>🔄 عدد الجولات:</b> {info['round_count']}\n"
            f"<b>⏱️ الوقت المتوقع:</b> {info['min_time']} - {info['max_time']} ثانية\n"
            f"<b>📊 الحالة:</b> {info['state_text']}\n<b>📍 المنطقة:</b> {info['region']}")

# ---------- BOT ADMIN / USERS ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8976382861:AAE2bbirrONk7JzkcJzqhWbYTW0laOdJ-xE")
USERS_FILE = BASE / "users.json"
try:
    USERS = json.loads(USERS_FILE.read_text(encoding="utf-8")) if USERS_FILE.exists() else {}
except Exception:
    USERS = {}

def move_failed_accounts_to_da(failed_records):
    """Append failed account records to da.json and remove them from acc.json."""
    if not failed_records:
        return 0
    try:
        path = ACC_FILE
        da_path = BASE / "da.json"
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        if not isinstance(raw, list):
            raw = []

        failed_keys = set()
        records = []
        for rec in failed_records:
            if not isinstance(rec, dict):
                continue
            key = rec.get("uid")
            if key is None:
                key = rec.get("account_id")
            if key is not None:
                failed_keys.add(str(key))
                records.append(rec)

        if not failed_keys:
            return 0

        da_raw = json.loads(da_path.read_text(encoding="utf-8")) if da_path.exists() else []
        if not isinstance(da_raw, list):
            da_raw = []

        existing = set()
        for rec in da_raw:
            if isinstance(rec, dict):
                key = rec.get("uid")
                if key is None:
                    key = rec.get("account_id")
                if key is not None:
                    existing.add(str(key))

        added = 0
        for rec in records:
            key = rec.get("uid")
            if key is None:
                key = rec.get("account_id")
            if str(key) not in existing:
                da_raw.append(rec)
                existing.add(str(key))
                added += 1

        da_tmp = da_path.with_suffix(".json.tmp")
        da_tmp.write_text(json.dumps(da_raw, ensure_ascii=False, indent=2), encoding="utf-8")
        da_tmp.replace(da_path)

        kept = []
        for rec in raw:
            if not isinstance(rec, dict):
                kept.append(rec)
                continue
            key = rec.get("uid")
            if key is None:
                key = rec.get("account_id")
            if key is not None and str(key) in failed_keys:
                continue
            kept.append(rec)

        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return added
    except Exception:
        logging.exception("failed to move failed accounts to da.json")
        return 0

def remove_successful_accounts(successful_records):
    """Remove only successfully processed account records from acc.json."""
    if not successful_records:
        return 0
    try:
        path = ACC_FILE
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        if not isinstance(raw, list):
            return 0

        keys = set()
        for rec in successful_records:
            if isinstance(rec, dict):
                key = rec.get("uid")
                if key is None:
                    key = rec.get("account_id")
                if key is not None:
                    keys.add(str(key))

        if not keys:
            return 0

        kept = []
        removed = 0
        for rec in raw:
            if not isinstance(rec, dict):
                kept.append(rec)
                continue
            key = rec.get("uid")
            if key is None:
                key = rec.get("account_id")
            if key is not None and str(key) in keys:
                removed += 1
            else:
                kept.append(rec)

        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(kept, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        return removed
    except Exception:
        logging.exception("failed to remove successful accounts")
        return 0

def save_users():
    tmp = USERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(USERS, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(USERS_FILE)

def register_user(user):
    if not user:
        return False
    uid = str(user.id)
    old = USERS.get(uid, {})
    is_new = not bool(old)
    record = dict(old)
    record.update({
        "id": user.id,
        "name": user.full_name or "",
        "username": user.username or "",
        "blocked": bool(old.get("blocked", False)),
        "messages": int(old.get("messages", 0)) + 1,
        "last_seen": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    })
    USERS[uid] = record
    save_users()
    return is_new

def is_admin(uid):
    return int(uid) == ADMIN_ID

def is_blocked(uid):
    return bool(USERS.get(str(uid), {}).get("blocked", False))

MAINTENANCE_FILE = BASE / "maintenance.json"
def maintenance_enabled():
    try:
        return bool(json.loads(MAINTENANCE_FILE.read_text(encoding="utf-8")).get("enabled", False))
    except Exception:
        return False

def set_maintenance(enabled):
    MAINTENANCE_FILE.write_text(json.dumps({"enabled": bool(enabled)}, ensure_ascii=False, indent=2), encoding="utf-8")

def maintenance_notice():
    return ("🔧 <b>البوت في وضع الصيانة</b>\n\n"
            "نقوم حاليًا بإجراء تحديثات وتحسينات.\n"
            "يرجى المحاولة مرة أخرى بعد انتهاء الصيانة.")

# Custom Telegram emoji IDs can be changed here.
EMOJI_FILE = BASE / "emoji_config.json"
DEFAULT_EMOJIS = {
    "settings": "",
    "skins": "",
    "help": "",
    "support": "",
    "home": "",
    "account": "",
    "language": "",
    "stats": "",
    "users": "",
    "ban": "",
    "unban": "",
    "admins": "",
    "maintenance": "",
    "broadcast": "",
    "cleanup": "",
    "video": "",
    "add": "",
    "remove": "",
    "list": "",
    "info": "",
    "files": "",
    "history": "",
    "report": "",
    "improve": "",
    "back": "",
    "cancel": "",
    "category": "",
    "setting": "",
    "change": "",
    "export": "",
    "clear": "",
    "stars": "5404666019266467874",
    "likes": "5177431733565393227",
    "subs": "5176921066248865589",
    "codes": "5465166573570401247",
    "mystats": "5177431733565393227",
}
try:
    CUSTOM_EMOJIS = {**DEFAULT_EMOJIS, **json.loads(EMOJI_FILE.read_text(encoding="utf-8"))}
except Exception:
    CUSTOM_EMOJIS = dict(DEFAULT_EMOJIS)

def save_emojis():
    EMOJI_FILE.write_text(json.dumps(CUSTOM_EMOJIS, ensure_ascii=False, indent=2), encoding="utf-8")

def strip_normal_emojis(text):
    """Remove ordinary Unicode emoji/symbols from BUTTON labels only.
    Normal emoji in messages/texts are intentionally left untouched.
    """
    if not isinstance(text, str):
        return text
    return re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF\uFE0F\u200D]", "", text).strip()

def emoji_button(text, callback_data, emoji_key=None):
    """Create a button using only Telegram Custom Emoji icons."""
    kwargs = {"text": strip_normal_emojis(text), "callback_data": callback_data}
    if emoji_key and CUSTOM_EMOJIS.get(emoji_key):
        kwargs["icon_custom_emoji_id"] = CUSTOM_EMOJIS[emoji_key]
    try:
        return InlineKeyboardButton(**kwargs)
    except TypeError:
        kwargs.pop("icon_custom_emoji_id", None)
        return InlineKeyboardButton(**kwargs)

def plain_button(text, **kwargs):
    """Plain button helper: never leaves standard emoji in button labels."""
    return InlineKeyboardButton(strip_normal_emojis(text), **kwargs)

EMOJI_NAMES = {
    "settings": "إعدادات الخريطة",
    "skins": "السكنات",
    "account": "حسابي",
    "help": "طريقة الاستخدام",
    "support": "حل المشاكل",
    "stats": "إحصائيات البوت",
    "users": "المستخدمون",
    "ban": "حظر مستخدم",
    "unban": "فتح مستخدم",
    "admins": "المشرفون",
    "maintenance": "وضع الصيانة",
    "broadcast": "إذاعة",
    "cleanup": "تنظيف الملفات",
    "video": "فيديو طريقة الاستخدام",
    "add": "إضافة",
    "remove": "إزالة",
    "list": "القائمة",
    "info": "معلوماتي",
    "files": "ملفاتي",
    "history": "سجل العمليات",
    "report": "إبلاغ",
    "improve": "تحسينات",
    "back": "الرئيسية",
    "cancel": "إلغاء",
    "category": "القسم",
    "setting": "الإعداد",
    "change": "تغيير",
    "export": "تصدير",
    "clear": "حذف",
    "reports": "رسائل المشاكل",
    "image": "صورة الترحيب",
    "texts": "تعديل النصوص",
    "welcome": "تغيير الترحيب",
    "uid": "إزالة UID",
    "map_info": "معلومات الخرائط",
    "help_block": "شرح كتلة",
    "help_settings": "شرح تعديل إعدادات الخريطة",
    "help_skins": "شرح السكنات",
    "block": "كتلة",
    "stars": "إضافة نجوم",
    "likes": "إضافة إعجابات",
    "subs": "إضافة اشتراكات",
    "codes": "أكواد",
    "mystats": "إحصائيات حسابي",
}

def admin_emoji_kb():
    rows=[]
    keys=list(EMOJI_NAMES)
    for i in range(0,len(keys),2):
        a=keys[i]; row=[emoji_button(EMOJI_NAMES[a], f"emoji:pick:{a}", a)]
        if i+1<len(keys):
            b=keys[i+1]; row.append(emoji_button(EMOJI_NAMES[b], f"emoji:pick:{b}", b))
        rows.append(row)
    rows.append([emoji_button(" إعادة كل الإيموجيات", "emoji:reset", "change")])
    rows.append([emoji_button(" عرض الـ IDs الحالية", "emoji:list", "list")])
    rows.append([emoji_button(" الرئيسية", "main:home", "back")])
    return InlineKeyboardMarkup(rows)

def admin_kb():
    return InlineKeyboardMarkup([
        [emoji_button("اختبار اتصال الكروب", "admin:test_group", "test")],
        [emoji_button(EMOJI_NAMES["stats"], "admin:stats", "stats"), emoji_button(EMOJI_NAMES["users"], "admin:users", "users")],
        [emoji_button(EMOJI_NAMES["ban"], "admin:ban", "ban"), emoji_button(EMOJI_NAMES["unban"], "admin:unban", "unban")],
        [emoji_button(EMOJI_NAMES["admins"], "admin:admins", "admins"), emoji_button(EMOJI_NAMES["maintenance"], "admin:maintenance", "maintenance")],
        [emoji_button(EMOJI_NAMES["reports"], "admin:reports", "reports"), emoji_button(EMOJI_NAMES["video"], "admin:video", "video")],
        [emoji_button("شروحات الاستخدام", "admin:help_videos", "video"), emoji_button("إدارة الكتلة", "admin:block", "block")],
        [emoji_button(EMOJI_NAMES["broadcast"], "admin:broadcast", "broadcast"), emoji_button(EMOJI_NAMES["cleanup"], "admin:cleanup", "cleanup")],
        [emoji_button(EMOJI_NAMES["change"], "admin:emojis", "change"), emoji_button(EMOJI_NAMES["welcome"], "admin:welcome", "welcome")],
        [emoji_button(" إدارة أكواد النجوم", "admin:star_codes", "codes")],
        [emoji_button(EMOJI_NAMES["back"], "main:home", "back")]
    , [plain_button("إضافة نقاط لمستخدم", callback_data="admin:add_points")]])

def admin_stats_text():
    total = len(USERS)
    blocked = sum(1 for u in USERS.values() if u.get("blocked"))
    active = total - blocked
    messages = sum(int(u.get("messages", 0)) for u in USERS.values())
    return (
        "📊 <b>إحصائيات البوت</b>\n\n"
        f"👥 إجمالي المستخدمين: <b>{total}</b>\n"
        f"🟢 المستخدمون المسموحون: <b>{active}</b>\n"
        f"🚫 المحظورون: <b>{blocked}</b>\n"
        f"💬 إجمالي الرسائل المسجلة: <b>{messages}</b>"
    )

def users_text():
    if not USERS:
        return "👥 لا يوجد مستخدمون مسجلون بعد."
    lines = ["👥 <b>آخر المستخدمين</b>\n"]
    for u in list(USERS.values())[-30:][::-1]:
        status = "🚫 محظور" if u.get("blocked") else "🟢"
        uid = html.escape(str(u.get("id", "")))
        name = html.escape(str(u.get("name", "")))
        username = html.escape("@" + str(u.get("username"))) if u.get("username") else "بدون يوزر"
        lines.append(f"{status} <code>{uid}</code> — {name} — {username}")
    return "\n".join(lines)


def meta(name):
    return next((m for m in METADATA if m["Name"]==name),None)
def name(n):
    if n in TRANSLATIONS:return TRANSLATIONS[n]
    return re.sub(r"(?<!^)([A-Z])",r" \1",n)
def settings(msg):
    if not msg.ShahGCreator.settings:
        msg.ShahGCreator.settings.add()
    return msg.ShahGCreator.settings[0].settings
def find(st,sid):
    return next((x for x in st if x.id==sid),None)
def val(s,m):
    if m["Type"]=="boolean": return "مفعّل ✅" if s.enable else "معطّل ❌"
    return str(s.ratio if m["Type"]=="float" else s.value)

def cats_kb():
    keys=list(CATEGORY_MAPPING)
    rows=[]
    for i in range(0,len(keys),2):
        rows.append([emoji_button(keys[i],f"cat:{i}","category")] +
                    ([emoji_button(keys[i+1],f"cat:{i+1}","category")] if i+1<len(keys) else []))
    rows += [[emoji_button(" تصدير المشروع","export","export")],
             [emoji_button(" حذف الملف الحالي","clear","clear")]]
    return InlineKeyboardMarkup(rows)

def sets_kb(ci):
    rows=[]
    for n in list(CATEGORY_MAPPING.values())[ci]:
        m=meta(n)
        if m: rows.append([emoji_button("️ "+name(n),f"set:{m['ID']}:{ci}","setting")])
    rows.append([emoji_button("️ الأقسام","back","back")])
    return InlineKeyboardMarkup(rows)


# ---------- OUTFIT / SKINS PATCHER ----------
MARKER_RULES = [
    ("SetID", -10001, -269001),
    ("HairID", -10001, -269002),
    ("HeadAdditiveID", -10001, -269003),
    ("FaceID", -10001, -269004),
    ("ChestID", -10001, -269005),
    ("LegsID", -10001, -269006),
    ("FeetID", -10001, -269007),
    ("wSkinIDs", -10001, -14056),
    ("bSkinID", -10001, -14075),
]

def signed_varint64(n):
    v = n & ((1 << 64) - 1)
    out = bytearray()
    while v >= 0x80:
        out.append((v & 0x7f) | 0x80)
        v >>= 7
    out.append(v)
    return bytes(out)

def patch_marker(data, marker_name, old_value, new_value):
    search = b"\x88\x01" + signed_varint64(old_value)
    replace = b"\x88\x01" + signed_varint64(new_value)
    pos = 0
    while True:
        found = data.find(search, pos)
        if found < 0:
            return data, False
        marker_pos = found + len(search) + 94
        if data[marker_pos:marker_pos+len(marker_name)] == marker_name.encode():
            return data[:found] + replace + data[found+len(replace):], True
        pos = found + 1

def read_varint(data, pos):
    result=0
    shift=0
    start=pos
    while pos < len(data):
        b=data[pos]
        pos += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80):
            return result, pos, data[start:pos]
        shift += 7
    raise ValueError("Invalid varint")

def encode_varint(n):
    out=bytearray()
    n=int(n)
    while n >= 0x80:
        out.append((n & 0x7f) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)

def find_field(data, target):
    pos=0
    while pos < len(data):
        tag,pos,_=read_varint(data,pos)
        field=tag>>3
        wire=tag&7
        if wire==0:
            start=pos
            _,pos,raw=read_varint(data,pos)
            if field==target:
                return start,pos,raw,wire
        elif wire==1:
            if field==target: return pos,pos+8,data[pos:pos+8],wire
            pos += 8
        elif wire==2:
            length,p2,_=read_varint(data,pos)
            start=p2
            end=start+length
            if end>len(data): return None
            if field==target:
                return start,end,data[start:end],wire
            pos=end
        elif wire==5:
            if field==target: return pos,pos+4,data[pos:pos+4],wire
            pos += 4
        else:
            return None
    return None

def replace_range(data,start,end,new):
    return data[:start]+new+data[end:]

def patch_skins_zip(input_path, output_path):
    logs=[]
    with zipfile.ZipFile(input_path,"r") as zin:
        names=zin.namelist()
        slots={}
        for n in names:
            clean=n.rsplit("/",1)[-1]
            m=re.match(r"^ProjectData_slot_(\d+)\.bytes$",clean,re.I)
            if m: slots.setdefault(m.group(1),{})["pbytes"]=n
            m=re.match(r"^ProjectData_slot_(\d+)\.meta$",clean,re.I)
            if m: slots.setdefault(m.group(1),{})["meta"]=n
            m=re.match(r"^UserLevelData_(\d+)\.bytes$",clean,re.I)
            if m: slots.setdefault(m.group(1),{})["ul"]=n

        # تحقق من الملفات المطلوبة لكل Slot ولا تتجاهل النقص بصمت.
        missing=[]
        for slot, parts in sorted(slots.items(), key=lambda x:int(x[0])):
            for key, label in (("ul",f"UserLevelData_{slot}.bytes"),("meta",f"ProjectData_slot_{slot}.meta"),("pbytes",f"ProjectData_slot_{slot}.bytes")):
                if key not in parts:
                    missing.append(label)
        valid={k:v for k,v in slots.items() if all(x in v for x in ("ul","meta","pbytes"))}
        if missing:
            raise ValueError("ملف ناقص:\n" + "\n".join(f"• {x}" for x in missing))
        if not valid:
            raise ValueError("ملف السكنات لا يحتوي على ملفات Slot المطلوبة")

        with zipfile.ZipFile(output_path,"w",zipfile.ZIP_DEFLATED) as zout:
            for slot,s in valid.items():
                logs.append(f"STARTING PATCH SEQUENCE FOR SLOT: {slot}")
                ul=zin.read(s["ul"])
                pbytes=zin.read(s["pbytes"])
                meta=zin.read(s["meta"])

                old_ul_md5=hashlib.md5(ul).digest()
                ul_field=find_field(meta,19)
                if ul_field and ul_field[3]==2 and ul_field[2] != old_ul_md5:
                    logs.append(f"CRITICAL ERROR: USERLEVEL MD5 MISMATCH ON SLOT {slot}")
                    continue

                success=0
                fail=0
                for nm,oldv,newv in MARKER_RULES:
                    before=ul
                    ul,changed=patch_marker(ul,nm,oldv,newv)
                    if changed:
                        success += 1
                        logs.append(f"✓ {nm} Injected Successfully")
                    else:
                        fail += 1
                        logs.append(f"× {nm} Layer Skip")

                logs.append(f"SUCCESSFULLY PATCHED OUTFIT LAYERS: {success}")
                if fail:
                    logs.append(f"SKIPPED OUTFIT LAYERS: {fail}")

                # Repair metadata MD5 fields exactly like the original Netlify function.
                new_ul_md5=hashlib.md5(ul).digest()
                size_field=find_field(meta,15)
                if size_field:
                    meta=replace_range(meta,size_field[0],size_field[1],encode_varint(len(pbytes)))

                pmd5_field=find_field(meta,20)
                if pmd5_field and pmd5_field[3]==2:
                    meta=replace_range(meta,pmd5_field[0],pmd5_field[1],hashlib.md5(pbytes).digest())

                ulmd5_field=find_field(meta,19)
                if ulmd5_field and ulmd5_field[3]==2:
                    meta=replace_range(meta,ulmd5_field[0],ulmd5_field[1],new_ul_md5)

                zout.writestr(s["ul"].rsplit("/",1)[-1],ul)
                zout.writestr(s["pbytes"].rsplit("/",1)[-1],pbytes)
                zout.writestr(s["meta"].rsplit("/",1)[-1],meta)

    logs.append("PROCESS COMPLETE!")
    return logs

# ---------- TELEGRAM UI ----------

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    if not is_admin(user.id):
        await update.message.reply_text("⛔ هذا الأمر للمالك فقط.")
        return
    context.user_data.pop("admin_action", None)
    await update.message.reply_text(
        "👑 <b>لوحة تحكم المالك</b>\n\nاختر العملية:",
        reply_markup=admin_kb(), parse_mode="HTML"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = str(user.id) not in USERS
    referrer_id = parse_referrer(update) if is_new else None
    register_user(user)
    if maintenance_enabled() and user.id != ADMIN_ID:
        await update.message.reply_text(maintenance_notice(), parse_mode="HTML")
        return
    if is_new and referrer_id:
        set_referral_on_new_user(user.id, referrer_id)
    # أي مستخدم يدخل من رابط دعوة يجب أن يحل تحققاً رياضياً بسيطاً قبل التفعيل.
    if referral_pending(user.id):
        question = create_math_captcha(user.id)
        context.user_data["await_referral_captcha"] = True
        await update.message.reply_text(
            "🛡️ <b>تحقق سريع</b>\n\n"
            "لإكمال الدخول عبر رابط الدعوة، حل المسألة التالية:\n\n"
            f"🧮 <b>{question} = ؟</b>\n\n"
            "أرسل الناتج فقط.",
            parse_mode="HTML"
        )
        return
    if is_new and user.id != ADMIN_ID:
        try:
            username = f"@{user.username}" if user.username else "بدون يوزر"
            await context.bot.send_message(chat_id=ADMIN_ID, text=(
                "عضو جديد دخل البوت\n\n"
                f"الاسم: {user.full_name}\n"
                f"اليوزر: {username}\n"
                f"الآيدي: {user.id}\n"
                f"إجمالي المستخدمين: {len(USERS)}"
            ))
        except Exception:
            logging.exception("new user notification failed")
    if is_blocked(user.id) and not is_admin(user.id):
        await update.message.reply_text(" تم حظرك من استخدام البوت.")
        return
    # Keep only one main menu message per user.
    old_menu_id = USERS.get(str(user.id), {}).get("menu_message_id")
    if old_menu_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=int(old_menu_id))
        except Exception:
            pass
    dpts=stars_core.load_data(); upts=stars_core.get_user(dpts,user.id); upts["name"]=user.full_name or ""; upts["username"]=user.username or ""; stars_core.save_data(dpts)
    welcome=WELCOME_TEXT.format(user_id=user.id)+f"\n | <b>نقاطك :</b> <code>{upts.get('points',0)}</code>"
    sent = await update.message.reply_text(welcome,reply_markup=main_menu_kb(),parse_mode="HTML")
    USERS[str(user.id)]["menu_message_id"] = sent.message_id
    save_users()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    s=SESSIONS.pop(update.effective_chat.id,None)
    if s and s.get("dir"): shutil.rmtree(s["dir"],ignore_errors=True)
    await update.message.reply_text("🗑 تم إلغاء العملية.")

def main_menu_kb():
    return InlineKeyboardMarkup([
        [emoji_button("تعديل إعدادات الخريطة", "main:settings", "settings"), emoji_button("قسم السكنات", "main:skins", "skins")],
        [emoji_button("حسابي", "main:account", "account")],
        [emoji_button("معلومات خريطة", "main:map_info", "map_info"), emoji_button("إزالة UID", "main:uid", "uid")],
        [emoji_button("إضافة نجوم", "main:stars", "stars")],
        [emoji_button("كتلة", "main:block", "block"), emoji_button("طريقة الاستخدام", "main:help", "help")],
        [emoji_button("حل مشاكل", "main:support", "support")],
    ])

def home_button():
    return InlineKeyboardMarkup([[emoji_button(" الرئيسية","main:home","back")]])

def help_menu():
    # طريقة الاستخدام: 6 أقسام
    return InlineKeyboardMarkup([
        [emoji_button("معلومات الخريطة", "guide:map_info", "help_map_info"),
         emoji_button("إضافة نجوم", "guide:stars", "help_stars")],
        [emoji_button("إزالة UID", "guide:uid", "uid"),
         emoji_button("شرح كتلة", "guide:block", "help_block")],
        [emoji_button("تعديل إعدادات الخريطة", "guide:settings", "help_settings"),
         emoji_button("السكنات", "guide:skins", "help_skins")],
        [emoji_button("الرئيسية", "main:home", "back")]
    ])

def guide_text(key):
    guides = {
        "map_info": (
            "🗺️ <b>طريقة استخدام معلومات الخريطة</b>\n\n"
            "1️⃣ اضغط زر <b>معلومات الخريطة</b>.\n"
            "2️⃣ أرسل رمز الخريطة.\n"
            "3️⃣ سيعرض لك البوت معلومات الخريطة المتوفرة."
        ),
        "stars": (
            " <b>طريقة استخدام إضافة نجوم</b>\n\n"
            "1️⃣ افتح <b>إضافة نجوم</b>.\n"
            "2️⃣ راجع رصيد نقاطك.\n"
            "3️⃣ اختر إضافة إعجابات أو إضافة اشتراكات.\n"
            "4️⃣ يمكنك استخدام الأكواد لإضافة نقاط إلى حسابك."
        ),
        "uid": (
            "🆔 <b>طريقة استخدام إزالة UID</b>\n\n"
            "1️⃣ اضغط <b>إزالة UID</b>.\n"
            "2️⃣ أرسل ملف <code>.bytes</code>.\n"
            "3️⃣ سيحذف البوت UID من الملف ويرسل لك الملف المعدل."
        ),
        "block": (
            "🧱 <b>طريقة استخدام الكتلة</b>\n\n"
            "1️⃣ اضغط <b>كتلة</b> من الرئيسية.\n"
            "2️⃣ أرسل ملف الكتلة المطلوب حسب التعليمات.\n"
            "3️⃣ انتظر معالجة الملف ثم استلم النتيجة."
        ),
        "settings": (
            "⚙️ <b>طريقة استخدام تعديل إعدادات الخريطة</b>\n\n"
            "1️⃣ اضغط <b>تعديل إعدادات الخريطة</b>.\n"
            "2️⃣ أرسل ملف المشروع بصيغة <code>.bytes</code>.\n"
            "3️⃣ اختر القسم والإعداد الذي تريد تعديله.\n"
            "4️⃣ بعد الانتهاء استلم الملف المعدل."
        ),
        "skins": (
            "👕 <b>طريقة استخدام السكنات</b>\n\n"
            "1️⃣ اضغط <b>قسم السكنات</b>.\n"
            "2️⃣ جهز الملفات المطلوبة داخل ملف ZIP.\n"
            "3️⃣ ارفع ملف ZIP وانتظر الفحص والمعالجة.\n"
            "4️⃣ إذا كان ملف مطلوب ناقصًا سيخبرك البوت باسم الملف الناقص."
        )
    }
    return guides[key]

def admin_help_videos_kb():
    rows=[]
    for key, label in (("block","شرح كتلة"),("settings","تعديل إعدادات الخريطة"),("skins","سكنات")):
        rows.append([emoji_button("إضافة/تغيير " + label, f"admin:help_video:{key}", "video")])
    rows.append([emoji_button("حذف شرح", "admin:help_delete", "clear")])
    rows.append([emoji_button("الرئيسية", "admin:back", "back")])
    return InlineKeyboardMarkup(rows)

def support_menu():
    return InlineKeyboardMarkup([
        [emoji_button(" إبلاغ","support:report","report"),
         emoji_button(" إرسال تحسينات","support:improve","improve")],
        [emoji_button(" الرئيسية","main:home","back")]
    ])

def report_attach_menu():
    return InlineKeyboardMarkup([
        [plain_button("️ رفع مع صورة",callback_data="support:photo"),
         plain_button(" عدم رفع",callback_data="support:no_photo")],
        [emoji_button(" إلغاء","support:cancel","cancel")]
    ])


# ---------- نظام النجوم والنقاط ----------
REGION_FLAGS_LOCAL=getattr(stars_core,"REGION_FLAGS",{})
REGION_URLS_LOCAL=getattr(stars_core,"REGION_URLS",{})

def sync_points_user(user):
    data=stars_core.load_data(); u=stars_core.get_user(data,user.id)
    u["name"]=user.full_name or ""; u["username"]=user.username or ""; stars_core.save_data(data); return data,u

DAILY_REWARD_POINTS = 10
DAILY_REWARD_SECONDS = 24 * 60 * 60

# ---------- Stars FIFO queue (max 3 waiting + 1 active) ----------
STARS_QUEUE_LIMIT = 3
STARS_QUEUE = []
STARS_QUEUE_LOCK = asyncio.Lock()
STARS_QUEUE_WORKER = None
STARS_ACTIVE_CHAT = None
STARS_TICKETS = 0

def stars_queue_position(chat_id):
    for i, item in enumerate(STARS_QUEUE):
        if item["chat_id"] == chat_id:
            return i + 1
    return 0

def stars_user_busy(chat_id):
    return STARS_ACTIVE_CHAT == chat_id or any(x["chat_id"] == chat_id for x in STARS_QUEUE)

def stars_queue_size():
    return len(STARS_QUEUE)

async def stars_queue_worker(ctx):
    global STARS_ACTIVE_CHAT, STARS_QUEUE_WORKER
    try:
        while STARS_QUEUE:
            item = STARS_QUEUE.pop(0)
            STARS_ACTIVE_CHAT = item["chat_id"]
            try:
                await ctx.bot.send_message(item["chat_id"], "🟢 <b>جاء دورك الآن</b>\n\n📊 ستظهر حالة التقدم هنا مع كل حساب تتم معالجته.", parse_mode="HTML")
                await run_star_job(ctx, item["chat_id"], item["action"], item["region"], item["map_code"], item["amount"])
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("stars queue item failed")
            finally:
                STARS_ACTIVE_CHAT = None
                # Refresh positions for remaining users.
                for idx, queued in enumerate(STARS_QUEUE, 1):
                    try:
                        await ctx.bot.send_message(queued["chat_id"], f"⏳ <b>حالة الطابور</b>\n\n📍 مركزك: <b>{idx}</b>\n👥 قبلك: <b>{idx-1}</b>", parse_mode="HTML")
                    except Exception:
                        logging.exception("queue position update failed")
    finally:
        STARS_QUEUE_WORKER = None

async def enqueue_star_job(ctx, chat_id, action, region, map_code, amount):
    global STARS_QUEUE_WORKER, STARS_TICKETS
    async with STARS_QUEUE_LOCK:
        if stars_user_busy(chat_id):
            pos = stars_queue_position(chat_id)
            return False, f"⚠️ عندك طلب قيد التنفيذ أو الانتظار حالياً.\n📍 مركزك بالطابور: <b>{pos}</b>"
        if len(STARS_QUEUE) >= STARS_QUEUE_LIMIT:
            return False, "⛔ الطابور ممتلئ حالياً.\n\nالحد الأقصى 3 أشخاص بالانتظار."
        STARS_TICKETS += 1
        ticket = STARS_TICKETS
        STARS_QUEUE.append({"ticket":ticket,"chat_id":chat_id,"action":action,"region":region,"map_code":map_code,"amount":amount})
        pos = len(STARS_QUEUE)
        if STARS_QUEUE_WORKER is None:
            STARS_QUEUE_WORKER = asyncio.create_task(stars_queue_worker(ctx))
    if STARS_ACTIVE_CHAT is None and pos == 1:
        return True, f"🟢 <b>سيبدأ طلبك الآن</b>\n\n🔢 رقم الطلب: <code>#{ticket}</code>"
    return True, f"⏳ <b>تمت إضافة طلبك للطابور</b>\n\n🔢 رقم الطلب: <code>#{ticket}</code>\n📍 مركزك: <b>{pos}</b>\n👥 قبلك: <b>{pos-1}</b>"

def daily_reward_status(user_id):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    last = float(u.get("daily_reward_at", 0) or 0)
    remaining = int(last + DAILY_REWARD_SECONDS - time.time())
    if remaining > 0:
        h, rem = divmod(remaining, 3600)
        m, sec = divmod(rem, 60)
        return False, f"{h:02d}:{m:02d}:{sec:02d}"
    return True, "00:00:00"

def claim_daily_reward(user_id):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    last = float(u.get("daily_reward_at", 0) or 0)
    if time.time() - last < DAILY_REWARD_SECONDS:
        return False, int(u.get("points", 0))
    u["points"] = int(u.get("points", 0)) + DAILY_REWARD_POINTS
    u["daily_reward_at"] = time.time()
    stars_core.save_data(data)
    return True, int(u["points"])


# ---------- نظام المكافآت الإضافية ----------
REFERRAL_REWARD_POINTS = 100
DAILY_CHALLENGE_REWARD = 20
DAILY_SPIN_SECONDS = 24 * 60 * 60
DAILY_SECRET_MAX_USERS = 50
DAILY_SECRET_REWARD = 100
DAILY_SPIN_REWARDS = [5, 10, 15, 20, 30, 50, 100]

def _day_key():
    return time.strftime("%Y-%m-%d")

def _user_data(user_id):
    data = stars_core.load_data()
    return data, stars_core.get_user(data, user_id)

def _save_user_fields(user_id, **fields):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    for k, v in fields.items():
        u[k] = v
    stars_core.save_data(data)
    return u

def add_points(user_id, amount):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    u["points"] = int(u.get("points", 0)) + int(amount)
    stars_core.save_data(data)
    return int(u["points"])

def referral_link(bot_username, user_id):
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

def parse_referrer(update):
    msg = getattr(update, "message", None)
    if not msg or not getattr(msg, "text", None):
        return None
    parts = msg.text.strip().split(maxsplit=1)
    if len(parts) != 2:
        return None
    arg = parts[1].strip()
    if not arg.startswith("ref_"):
        return None
    raw = arg[4:]
    return int(raw) if raw.isdigit() else None

def set_referral_on_new_user(user_id, referrer_id):
    if not referrer_id or int(referrer_id) == int(user_id):
        return False
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    if u.get("referrer_id"):
        return False
    u["referrer_id"] = int(referrer_id)
    u["referral_verified"] = False
    u["referral_qualified"] = False
    u["referral_captcha"] = None
    stars_core.save_data(data)
    return True

def referral_pending(user_id):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    return bool(u.get("referrer_id")) and not bool(u.get("referral_verified"))

def create_math_captcha(user_id):
    a = random.randint(2, 20)
    b = random.randint(1, 20)
    op = random.choice(["+", "-"])
    if op == "+":
        answer = a + b
    else:
        if a < b:
            a, b = b, a
        answer = a - b
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    u["referral_captcha"] = {"question": f"{a} {op} {b}", "answer": answer, "created": time.time()}
    stars_core.save_data(data)
    return f"{a} {op} {b}"

def verify_referral_captcha(user_id, answer):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    cap = u.get("referral_captcha") or {}
    if not cap or str(answer).strip() != str(cap.get("answer")):
        return False
    u["referral_verified"] = True
    u["referral_captcha"] = None
    stars_core.save_data(data)
    return True

def qualify_referral(user_id):
    """تُستدعى عند أول استخدام فعلي بعد التحقق؛ المكافأة تُمنح مرة واحدة فقط."""
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    if not u.get("referrer_id") or not u.get("referral_verified") or u.get("referral_qualified"):
        return None
    # أي نشاط فعلي ناجح بعد التحقق يؤهل الدعوة.
    ref_id = int(u["referrer_id"])
    ref = stars_core.get_user(data, ref_id)
    ref["points"] = int(ref.get("points", 0)) + REFERRAL_REWARD_POINTS
    ref.setdefault("successful_referrals", 0)
    ref["successful_referrals"] += 1
    u["referral_qualified"] = True
    stars_core.save_data(data)
    return ref_id

async def qualify_referral_and_notify(context, user_id):
    """تؤهل الدعوة بعد أول استخدام فعلي وترسل إشعاراً لصاحب الرابط مرة واحدة."""
    ref_id = qualify_referral(user_id)
    if not ref_id:
        return None
    try:
        await context.bot.send_message(
            chat_id=ref_id,
            text=(
                "🎉 <b>إشعار دعوة جديدة</b>\n\n"
                "👤 أحد المستخدمين دخل البوت من رابط دعوتك وأكمل أول استخدام فعلي.\n"
                f"🎁 تمت إضافة <b>{REFERRAL_REWARD_POINTS}</b> نقطة إلى رصيدك.\n"
                "📊 يمكنك مشاهدة إحصائيات الدعوات من <b>إحصائيات حسابي</b>."
            ),
            parse_mode="HTML"
        )
    except Exception:
        logging.exception("could not notify referrer")
    return ref_id

def referral_text(user, bot_username):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user.id)
    link = referral_link(bot_username, user.id)
    successful = int(u.get("successful_referrals", 0))
    return (
        "👥 <b>رابط الدعوة</b>\n\n"
        "🔗 رابطك الخاص:\n"
        f"<code>{link}</code>\n\n"
        f"🎁 مكافأة الدعوة: <b>{REFERRAL_REWARD_POINTS}</b> نقطة\n"
        f"👥 الدعوات الناجحة: <b>{successful}</b>\n\n"
        "✅ تنحسب مكافأة الدعوة بعد أول استخدام فعلي للعضو الجديد."
    )

def daily_challenge_question():
    # سؤال يومي ثابت خلال نفس اليوم حتى لا يتغير أثناء المحاولة.
    seed = int(time.strftime("%Y%m%d"))
    rng = random.Random(seed)
    a = rng.randint(5, 40)
    b = rng.randint(2, 30)
    if a < b:
        a, b = b, a
    op = rng.choice(["+", "-", "×"])
    ans = a + b if op == "+" else a - b if op == "-" else a * b
    return f"{a} {op} {b}", ans

def claim_daily_challenge(user_id, answer):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    if u.get("daily_challenge_day") == _day_key():
        return False, "already", int(u.get("points", 0))
    _, correct = daily_challenge_question()
    if str(answer).strip() != str(correct):
        return False, "wrong", int(u.get("points", 0))
    u["points"] = int(u.get("points", 0)) + DAILY_CHALLENGE_REWARD
    u["daily_challenge_day"] = _day_key()
    stars_core.save_data(data)
    return True, "ok", int(u["points"])

def claim_daily_spin(user_id):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    last = float(u.get("daily_spin_at", 0) or 0)
    if time.time() - last < DAILY_SPIN_SECONDS:
        remain = int(last + DAILY_SPIN_SECONDS - time.time())
        h, rem = divmod(remain, 3600); m, sec = divmod(rem, 60)
        return False, 0, f"{h:02d}:{m:02d}:{sec:02d}"
    reward = random.choice(DAILY_SPIN_REWARDS)
    u["points"] = int(u.get("points", 0)) + reward
    u["daily_spin_at"] = time.time()
    stars_core.save_data(data)
    return True, reward, "00:00:00"

def daily_secret_code():
    # يتغير تلقائياً كل يوم. يمكن للأدمن نشره للمستخدمين.
    return "SECRET-" + hashlib.sha256(_day_key().encode()).hexdigest()[:8].upper()

def redeem_daily_secret(user_id, code):
    data = stars_core.load_data()
    u = stars_core.get_user(data, user_id)
    if u.get("daily_secret_day") == _day_key():
        return False, "already", 0
    if stars_core.clean_code(code) != stars_core.clean_code(daily_secret_code()):
        return False, "wrong", 0
    used = int(data.get("daily_secret_used", 0) or 0)
    if used >= DAILY_SECRET_MAX_USERS:
        return False, "full", 0
    u["points"] = int(u.get("points", 0)) + DAILY_SECRET_REWARD
    u["daily_secret_day"] = _day_key()
    data["daily_secret_used"] = used + 1
    stars_core.save_data(data)
    return True, "ok", int(u["points"])

def rewards_menu():
    return InlineKeyboardMarkup([
        [emoji_button(" انشر واربح", "publish:earn", "stars")],
        [emoji_button(" رابط دعوتي", "reward:referral", "account")],
        [emoji_button(" رجوع", "main:stars", "back")]
    ])

def stars_menu(user):
    _,u=sync_points_user(user); pts=int(u.get("points",0))
    text=(
        f" <b>إضافة نجوم</b>\n\n"
        f"💰 نقاطك الحالية: <b>{pts}</b>\n\n"
        "اختر الخدمة التي تريدها:"
    )
    kb=InlineKeyboardMarkup([
        [emoji_button(" إضافة اشتراكات","stars:sub","subs"), emoji_button(" إضافة اشتراكات رمز طويل","stars:long_sub","subs")],
        [emoji_button(" شراء بالنجوم","stars:buy","stars")],
        [emoji_button(" الأكواد","stars:codes","codes"), emoji_button(" انشر واربح","publish:earn","stars")],
        [emoji_button(" إحصائيات حسابي","stars:stats","mystats"), emoji_button(" رابط دعوتي","reward:referral","account")],
        [emoji_button(" الرئيسية","main:home","back")]
    ])
    return text,kb

# باقات النقاط المدفوعة بـ Telegram Stars
STAR_POINT_PACKAGES = {
    100: 1,
    200: 2,
    300: 3,
    400: 4,
    500: 5,
    600: 6,
    700: 7,
    800: 8,
    900: 9,
    1000: 10,
}

def stars_buy_menu():
    rows=[]
    packages=list(STAR_POINT_PACKAGES.items())
    for i in range(0, len(packages), 2):
        row=[]
        for points, stars in packages[i:i+2]:
            row.append(
                emoji_button(f"{points} نقطة — {stars} ", f"stars:buy:{points}", "stars")
            )
        rows.append(row)
    rows.append([emoji_button(" رجوع", "main:stars", "back")])
    return InlineKeyboardMarkup(rows)

async def send_points_invoice(ctx, chat_id, user_id, points, stars):
    payload=f"points:{user_id}:{points}:{stars}"
    await ctx.bot.send_invoice(
        chat_id=chat_id,
        title=f"شراء {points} نقطة",
        description=f"إضافة {points} نقطة إلى رصيدك مقابل {stars} نجمة Telegram.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"{points} نقطة", amount=stars)]
    )

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query=update.pre_checkout_query
    try:
        parts=query.invoice_payload.split(":")
        if len(parts) != 4 or parts[0] != "points":
            await query.answer(ok=False, error_message="❌ بيانات الدفع غير صالحة.")
            return

        payload_user=int(parts[1])
        points=int(parts[2])
        stars=int(parts[3])

        if payload_user != query.from_user.id:
            await query.answer(ok=False, error_message="❌ هذه الفاتورة ليست لحسابك.")
            return

        if STAR_POINT_PACKAGES.get(points) != stars or query.currency != "XTR" or query.total_amount != stars:
            await query.answer(ok=False, error_message="❌ بيانات السعر غير صحيحة.")
            return

        await query.answer(ok=True)
    except Exception:
        logging.exception("pre-checkout validation failed")
        await query.answer(ok=False, error_message="❌ تعذر التحقق من عملية الدفع.")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment=update.message.successful_payment
    user=update.effective_user
    if not payment:
        return

    try:
        parts=payment.invoice_payload.split(":")
        if len(parts) != 4 or parts[0] != "points":
            return

        payload_user=int(parts[1])
        points=int(parts[2])
        stars=int(parts[3])

        if payload_user != user.id:
            return
        if STAR_POINT_PACKAGES.get(points) != stars:
            return
        if payment.currency != "XTR" or payment.total_amount != stars:
            return

        data=stars_core.load_data()
        u=stars_core.get_user(data, user.id)

        # منع إضافة النقاط مرتين لنفس عملية الدفع
        charge_id=getattr(payment, "telegram_payment_charge_id", "") or ""
        paid_ids=data.setdefault("star_payments", {})
        if charge_id and charge_id in paid_ids:
            await update.message.reply_text("ℹ️ تم تسجيل عملية الدفع هذه مسبقاً.", reply_markup=home_button())
            return

        u["points"]=int(u.get("points",0)) + points
        u.setdefault("star_purchases", []).append({
            "points": points,
            "stars": stars,
            "charge_id": charge_id,
            "time": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        if charge_id:
            paid_ids[charge_id]={
                "user_id": user.id,
                "points": points,
                "stars": stars,
                "time": time.time()
            }
        stars_core.save_data(data)

        await update.message.reply_text(
            f"✅ <b>تم الدفع بنجاح!</b>\n\n"
            f" المدفوع: <b>{stars}</b> نجوم\n"
            f"💰 تمت إضافة: <b>{points}</b> نقطة\n"
            f"📊 رصيدك الآن: <b>{u['points']}</b> نقطة",
            reply_markup=home_button(),
            parse_mode="HTML"
        )
    except Exception:
        logging.exception("successful payment handling failed")
        await update.message.reply_text(
            "⚠️ تم استلام الدفع، لكن حدث خطأ أثناء إضافة النقاط. يرجى التواصل مع الدعم.",
            reply_markup=home_button()
        )

def codes_text():
    data=stars_core.load_data(); codes=data.get("codes",{})
    if not codes:return "🔑 <b>أكواد النجوم</b>\n\nلا توجد أكواد حالياً."
    out=["🔑 <b>أكواد النجوم</b>"]
    for c,info in list(codes.items())[-30:][::-1]:
        if isinstance(info,(int,float)): out.append(f"<code>{c}</code> —  {int(info)}")
        else: out.append(f"<code>{c}</code> —  {info.get('points',0)} — {info.get('used',0)}/{info.get('max_redeem',10)}")
    return "\n".join(out)

def make_star_code(): return "STAR-"+"".join(random.choice(string.ascii_uppercase+string.digits) for _ in range(10))


USAGE_GROUP_ID = -1004493541592

async def notify_usage_group(ctx, user, section, details=""):
    try:
        name = getattr(user, "full_name", None) or getattr(user, "first_name", None) or "بدون اسم"
        username = getattr(user, "username", None)
        uid = getattr(user, "id", "")
        text = (
            "📌 استخدام جديد للبوت\n\n"
            f"👤 الاسم: {name}\n"
            f"🆔 ID: {uid}\n"
            f"🔗 اليوزر: @{username}" if username else f"🔗 اليوزر: بدون يوزر"
        )
        text += f"\n📂 القسم: {section}"
        if details:
            text += f"\n📝 التفاصيل: {details}"
        await ctx.bot.send_message(
            chat_id=USAGE_GROUP_ID,
            text=text,
            disable_web_page_preview=True
        )
        logging.info("Usage notification sent to %s for user %s", USAGE_GROUP_ID, uid)
    except Exception as exc:
        # Do not hide Telegram's actual error.
        logging.exception("Usage group send failed: %s", exc)

async def test_usage_group(ctx, user_id):
    try:
        await ctx.bot.send_message(
            chat_id=USAGE_GROUP_ID,
            text="🔔 اختبار اتصال سجل الاستخدام\n\nالبوت متصل بهذه المجموعة بنجاح."
        )
        return True, ""
    except Exception as exc:
        logging.exception("Usage group test failed: %s", exc)
        return False, f"{type(exc).__name__}: {exc}"



async def run_star_job(ctx, chat_id, action, region, map_code, amount):
    deducted = 0
    progress_message = None
    try:
        data = stars_core.load_data()
        u = stars_core.get_user(data, chat_id)
        points = int(u.get("points", 0))
        amount = int(amount)
        if amount <= 0:
            await ctx.bot.send_message(chat_id, "❌ العدد غير صحيح.", reply_markup=home_button()); return
        if points < amount:
            await ctx.bot.send_message(chat_id, f"❌ نقاطك غير كافية.\n💰 رصيدك: <b>{points}</b>", reply_markup=home_button(), parse_mode="HTML"); return
        u["points"] = points - amount
        stars_core.save_data(data); deducted = amount
        raw = stars_core.load_raw_accounts_file() or []
        accounts=[]
        for rec in raw:
            if isinstance(rec,dict):
                uid=rec.get("uid"); password=rec.get("password") or rec.get("pass")
                if uid is not None and password:
                    accounts.append({"record":rec,"u":str(uid),"p":str(password)})
        take=accounts[:amount]
        if not take:
            data=stars_core.load_data(); u=stars_core.get_user(data,chat_id); u["points"]=int(u.get("points",0))+deducted; stars_core.save_data(data); deducted=0
            await ctx.bot.send_message(chat_id," لا توجد حسابات متوفرة في acc.json.\n تمت إعادة نقاطك.",reply_markup=home_button()); return

        progress_message=await ctx.bot.send_message(chat_id, f"📊 <b>حالة العملية</b>\n\n🗺️ الخريطة: <code>{map_code}</code>\n📈 التقدم: <b>0</b> / <b>{len(take)}</b>\n📥 الاشتراكات: <b>0</b>\n❌ فشل: <b>0</b>", parse_mode="HTML")

        def run_one(item):
            try:
                result=stars_core.execute_with_retry({"u":item["u"],"p":item["p"]},region,action,map_code)
                return (bool(result[0]), str(result[1] or "")) if isinstance(result,tuple) else (bool(result),"")
            except Exception as exc:
                logging.exception("account execution failed uid=%s",item["u"]); return False,str(exc)

        good=[]; bad=[]; done=0
        loop=asyncio.get_running_loop()
        # تنفيذ الحسابات واحداً تلو الآخر حتى تبقى العملية واضحة،
        # وعند اكتمال كل الحسابات تتوقف العملية وتعرض النتيجة النهائية.
        for item in take:
            try:
                ok,reason=await loop.run_in_executor(None, run_one, item)
            except Exception as exc:
                ok,reason=False,str(exc)
            (good if ok else bad).append(item); done+=1
            try:
                await progress_message.edit_text(
                    f"📊 <b>حالة العملية</b>\n\n🗺️ الخريطة: <code>{map_code}</code>\n📈 التقدم: <b>{done}</b> / <b>{len(take)}</b>\n📥 الاشتراكات: <b>{len(good)}</b>\n❌ فشل: <b>{len(bad)}</b>", parse_mode="HTML")
            except Exception:
                pass

        if good:
            try: stars_core.consume_successful_accounts([x["u"] for x in good])
            except Exception: logging.exception("successful-account cleanup failed")
        if bad:
            try: stars_core.move_failed_accounts_to_da([x["record"] for x in bad])
            except Exception: logging.exception("failed-account archive failed")

        refund=len(bad)+max(0,amount-len(take))
        data=stars_core.load_data(); u=stars_core.get_user(data,chat_id); u["points"]=int(u.get("points",0))+refund; u["total_subs"]=int(u.get("total_subs",0))+len(good); stars_core.save_data(data); deducted=0
        if good: set_feature_cooldown(chat_id,"stars")
        final=(f"{'✅' if good else '❌'} <b>انتهت العملية</b>\n\n🗺️ الخريطة: <code>{map_code}</code>\n📥 اشتراكات: <b>{len(good)}</b>\n❌ فشل: <b>{len(bad)}</b>\n💰 مسترجع: <b>{refund}</b>\n💳 رصيدك: <b>{u.get('points',0)}</b>")
        try: await progress_message.edit_text(final,reply_markup=home_button(),parse_mode="HTML")
        except Exception: await ctx.bot.send_message(chat_id,final,reply_markup=home_button(),parse_mode="HTML")
        if good:
            await qualify_referral_and_notify(ctx, chat_id)
            try:
                await ctx.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        "🎉 <b>تمت العملية بنجاح!</b>\n\n"
                        f"🗺️ الخريطة: <code>{map_code}</code>\n"
                        f"📥 تمت إضافة: <b>{len(good)}</b> اشتراك\n"
                        f"❌ الفشل: <b>{len(bad)}</b>\n"
                        f"💳 رصيدك الحالي: <b>{u.get('points',0)}</b> نقطة"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                logging.exception("operation success notification failed")
            await notify_usage_group(ctx, u, "إضافة نجوم", f"الخريطة: {map_code} | المطلوب: {amount} | نجح: {len(good)} | فشل: {len(bad)}")
    except asyncio.CancelledError:
        raise
    except Exception:
        logging.exception("STAR JOB UNHANDLED ERROR")
        if deducted:
            try:
                data=stars_core.load_data(); u=stars_core.get_user(data,chat_id); u["points"]=int(u.get("points",0))+deducted; stars_core.save_data(data)
            except Exception: logging.exception("stars refund failed")
        try: await ctx.bot.send_message(chat_id,"❌ حدث خطأ أثناء معالجة الطلب.\n💰 تمت إعادة النقاط المحجوزة، والبوت مستمر بالعمل.",reply_markup=home_button())
        except Exception: logging.exception("could not report star failure")


LONG_SUB_CODE_PATTERN = re.compile(r"^#FREEFIRE[0-9A-Fa-f]{36}$")

def validate_long_sub_code(raw):
    code=(raw or "").strip().split()[0] if (raw or "").strip() else ""
    if not LONG_SUB_CODE_PATTERN.fullmatch(code):
        return None
    return code

LONG_SUB_ACTIVE = set()
LONG_SUB_TASKS = set()

def _track_long_sub_task(task):
    LONG_SUB_TASKS.add(task)
    def _done(t):
        LONG_SUB_TASKS.discard(t)
        try:
            exc = t.exception()
            if exc:
                logging.exception("LONG SUB background task ended with error", exc_info=exc)
        except (asyncio.CancelledError, Exception):
            pass
    task.add_done_callback(_done)
    return task

async def enqueue_long_sub_job(ctx,chat_id,region,map_code,amount):
    if cooldown_text(chat_id,"stars_long_sub"):
        return False,cooldown_text(chat_id,"stars_long_sub")
    if chat_id in LONG_SUB_ACTIVE or stars_user_busy(chat_id):
        return False,"⚠️ عندك طلب قيد التنفيذ أو الانتظار حالياً."
    LONG_SUB_ACTIVE.add(chat_id)
    _track_long_sub_task(asyncio.create_task(run_long_sub_job(ctx,chat_id,region,map_code,amount)))
    return True,"🚀 <b>بدأت العملية.</b> سيتم تحديث حالة التنفيذ هنا."

async def run_long_sub_job(ctx, chat_id, region, map_code, amount):
    deducted = 0
    progress_message = None
    executor = None
    good = []
    bad = []
    try:
        data = stars_core.load_data()
        u = stars_core.get_user(data, chat_id)
        points = int(u.get("points", 0))
        amount = int(amount)
        if amount <= 0:
            await ctx.bot.send_message(chat_id, "❌ العدد غير صحيح.", reply_markup=home_button())
            return
        if points < amount:
            await ctx.bot.send_message(chat_id, f"❌ نقاطك غير كافية.\n💰 رصيدك: <b>{points}</b>", reply_markup=home_button(), parse_mode="HTML")
            return

        lookup_code = map_code.lstrip("#")
        info, error = get_map_info(lookup_code)
        if error or not info:
            await ctx.bot.send_message(
                chat_id,
                "❌ رمز الخريطة غير صحيح أو الخريطة غير موجودة.\nلم تبدأ العملية ولم يتم خصم أي نقاط.",
                reply_markup=home_button(), parse_mode="HTML"
            )
            return

        u["points"] = points - amount
        stars_core.save_data(data)
        deducted = amount

        raw = stars_core.load_raw_accounts_file() or []
        accounts = []
        for rec in raw:
            if isinstance(rec, dict):
                uid = rec.get("uid")
                password = rec.get("password") or rec.get("pass")
                if uid is not None and password:
                    accounts.append({"record": rec, "u": str(uid), "p": str(password)})
        take = accounts[:amount]
        if not take:
            data = stars_core.load_data()
            u = stars_core.get_user(data, chat_id)
            u["points"] = int(u.get("points", 0)) + deducted
            stars_core.save_data(data)
            deducted = 0
            await ctx.bot.send_message(chat_id, "❌ لا توجد حسابات متوفرة في acc.json.\n💰 تمت إعادة نقاطك.", reply_markup=home_button())
            return

        map_name = html.escape(str(info.get("name", "غير معروف")))
        progress_message = await ctx.bot.send_message(
            chat_id,
            f"📊 <b>حالة العملية</b>\n\n🗺️ الخريطة: <code>{html.escape(str(map_code))}</code>\n📌 الاسم: <b>{map_name}</b>\n🔑 النوع: <b>رمز طويل</b>\n📈 التقدم: <b>0</b> / <b>{len(take)}</b>\n📥 الاشتراكات: <b>0</b>\n❌ فشل: <b>0</b>",
            parse_mode="HTML"
        )

        def run_one(item):
            try:
                return bool(long_sub_core.run_task(item["u"], item["p"], region, "1", map_code))
            except BaseException as exc:
                logging.error("long subscription failed uid=%s: %s", item.get("u"), exc, exc_info=True)
                return False

        # Run workers in a separate executor and make sure an exception in one worker
        # can never terminate the bot's polling loop.
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=max(1, min(5, len(take))))
        future_map = {loop.run_in_executor(executor, run_one, item): item for item in take}
        while future_map:
            done_set, _ = await asyncio.wait(list(future_map.keys()), return_when=asyncio.FIRST_COMPLETED)
            for fut in done_set:
                item = future_map.pop(fut)
                try:
                    ok = bool(await fut)
                except BaseException as exc:
                    logging.error("long subscription future failed: %s", exc, exc_info=True)
                    ok = False
                (good if ok else bad).append(item)
                done = len(good) + len(bad)
                try:
                    await progress_message.edit_text(
                        f"📊 <b>حالة العملية</b>\n\n🗺️ الخريطة: <code>{html.escape(str(map_code))}</code>\n📌 الاسم: <b>{map_name}</b>\n🔑 النوع: <b>رمز طويل</b>\n📈 التقدم: <b>{done}</b> / <b>{len(take)}</b>\n📥 الاشتراكات: <b>{len(good)}</b>\n❌ فشل: <b>{len(bad)}</b>",
                        parse_mode="HTML"
                    )
                except Exception:
                    logging.exception("long-sub progress update failed")

        # At this point every account has finished. Send the final result BEFORE
        # any account-file cleanup, so a slow/failed cleanup cannot hide the result.
        refund = len(bad) + max(0, amount - len(take))
        data = stars_core.load_data()
        u = stars_core.get_user(data, chat_id)
        new_points = int(u.get("points", 0)) + refund
        final = (
            f"{'✅' if good else '❌'} <b>انتهت العملية</b>\n\n"
            f"🗺️ الخريطة: <code>{html.escape(str(map_code))}</code>\n"
            f"📌 الاسم: <b>{map_name}</b>\n"
            f"🔑 النوع: <b>رمز طويل</b>\n"
            f"📥 اشتراكات: <b>{len(good)}</b>\n"
            f"❌ فشل: <b>{len(bad)}</b>\n"
            f"💰 مسترجع: <b>{refund}</b>\n"
            f"💳 رصيدك: <b>{new_points}</b>"
        )
        try:
            await progress_message.edit_text(final, reply_markup=home_button(), parse_mode="HTML")
        except Exception:
            await ctx.bot.send_message(chat_id, final, reply_markup=home_button(), parse_mode="HTML")

        # Save points immediately; cleanup is isolated so it cannot crash the bot.
        u["points"] = new_points
        u["total_subs"] = int(u.get("total_subs", 0)) + len(good)
        stars_core.save_data(data)
        deducted = 0
        if good:
            set_feature_cooldown(chat_id, "stars_long_sub")

        async def safe_cleanup():
            try:
                if good:
                    await asyncio.to_thread(stars_core.consume_successful_accounts, [x["u"] for x in good])
                if bad:
                    await asyncio.to_thread(stars_core.move_failed_accounts_to_da, [x["record"] for x in bad])
            except Exception:
                logging.exception("long-sub account cleanup failed; bot will continue running")

        # Cleanup is best-effort and is never allowed to block Telegram polling.
        _track_long_sub_task(asyncio.create_task(safe_cleanup()))

        if good:
            try:
                await asyncio.wait_for(qualify_referral_and_notify(ctx, chat_id), timeout=10)
            except Exception:
                logging.exception("long-sub referral notification failed")
            try:
                await asyncio.wait_for(
                    notify_usage_group(ctx, u, "إضافة اشتراكات رمز طويل",
                                       f"الخريطة: {map_code} | المطلوب: {amount} | نجح: {len(good)} | فشل: {len(bad)}"),
                    timeout=10
                )
            except Exception:
                logging.exception("long-sub usage notification failed")

    except asyncio.CancelledError:
        raise
    except BaseException as exc:
        logging.error("LONG SUB JOB UNHANDLED ERROR: %s", exc, exc_info=True)
        if deducted:
            try:
                data = stars_core.load_data()
                u = stars_core.get_user(data, chat_id)
                u["points"] = int(u.get("points", 0)) + deducted
                stars_core.save_data(data)
            except Exception:
                logging.exception("long-sub refund failed")
        try:
            await ctx.bot.send_message(
                chat_id,
                "❌ حدث خطأ أثناء معالجة الطلب.\n💰 تمت إعادة النقاط المحجوزة.\n\nالبوت مستمر بالعمل.",
                reply_markup=home_button()
            )
        except Exception:
            logging.exception("could not report long-sub failure")
    finally:
        if executor is not None:
            try:
                executor.shutdown(wait=False, cancel_futures=False)
            except Exception:
                pass
        LONG_SUB_ACTIVE.discard(chat_id)

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    chat=q.message.chat.id
    data=q.data
    user=update.effective_user
    register_user(user)
    if is_blocked(user.id) and not is_admin(user.id):
        await q.edit_message_text("🚫 تم حظرك من استخدام البوت.")
        return
    s=SESSIONS.get(chat)

    if maintenance_enabled() and user.id != ADMIN_ID and not data.startswith("admin:"):
        await q.answer("🔧 البوت في وضع الصيانة حالياً", show_alert=True)
        return
    if data=="main:stars":
        cd=cooldown_text(user.id,"stars")
        if cd:
            await q.edit_message_text(cd,reply_markup=home_button(),parse_mode="HTML"); return
        t,k=stars_menu(user); await q.edit_message_text(t+"\n\n📌 <b>طريقة الاستخدام:</b> اختر الإعجابات أو الاشتراكات ثم أدخل العدد والمنطقة وكود الخريطة.",reply_markup=k,parse_mode="HTML"); return
    if data=="publish:earn":
        await q.answer()
        await q.edit_message_text(' انشر واربح مع عبودي التوب \n\n المكافأة:\n️ كل 1,000 مشاهدة = 500 نقطة \n\n البوت: @Abouditop1bot\n️ الهاشتاك المطلوب: #Abouditop1bot\n\n━━━━━━━━━━━━━━\n\n طريقة النشر:\n\n تيليجرام\nانشر منشور جديد أو أعد توجيه المنشور، وأضف في نهاية المنشور:\n#Abouditop1bot\nثم انشر رابط البوت:\n@Abouditop1bot\n\n فيسبوك\nأنشئ منشورًا جديدًا، اكتب عن البوت، ثم أضف:\n#Abouditop1bot\nوأرفق رابط البوت أو اكتب @Abouditop1bot.\n\n إنستغرام\nانشر صورة أو فيديو عن البوت، وفي وصف المنشور (Caption) أضف:\n#Abouditop1bot\nثم ضع رابط البوت في المكان المناسب.\n\n تيك توك\nانشر فيديو عن البوت، وفي وصف الفيديو أضف:\n#Abouditop1bot\nويمكنك ذكر:\n@Abouditop1bot\n\n▶️ يوتيوب\nانشر فيديو عن البوت، وفي وصف الفيديو أضف:\n#Abouditop1bot\nواكتب رابط البوت أيضًا.\n\n X / تويتر\nاكتب منشورًا عن البوت، وأضف في نهاية المنشور:\n#Abouditop1bot\nثم أرسل المنشور.\n\n━━━━━━━━━━━━━━\n\n بعد النشر:\n كلما زادت المشاهدات على منشورك، زادت نقاطك.\n\n 1,000 مشاهدة = 500 نقطة\n\n️ يجب أن يكون المنشور عامًا والمشاهدات حقيقية وطبيعية.\n المشاهدات الوهمية أو التلاعب قد يؤدي إلى إلغاء النقاط.\n\n انشر الآن وابدأ بجمع النقاط!\n\n @Abouditop1bot\n#Abouditop1bot', reply_markup=home_button(), parse_mode="HTML")
        return
    if data=="stars:buy":
        await q.edit_message_text(
            " <b>شراء النقاط بالنجوم</b>\n\n"
            "اختر الباقة التي تريد شراءها:",
            reply_markup=stars_buy_menu(),
            parse_mode="HTML"
        )
        return

    if data.startswith("stars:buy:"):
        try:
            points=int(data.split(":",2)[2])
            stars=STAR_POINT_PACKAGES.get(points)
        except Exception:
            points=0
            stars=None

        if not stars:
            await q.answer("❌ الباقة غير متاحة.", show_alert=True)
            return

        try:
            await send_points_invoice(context, chat, user.id, points, stars)
        except Exception:
            logging.exception("could not send Stars invoice")
            await q.answer("❌ تعذر فتح الدفع حالياً.", show_alert=True)
        return
    if data=="stars:stats":
        _,u=sync_points_user(user)
        me = await context.bot.get_me()
        link = referral_link(me.username, user.id)
        successful = int(u.get("successful_referrals", 0))
        t=(
            f"📊 <b>إحصائيات حسابي</b>\n\n"
            f"💰 النقاط: <b>{u.get('points',0)}</b>\n"
            f"📥 الاشتراكات: <b>{u.get('total_subs',0)}</b>\n"
            f"👥 الدعوات الناجحة: <b>{successful}</b>\n\n"
            f"🔗 <b>رابط دعوتك:</b>\n<code>{link}</code>"
        )
        await q.edit_message_text(t,reply_markup=home_button(),parse_mode="HTML")
        return
    if data=="stars:daily":
        ok, value = claim_daily_reward(user.id)
        if ok:
            await q.edit_message_text(
                f" <b>تم استلام الهدية اليومية</b>\n\n تمت إضافة <b>{DAILY_REWARD_POINTS}</b> نقطة.\n رصيدك الآن: <b>{value}</b>",
                reply_markup=home_button(), parse_mode="HTML")
        else:
            _, remain = daily_reward_status(user.id)
            await q.edit_message_text(
                f"⏳ <b>الهدية اليومية غير متاحة الآن</b>\n\nتقدر تستلمها بعد: <b>{remain}</b>",
                reply_markup=home_button(), parse_mode="HTML")
        return
    if data=="stars:codes":
        context.user_data["redeem_stars"]=True; await q.edit_message_text("🔑 <b>استبدال كود</b>\n\nأرسل الكود الآن:",reply_markup=home_button(),parse_mode="HTML"); return
    if data == "stars:sub":
        context.user_data["stars_action"]="subscribe"; context.user_data["stars_step"]="amount"; await q.edit_message_text("🔢 <b>أرسل عدد النقاط:</b>\n\n1 نقطة = 1 عملية",parse_mode="HTML",reply_markup=home_button()); return
    if data == "stars:long_sub":
        context.user_data["long_sub_step"]="amount"
        await q.edit_message_text("🔢 <b>إضافة اشتراكات رمز طويل</b>\n\nأرسل عدد النقاط:\n1 نقطة = 1 عملية",parse_mode="HTML",reply_markup=home_button())
        return
    if data.startswith("longsub:region:"):
        context.user_data["long_sub_region"]=data.split(":",2)[2]
        context.user_data["long_sub_step"]="map"
        await q.edit_message_text("🔑 <b>أرسل رمز الخريطة الطويل الآن:</b>\n\nمثال: <code>#FREEFIRE4BF301D023908082FC89525F539459CC7825</code>",parse_mode="HTML",reply_markup=home_button())
        return
    if data.startswith("stars:region:"):
        context.user_data["stars_region"]=data.split(":",2)[2]; context.user_data["stars_step"]="map"; await q.edit_message_text("🗺️ أرسل كود الخريطة الآن:",reply_markup=home_button()); return

    if data == "main:rewards":
        await q.edit_message_text(
            "🎁 <b>طرق جمع النقاط</b>\n\nاختر الطريقة التي تريدها:",
            reply_markup=rewards_menu(), parse_mode="HTML")
        return
    if data == "reward:challenge":
        question, _ = daily_challenge_question()
        data2 = stars_core.load_data()
        uu = stars_core.get_user(data2, user.id)
        if uu.get("daily_challenge_day") == _day_key():
            await q.edit_message_text("🧩 <b>تحدي اليوم</b>\n\n✅ أكملت تحدي اليوم بالفعل.", reply_markup=home_button(), parse_mode="HTML")
            return
        context.user_data["await_daily_challenge"] = True
        await q.edit_message_text(
            f"🧩 <b>تحدي اليوم</b>\n\n🧮 <b>{question} = ؟</b>\n\nأرسل الإجابة فقط.",
            reply_markup=home_button(), parse_mode="HTML")
        return
    if data == "reward:spin":
        ok, reward, remain = claim_daily_spin(user.id)
        if ok:
            await qualify_referral_and_notify(context, user.id)
            await q.edit_message_text(
                f"🎰 <b>Spin اليوم</b>\n\n🎉 ربحت <b>{reward}</b> نقطة!\n💰 رصيدك: <b>{stars_core.get_user(stars_core.load_data(), user.id).get('points',0)}</b>",
                reply_markup=home_button(), parse_mode="HTML")
        else:
            await q.edit_message_text(
                f"⏳ <b>Spin غير متاح حالياً</b>\n\nارجع بعد: <b>{remain}</b>",
                reply_markup=home_button(), parse_mode="HTML")
        return
    if data == "reward:secret":
        context.user_data["await_daily_secret"] = True
        await q.edit_message_text(
            "🕵️ <b>الكود السري اليومي</b>\n\nأرسل الكود السري الذي حصلت عليه.\n"
            f"👥 الحد: <b>{DAILY_SECRET_MAX_USERS}</b> مستخدم\n🎁 الجائزة: <b>{DAILY_SECRET_REWARD}</b> نقطة",
            reply_markup=home_button(), parse_mode="HTML")
        return
    if data == "reward:referral":
        me = await context.bot.get_me()
        await q.edit_message_text(
            referral_text(user, me.username),
            reply_markup=home_button(), parse_mode="HTML")
        return

    if data == "main:uid":
        context.user_data["upload_mode"] = "remove_uid"
        await q.edit_message_text("📁 أرسل الآن ملف .bytes لإزالة UID منه.", reply_markup=home_button())
        return
    if data == "main:map_info":
        MAP_STATES[chat] = "waiting_for_map_code"
        await q.edit_message_text("🗺️ أرسل رمز الخريطة الآن.\nمثال: #K15M53", reply_markup=home_button())
        return
    if data == "main:block":
        file_id=SAVED_BLOCK.get("file_id")
        if not file_id:
            await q.edit_message_text("ميزة الكتلة غير متوفرة حالياً.", reply_markup=home_button())
            return
        try:
            await context.bot.send_document(chat_id=chat, document=file_id, caption="ملف الكتلة", reply_markup=home_button())
        except Exception:
            await q.edit_message_text("تعذر إرسال ملف الكتلة حالياً.", reply_markup=home_button())
        return

    # Owner-only administration
    if data.startswith("admin:"):
        # Admin navigation is independent from the previous user section.
        MAP_STATES.pop(chat, None)
        for k in ("upload_mode", "await_skins", "stars_step", "stars_amount", "stars_action", "stars_region", "redeem_stars", "report_wait_text", "report_kind"):
            context.user_data.pop(k, None)
        if not is_admin(user.id):
            await q.answer("⛔ للمالك فقط", show_alert=True)
            return
        if data=="admin:maintenance":
            enabled = not maintenance_enabled()
            set_maintenance(enabled)
            status = "🟢 مفعّل" if enabled else "🔴 متوقف"
            await q.edit_message_text(
                f"🔧 <b>وضع الصيانة</b>\n\nالحالة الحالية: {status}",
                reply_markup=admin_kb(), parse_mode="HTML")
            return
        if data=="admin:admins":
            await q.edit_message_text(
                "👑 <b>إدارة المشرفين</b>\n\n"
                f"المالك الرئيسي: <code>{ADMIN_ID}</code>\n\n"
                "صلاحيات الإدارة الحالية مخصصة للمالك الرئيسي.",
                reply_markup=admin_kb(), parse_mode="HTML")
            return
        if data=="admin:add_points":
            context.user_data["admin_action"] = "add_points_id"
            await q.edit_message_text("إضافة نقاط لمستخدم\n\nأرسل ID المستخدم:")
            return
        if data=="admin:test_group":
            ok, err = await test_usage_group(context, user.id)
            if ok:
                await q.answer("تم إرسال رسالة الاختبار للكروب", show_alert=True)
            else:
                await q.answer("فشل الإرسال: " + err[:180], show_alert=True)
            return
        if data=="admin:stats":
            await q.edit_message_text(admin_stats_text(), reply_markup=admin_kb(), parse_mode="HTML")
            return
        if data=="admin:users":
            await q.edit_message_text(users_text(), reply_markup=admin_kb(), parse_mode="HTML")
            return
        if data=="admin:ban":
            context.user_data["admin_action"]="ban"
            await q.edit_message_text("🚫 أرسل ID المستخدم الذي تريد حظره:")
            return
        if data=="admin:unban":
            context.user_data["admin_action"]="unban"
            await q.edit_message_text("🔓 أرسل ID المستخدم الذي تريد فتحه:")
            return
        if data=="admin:reports":
            if not REPORTS:
                await q.edit_message_text("رسائل المشاكل\n\nلا توجد رسائل حالياً.", reply_markup=admin_kb())
                return
            rows=[]
            for rid,r in list(REPORTS.items())[-20:]:
                status=r.get("status","جديدة")
                label=f"{r.get('kind','إبلاغ')} | {r.get('user_id')} | {status}"
                rows.append([plain_button(label, callback_data=f"admin:report:{rid}")])
            rows.append([emoji_button(EMOJI_NAMES["back"],"admin:back","back")])
            await q.edit_message_text("رسائل المشاكل\n\nاختر رسالة:", reply_markup=InlineKeyboardMarkup(rows))
            return
        if data.startswith("admin:report:"):
            rid=data.split(":",2)[2]; r=REPORTS.get(rid)
            if not r:
                await q.answer("الرسالة غير موجودة", show_alert=True); return
            await q.edit_message_text(
                f"رسالة مشكلة\n\nالمستخدم: {r.get('user_id')}\nالنوع: {r.get('kind','إبلاغ')}\nالحالة: {r.get('status','جديدة')}\n\n{r.get('text','')}",
                reply_markup=InlineKeyboardMarkup([
                    [plain_button("رد",callback_data=f"reply_report:{rid}"), plain_button("تم الحل",callback_data=f"report:done:{rid}")],
                    [plain_button("حذف",callback_data=f"report:delete:{rid}")],
                    [emoji_button(EMOJI_NAMES["back"],"admin:reports","back")]
                ]))
            return
        if data=="admin:star_codes":
            await q.edit_message_text("🔑 <b>إدارة أكواد النجوم</b>\n\n"+codes_text(),reply_markup=InlineKeyboardMarkup([
                [emoji_button(" إنشاء كود","admin:star_new","add"),emoji_button(" حذف كود","admin:star_del","remove")],
                [emoji_button(" سجل استخدام الأكواد","admin:star_log","stats")],
                [emoji_button(" رجوع","admin:back","back")]
            ]),parse_mode="HTML"); return
        if data=="admin:star_log":
            data_codes=stars_core.load_data().get("codes",{})
            lines=["🧾 <b>سجل استخدام الأكواد</b>"]
            any_log=False
            for c, info in data_codes.items():
                if not isinstance(info, dict):
                    continue
                for rec in info.get("redemptions",[])[-50:]:
                    any_log=True
                    uname=f"@{rec.get('username')}" if rec.get("username") else "بدون يوزر"
                    lines.append(
                        f"🔑 <code>{c}</code>\n"
                        f"👤 {rec.get('name','')} | {uname}\n"
                        f"🆔 <code>{rec.get('user_id')}</code>\n"
                        f" {rec.get('points',0)} |  {rec.get('time','')}"
                    )
            if not any_log:
                lines.append("\nلا توجد استخدامات مسجلة.")
            await q.edit_message_text("\n\n".join(lines), reply_markup=admin_kb(), parse_mode="HTML")
            return
        if data=="admin:star_new":
            context.user_data["admin_action"]="star_points"; context.user_data["generated_code"]=make_star_code(); await q.edit_message_text(" أرسل عدد النقاط التي يعطيها الكود:"); return
        if data=="admin:star_del":
            context.user_data["admin_action"]="star_delete"; await q.edit_message_text("🗑 أرسل الكود المراد حذفه:"); return
        if data=="admin:video":
            context.user_data["admin_action"]="help_video"
            await q.edit_message_text("أرسل فيديو طريقة الاستخدام الآن.\n\nسيتم استبدال الفيديو القديم تلقائياً.")
            return
        if data=="admin:help_videos":
            await q.edit_message_text("🎥 شروحات طريقة الاستخدام\n\nاختر الشرح الذي تريد رفعه أو تغييره:", reply_markup=admin_help_videos_kb())
            return
        if data.startswith("admin:help_video:"):
            key=data.split(":",2)[2]
            if key not in ("block","settings","skins"):
                return
            context.user_data["admin_action"]="help_video:"+key
            await q.edit_message_text("أرسل فيديو الشرح الآن.\nسيتم حفظه واستبدال القديم تلقائياً.", reply_markup=InlineKeyboardMarkup([[emoji_button("إلغاء","admin:help_videos","cancel")]]))
            return
        if data=="admin:help_delete":
            SAVED_HELP_VIDEOS.clear(); save_help_videos()
            await q.edit_message_text("تم حذف جميع شروحات طريقة الاستخدام.", reply_markup=admin_help_videos_kb())
            return
        if data=="admin:block":
            await q.edit_message_text("🧱 إدارة الكتلة\n\nارفع ملف الكتلة لتفعيله.\nرفع ملف جديد يستبدل الملف القديم.", reply_markup=InlineKeyboardMarkup([
                [emoji_button("رفع/تغيير ملف الكتلة","admin:block_upload","add")],
                [emoji_button("حذف ملف الكتلة","admin:block_delete","clear")],
                [emoji_button("الرئيسية","admin:back","back")]
            ]))
            return
        if data=="admin:block_upload":
            context.user_data["admin_action"]="block_upload"
            await q.edit_message_text("أرسل الآن ملف الكتلة كملف Document.")
            return
        if data=="admin:block_delete":
            SAVED_BLOCK.clear(); save_block()
            await q.edit_message_text("تم حذف ملف الكتلة وتعطيل الزر.", reply_markup=admin_kb())
            return
        if data=="admin:welcome":
            context.user_data["admin_action"]="welcome_text"
            preview = WELCOME_TEXT.format(user_id=user.id)
            await q.edit_message_text(
                "🎨 <b>تغيير رسالة الترحيب</b>\n\n"
                "أرسل الآن نص الترحيب الجديد.\n"
                "يمكنك استخدام {user_id} لعرض آيدي المستخدم تلقائياً.\n\n"
                "<b>الترحيب الحالي:</b>\n" + preview,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[emoji_button("إلغاء", "admin:back", "cancel")]])
            )
            return
        if data=="admin:emojis":
            await q.edit_message_text("إدارة إيموجيات الأزرار\n\nاختر الزر الذي تريد تغيير إيموجيه:", reply_markup=admin_emoji_kb(), parse_mode="HTML")
            return

    if data.startswith("emoji:") and is_admin(user.id):
        parts=data.split(":")
        if data=="emoji:reset":
            CUSTOM_EMOJIS.clear(); CUSTOM_EMOJIS.update(DEFAULT_EMOJIS); save_emojis()
            await q.edit_message_text("✅ تمت إعادة جميع الإيموجيات الافتراضية.", reply_markup=admin_emoji_kb())
            return
        if data=="emoji:list":
            lines=["📋 <b>الإيموجيات الحالية</b>"]
            for k in EMOJI_NAMES:
                lines.append(f"{EMOJI_NAMES[k]}\n<code>{CUSTOM_EMOJIS.get(k,'')}</code>")
            await q.edit_message_text("\n\n".join(lines), reply_markup=admin_emoji_kb(), parse_mode="HTML")
            return
        if len(parts)==3 and parts[1]=="pick":
            key=parts[2]
            if key not in EMOJI_NAMES: return
            context.user_data["admin_action"]="emoji:"+key
            await q.edit_message_text(f" <b>{EMOJI_NAMES[key]}</b>\n\nأرسل الآن <b>Custom Emoji ID</b> الجديد.\n\nمثال:\n<code>5177431733565393227</code>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[emoji_button(" إلغاء","admin:emojis","cancel")]]))
            return

    if data=="admin:back":
        await q.edit_message_text("لوحة تحكم المالك", reply_markup=admin_kb())
        return
    if data.startswith("report:done:") and is_admin(user.id):
        rid=data.split(":",2)[2]
        if rid in REPORTS:
            REPORTS[rid]["status"]="تم الحل"; save_reports()
        await q.edit_message_text("تم وضع الرسالة كـتم الحل.", reply_markup=admin_kb())
        return
    if data.startswith("report:delete:") and is_admin(user.id):
        rid=data.split(":",2)[2]
        REPORTS.pop(rid,None); save_reports()
        await q.edit_message_text("تم حذف رسالة المشكلة.", reply_markup=admin_kb())
        return

    if data=="main:home":
        dpts=stars_core.load_data(); upts=stars_core.get_user(dpts,user.id); await q.edit_message_text(WELCOME_TEXT.format(user_id=user.id)+f"\n | <b>نقاطك :</b> <code>{upts.get('points',0)}</code>",reply_markup=main_menu_kb(),parse_mode="HTML")
        return

    if data=="main:account":
        u=USERS.get(str(user.id),{})
        await q.edit_message_text(f"<b>حسابي</b>\n\nالاسم: {user.full_name}\nاليوزر: @{user.username if user.username else 'لا يوجد'}\nالآيدي: <code>{user.id}</code>", reply_markup=home_button(), parse_mode="HTML")
        return

    if data=="main:language":
        await q.edit_message_text("🌐 <b>اللغة</b>\n\n🇮🇶 العربية\n\nسيتم حفظ اختيار اللغة في تحديث لاحق.", reply_markup=home_button(), parse_mode="HTML")
        return

    if data=="admin:emojis":
        if is_admin(user.id):
            await q.edit_message_text("🎨 <b>إدارة إيموجيات الأزرار</b>\n\nاختر الزر الذي تريد تغيير إيموجيه:", reply_markup=admin_emoji_kb(), parse_mode="HTML")
        return

    if data=="main:settings":
        cd=cooldown_text(user.id,"settings")
        if cd:
            await q.edit_message_text(cd,reply_markup=home_button(),parse_mode="HTML"); return
        context.user_data["upload_mode"]="settings"
        await q.edit_message_text(
            feature_description("settings") + "\n\n📌 <b>طريقة الاستخدام:</b> أرسل ملف <code>.bytes</code> الآن.",
            reply_markup=home_button(),parse_mode="HTML")
        return

    if data=="main:skins":
        cd=cooldown_text(user.id,"skins")
        if cd:
            await q.edit_message_text(cd,reply_markup=home_button(),parse_mode="HTML"); return
        context.user_data["upload_mode"]="skins"
        context.user_data["await_skins"]=True
        await q.edit_message_text(
            feature_description("skins") + "\n\n"
            "📦 <b>الملفات المطلوبة:</b>\n"
            "• <code>ProjectData_slot_رقم.bytes</code>\n"
            "• <code>ProjectData_slot_رقم.meta</code>\n"
            "• <code>UserLevelData_رقم.bytes</code>\n\n"
            "⚠️ يجب أن تكون ملفات الـSlot الثلاثة موجودة معًا داخل ZIP.",
            reply_markup=home_button(),parse_mode="HTML")
        return

    if data=="main:help":
        await q.edit_message_text("📖 <b>طريقة الاستخدام</b>\n\nاختر القسم الذي تريد معرفة طريقة استخدامه:", reply_markup=help_menu(), parse_mode="HTML")
        return
    if data.startswith("guide:"):
        key=data.split(":",1)[1]
        if key not in ("map_info","stars","uid","block","settings","skins"):
            return
        text = guide_text(key)
        actions = {
            "map_info": emoji_button("️ فتح معلومات الخريطة", "main:map_info", "map_info"),
            "stars": emoji_button(" فتح إضافة نجوم", "main:stars", "stars"),
            "uid": emoji_button(" فتح إزالة UID", "main:uid", "uid"),
            "block": emoji_button(" فتح الكتلة", "main:block", "block"),
            "settings": emoji_button("️ فتح تعديل إعدادات الخريطة", "main:settings", "settings"),
            "skins": emoji_button(" فتح السكنات", "main:skins", "skins"),
        }
        await q.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([
                [actions[key]],
                [emoji_button(" طريقة الاستخدام", "main:help", "help")]
            ]),
            parse_mode="HTML"
        )
        return
    if data in ("help:block","help:settings","help:skins"):
        key=data.split(":",1)[1]
        vid=SAVED_HELP_VIDEOS.get(key,{}).get("file_id")
        labels={"block":"شرح كتلة","settings":"تعديل إعدادات الخريطة","skins":"سكنات"}
        if not vid:
            await q.edit_message_text(f"لم تتم إضافة {labels[key]} حتى الآن.", reply_markup=help_menu())
            return
        try:
            await context.bot.send_video(chat_id=chat, video=vid, caption=labels[key], reply_markup=help_menu())
        except Exception:
            await q.edit_message_text("تعذر إرسال فيديو الشرح.", reply_markup=help_menu())
        return

    if data=="main:support":
        await q.edit_message_text(
            "مرحبا في دعم بوت عبودي التوب 👋\n\nاختر تقرير الذي تريد إرسال:",
            reply_markup=support_menu())
        return

    # Support flow
    if data in ("support:report","support:improve"):
        kind="إبلاغ" if data=="support:report" else "تحسينات"
        context.user_data["report_kind"]=kind
        context.user_data["report_wait_text"]=True
        await q.edit_message_text(
            f"لقد اخترت {kind}.\nاكتب البلاغ (ما الذي حدث لك؟)" if kind=="إبلاغ"
            else "لقد اخترت إرسال تحسينات.\nاكتب التحسين أو الاقتراح:",
            reply_markup=InlineKeyboardMarkup([[emoji_button(" إلغاء","support:cancel","cancel")]]))
        return

    if data=="support:photo":
        if not context.user_data.get("report_text"):
            await q.edit_message_text("❌ لا يوجد تقرير قيد الإرسال.",reply_markup=support_menu()); return
        context.user_data["await_report_photo"]=True
        await q.edit_message_text("🖼️ أرسل الصورة الآن مع رسالة اختيارية، أو أرسل الصورة فقط.")
        return

    if data=="support:no_photo":
        await finalize_report(update, context, with_photo=False)
        return

    if data=="support:cancel":
        for k in ("report_kind","report_wait_text","report_text","await_report_photo"):
            context.user_data.pop(k,None)
        await q.edit_message_text("❌ تم إلغاء التقرير.",reply_markup=main_menu_kb())
        return

    if data.startswith("reply_report:") and chat==ADMIN_ID:
        rid=data.split(":",1)[1]
        report=REPORTS.get(rid)
        if not report:
            await q.answer("التقرير غير موجود",show_alert=True); return
        context.user_data["admin_reply_to"]=rid
        await q.edit_message_text(f"↩️ الرد على الشكوى رقم {rid}\n\nاكتب الرد الآن:")
        return

    # Existing settings callbacks
    if data=="back":
        if not s or not s.get("msg"):
            await q.edit_message_text("🏠 الرئيسية",reply_markup=main_menu_kb())
        else:
            s["pending"]=None
            await q.edit_message_text("📂 اختر القسم:",reply_markup=cats_kb())
        return

    if not s or not s.get("msg"):
        await q.edit_message_text("❌ أرسل ملف .bytes أولاً.",reply_markup=main_menu_kb()); return

    if data=="clear":
        SESSIONS.pop(chat,None)
        shutil.rmtree(s["dir"],ignore_errors=True)
        await q.edit_message_text("🗑 تم حذف ملف الإعدادات.",reply_markup=main_menu_kb()); return

    if data=="export":
        out=Path(s["dir"])/s["file"]
        out.write_bytes(s["msg"].SerializeToString())
        await q.message.reply_document(out.open("rb"),caption="✅ تم تصدير مشروع الإعدادات.")
        return

    if data.startswith("cat:"):
        ci=int(data.split(":")[1]); s["pending"]=None
        await q.edit_message_text("⚙️ "+list(CATEGORY_MAPPING)[ci]+"\n\nاختر الإعداد:",reply_markup=sets_kb(ci)); return

    if data.startswith("set:"):
        _,sid,ci=data.split(":"); sid=int(sid); ci=int(ci)
        m=next((x for x in METADATA if x["ID"]==sid),None)
        if not m:return
        st=settings(s["msg"]); x=find(st,sid)
        if x is None:x=st.add(); x.id=sid
        if m["Type"]=="boolean":
            x.enable=not x.enable
            kb=InlineKeyboardMarkup([
                [plain_button(" تغيير الحالة",callback_data=f"set:{sid}:{ci}")],
                [plain_button("️ الإعدادات",callback_data=f"cat:{ci}")],
                [emoji_button(" الرئيسية","main:home","back")]])
            await q.edit_message_text(f"🔧 {name(m['Name'])}\nالحالة: {val(x,m)}",reply_markup=kb)
        else:
            s["pending"]={"sid":sid,"ci":ci}
            await q.edit_message_text(f"✏️ {name(m['Name'])}\nالقيمة الحالية: {val(x,m)}\n\nأرسل القيمة الجديدة كرقم.")
        return

async def finalize_report(update: Update, context: ContextTypes.DEFAULT_TYPE, with_photo=False):
    user=update.effective_user
    kind=context.user_data.get("report_kind","إبلاغ")
    body=context.user_data.get("report_text","")
    rid=str(user.id)+"_"+str(update.message.message_id if update.message else update.callback_query.message.message_id)
    username=f"@{user.username}" if user.username else "لا يوجد"
    report={"user_id":user.id,"chat_id":update.effective_chat.id,"kind":kind,"text":body,"photo":None}
    REPORTS[rid]=report
    REPORTS[rid]["status"]="جديدة"
    save_reports()
    caption=(
        "📣 تقرير جديد من بوت عبودي التوب\n\n"
        f"👤 اسم المستخدم: {user.full_name}\n"
        f"🔹 المعرف (يوزر): {username}\n"
        f"🆔 الآي دي: {user.id}\n"
        "📦 النوع: شكوى\n"
        f"🎯 نوع الشكوى ({kind}):\n"
        f"📝 النص:\n{body}"
    )
    kb=InlineKeyboardMarkup([[plain_button("↩️ رد على شكوى",callback_data=f"reply_report:{rid}")]])
    photo_id=context.user_data.get("report_photo")
    try:
        if with_photo and photo_id:
            await context.bot.send_photo(chat_id=ADMIN_ID,photo=photo_id,caption=caption,reply_markup=kb)
        else:
            await context.bot.send_message(chat_id=ADMIN_ID,text=caption,reply_markup=kb)
    except Exception as e:
        logging.exception("report send failed")
        await update.effective_message.reply_text("❌ تعذر إرسال الطلب للمشرف. تأكد أن البوت والمشرف في محادثة تسمح للبوت بالإرسال.")
        return
    for k in ("report_kind","report_wait_text","report_text","await_report_photo","report_photo"):
        context.user_data.pop(k,None)
    await update.effective_message.reply_text("✅ تم ارسال طلبك، يرجى الانتظار.",reply_markup=main_menu_kb())

async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user=update.effective_user
    register_user(user)
    if not is_admin(user.id):
        return
    action=context.user_data.get("admin_action","")
    if action.startswith("help_video:"):
        key=action.split(":",1)[1]
        SAVED_HELP_VIDEOS[key]={"file_id":update.message.video.file_id,"updated_by":user.id}
        save_help_videos()
        context.user_data.pop("admin_action",None)
        await update.message.reply_text("تم حفظ شرح طريقة الاستخدام.", reply_markup=admin_help_videos_kb())
        return
    if action=="help_video":
        SAVED_HELP_VIDEOS["settings"]={"file_id":update.message.video.file_id,"updated_by":user.id}
        save_help_videos()
        context.user_data.pop("admin_action",None)
        await update.message.reply_text("تم حفظ الفيديو.", reply_markup=admin_help_videos_kb())
        return

async def document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    if is_blocked(user.id) and not is_admin(user.id):
        await update.message.reply_text(" تم حظرك من استخدام البوت.")
        return
    d=update.message.document
    if is_admin(user.id) and context.user_data.get("admin_action")=="block_upload":
        if not d:
            return
        SAVED_BLOCK={"file_id":d.file_id,"file_name":d.file_name or "block_file"}
        globals()["SAVED_BLOCK"]=SAVED_BLOCK
        save_block()
        context.user_data.pop("admin_action",None)
        await update.message.reply_text("تم رفع ملف الكتلة وتفعيل الزر.", reply_markup=admin_kb())
        return
    # A report may optionally use an image/document as evidence.
    if context.user_data.get("await_report_photo"):
        context.user_data["report_photo"]=d.file_id if d else None
        await finalize_report(update, context, with_photo=False)
        return
    if not d:return
    chat=update.effective_chat.id

    if context.user_data.get("upload_mode") == "remove_uid":
        context.user_data.pop("upload_mode", None)
        if not d.file_name.lower().endswith(".bytes"):
            await update.message.reply_text("❌ يجب أن يكون الملف بامتداد .bytes", reply_markup=main_menu_kb())
            return
        f = await context.bot.get_file(d.file_id)
        bio = BytesIO(); await f.download_to_memory(out=bio)
        modified, ok = remove_uid_pattern(bio.getvalue())
        if not ok:
            await update.message.reply_text("❌ النمط المطلوب غير موجود. لم يتم تعديل الملف.", reply_markup=main_menu_kb())
            return
        out = BytesIO(modified); out.name = f"modified_{d.file_name}"; out.seek(0)
        await update.message.reply_document(out, filename=out.name, caption="✅ تم حذف UID بنجاح")
        set_feature_cooldown(user.id,"uid")
        return

    # The user must choose a section before sending a file.
    upload_mode = context.user_data.get("upload_mode")
    if not upload_mode:
        # Intentionally stay silent until a section is selected.
        return

    # Skins mode
    if upload_mode == "skins" and context.user_data.get("await_skins"):
        context.user_data["await_skins"]=False
        if not d.file_name.lower().endswith(".zip"):
            await update.message.reply_text("❌ قسم السكنات يحتاج ملف ZIP فقط.",reply_markup=main_menu_kb())
            return
        work=Path(tempfile.mkdtemp(prefix="skins_"))
        src=work/d.file_name
        f=await context.bot.get_file(d.file_id)
        await f.download_to_drive(src)
        out=work/("patched_"+d.file_name)
        try:
            logs=patch_skins_zip(src,out)
            caption="👕 تم تجهيز السكنات بنجاح.\n\n" + "\n".join(logs[-5:])
            await update.message.reply_document(out.open("rb"),caption=caption)
            set_feature_cooldown(user.id,"skins")
        except Exception as e:
            logging.exception("skin patch failed")
            msg = str(e)
            if msg.startswith("ملف ناقص:"):
                await update.message.reply_text("❌ <b>ملف ناقص</b>:\n" + msg.split("\n",1)[1], reply_markup=main_menu_kb(), parse_mode="HTML")
            else:
                await update.message.reply_text(f"❌ فشل تجهيز السكنات:\n{msg}",reply_markup=main_menu_kb())
        finally:
            shutil.rmtree(work,ignore_errors=True)
        return

    # Settings project .bytes
    if upload_mode != "settings":
        return
    if not d.file_name.lower().endswith(".bytes"):
        await update.message.reply_text("❌ أرسل ملف .bytes لقسم إعدادات البوت الأول، أو اختر «سكنات» من القائمة.")
        return
    await update.message.chat.send_action(ChatAction.TYPING)
    work=Path(tempfile.mkdtemp(prefix="ugc_"))
    path=work/d.file_name
    f=await context.bot.get_file(d.file_id)
    await f.download_to_drive(path)
    try:
        msg=UGC(); msg.ParseFromString(path.read_bytes())
    except Exception:
        shutil.rmtree(work,ignore_errors=True)
        await update.message.reply_text("❌ الملف غير صالح أو غير مدعوم.",reply_markup=main_menu_kb()); return
    SESSIONS[chat]={"msg":msg,"file":d.file_name,"dir":str(work),"pending":None}
    set_feature_cooldown(user.id,"settings")
    context.user_data.pop("upload_mode", None)
    await update.message.reply_text(
        "✅ تم تحميل ملف إعدادات البوت الأول.\n\n📂 اختر قسم الإعدادات الذي تريد تعديله:",
        reply_markup=cats_kb()
    )

async def stars_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """فتح قسم النجوم عند كتابة ستار/نجوم، لجميع المستخدمين المسموح لهم."""
    user = update.effective_user
    register_user(user)
    if is_blocked(user.id) and not is_admin(user.id):
        await update.message.reply_text(" تم حظرك من استخدام البوت.")
        return
    t, k = stars_menu(user)
    await update.message.reply_text(t, reply_markup=k, parse_mode="HTML")

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    admin_action = context.user_data.get("admin_action")

    if is_admin(user.id) and admin_action == "add_points_id":
        raw_id = (update.message.text or "").strip()
        if not raw_id.isdigit():
            await update.message.reply_text("❌ أرسل ID صحيحًا، أرقام فقط.")
            return

        target_id = int(raw_id)
        data = stars_core.load_data()
        target = data.get("users", {}).get(str(target_id))
        if target is None:
            await update.message.reply_text(
                f"❌ لم يتم العثور على المستخدم: <code>{target_id}</code>",
                parse_mode="HTML"
            )
            context.user_data.pop("admin_action", None)
            return

        context.user_data["points_target_id"] = target_id
        context.user_data["admin_action"] = "add_points_amount"
        await update.message.reply_text(
            "👤 <b>تم العثور على المستخدم</b>\n\n"
            f"🆔 ID: <code>{target_id}</code>\n"
            f"💳 الرصيد الحالي: <b>{int(target.get('points', 0) or 0)}</b> نقطة\n\n"
            " أرسل الآن <b>عدد النقاط</b> التي تريد إضافتها:",
            parse_mode="HTML"
        )
        return

    if is_admin(user.id) and admin_action == "add_points_amount":
        raw_amount = (update.message.text or "").strip()
        if not raw_amount.isdigit() or int(raw_amount) <= 0:
            await update.message.reply_text("❌ أرسل عدد نقاط صحيح أكبر من صفر.")
            return

        amount = int(raw_amount)
        target_id = int(context.user_data.get("points_target_id", 0))
        data = stars_core.load_data()
        target = data.get("users", {}).get(str(target_id))
        if target is None:
            await update.message.reply_text("❌ المستخدم غير موجود.")
            context.user_data.pop("admin_action", None)
            context.user_data.pop("points_target_id", None)
            return

        old_balance = int(target.get("points", 0) or 0)
        new_balance = old_balance + amount
        target["points"] = new_balance
        stars_core.save_data(data)

        context.user_data.pop("admin_action", None)
        context.user_data.pop("points_target_id", None)

        await update.message.reply_text(
            "✅ <b>تمت إضافة النقاط بنجاح</b>\n\n"
            f"👤 المستخدم: <code>{target_id}</code>\n"
            f" المضاف: <b>+{amount}</b> نقطة\n"
            f"💳 الرصيد الجديد: <b>{new_balance}</b> نقطة",
            parse_mode="HTML"
        )

        # Notify ONLY after the points have actually been saved.
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    "🎉 <b>تم حصولك على نقاط!</b>\n\n"
                    f" تمت إضافة: <b>+{amount} نقطة</b>\n"
                    f"💳 رصيدك الحالي: <b>{new_balance} نقطة</b>\n\n"
                    "✅ تمت العملية بنجاح."
                ),
                parse_mode="HTML"
            )
        except Exception:
            logging.exception("points success notification failed")
        return

    if is_blocked(user.id) and not is_admin(user.id):
        await update.message.reply_text(" تم حظرك من استخدام البوت.")
        return

    # فتح قسم إضافة نجوم عند كتابة الكلمة مباشرة
    raw_text = re.sub(r"\s+", " ", (update.message.text or "").strip().casefold())
    if raw_text in {"ستار", "ستارز", "star", "stars", "نجوم", "إضافة نجوم", "اضافة نجوم", " ستار", " نجوم"}:
        t, k = stars_menu(user)
        await update.message.reply_text(t, reply_markup=k, parse_mode="HTML")
        return

    if context.user_data.get("await_referral_captcha"):
        raw = (update.message.text or "").strip()
        if not verify_referral_captcha(user.id, raw):
            await update.message.reply_text("❌ إجابة غير صحيحة. حاول مرة ثانية بنفس المسألة.")
            return
        context.user_data.pop("await_referral_captcha", None)
        try:
            bonus_data = stars_core.load_data()
            bonus_user = stars_core.get_user(bonus_data, user.id)
            if not bonus_user.get("welcome_bonus_claimed", False):
                bonus_user["points"] = int(bonus_user.get("points", 0)) + 150
                bonus_user["welcome_bonus_claimed"] = True
                stars_core.save_data(bonus_data)
        except Exception:
            logging.exception("verified welcome bonus failed")
        await update.message.reply_text(
            "✅ تم التحقق بنجاح!\n\n"
            "🎁 تم تفعيل حسابك بنجاح. ابدأ باستخدام البوت الآن.",
            reply_markup=main_menu_kb())
        return

    if MAP_STATES.get(update.effective_chat.id) == "waiting_for_map_code":
        MAP_STATES.pop(update.effective_chat.id, None)
        map_code = (update.message.text or "").strip().split()[0] if (update.message.text or "").strip() else ""
        map_code = map_code.lstrip("#")
        wait = await update.message.reply_text("⏳ جاري البحث عن الخريطة...")
        info, error = get_map_info(map_code)
        if error:
            await wait.edit_text(error)
            return
        set_feature_cooldown(user.id,"map_info")
        await qualify_referral_and_notify(context, user.id)
        formatted = format_map_info(info)
        try:
            if info.get("image"):
                r = rq.get(info["image"], timeout=10, verify=False)
                if r.status_code == 200:
                    await wait.delete()
                    await update.message.reply_photo(photo=r.content, caption=formatted, parse_mode="HTML")
                    return
        except Exception:
            pass
        await wait.edit_text(formatted, parse_mode="HTML")
        return

    # Long subscription user input
    long_step=context.user_data.get("long_sub_step")
    if long_step:
        raw=(update.message.text or "").strip()
        if long_step=="amount":
            if not raw.isdigit() or int(raw)<=0:
                await update.message.reply_text("❌ أرسل رقم صحيح."); return
            amount=int(raw); _,u=sync_points_user(user)
            if amount>int(u.get("points",0)):
                await update.message.reply_text(f"❌ نقاطك غير كافية. رصيدك: {u.get('points',0)}"); return
            context.user_data["long_sub_amount"]=amount; context.user_data["long_sub_step"]="region"
            keys=list(REGION_URLS_LOCAL.keys()) or ["ME"]; rows=[]
            for i in range(0,len(keys),3):
                rows.append([plain_button(f"{REGION_FLAGS_LOCAL.get(k,'')} {k}",callback_data=f"longsub:region:{k}") for k in keys[i:i+3]])
            await update.message.reply_text(f" {amount} نقطة\n\n اختر المنطقة:",reply_markup=InlineKeyboardMarkup(rows)); return
        if long_step=="map":
            code=validate_long_sub_code(raw)
            if not code:
                await update.message.reply_text("❌ رمز طويل غير صالح.\nيجب أن يكون بالشكل: <code>#FREEFIRE</code> + 36 حرف HEX (المجموع 45 حرفاً).",parse_mode="HTML",reply_markup=home_button()); return
            amount=int(context.user_data.get("long_sub_amount",0)); region=context.user_data.get("long_sub_region","ME")
            context.user_data.pop("long_sub_step",None); context.user_data.pop("long_sub_amount",None); context.user_data.pop("long_sub_region",None)
            wait=await update.message.reply_text("⏳ جاري البحث عن الخريطة قبل بدء العملية...",parse_mode="HTML")
            info,error=get_map_info(code.lstrip("#"))
            if error or not info:
                await wait.edit_text("❌ رمز الخريطة غير صحيح أو الخريطة غير موجودة.\nلم تبدأ العملية ولم يتم خصم أي نقاط.",reply_markup=home_button(),parse_mode="HTML"); return
            await wait.edit_text(f"✅ تم العثور على الخريطة: <b>{html.escape(str(info.get('name','غير معروف')))}</b>\n⏳ جاري بدء عملية الاشتراكات بالرمز الطويل...",parse_mode="HTML")
            ok,status=await enqueue_long_sub_job(context,update.effective_chat.id,region,code,amount)
            await update.message.reply_text(status,parse_mode="HTML",reply_markup=home_button()); return

    # Stars user input
    stars_step=context.user_data.get("stars_step")
    if stars_step:
        raw=(update.message.text or "").strip()
        if stars_step=="amount":
            if not raw.isdigit() or int(raw)<=0: await update.message.reply_text("❌ أرسل رقم صحيح."); return
            amount=int(raw); _,u=sync_points_user(user)
            if amount>int(u.get("points",0)): await update.message.reply_text(f"❌ نقاطك غير كافية. رصيدك: {u.get('points',0)}"); return
            context.user_data["stars_amount"]=amount; context.user_data["stars_step"]="region"; keys=list(REGION_URLS_LOCAL.keys()) or ["ME"]; rows=[]
            for i in range(0,len(keys),3): rows.append([plain_button(f"{REGION_FLAGS_LOCAL.get(k,'')} {k}",callback_data=f"stars:region:{k}") for k in keys[i:i+3]])
            await update.message.reply_text(f" {amount} نقطة\n\n اختر المنطقة:",reply_markup=InlineKeyboardMarkup(rows)); return
        if stars_step=="map":
            code=stars_core.clean_code(raw); amount=int(context.user_data.get("stars_amount",0)); action=context.user_data.get("stars_action","like"); region=context.user_data.get("stars_region","ME")
            if action == "subscribe":
                if not re.fullmatch(r"#[A-Za-z0-9]{6}", raw.strip()):
                    await update.message.reply_text("❌ رمز الاشتراك القصير غير صالح.\nاستخدم رمزاً بالشكل <code>#G09P75</code> (7 أحرف مع #).",parse_mode="HTML",reply_markup=home_button()); return
                wait=await update.message.reply_text("🔎 جاري البحث عن الخريطة...",parse_mode="HTML")
                info,error=get_map_info(code.lstrip("#"))
                if error or not info:
                    await wait.edit_text("❌ رمز الخريطة غير صحيح أو الخريطة غير موجودة.\nلم تبدأ العملية ولم يتم خصم أي نقاط.",parse_mode="HTML",reply_markup=home_button()); return
                await wait.edit_text(f"✅ تم العثور على الخريطة: <b>{html.escape(str(info.get('name','غير معروف')))}</b>\n⏳ جاري بدء عملية الاشتراكات...",parse_mode="HTML")
            elif len(code)<3:
                await update.message.reply_text("❌ كود الخريطة غير صالح.",reply_markup=home_button()); return
            for k in ("stars_step","stars_amount","stars_action","stars_region"): context.user_data.pop(k,None)
            ok, status = await enqueue_star_job(context, update.effective_chat.id, action, region, code, amount)
            await update.message.reply_text(status, parse_mode="HTML", reply_markup=home_button())
            return

    # Redeem stars code
    if context.user_data.get("redeem_stars"):
        code=stars_core.clean_code(update.message.text or ""); data2=stars_core.load_data(); u2=stars_core.get_user(data2,user.id); info=data2.get("codes",{}).get(code)
        if not info: await update.message.reply_text("❌ الكود غير صالح."); return
        if code in u2.get("redeemed",[]): await update.message.reply_text("❌ استخدمت هذا الكود مسبقاً."); return
        if isinstance(info,(int,float)): pts=int(info); used=0; maxr=10; unlimited=False
        else: pts=int(info.get("points",0)); used=int(info.get("used",0)); maxr=int(info.get("max_redeem",10)); unlimited=bool(info.get("unlimited",False))
        if not unlimited and used>=maxr: await update.message.reply_text("❌ انتهت صلاحية الكود."); return
        u2["points"]=u2.get("points",0)+pts
        u2.setdefault("redeemed",[]).append(code)
        if not isinstance(info, dict):
            info={"points":pts,"used":used,"max_redeem":maxr,"unlimited":unlimited}
        info["points"]=pts
        info["used"]=used+1
        info["max_redeem"]=maxr
        info["unlimited"]=unlimited
        info.setdefault("redemptions",[]).append({
            "user_id": int(user.id),
            "username": user.username or "",
            "name": user.full_name or "",
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "points": pts
        })
        if not unlimited and info["used"]>=maxr: data2["codes"].pop(code,None)
        else: data2["codes"][code]=info
        stars_core.save_data(data2); context.user_data.pop("redeem_stars",None); await update.message.reply_text(f"✅ تم إضافة <b>{pts}</b> نقطة.\n💰 رصيدك: <b>{u2['points']}</b>",parse_mode="HTML",reply_markup=home_button()); return

    admin_action = context.user_data.get("admin_action")
    if admin_action=="star_points" and is_admin(user.id):
        raw=(update.message.text or "").strip()
        if not raw.isdigit() or int(raw)<=0:
            await update.message.reply_text("❌ أرسل عدد نقاط صحيح.")
            return
        context.user_data["star_code_points"]=int(raw)
        context.user_data["admin_action"]="star_max"
        await update.message.reply_text("👥 أرسل عدد الأشخاص المسموح لهم باستخدام الكود:")
        return
    if admin_action=="star_max" and is_admin(user.id):
        raw=(update.message.text or "").strip()
        if not raw.isdigit() or int(raw)<=0:
            await update.message.reply_text("❌ أرسل عدد صحيح أكبر من صفر.")
            return
        max_redeem=int(raw)
        points=int(context.user_data.pop("star_code_points",0))
        code=context.user_data.pop("generated_code",make_star_code())
        data2=stars_core.load_data()
        data2.setdefault("codes",{})[code]={
            "points":points,"used":0,"max_redeem":max_redeem,
            "unlimited":False,"redemptions":[]
        }
        stars_core.save_data(data2)
        context.user_data.pop("admin_action",None)
        await update.message.reply_text(
            f" <b>تم إنشاء الكود</b>\n\n <code>{code}</code>\n النقاط: <b>{points}</b>\n عدد الاستخدامات: <b>{max_redeem}</b>",
            parse_mode="HTML",reply_markup=admin_kb())
        return
    if admin_action=="star_delete" and is_admin(user.id):
        code=stars_core.clean_code(update.message.text or ""); data2=stars_core.load_data(); ok=code in data2.get("codes",{}); data2.get("codes",{}).pop(code,None); stars_core.save_data(data2); context.user_data.pop("admin_action",None); await update.message.reply_text("✅ تم حذف الكود." if ok else "❌ الكود غير موجود.",reply_markup=admin_kb()); return

    # Owner admin text actions
    admin_action = context.user_data.get("admin_action")
    if admin_action == "welcome_text" and is_admin(user.id):
        global WELCOME_TEXT
        value=(update.message.text or "").strip()
        if not value:
            await update.message.reply_text("❌ أرسل نص الترحيب.")
            return
        WELCOME_TEXT=value
        save_welcome()
        context.user_data.pop("admin_action",None)
        await update.message.reply_text("✅ تم تغيير رسالة الترحيب وحفظها.", reply_markup=admin_kb())
        return

    # Custom emoji ID
    if admin_action and is_admin(user.id) and admin_action.startswith("emoji:"):
        key=admin_action.split(":",1)[1]
        value=(update.message.text or "").strip()
        if not value.isdigit():
            await update.message.reply_text("❌ أرسل Custom Emoji ID رقمي فقط.")
            return
        CUSTOM_EMOJIS[key]=value
        save_emojis()
        context.user_data.pop("admin_action",None)
        await update.message.reply_text(f"✅ تم تغيير إيموجي {EMOJI_NAMES.get(key,key)} إلى:\n<code>{value}</code>", reply_markup=admin_emoji_kb(), parse_mode="HTML")
        return

    if admin_action and is_admin(user.id):
        raw_id = update.message.text.strip()
        if not raw_id.isdigit():
            await update.message.reply_text("❌ أرسل ID رقمي فقط.")
            return
        uid = str(int(raw_id))
        if uid == str(ADMIN_ID):
            await update.message.reply_text("❌ لا يمكن حظر المالك.")
            context.user_data.pop("admin_action", None)
            return
        if uid not in USERS:
            USERS[uid] = {"id": int(uid), "name": "", "username": "", "blocked": False, "messages": 0}
        if admin_action == "ban":
            USERS[uid]["blocked"] = True
            msg = f"🚫 تم حظر المستخدم <code>{uid}</code>."
        else:
            USERS[uid]["blocked"] = False
            msg = f"🔓 تم فتح المستخدم <code>{uid}</code>."
        save_users()
        context.user_data.pop("admin_action", None)
        await update.message.reply_text(msg, reply_markup=admin_kb(), parse_mode="HTML")
        return

    # Admin reply to a report
    rid=context.user_data.get("admin_reply_to")
    if rid and update.effective_user.id==ADMIN_ID:
        report=REPORTS.get(rid)
        if not report:
            context.user_data.pop("admin_reply_to",None)
            await update.message.reply_text("❌ التقرير غير موجود.")
            return
        try:
            await context.bot.send_message(
                chat_id=report["chat_id"],
                text=f"📩 رد من دعم بوت عبودي التوب:\n\n{update.message.text}"
            )
            REPORTS.pop(rid, None)
            save_reports()
            await update.message.reply_text("تم إرسال الرد وحذف الشكوى من رسائل المشاكل.", reply_markup=admin_kb())
        except Exception:
            await update.message.reply_text("❌ تعذر إرسال الرد، ولم يتم حذف الشكوى.")
        context.user_data.pop("admin_reply_to",None)
        return

    # User report text
    if context.user_data.get("report_wait_text"):
        context.user_data["report_text"]=update.message.text.strip()
        context.user_data["report_wait_text"]=False
        await update.message.reply_text(
            "هل تريد رفع التقرير مع صورة؟",
            reply_markup=report_attach_menu())
        return

    s=SESSIONS.get(update.effective_chat.id)
    if not s or not s.get("pending"): return
    p=s["pending"]; m=next((x for x in METADATA if x["ID"]==p["sid"]),None)
    raw=update.message.text.strip().replace(",",".")
    try:
        v=float(raw) if m["Type"]=="float" else int(raw)
    except:
        await update.message.reply_text("❌ قيمة غير صحيحة، أرسل رقماً فقط."); return
    st=settings(s["msg"]); x=find(st,p["sid"])
    if x is None:x=st.add(); x.id=p["sid"]
    if m["Type"]=="float":x.ratio=v
    else:x.value=v
    s["pending"]=None
    await update.message.reply_text(f"✅ تم حفظ {name(m['Name'])} = {v}",reply_markup=sets_kb(p["ci"]))

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    if is_blocked(user.id) and not is_admin(user.id):
        await update.message.reply_text(" تم حظرك من استخدام البوت.")
        return
    if context.user_data.get("await_report_photo"):
        context.user_data["report_photo"]=update.message.photo[-1].file_id
        await finalize_report(update, context, with_photo=True)

async def post_init(application):
    return None

async def global_error_handler(update, context):
    logging.exception("Unhandled update error", exc_info=context.error)
    try:
        msg = getattr(update, "effective_message", None)
        if msg:
            await msg.reply_text("❌ حدث خطأ في هذه العملية فقط. البوت مستمر بالعمل.")
    except Exception:
        pass

def main():
    token = BOT_TOKEN
    if not token:
        raise SystemExit("توكن البوت غير موجود — ضع BOT_TOKEN في متغيرات البيئة")
    app=Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CommandHandler("cancel",cancel))
    app.add_handler(MessageHandler(filters.VIDEO,video_handler))
    app.add_handler(MessageHandler(filters.PHOTO,photo_handler))
    app.add_handler(MessageHandler(filters.Document.ALL,document))
    app.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    app.add_handler(CallbackQueryHandler(callbacks))
    # Dedicated public Stars text trigger. Keep it before the generic text handler.
    app.add_handler(MessageHandler(filters.Regex(r"^(?:\s*(?:ستار|ستارز|نجوم|إضافة\s+نجوم|اضافة\s+نجوم|star|stars)\s*)$"), stars_text_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text))
    app.add_error_handler(global_error_handler)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()
