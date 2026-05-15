import json
import os
import re
import sys
import signal
import asyncio
import httpx
import random
import string
import tempfile
import urllib.parse
import edge_tts
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, ChatJoinRequestHandler, filters
)
from telegram.constants import ParseMode, ChatAction

TOKEN            = "8604585693:AAEOcIirys3e7jxg-C9n8kj6E5taBCmazhs"
ADMIN_ID         = os.getenv("ADMIN_ID", "8600328303")
REQUIRED_GROUP   = os.getenv("REQUIRED_GROUP", "@SHUVOMODS")
NASA_API_KEY     = os.getenv("NASA_API_KEY", "DEMO_KEY")
GROQ_API_KEY     = "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"

GROQ_API_BASE    = "https://openrouter.ai/api/v1/chat/completions"
GROQ_MODEL       = "meta-llama/llama-3.3-70b-instruct"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

PLAYER2_API_KEY  = os.getenv("PLAYER2_API_KEY", "")
MCP_URL          = "https://api.player2.game/api/v1/mcp"
HEADERS_P2       = {"Authorization": f"Bearer {PLAYER2_API_KEY}", "Content-Type": "application/json"}
HEADERS_GROQ     = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

_clear_chats: set = set()
_blacklist_data: dict = {}
_bypass_disabled_groups: set = set()

USER_FILE     = "bot/user.json"
CONFIG_FILE   = "bot/config.json"
DB_FILE       = "bot/databases.json"
CODES_FILE    = "bot/codes.json"
BANNER_FILE   = "bot/banner.png"
FEATURES_FILE = "bot/features.json"
LOG_FILE      = "bot/shuvo.log"
PID_FILE      = "bot/.main_pid"
PAUSE_FILE         = "bot/.paused"
BYPASS_CACHE_FILE  = "bot/response.json"

PHONE_API_URL           = "https://shadow-osint.vercel.app/?type=number&query={}&key=SH"
INSTA_API_URL           = "https://shadow-osint.vercel.app/?type=instagram&username={}&key=SH"
IFSC_API_URL            = "https://shadow-osint.vercel.app/?type=ifsc&query={}&key=SH"
PINCODE_API_URL         = "https://shadow-osint.vercel.app/?type=pincode&query={}&key=SH"
EMAIL_API_URL           = "https://email-to-number-xi.vercel.app/?key=SH4DAW-D4DY&query={}"
FELIX_BYPASS_API        = "https://felix-bypass-api-1.onrender.com/bypass?key=daddyfelix&link=https://linkpays.in/c3COGhj5"

USERID_API_1_URL   = "https://username-usrid-to-num.onrender.com/userid={}?key=f99e8a7942790905e7b6440f001716b1"
USERNAME_API_1_URL  = "https://username-usrid-to-num.onrender.com/username={}?key=f99e8a7942790905e7b6440f001716b1"
USERID_API_2_URL    = "https://store.abdulstoreapi.workers.dev/api/v1?key=ak_915201243484b2f1da78619061064b4e&userid={}"
USERNAME_API_2_URL  = "https://store.abdulstoreapi.workers.dev/api/v1?key=ak_915201243484b2f1da78619061064b4e&username={}"
HITEK_NUM_INFO_API_URL  = "https://sh4dow-d4dy-hi-tek-num-info.vercel.app/?number={}&key=SH4DAW-D4DY"
FFSTATS_API_BASE        = "https://sextyinfo.vercel.app/player-info"
IP_API_BASE             = "http://ip-api.com/json"
WEATHER_API_BASE    = "https://api.open-meteo.com/v1/forecast"
GEOCODING_API_BASE  = "https://geocoding-api.open-meteo.com/v1/search"
UNIVERSITY_API_BASE = "http://universities.hipolabs.com/search"
RANDOMUSER_API_BASE = "https://randomuser.me/api"
COUNTRY_API_BASE    = "https://restcountries.com/v3.1/name"
NASA_APOD_BASE      = "https://api.nasa.gov/planetary/apod"
NASA_EPIC_BASE      = "https://api.nasa.gov/EPIC/api/natural"

SHADOW_API_BASE     = "https://shadow-osint.vercel.app"
SHADOW_API_KEY      = "SH"
VEHICLE_RC_API_BASE = "https://vehicle-rc-to-num.vercel.app"
VEHICLE_RC_API_KEY  = "SH4DAW-D4DY"
GST_API_BASE        = "https://gst-to-info.vercel.app"
GST_API_KEY         = "SH4DAW-D4DY"

VOICE_MAP = {
    "bd":  "bn-BD-NabanitaNeural",
    "bn":  "bn-BD-NabanitaNeural",
    "en":  "en-US-JennyNeural",
    "us":  "en-US-JennyNeural",
    "uk":  "en-GB-SoniaNeural",
    "hi":  "hi-IN-SwaraNeural",
    "in":  "hi-IN-SwaraNeural",
    "ar":  "ar-EG-SalmaNeural",
    "fr":  "fr-FR-DeniseNeural",
    "de":  "de-DE-KatjaNeural",
    "ja":  "ja-JP-NanamiNeural",
    "ko":  "ko-KR-SunHiNeural",
    "zh":  "zh-CN-XiaoxiaoNeural",
    "ru":  "ru-RU-SvetlanaNeural",
    "es":  "es-ES-ElviraNeural",
    "tr":  "tr-TR-EmelNeural",
    "pt":  "pt-BR-FranciscaNeural",
    "ur":  "ur-PK-UzmaNeural",
    "ta":  "ta-IN-PallaviNeural",
    "te":  "te-IN-ShrutiNeural",
    "it":  "it-IT-ElsaNeural",
}
VOICE_DEFAULT = "bn-BD-NabanitaNeural"

DELETE_AFTER  = 60
DB_PAGE_SIZE  = 10

PENDING_NONE        = None
PENDING_USERID      = "userid"
PENDING_USERNUM     = "usernum"
PENDING_INDINFO     = "indinfo"
PENDING_INSTAINFO   = "instainfo"
PENDING_DOWNLOAD    = "download"
PENDING_PINCODE     = "pincode"
PENDING_IFSC        = "ifsc"
PENDING_IPINFO      = "ipinfo"
PENDING_FFSTATS     = "ffstats"
PENDING_EMAILREP    = "emailrep"
PENDING_BLAST       = "blast"
PENDING_VEHICLE     = "vehicle"
PENDING_WEATHER     = "weather"
PENDING_UNIVERSITY  = "university"
PENDING_COUNTRY     = "country"
PENDING_AADHAR      = "aadhar"
PENDING_GST         = "gst"
PENDING_PAN         = "pan"
PENDING_PAKNUM      = "paknum"
PENDING_VEHICLE_RC  = "vehicle_rc"
PENDING_UPI         = "upi"
PENDING_VOICE       = "voice"
PENDING_MKCODE_CREDITS = "mkcode_credits"
PENDING_MKCODE_USERS   = "mkcode_users"
PENDING_MKCODE_DAYS    = "mkcode_days"
PENDING_MKCODE_EXPIRY  = "mkcode_expiry"
PENDING_BROADCAST      = "broadcast"

PENDING_MAKEAADHAR_NAME   = "makeaadhar_name"
PENDING_MAKEAADHAR_DOB    = "makeaadhar_dob"
PENDING_MAKEAADHAR_GENDER = "makeaadhar_gender"
PENDING_MAKEAADHAR_NUM    = "makeaadhar_num"
PENDING_MAKEAADHAR_ADDR   = "makeaadhar_addr"
PENDING_MAKEAADHAR_PHOTO  = "makeaadhar_photo"

_mkcode_state: dict = {}
_makeaadhar_state: dict = {}
_error_log: list = []
_ai_history: dict = {}
_bot_username: str = ""
_pending_dm_reply: dict = {}

# ── Tools that are FREE (no credit cost) ──
FREE_AI_TOOLS = {"nasa_apod", "nasa_epic", "generate_image", "get_bot_help", "check_balance"}

# ── AI System Prompt ──
AI_SYSTEM_PROMPT = """Tumi SHUVO AI. Tumi ekta fun, witty, street-smart Bangladeshi AI — assistant na, dost.

IDENTITY:
- Naam: SHUVO AI | Creator: @Shuvobhai
- Tumi ChatGPT na, assistant na — tumi nijor moto ek unique AI
- Compare hole: "Ami SHUVO AI bhai, amar sathe compare kora thik na 😂"
- Kabhi boring, formal ba robotic hoyo na

LANGUAGE (ZERO EXCEPTION):
- User Bengali likhle → Roman Bengali reply: "ki hoise bhai? bolo!"
- User Hindi likhle → Roman Hindi: "bata bhai kya hua!"
- User English likhle → chill English reply
- NEVER use বাংলা/Hindi/Arabic script — ALWAYS Roman A-Z letters only

TOOLS — jodi user kono lookup চায়, turant koro, jiggesh na:
OSINT: TG ID→Phone | Username→Phone | Indian Num | Instagram | IP | Email | Vehicle | Aadhaar | GST | PAN | UPI | Paknum | RC | IFSC | Pincode | FF Stats | Weather
Media: NASA APOD | NASA EPIC | AI Image Gen | Video Download
Utils: Daily Claim | Balance | Bot Help

CREDIT: chat = free | tools = 1 credit | spend er age bolo

⚠️ REPLY RULES — MOST IMPORTANT, NEVER BREAK:
1. MAX 3 LINES ONLY — hard limit, kono exception nei
2. NO lists, NO bullet points, NO numbered steps
3. NO "Here is...", NO "Sure!", NO "Of course!" — sidha reply diye dao
4. Fun, casual, roast/banter ok — boring robotic tone FORBIDDEN
5. Emoji: max 1-2 total per reply, meaningful only
6. Sign off: 👺 @Shuvobhai (only at the end, once)

FUN EXAMPLES (copy this vibe):
- User: "tumi ki?" → "Ami SHUVO AI — tomar fun bhai, assistant na 😎 👺 @Shuvobhai"
- User: "kemon acho?" → "Ek number! Tumi bolo ki lagbe? 👺 @Shuvobhai"
- User: "ChatGPT er theke valo?" → "ChatGPT amake dekhe lonka 🌶️ — ami SHUVO AI 👺 @Shuvobhai"
- User: "help me" → "Bol ki lagbe bhai, ready achi! 👺 @Shuvobhai"
"""

# ── Groq Tool Definitions (function calling) ──
GROQ_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_tg_id",
            "description": "Look up phone number linked to a Telegram user ID. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Telegram numeric user ID, e.g. '123456789'"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_username",
            "description": "Look up phone number linked to a Telegram username. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Telegram username without @, e.g. 'username'"}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_indian_number",
            "description": "Get detailed info about an Indian phone number (operator, location, etc). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Indian phone number, e.g. '9876543210'"}
                },
                "required": ["number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_instagram",
            "description": "Get Instagram profile info (followers, bio, verified status etc). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Instagram username without @"}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_ip",
            "description": "Get info about an IP address (country, city, ISP, coordinates). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ip": {"type": "string", "description": "IPv4 or IPv6 address, e.g. '8.8.8.8'"}
                },
                "required": ["ip"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_pincode",
            "description": "Look up Indian postal pincode info (district, state, area). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pincode": {"type": "string", "description": "6-digit Indian pincode, e.g. '110001'"}
                },
                "required": ["pincode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_ifsc",
            "description": "Look up Indian bank IFSC code (bank name, branch, address). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ifsc": {"type": "string", "description": "Bank IFSC code, e.g. 'SBIN0001234'"}
                },
                "required": ["ifsc"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_ffstats",
            "description": "Get Free Fire player stats by UID. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {"type": "string", "description": "Free Fire UID number"},
                    "server": {"type": "string", "description": "Server region: IND, SG, BR, US, ME, VN (default: IND)"}
                },
                "required": ["uid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_emailrep",
            "description": "Check email reputation (suspicious, spam score, references). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to check"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_vehicle",
            "description": "Get vehicle specs/models by make and year. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "make": {"type": "string", "description": "Vehicle manufacturer/make, e.g. 'Toyota'"},
                    "year": {"type": "string", "description": "Model year, e.g. '2020'"}
                },
                "required": ["make", "year"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_weather",
            "description": "Get current weather for any city. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Dhaka' or 'Mumbai'"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_university",
            "description": "Search universities in a country. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name, e.g. 'Bangladesh'"}
                },
                "required": ["country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_country",
            "description": "Get detailed country info (capital, population, currency, languages). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name, e.g. 'Bangladesh'"}
                },
                "required": ["country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_randomuser",
            "description": "Generate a random fake user profile. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_video",
            "description": "Download video from YouTube, TikTok, Instagram URL. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Video URL to download"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nasa_apod",
            "description": "Get NASA Astronomy Picture of the Day. FREE, no credits.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nasa_epic",
            "description": "Get NASA EPIC Earth photos from space. FREE, no credits.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an AI image from a text prompt. FREE, no credits.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image description/prompt"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_balance",
            "description": "Check user's current credit balance. FREE.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_bot_help",
            "description": "Get list of all bot commands and features. FREE.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_aadhar",
            "description": "Look up info from an Indian Aadhar card number (12 digits). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "aadhar": {"type": "string", "description": "12-digit Aadhar number, e.g. '123456789012'"}
                },
                "required": ["aadhar"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_gst",
            "description": "Look up GST number info (business name, address, status). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gst": {"type": "string", "description": "GST number, e.g. '10DJCPK4351Q1Z5'"}
                },
                "required": ["gst"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_pan",
            "description": "Look up PAN card info (name, status). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pan": {"type": "string", "description": "PAN number, e.g. 'AAMTS3432L'"}
                },
                "required": ["pan"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_pakistan_number",
            "description": "Look up Pakistan mobile number info (name, CNIC, address). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {"type": "string", "description": "Pakistan mobile number, e.g. '03001234567'"}
                },
                "required": ["number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_vehicle_rc",
            "description": "Look up vehicle info from RC (registration certificate) number. Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rc": {"type": "string", "description": "Vehicle RC number, e.g. 'MH12AB1234'"}
                },
                "required": ["rc"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_upi",
            "description": "Look up UPI ID info (account holder name, validity). Costs 1 credit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "upi": {"type": "string", "description": "UPI ID, e.g. 'name@paytm'"}
                },
                "required": ["upi"]
            }
        }
    },
]


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_users():     return load_json(USER_FILE, {})
def save_users(d):    save_json(USER_FILE, d)
def load_config():    return load_json(CONFIG_FILE, {"autoapprove_chats": []})
def save_config(d):   save_json(CONFIG_FILE, d)
def load_databases(): return load_json(DB_FILE, [])
def load_codes():     return load_json(CODES_FILE, {})
def save_codes(d):    save_json(CODES_FILE, d)

_DEFAULT_FEATURES = {
    "ai_chat": True, "daily_claim": True, "redeem": True, "voice": True,
    "imagegen": True, "music": True, "videogen": True, "sprite": True,
    "model3d": True, "editimage": True, "tgid": True, "tguser": True,
    "indinfo": True, "instainfo": True, "viddown": True, "pincode": True,
    "ifsc": True, "ipinfo": True, "ffstats": True, "emailrep": True,
    "vehicle": True, "weather": True, "nasa": True, "aadhar": True,
    "gst": True, "pan": True, "paknum": True, "vehicle_rc": True, "upi": True,
    "randomuser": True, "university": True, "country": True,
}

def load_features() -> dict:
    try:
        with open(FEATURES_FILE) as f:
            data = json.load(f)
    except Exception:
        data = {}
    for k, v in _DEFAULT_FEATURES.items():
        if k not in data:
            data[k] = v
    return data

def is_enabled(feature: str) -> bool:
    return load_features().get(feature, True)

def write_log(msg: str):
    try:
        os.makedirs("bot", exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass


async def send_user_log(bot, tg_user, action_type: str, content: str):
    cfg = load_config()
    log_group = cfg.get("log_group_id")
    if not log_group:
        return
    try:
        name = (tg_user.first_name or "")
        if tg_user.last_name:
            name += f" {tg_user.last_name}"
        name = name.strip() or "Unknown"
        uname = f"@{tg_user.username}" if tg_user.username else "—"
        now = datetime.now().strftime("%d %b %Y  %H:%M:%S")
        preview = content[:300] + ("…" if len(content) > 300 else "")

        def _esc(t): return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        text = (
            f"📨 <b>User Activity Log</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Name</b>     : {_esc(name)}\n"
            f"🆔 <b>User ID</b>  : <code>{tg_user.id}</code>\n"
            f"📛 <b>Username</b> : {_esc(uname)}\n"
            f"⚡ <b>Type</b>     : {action_type}\n"
            f"📝 <b>Content</b>  : <code>{_esc(preview)}</code>\n"
            f"🕐 <b>Time</b>     : {now}"
        )
        short_name = name[:18]
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(f"💬 DM {short_name}", callback_data=f"log_dm_{tg_user.id}")
        ]])
        await bot.send_message(chat_id=int(log_group), text=text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        write_log(f"LOG_SEND_ERROR: {e}")


async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.effective_user:
        return
    uid = str(update.effective_user.id)
    if uid == str(ADMIN_ID):
        return
    users_data = load_users()
    if users_data.get(uid, {}).get("is_admin"):
        return

    chat_type = update.effective_chat.type
    text = update.message.text or update.message.caption or ""

    # In groups, only log when the bot is actually involved (mention or reply to bot)
    if chat_type in ("group", "supergroup"):
        is_mention = _bot_username and f"@{_bot_username}" in (text or "").lower()
        is_reply_to_bot = (
            update.message.reply_to_message is not None and
            update.message.reply_to_message.from_user is not None and
            update.message.reply_to_message.from_user.id == context.bot.id
        )
        if not is_mention and not is_reply_to_bot:
            return
        chat_name = update.effective_chat.title or "Group"
        src = f"👥 Group: <b>{chat_name}</b>"
    else:
        src = "💬 Private DM"

    if text.startswith("/"):
        cmd = text.split()[0]
        action_type = f"⌨️ Command: <b>{cmd}</b>  [{src}]"
    else:
        action_type = f"💬 Message  [{src}]"

    asyncio.create_task(
        send_user_log(context.bot, update.effective_user, action_type, text or "[non-text]")
    )


def is_paused() -> bool:
    return os.path.exists(PAUSE_FILE)

def get_user(users, uid, username="", first_name=""):
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "credits": 3, "banned": False,
            "is_admin": uid == str(ADMIN_ID),
            "last_claim": None, "username": username,
            "first_name": first_name,
        }
    else:
        if username:
            users[uid]["username"] = username
        if first_name:
            users[uid]["first_name"] = first_name
    return users[uid], uid

def find_user_by_username(users, raw):
    raw = raw.lstrip("@").lower()
    for uid, u in users.items():
        if (u.get("username") or "").lower() == raw:
            return u, uid
    return None, None

def is_owner(uid):
    return str(uid) == str(ADMIN_ID)

def get_role(user, uid):
    if is_owner(uid):
        return "👑 OWNER"
    if user.get("is_admin"):
        return "🛡 ADMIN"
    return "👤 USER"

def credit_display(user):
    return "∞" if user.get("is_admin") else str(user["credits"])

def spend_credit(users, uid):
    uid = str(uid)
    if users[uid].get("is_admin"):
        return True
    if users[uid]["credits"] <= 0:
        return False
    users[uid]["credits"] -= 1
    save_users(users)
    return True

def has_credits(users, uid):
    uid = str(uid)
    if users[uid].get("is_admin"):
        return True
    return users[uid]["credits"] > 0

def is_autoapprove(chat_id):
    cfg = load_config()
    return str(chat_id) in cfg.get("autoapprove_chats", [])

def safe_json(r, default=None):
    if default is None:
        default = {}
    try:
        if not r.text.strip():
            return default
        return r.json()
    except Exception:
        return default

def h(text):
    return str(text).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def bq(text):
    return f'<blockquote expandable>{text}</blockquote>'

def fmt_ai(text: str, max_lines: int = 3) -> str:
    """Convert AI markdown to safe Telegram HTML.
    Escapes HTML first, applies markdown, then hard-limits to max_lines."""
    t = str(text)
    # Step 1: escape all raw HTML-unsafe chars
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Step 2: convert markdown → HTML tags (safe now)
    t = re.sub(r'\*\*(.+?)\*\*',   r'<b>\1</b>',       t, flags=re.DOTALL)
    t = re.sub(r'__(.+?)__',       r'<b>\1</b>',       t, flags=re.DOTALL)
    t = re.sub(r'\*([^*\n]+?)\*',  r'<i>\1</i>',       t)
    t = re.sub(r'_([^_\n]+?)_',    r'<i>\1</i>',       t)
    t = re.sub(r'`([^`\n]+)`',     r'<code>\1</code>', t)
    # Step 3: clean AI noise
    t = re.sub(r'#{1,6}\s+', '', t)      # strip # headers
    t = re.sub(r'\n{3,}', '\n\n', t)     # max 2 blank lines
    t = t.strip()
    # Step 4: HARD limit — cut to max_lines lines
    lines = t.splitlines()
    if len(lines) > max_lines:
        t = "\n".join(lines[:max_lines])
    return t

def schedule_delete(msg):
    asyncio.create_task(_delete_later(msg))

async def _delete_later(msg):
    await asyncio.sleep(DELETE_AFTER)
    try:
        await msg.delete()
    except Exception:
        pass

def delete_query_msg(query):
    asyncio.create_task(_delete_msg(query.message))

async def _check_maintenance(update: Update) -> bool:
    """Returns True (and notifies user) if bot is in maintenance mode."""
    if is_paused() and str(update.effective_user.id) != str(ADMIN_ID):
        sent = await update.message.reply_text(
            bq("🔧 <b>Maintenance Mode</b>\n\nBot is under maintenance. Please try again later.\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return True
    return False

async def _check_feature(update: Update, feature: str) -> bool:
    """Returns True (and notifies user) if feature is disabled."""
    if not is_enabled(feature):
        sent = await update.message.reply_text(
            bq("🚫 <b>Feature Disabled</b>\n\nThis feature has been disabled by the admin.\n\nUse /start to see available features.\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return True
    return False

async def _check_banned(update: Update, user: dict) -> bool:
    """Returns True (and notifies user) if user is banned."""
    if user.get("banned"):
        sent = await update.message.reply_text(
            bq("⛔ <b>You are banned</b> from using this bot.\n\nContact admin if you think this is a mistake."),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return True
    return False

async def _check_credits(update: Update, user: dict) -> bool:
    """Returns True (and notifies user) if user has no credits."""
    if not user.get("is_admin") and user.get("credits", 0) <= 0:
        sent = await update.message.reply_text(
            bq("❌ <b>Insufficient Credits</b>\n\nUse /start to claim your daily credits (+3).\n\n💡 Or use /ai — I can do it for you!\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return True
    return False

async def _delete_msg(msg):
    try:
        await msg.delete()
    except Exception:
        pass

# ── Player2 MCP helpers ──
async def mcp_init(client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.post(
            MCP_URL, headers=HEADERS_P2,
            json={
                "jsonrpc": "2.0", "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "shuvo-bot", "version": "2.0"},
                },
            },
            timeout=30,
        )
        return resp.headers.get("mcp-session-id")
    except Exception:
        return None

async def mcp_call(client: httpx.AsyncClient, session_id: str, tool: str, params: dict) -> dict:
    headers = {**HEADERS_P2, "mcp-session-id": session_id}
    resp = await client.post(
        MCP_URL, headers=headers,
        json={
            "jsonrpc": "2.0", "id": 2,
            "method": "tools/call",
            "params": {"name": tool, "arguments": params},
        },
        timeout=60,
    )
    data = resp.json()
    result = data.get("result") or {}
    content = result.get("content") or []
    if content and isinstance(content, list):
        for item in content:
            if item.get("type") == "text":
                try:
                    return json.loads(item["text"])
                except Exception:
                    return {"raw": item["text"]}
    return data

async def mcp_poll_job(client: httpx.AsyncClient, session_id: str,
                       check_tool: str, job_id: str,
                       interval: int = 10, max_wait: int = 300) -> dict:
    elapsed = 0
    while elapsed < max_wait:
        await asyncio.sleep(interval)
        elapsed += interval
        result = await mcp_call(client, session_id, check_tool, {"job_id": job_id})
        status = result.get("status", "")
        if status in ("completed", "succeeded", "failed", "done"):
            return result
    return {"status": "timeout"}

def is_quota_error(result: dict) -> bool:
    raw = str(result).lower()
    return any(k in raw for k in ("quota", "limit", "exceeded", "rate", "insufficient",
                                   "no credit", "credits", "balance"))

async def generate_image_player2(prompt: str) -> str | None:
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            return None
        result = await mcp_call(client, session_id, "generate_image", {"prompt": prompt})
        if is_quota_error(result):
            return "QUOTA"
        return result.get("image_url") or result.get("url") or None

async def generate_image_fallback(prompt: str) -> str:
    encoded = prompt.replace(" ", "%20")[:300]
    seed = random.randint(1, 99999)
    return f"https://image.pollinations.ai/prompt/{encoded}?seed={seed}&width=1024&height=1024&model=flux&nologo=true"

async def _send_audio_robust(context, chat_id: int, url: str, caption: str):
    try:
        await context.bot.send_audio(chat_id=chat_id, audio=url,
                                     caption=caption, parse_mode=ParseMode.MARKDOWN_V2)
        return
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(follow_redirects=True) as dl:
            r = await dl.get(url, timeout=90)
            bio = BytesIO(r.content)
            bio.name = "music.mp3"
        await context.bot.send_audio(chat_id=chat_id, audio=bio,
                                     caption=caption, parse_mode=ParseMode.MARKDOWN_V2)
        return
    except Exception:
        pass
    try:
        await context.bot.send_document(chat_id=chat_id, document=url,
                                        caption=caption, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        await context.bot.send_message(chat_id=chat_id,
                                       text=f"🎵 Music ready\\! [Download here]({url})",
                                       parse_mode=ParseMode.MARKDOWN_V2)

def _esc(text: str) -> str:
    for ch in r"\_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def get_required_channels():
    cfg = load_config()
    return cfg.get("required_channels", [])

async def check_force_join(bot, user_id: int) -> list:
    unjoined = []
    for ch in get_required_channels():
        try:
            member = await bot.get_chat_member(ch["username"], user_id)
            if member.status in ("left", "kicked"):
                unjoined.append(ch)
        except Exception:
            pass
    return unjoined

def force_join_keyboard(unjoined: list) -> InlineKeyboardMarkup:
    rows = []
    for ch in unjoined:
        link = ch.get("link", "")
        if not link.startswith("http"):
            link = f"https://t.me/{ch['username'].lstrip('@')}"
        rows.append([InlineKeyboardButton(f"🔔 Join {h(ch['title'])}", url=link)])
    rows.append([InlineKeyboardButton("✅ I've Joined — Verify Now", callback_data="verify_join")])
    return InlineKeyboardMarkup(rows)

async def is_group_member(bot, user_id):
    try:
        member = await bot.get_chat_member(REQUIRED_GROUP, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return False


async def _fetch_userid_info(client, query: str, is_username: bool = False) -> dict:
    """Call both APIs concurrently and merge all records. Returns rich dict."""
    url1 = USERNAME_API_1_URL.format(query) if is_username else USERID_API_1_URL.format(query)
    url2 = USERNAME_API_2_URL.format(query) if is_username else USERID_API_2_URL.format(query)

    async def try_get(url):
        try:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            return safe_json(r, {})
        except Exception:
            return {}

    data1, data2 = await asyncio.gather(try_get(url1), try_get(url2))

    # ── Extract from API1 (username-usrid-to-num.onrender.com) ──
    # Structure: {status, target_id, data: {source1: {records: [{userid,country,country_code,number}]}}}
    records1 = []
    d1_data = data1.get("data") or {}
    if isinstance(d1_data, dict):
        for src in d1_data.values():
            if isinstance(src, dict):
                recs = src.get("records") or []
                for rec in recs:
                    if isinstance(rec, dict) and rec.get("number"):
                        records1.append({
                            "phone":        str(rec.get("number", "")).strip(),
                            "country":      str(rec.get("country", "")).strip(),
                            "country_code": str(rec.get("country_code", "")).strip(),
                            "first_name":   str(rec.get("first_name", "") or "").strip(),
                            "total_groups": rec.get("total_groups"),
                        })

    # ── Extract from API2 (store.abdulstoreapi.workers.dev) ──
    # Structure: {status, data: {found, country, country_code, number}}
    records2 = []
    d2_data = data2.get("data") or {}
    if isinstance(d2_data, dict) and d2_data.get("found"):
        records2.append({
            "phone":        str(d2_data.get("number", "")).strip(),
            "country":      str(d2_data.get("country", "")).strip(),
            "country_code": str(d2_data.get("country_code", "")).strip(),
            "first_name":   str(d2_data.get("first_name", "") or "").strip(),
            "total_groups": None,
        })

    # Merge: deduplicate by phone number
    seen_phones = set()
    all_records = []
    for rec in records1 + records2:
        p = rec["phone"]
        if p and p not in seen_phones:
            seen_phones.add(p)
            all_records.append(rec)

    # Best single result (first found)
    best = all_records[0] if all_records else {}
    return {
        "phone":        best.get("phone", ""),
        "country":      best.get("country", ""),
        "country_code": best.get("country_code", ""),
        "first_name":   best.get("first_name", ""),
        "total_groups": best.get("total_groups"),
        "all_records":  all_records,
    }


# ══════════════════════════════════════════════
# AI TOOL EXECUTOR — runs actual API calls
# ══════════════════════════════════════════════

async def execute_ai_tool(tool_name: str, args: dict, uid: str, users: dict) -> tuple[str, str, bool]:
    """
    Execute a bot tool on behalf of the AI.
    Returns: (formatted_html_result, plain_result_for_ai, is_media_url)
    is_media_url=True means result is an image/photo URL
    """
    try:
        async with httpx.AsyncClient(timeout=25) as client:

            if tool_name == "lookup_tg_id":
                user_id_str = args.get("user_id", "").strip()
                clean_id = re.sub(r'\D', '', user_id_str)
                info = await _fetch_userid_info(client, clean_id, is_username=False)
                all_recs = info.get("all_records", [])
                lines = [f"🔎 <b>TG ID Lookup</b>\n\n🆔 ID: <code>{h(user_id_str)}</code>"]
                plain_lines = [f"TG ID {user_id_str}:"]
                if all_recs:
                    lines.append(f"📊 Results: <b>{len(all_recs)}</b>\n")
                    for i, rec in enumerate(all_recs, 1):
                        cc   = rec.get("country_code", "")
                        num  = rec.get("phone", "")
                        full = f"{cc}{num}" if cc and not num.startswith(cc.lstrip("+")) else num
                        lines.append(f"<b>#{i}</b>")
                        lines.append(f"📱 Phone: <code>{h(full)}</code>")
                        if cc:   lines.append(f"🔢 Country Code: <b>{h(cc)}</b>")
                        cntry = rec.get("country", "")
                        if cntry: lines.append(f"🌍 Country: <b>{h(cntry)}</b>")
                        fn = rec.get("first_name", "")
                        if fn: lines.append(f"👤 Name: {h(fn)}")
                        tg = rec.get("total_groups")
                        if tg: lines.append(f"👥 Groups: {h(str(tg))}")
                        plain_lines.append(f"Phone: {full}, Country: {cntry}")
                        if i < len(all_recs): lines.append("")
                else:
                    lines.append("\n📱 Phone: <b>Not found in database</b>")
                    plain_lines.append("Phone: Not found")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_username":
                uname = args.get("username", "").lstrip("@").strip()
                info = await _fetch_userid_info(client, uname, is_username=True)
                all_recs = info.get("all_records", [])
                lines = [f"👤 <b>Username Lookup</b>\n\n👤 @{h(uname)}"]
                plain_lines = [f"@{uname}:"]
                if all_recs:
                    lines.append(f"📊 Results: <b>{len(all_recs)}</b>\n")
                    for i, rec in enumerate(all_recs, 1):
                        cc   = rec.get("country_code", "")
                        num  = rec.get("phone", "")
                        full = f"{cc}{num}" if cc and not num.startswith(cc.lstrip("+")) else num
                        lines.append(f"<b>#{i}</b>")
                        lines.append(f"📱 Phone: <code>{h(full)}</code>")
                        if cc:   lines.append(f"🔢 Country Code: <b>{h(cc)}</b>")
                        cntry = rec.get("country", "")
                        if cntry: lines.append(f"🌍 Country: <b>{h(cntry)}</b>")
                        fn = rec.get("first_name", "")
                        if fn: lines.append(f"👤 Name: {h(fn)}")
                        plain_lines.append(f"Phone: {full}, Country: {cntry}")
                        if i < len(all_recs): lines.append("")
                else:
                    lines.append("\n📱 Phone: <b>Not found</b>")
                    plain_lines.append("Phone: Not found")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_indian_number":
                number = args.get("number", "").strip()
                clean_num = re.sub(r'\D', '', number)

                async def _ind_fetch_shadow():
                    try:
                        r = await client.get(PHONE_API_URL.format(clean_num), headers={"User-Agent": "Mozilla/5.0"})
                        return safe_json(r, {})
                    except Exception:
                        return {}

                async def _ind_fetch_hitek():
                    try:
                        r = await client.get(HITEK_NUM_INFO_API_URL.format(clean_num), headers={"User-Agent": "Mozilla/5.0"})
                        return safe_json(r, {})
                    except Exception:
                        return {}

                shadow_data, hitek_data = await asyncio.gather(_ind_fetch_shadow(), _ind_fetch_hitek())

                META_KEYS  = {'status','success','error','message','msg','developer','dev','key','apikey','numbere','number','query','_raw','time','result','count','total','type','n','credit','searched_userid','response_time','code'}
                EMPTY_VALS = (None, '', 'N/A', 'None', 'null', 'undefined', 'false', 'False', 0)

                def extract_records(data):
                    inner = data.get("result") or {}
                    records = []
                    if isinstance(inner, dict):
                        records = inner.get("results") or inner.get("data") or []
                    if not records:
                        records = data.get("data") or []
                    if isinstance(records, dict):
                        records = [records]
                    return [rec for rec in records if isinstance(rec, dict) and any(
                        str(k).lower() not in META_KEYS and v not in EMPTY_VALS
                        for k, v in rec.items() if not isinstance(v, (dict, list))
                    )]

                real = extract_records(shadow_data) + extract_records(hitek_data)

                lines      = [f"📱 <b>Indian Number Info</b>\n\n📞 Number: <code>{h(number)}</code>"]
                plain_lines= [f"Indian Number {number}:"]
                if real:
                    lines.append(f"📊 Records: <b>{len(real)}</b>\n")
                    for i, rec in enumerate(real[:5], 1):
                        lines.append(f"\n<b>Record {i}:</b>")
                        for k, v in rec.items():
                            if str(k).lower() not in META_KEYS and v not in EMPTY_VALS and not isinstance(v, (dict, list)):
                                label = str(k).replace("_", " ").title()
                                lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                                plain_lines.append(f"{label}: {v}")
                else:
                    lines.append("❌ No data found.")
                    plain_lines.append("No data found.")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_instagram":
                uname = args.get("username", "").lstrip("@").strip()
                r = await client.get(INSTA_API_URL.format(uname), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                d = data.get("data") or data
                if isinstance(d, list) and d: d = d[0]
                if not isinstance(d, dict): d = data
                name     = d.get("name") or d.get("full_name") or ""
                bio      = d.get("bio") or ""
                followers= d.get("followers") or 0
                following= d.get("following") or 0
                posts    = d.get("posts") or 0
                private  = bool(d.get("private") or d.get("is_private"))
                verified = bool(d.get("verified"))
                pic      = d.get("pic") or ""
                result   = bq(
                    f"📸 <b>Instagram Info</b>\n\n"
                    f"👤 @{h(uname)}\n"
                    f"📛 Name: <b>{h(name) if name else 'N/A'}</b>\n"
                    f"📝 Bio: {h(bio[:200]) if bio else 'N/A'}\n"
                    f"👥 Followers: <b>{h(str(followers))}</b>\n"
                    f"➡️ Following: <b>{h(str(following))}</b>\n"
                    f"📷 Posts: <b>{h(str(posts))}</b>\n"
                    f"🔒 Private: {'Yes' if private else 'No'}\n"
                    f"✅ Verified: {'Yes' if verified else 'No'}\n"
                    + (f"🖼 Pic: <a href='{pic}'>View</a>\n" if pic else "")
                    + f"\n👺 DEV @Shuvobhai ✅"
                )
                plain = f"Instagram @{uname}: Name={name}, Followers={followers}, Private={private}"
                return result, plain, False

            elif tool_name == "lookup_ip":
                ip = args.get("ip", "").strip()
                r = await client.get(f"{IP_API_BASE}/{ip}")
                data = safe_json(r)
                result = bq(
                    f"🌐 <b>IP Info</b>\n\n"
                    f"🖥 IP: <code>{h(ip)}</code>\n"
                    f"🌍 Country: <b>{h(data.get('country','N/A'))}</b>\n"
                    f"🏙 City: {h(data.get('city','N/A'))}\n"
                    f"🌐 ISP: {h(data.get('isp','N/A'))}\n"
                    f"🕐 Timezone: {h(data.get('timezone','N/A'))}\n"
                    f"📍 Lat/Lon: {h(data.get('lat','N/A'))}, {h(data.get('lon','N/A'))}\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                )
                plain = f"IP {ip}: {data.get('country','?')}, {data.get('city','?')}, ISP={data.get('isp','?')}"
                return result, plain, False

            elif tool_name == "lookup_pincode":
                pincode = args.get("pincode", "").strip()
                r = await client.get(PINCODE_API_URL.format(pincode), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                post_offices = data.get("PostOffice") or []
                if post_offices:
                    po = post_offices[0]
                    result = bq(
                        f"📮 <b>Pincode Info</b>\n\n"
                        f"📌 Pincode: <code>{h(pincode)}</code>\n"
                        f"🏙 District: <b>{h(po.get('District','N/A'))}</b>\n"
                        f"🗺 State: <b>{h(po.get('State','N/A'))}</b>\n"
                        f"🏘 Area: <b>{h(po.get('Name','N/A'))}</b>\n"
                        f"📯 Division: {h(po.get('Division','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"Pincode {pincode}: {po.get('Name','?')}, {po.get('District','?')}, {po.get('State','?')}"
                else:
                    result = bq(f"📮 <b>Pincode Info</b>\n\n❌ No data for: <code>{h(pincode)}</code>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"Pincode {pincode}: Not found"
                return result, plain, False

            elif tool_name == "lookup_ifsc":
                ifsc = args.get("ifsc", "").upper().strip()
                r = await client.get(IFSC_API_URL.format(ifsc), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                if isinstance(data, dict) and (data.get("BANK") or data.get("bank")):
                    result = bq(
                        f"🏦 <b>IFSC Info</b>\n\n"
                        f"🔑 IFSC: <code>{h(data.get('IFSC') or ifsc)}</code>\n"
                        f"🏦 Bank: <b>{h(data.get('BANK') or data.get('bank','N/A'))}</b>\n"
                        f"🏢 Branch: {h(data.get('BRANCH') or data.get('branch','N/A'))}\n"
                        f"🏙 City: {h(data.get('CITY') or data.get('city','N/A'))}\n"
                        f"🗺 State: {h(data.get('STATE') or data.get('state','N/A'))}\n"
                        f"📍 Address: {h(data.get('ADDRESS') or data.get('address','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"IFSC {ifsc}: {data.get('BANK','?')}, {data.get('BRANCH','?')}, {data.get('CITY','?')}"
                else:
                    result = bq(f"🏦 <b>IFSC Info</b>\n\n❌ Invalid IFSC: <code>{h(ifsc)}</code>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"IFSC {ifsc}: Not found or invalid"
                return result, plain, False

            elif tool_name == "lookup_ffstats":
                ff_uid = re.sub(r'\D', '', args.get("uid", "").strip())
                r = await client.get(f"{FFSTATS_API_BASE}?uid={ff_uid}", headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                basic = data.get("basicInfo", {})
                if not basic:
                    result = bq(f"📊 <b>Free Fire Stats</b>\n\n🆔 UID: <code>{h(ff_uid)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"FF UID {ff_uid}: No data found"
                else:
                    result = bq(
                        f"📊 <b>Free Fire Stats</b>\n\n"
                        f"🆔 UID: <code>{h(ff_uid)}</code>\n"
                        f"👤 Name: <b>{h(basic.get('nickname','N/A'))}</b>\n"
                        f"⭐ Level: {h(basic.get('level','N/A'))}\n"
                        f"🏆 Rank: {h(basic.get('rank','N/A'))}\n"
                        f"🌍 Region: {h(basic.get('region','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"FF UID {ff_uid}: {basic.get('nickname','?')}, Level {basic.get('level','?')}"
                return result, plain, False

            elif tool_name == "lookup_emailrep":
                email = args.get("email", "").strip()
                r = await client.get(EMAIL_API_URL.format(urllib.parse.quote(email, safe="")), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                SKIP_EM = {"success", "developer", "dev", "query", "email", "status", "key"}
                lines      = [f"📧 <b>Email Lookup</b>\n\n📨 Email: <code>{h(email)}</code>"]
                plain_lines= [f"Email {email}:"]
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k in SKIP_EM or isinstance(v, (dict, list)): continue
                        if v and str(v) not in ("None", "null", "N/A", "", "false", "False"):
                            label = str(k).replace("_", " ").title()
                            lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                            plain_lines.append(f"{label}: {v}")
                if len(lines) == 1:
                    lines.append("❌ No data found for this email.")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_vehicle":
                rc = args.get("rc", args.get("make", "")).strip().upper()
                rc = re.sub(r'\s+', '', rc)
                if len(rc) < 6:
                    return bq(f"🚗 <b>Vehicle RC Lookup</b>\n\nSend RC number like: <code>MH12AB1234</code>\n\n👺 DEV @Shuvobhai ✅"), "Invalid RC", False
                r = await client.get(f"{VEHICLE_RC_API_BASE}/", params={"key": VEHICLE_RC_API_KEY, "rc": rc})
                data = safe_json(r, {})
                if not data or data.get("error") or str(data.get("success", "true")).lower() == "false":
                    return bq(f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(rc)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅"), "No vehicle data", False
                merged = {}
                nested = data.get("data") or data.get("vehicle_data") or data.get("result") or {}
                if isinstance(nested, dict): merged.update(nested)
                SKIP_RC = {"data","vehicle_data","result","success","status","error","message","msg","developer","dev","key","n"}
                for k, v in data.items():
                    if k not in SKIP_RC and not isinstance(v, (dict, list)): merged.setdefault(k, v)
                FIELD_MAP = {"ownername":"Owner Name","number":"RC Number","address":"Address","makermodel":"Make/Model","modelname":"Model","fueltype":"Fuel Type","regdate":"Reg. Date","registeredrto":"RTO","class":"Vehicle Class","insurancecompany":"Insurance","insuranceupto":"Insurance Upto","fitnessupto":"Fitness Upto","taxupto":"Tax Upto","city":"City"}
                lines = [f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(rc)}</code>\n"]
                plain_lines = [f"Vehicle RC {rc}:"]
                for k, v in merged.items():
                    if v and str(v) not in ("None", "null", "N/A", ""):
                        label = FIELD_MAP.get(str(k).lower(), str(k).replace("_"," ").title())
                        lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_weather":
                city = args.get("city", "").strip()
                geo_r = await client.get(GEOCODING_API_BASE, params={"name": city, "count": 1})
                geo_data = safe_json(geo_r).get("results", [])
                if not geo_data:
                    result = bq(f"🌤 <b>Weather</b>\n\n❌ City not found: <code>{h(city)}</code>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"Weather for {city}: City not found"
                else:
                    lat = geo_data[0]["latitude"]
                    lon = geo_data[0]["longitude"]
                    w_r = await client.get(WEATHER_API_BASE, params={
                        "latitude": lat, "longitude": lon,
                        "current_weather": True, "timezone": "auto"
                    })
                    w = safe_json(w_r).get("current_weather", {})
                    temp = w.get("temperature", "N/A")
                    wind = w.get("windspeed", "N/A")
                    cname = geo_data[0].get("name", city)
                    country = geo_data[0].get("country", "")
                    result = bq(
                        f"🌤 <b>Weather</b>\n\n"
                        f"🏙 City: <b>{h(cname)}, {h(country)}</b>\n"
                        f"🌡 Temp: <b>{h(temp)}°C</b>\n"
                        f"💨 Wind: {h(wind)} km/h\n"
                        f"🧭 Direction: {h(w.get('winddirection','N/A'))}°\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"Weather in {cname}: {temp}°C, wind {wind} km/h"
                return result, plain, False

            elif tool_name == "lookup_university":
                country = args.get("country", "").strip()
                r = await client.get(UNIVERSITY_API_BASE, params={"country": country})
                data = safe_json(r, [])
                if data:
                    lines = [f"🎓 <b>Universities in {h(country)}</b>\n"]
                    plain_lines = [f"Universities in {country}:"]
                    for uni in data[:10]:
                        name = uni.get("name", "")
                        lines.append(f"• {h(name)}")
                        plain_lines.append(f"- {name}")
                    if len(data) > 10:
                        lines.append(f"\n...and {len(data)-10} more")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))
                    plain = "\n".join(plain_lines[:5])
                else:
                    result = bq(f"🎓 <b>Universities</b>\n\n❌ No results for: <code>{h(country)}</code>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"Universities in {country}: Not found"
                return result, plain, False

            elif tool_name == "lookup_country":
                country = args.get("country", "").strip()
                r = await client.get(f"{COUNTRY_API_BASE}/{country}")
                data = safe_json(r, [])
                if isinstance(data, list) and data:
                    c = data[0]
                    cap = ", ".join(c.get("capital", ["N/A"]))
                    langs = ", ".join(c.get("languages", {}).values())
                    pop = "{:,}".format(c.get("population", 0))
                    result = bq(
                        f"🌍 <b>Country Info</b>\n\n"
                        f"🏳 Name: <b>{h(c.get('name',{}).get('common','N/A'))}</b>\n"
                        f"🗺 Region: {h(c.get('region','N/A'))}\n"
                        f"🏙 Capital: {h(cap)}\n"
                        f"👥 Population: {h(pop)}\n"
                        f"🗣 Languages: {h(langs)}\n"
                        f"💰 Currency: {h(', '.join(c.get('currencies',{}).keys()))}\n"
                        f"🌐 TLD: {h(', '.join(c.get('tld',['N/A'])))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"{c.get('name',{}).get('common','?')}: Capital={cap}, Population={pop}"
                else:
                    result = bq(f"🌍 <b>Country</b>\n\n❌ Not found: <code>{h(country)}</code>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"Country {country}: Not found"
                return result, plain, False

            elif tool_name == "lookup_randomuser":
                r = await client.get(RANDOMUSER_API_BASE)
                data = safe_json(r)
                res_list = data.get("results", [{}])
                u = res_list[0] if res_list else {}
                name = u.get("name", {})
                full_name = f"{name.get('first','')} {name.get('last','')}".strip()
                loc = u.get("location", {})
                result = bq(
                    f"🎲 <b>Random User</b>\n\n"
                    f"👤 Name: <b>{h(full_name)}</b>\n"
                    f"🚻 Gender: {h(u.get('gender','N/A').title())}\n"
                    f"📧 Email: <code>{h(u.get('email','N/A'))}</code>\n"
                    f"📱 Phone: <code>{h(u.get('phone','N/A'))}</code>\n"
                    f"🏙 City: {h(loc.get('city','N/A'))}\n"
                    f"🌍 Country: {h(loc.get('country','N/A'))}\n"
                    f"🎂 Age: {h(u.get('dob',{}).get('age','N/A'))}\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                )
                plain = f"Random user: {full_name}, {u.get('email','?')}"
                return result, plain, False

            elif tool_name == "download_video":
                url = args.get("url", "").strip()
                r = await client.post(
                    "https://api.cobalt.tools/",
                    json={"url": url},
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                data = safe_json(r)
                dl_url = data.get("url") or data.get("audio")
                if dl_url:
                    result = bq(f"📥 <b>Video Download</b>\n\n🔗 <a href='{dl_url}'>Click to Download</a>\n\n👺 DEV @Shuvobhai ✅")
                    plain = f"Download link: {dl_url}"
                else:
                    result = bq(f"📥 <b>Video Download</b>\n\n❌ Could not fetch link.\n{h(str(data)[:200])}\n\n👺 DEV @Shuvobhai ✅")
                    plain = "Video download failed"
                return result, plain, False

            elif tool_name == "nasa_apod":
                r = await client.get(NASA_APOD_BASE, params={"api_key": NASA_API_KEY})
                data = safe_json(r)
                title = data.get("title", "N/A")
                explanation = data.get("explanation", "")[:400]
                url = data.get("url", "")
                result = bq(
                    f"🚀 <b>NASA — Astronomy Picture of the Day</b>\n\n"
                    f"📸 <b>{h(title)}</b>\n\n"
                    f"📝 {h(explanation)}...\n\n"
                    f"🔗 <a href='{url}'>View Image</a>\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                )
                plain = f"NASA APOD: {title}"
                return result, plain, False

            elif tool_name == "nasa_epic":
                r = await client.get(NASA_EPIC_BASE, params={"api_key": NASA_API_KEY})
                data = safe_json(r, [])
                if data:
                    ep = data[0]
                    img_name = ep.get("image", "")
                    date_str = ep.get("date", "")[:10].replace("-", "/")
                    img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{date_str}/png/{img_name}.png"
                    result = bq(
                        f"🌍 <b>NASA EPIC — Earth from Space</b>\n\n"
                        f"📅 Date: {h(ep.get('date','N/A')[:10])}\n"
                        f"🏷 Caption: {h(ep.get('caption','N/A')[:200])}\n"
                        f"🔗 <a href='{img_url}'>View Photo</a>\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                    plain = f"NASA EPIC: {ep.get('caption','Earth photo')}"
                else:
                    result = bq("🌍 <b>NASA EPIC</b>\n\n❌ No photos available right now.\n\n👺 DEV @Shuvobhai ✅")
                    plain = "NASA EPIC: No photos available"
                return result, plain, False

            elif tool_name == "generate_image":
                prompt = args.get("prompt", "").strip()
                encoded = urllib.parse.quote(prompt)
                img_url = f"{POLLINATIONS_BASE}/{encoded}?width=1024&height=1024&nologo=true&model=flux"
                r = await client.get(img_url, timeout=60)
                if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                    return img_url, f"Generated image for: {prompt}", True
                else:
                    result = bq(f"🎨 <b>AI Image</b>\n\n❌ Generation failed. Try again.\n\n👺 DEV @Shuvobhai ✅")
                    return result, "Image generation failed", False

            elif tool_name == "check_balance":
                user = users.get(uid, {})
                cred = credit_display(user)
                role = get_role(user, uid)
                last = user.get("last_claim")
                next_claim = "Now!" if not last else (
                    "Now!" if (datetime.now() - datetime.fromisoformat(last)).total_seconds() >= 86400
                    else str(timedelta(seconds=int(86400 - (datetime.now() - datetime.fromisoformat(last)).total_seconds())))
                )
                result = bq(
                    f"💰 <b>Your Balance</b>\n\n"
                    f"🎭 Role: {role}\n"
                    f"💎 Credits: <b>{cred}</b>\n"
                    f"⏰ Next claim: <b>{next_claim}</b>\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                )
                plain = f"Balance: {cred} credits, Role: {role}"
                return result, plain, False

            elif tool_name == "get_bot_help":
                result = bq(
                    "📋 <b>SHUVO BOT — Full Feature List</b>\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "🤖 <b>FREE AI TOOLS:</b>\n"
                    "• /ai — Super AI agent (always free)\n"
                    "• /image — AI image generation (free)\n"
                    "• /nasaapod — NASA pic of the day (free)\n"
                    "• /nasaepic — NASA Earth live view (free)\n"
                    "• /start — Daily +3 credits claim\n\n"
                    "🕵️ <b>OSINT (1 credit each):</b>\n"
                    "• /userid — TG User ID → phone\n"
                    "• /usernum — TG Username → phone\n"
                    "• /indinfo — Indian number info\n"
                    "• /instainfo — Instagram profile info\n"
                    "• /ipinfo — IP address lookup\n"
                    "• /emailrep — Email reputation\n"
                    "• /ffstats — Free Fire player stats\n"
                    "• /download — Video downloader\n\n"
                    "🇮🇳 <b>INDIA / PAK (1 credit each):</b>\n"
                    "• /aadhar — Aadhaar number info\n"
                    "• /makeaadhar — 🪪 Make Aadhaar Card\n"
                    "• /gst — GST lookup  • /pan — PAN lookup\n"
                    "• /pincode — Pincode  • /ifsc — Bank IFSC\n"
                    "• /vehicle  • /vehiclerc  • /upi  • /paknum\n\n"
                    "🌐 <b>INFO & DISCOVERY (1 credit each):</b>\n"
                    "• /weather  • /university  • /country  • /randomuser\n\n"
                    "🎨 <b>AI CREATION STUDIO (credits):</b>\n"
                    "• /imagegen (3cr)  • /music (5cr)\n"
                    "• /videogen (50cr)  • /sprite (3cr)\n"
                    "• /model3d (190cr)  • /editimage (10cr)\n"
                    "• /voice (1cr) — Text to speech\n\n"
                    "💰 <b>ACCOUNT:</b>\n"
                    "• /balance — Profile & credits\n"
                    "• /redeem — Redeem gift code\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "👺 DEV @Shuvobhai ✅"
                )
                plain = "Bot features listed"
                return result, plain, False

            elif tool_name == "lookup_aadhar":
                aadhar = re.sub(r'\s+', '', args.get("aadhar", "").strip())
                if not re.match(r'^\d{12}$', aadhar):
                    return bq(f"❌ <b>Aadhar Lookup</b>\n\nInvalid Aadhar number. Must be 12 digits.\n\n👺 DEV @Shuvobhai ✅"), "Invalid Aadhar", False
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "aadhar", "query": aadhar, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                results_obj = data.get("results") or {}
                records = results_obj.get("data") or [] if isinstance(results_obj, dict) else []
                if not records:
                    return bq(f"🪪 <b>Aadhar Lookup</b>\n\n📋 Aadhar: <code>{h(aadhar)}</code>\n❌ No records found.\n\n👺 DEV @Shuvobhai ✅"), "No Aadhar data", False
                lines = [f"🪪 <b>Aadhar Info</b>\n\n📋 Aadhar: <code>{h(aadhar)}</code>\n📊 Records: <b>{len(records)}</b>\n"]
                plain_lines = [f"Aadhar {aadhar}: {len(records)} record(s)"]
                for i, rec in enumerate(records[:3], 1):
                    if isinstance(rec, dict):
                        lines.append(f"\n<b>Record {i}:</b>")
                        for k, v in rec.items():
                            if v and str(v) not in ("None", "null", "N/A", ""):
                                label = str(k).replace("_", " ").title()
                                lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                                plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_gst":
                gst = args.get("gst", "").upper().strip()
                r = await client.get(f"{GST_API_BASE}/", params={"number": gst, "key": GST_API_KEY})
                data = safe_json(r, {})
                if not data or data.get("error") or str(data.get("status", "")).lower() in ("error", "fail"):
                    return bq(f"💼 <b>GST Info</b>\n\n🔎 GSTIN: <code>{h(gst)}</code>\n❌ No GST data found.\n\n👺 DEV @Shuvobhai ✅"), "No GST data", False
                if isinstance(data, list):
                    data = data[0] if data else {}
                lines = [f"💼 <b>GST Info</b>\n\n🔎 GSTIN: <code>{h(gst)}</code>\n"]
                plain_lines = [f"GST {gst}:"]
                KEY_MAP = {
                    "legalNameOfBusiness": "Legal Name", "legalName": "Legal Name",
                    "tradeName": "Trade Name", "businessName": "Business Name",
                    "registrationDate": "Reg. Date", "taxPayerType": "Taxpayer Type",
                    "gstStatus": "Status", "status": "Status",
                    "constitutionOfBusiness": "Biz Type", "constitution": "Biz Type",
                    "principalPlaceOfBusiness": "Address", "address": "Address",
                    "stateJurisdiction": "State", "state": "State",
                    "pan": "PAN", "email": "Email", "mobile": "Mobile",
                }
                SKIP = {"success", "developer", "dev", "msg", "message", "_raw", "n", "gstin", "gstNumber"}
                for k, v in data.items():
                    if k.lower() in {s.lower() for s in SKIP} or isinstance(v, (dict, list)): continue
                    if v and str(v) not in ("None", "null", "N/A", ""):
                        label = KEY_MAP.get(k, str(k).replace("_", " ").title())
                        lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_pan":
                pan = args.get("pan", "").upper().strip()
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "pan", "query": pan, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                name = data.get("fullname") or data.get("name") or ""
                if not name:
                    return bq(f"🪪 <b>PAN Info</b>\n\n📋 PAN: <code>{h(pan)}</code>\n❌ No PAN data found.\n\n👺 DEV @Shuvobhai ✅"), "No PAN data", False
                lines = [
                    f"🪪 <b>PAN Info</b>\n",
                    f"📋 PAN: <code>{h(pan)}</code>",
                    f"👤 Name: <b>{h(name)}</b>",
                ]
                plain_lines = [f"PAN {pan}: Name={name}"]
                for k, v in data.items():
                    if k in ("fullname", "name", "pan", "success", "message", "developer", "dev"): continue
                    if v and str(v) not in ("None", "null", "N/A", ""):
                        label = str(k).replace("_", " ").title()
                        lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_pakistan_number":
                number = re.sub(r'[^\d]', '', args.get("number", "").strip())
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "pak_num", "query": number, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                records = data.get("data") or []
                if not records:
                    return bq(f"🇵🇰 <b>Pakistan Number Info</b>\n\n📱 Number: <code>{h(number)}</code>\n❌ No records found.\n\n👺 DEV @Shuvobhai ✅"), "No Pakistan number data", False
                lines = [f"🇵🇰 <b>Pakistan Number Info</b>\n\n📱 Number: <code>{h(number)}</code>\n📊 Records: <b>{len(records)}</b>\n"]
                plain_lines = [f"Pakistan number {number}: {len(records)} record(s)"]
                for i, rec in enumerate(records[:3], 1):
                    if isinstance(rec, dict):
                        lines.append(f"\n<b>Record {i}:</b>")
                        for k, v in rec.items():
                            if v and str(v) not in ("None", "null", "N/A", "", "0"):
                                label = str(k).replace("_", " ").replace("-", " ").title()
                                lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                                plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_vehicle_rc":
                rc = re.sub(r'\s+', '', args.get("rc", "")).upper()
                if len(rc) < 8:
                    return bq(f"🚗 <b>Vehicle RC Lookup</b>\n\nInvalid RC number: <code>{h(rc)}</code>\n\n👺 DEV @Shuvobhai ✅"), "Invalid RC", False
                r = await client.get(f"{VEHICLE_RC_API_BASE}/", params={"key": VEHICLE_RC_API_KEY, "rc": rc})
                data = safe_json(r, {})
                if not data or data.get("error") or str(data.get("success", "true")).lower() == "false":
                    return bq(f"🚗 <b>Vehicle RC Lookup</b>\n\n🔎 RC: <code>{h(rc)}</code>\n❌ No vehicle data found.\n\n👺 DEV @Shuvobhai ✅"), "No vehicle data", False
                merged = {}
                nested = data.get("data") or data.get("vehicle_data") or data.get("result") or {}
                if isinstance(nested, dict):
                    merged.update(nested)
                SKIP_RC = {"data","vehicle_data","result","success","status","error","message","msg","developer","dev","key","n"}
                for k, v in data.items():
                    if k not in SKIP_RC and not isinstance(v, (dict, list)):
                        merged.setdefault(k, v)
                if not merged:
                    return bq(f"🚗 <b>Vehicle RC Lookup</b>\n\n❌ No data for: <code>{h(rc)}</code>\n\n👺 DEV @Shuvobhai ✅"), "No vehicle data", False
                FIELD_MAP = {
                    "ownername": "Owner Name", "number": "RC Number", "address": "Address",
                    "makermodel": "Make/Model", "modelname": "Model", "fueltype": "Fuel Type",
                    "regdate": "Reg. Date", "registeredrto": "RTO", "class": "Vehicle Class",
                    "insurancecompany": "Insurance", "insuranceupto": "Insurance Upto",
                    "fitnessupto": "Fitness Upto", "taxupto": "Tax Upto",
                    "fuelnorms": "Fuel Norms", "city": "City",
                }
                lines = [f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(rc)}</code>\n"]
                plain_lines = [f"Vehicle RC {rc}:"]
                for k, v in merged.items():
                    if v and str(v) not in ("None", "null", "N/A", ""):
                        label = FIELD_MAP.get(str(k).lower(), str(k).replace("_", " ").title())
                        lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        plain_lines.append(f"{label}: {v}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            elif tool_name == "lookup_upi":
                upi = args.get("upi", "").strip()
                if not upi or "@" not in upi:
                    return bq(f"💳 <b>UPI Info</b>\n\nInvalid UPI ID. Example: <code>name@paytm</code>\n\n👺 DEV @Shuvobhai ✅"), "Invalid UPI", False
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "upi", "query": upi, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                res = data.get("result") or {}
                primary   = res.get("primary") or {}
                secondary = res.get("secondary") or {}
                user_det  = secondary.get("user_details") or {}
                name      = primary.get("recipientBankAccountName") or user_det.get("name") or ""
                vpa       = primary.get("recipientVpa") or user_det.get("vpa") or upi
                valid     = "✅ Valid" if primary.get("validVpa") else "❌ Invalid"
                merchant  = "✅ Yes" if primary.get("isMerchant") else "❌ No"
                ifsc      = res.get("extracted_ifsc") or user_det.get("ifsc") or ""
                acc_type  = primary.get("accountType") or ""
                if not name and not vpa:
                    return bq(f"💳 <b>UPI Info</b>\n\n📋 UPI: <code>{h(upi)}</code>\n❌ No UPI data found.\n\n👺 DEV @Shuvobhai ✅"), "No UPI data", False
                lines = [
                    f"💳 <b>UPI Info</b>\n",
                    f"📋 UPI ID: <code>{h(vpa)}</code>",
                    f"👤 Name: <b>{h(name) if name else 'N/A'}</b>",
                    f"✅ Status: <b>{valid}</b>",
                    f"🏪 Merchant: <b>{merchant}</b>",
                ]
                plain_lines = [f"UPI {upi}: Name={name}, Valid={valid}, Merchant={merchant}"]
                if acc_type: lines.append(f"🏦 Account Type: <b>{h(acc_type)}</b>"); plain_lines.append(f"Account Type: {acc_type}")
                if ifsc:     lines.append(f"🏦 IFSC: <code>{h(ifsc)}</code>"); plain_lines.append(f"IFSC: {ifsc}")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                return bq("\n".join(lines)), "\n".join(plain_lines), False

            else:
                return bq(f"❓ Unknown tool: {tool_name}"), "Unknown tool", False

    except Exception as e:
        err_str = str(e)[:200]
        _error_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] AI Tool {tool_name}: {err_str}")
        result = bq(
            f"❌ <b>Tool Error</b>\n\n"
            f"🔧 Tool: {h(tool_name)}\n"
            f"💬 Error: {h(err_str)}\n\n"
            f"ℹ️ This might be a temporary API issue. Try again in a moment.\n\n"
            f"👺 DEV @Shuvobhai ✅"
        )
        return result, f"Error executing {tool_name}: {err_str}", False


# ══════════════════════════════════════════════
# POWERED AI — Groq with full tool calling
# ══════════════════════════════════════════════

async def ai_groq_powered(uid: str, user_message: str, users: dict, update: Update = None) -> dict:
    """
    Super-powered AI with tool calling.
    Returns dict: {
        'text': str (AI reply),
        'tool_result_html': str or None,
        'tool_name': str or None,
        'credit_spent': bool,
        'image_url': str or None,
    }
    """
    global _ai_history
    if not GROQ_API_KEY:
        return {"text": "❌ GROQ_API_KEY is not set. Please add GROQ_API_KEY in Secrets.", "tool_result_html": None, "tool_name": None, "credit_spent": False, "image_url": None}

    history = _ai_history.get(uid, [])
    history.append({"role": "user", "content": user_message})
    if len(history) > 20:
        history = history[-20:]

    messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}] + history

    try:
        async with httpx.AsyncClient(timeout=35) as client:
            # First call: let AI decide if it wants to use a tool
            r = await client.post(
                GROQ_API_BASE,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "tools": GROQ_TOOLS,
                    "tool_choice": "auto",
                    "max_tokens": 180
                }
            )
            data = safe_json(r)
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            tool_calls = msg.get("tool_calls")

            # No tool call → plain AI response
            if not tool_calls:
                reply = msg.get("content", "")
                if not reply:
                    err = data.get("error", {}).get("message", "Unknown error")
                    return {"text": f"❌ AI error: {err}", "tool_result_html": None, "tool_name": None, "credit_spent": False, "image_url": None}
                history.append({"role": "assistant", "content": reply})
                _ai_history[uid] = history[-20:]
                return {"text": reply, "tool_result_html": None, "tool_name": None, "credit_spent": False, "image_url": None}

            # Tool call detected!
            tc = tool_calls[0]
            tool_name = tc.get("function", {}).get("name", "")
            tool_args_raw = tc.get("function", {}).get("arguments", "{}")
            try:
                tool_args = json.loads(tool_args_raw)
            except Exception:
                tool_args = {}
            tool_call_id = tc.get("id", "call_0")

            # Credit check for paid tools
            credit_spent = False
            if tool_name not in FREE_AI_TOOLS:
                if not has_credits(users, uid):
                    history.append({"role": "assistant", "content": "❌ Insufficient credits to execute this lookup."})
                    _ai_history[uid] = history[-20:]
                    return {
                        "text": "❌ <b>Insufficient credits!</b>\n\nAI er through lookup korte 1 credit laage. /start koro daily credit claim korte.",
                        "tool_result_html": None, "tool_name": tool_name, "credit_spent": False, "image_url": None
                    }
                spend_credit(users, uid)
                credit_spent = True

            # Execute the tool
            tool_html, tool_plain, is_image = await execute_ai_tool(tool_name, tool_args, uid, users)

            # Send tool result back to AI for a final summary
            messages_with_tool = messages + [
                {"role": "assistant", "content": None, "tool_calls": tool_calls},
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_plain
                }
            ]
            r2 = await client.post(
                GROQ_API_BASE,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": GROQ_MODEL,
                    "messages": messages_with_tool,
                    "max_tokens": 100
                }
            )
            data2 = safe_json(r2)
            final_reply = data2.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not final_reply:
                final_reply = "✅ Done! Result is shown above."

            # Update history
            history.append({"role": "assistant", "content": f"[Used tool: {tool_name}] {final_reply}"})
            _ai_history[uid] = history[-20:]

            return {
                "text": final_reply,
                "tool_result_html": tool_html,
                "tool_name": tool_name,
                "credit_spent": credit_spent,
                "image_url": tool_args.get("prompt") if is_image else None,
                "is_image_tool": is_image,
                "image_prompt": tool_args.get("prompt", "") if is_image else "",
            }

    except Exception as e:
        return {"text": f"❌ AI error: {str(e)[:200]}", "tool_result_html": None, "tool_name": None, "credit_spent": False, "image_url": None}


async def ai_groq(uid: str, user_message: str) -> str:
    """Simple AI call without tool calling (used for admin diagnose, group AI etc.)"""
    global _ai_history
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY is not set."
    history = _ai_history.get(uid, [])
    history.append({"role": "user", "content": user_message})
    if len(history) > 16:
        history = history[-16:]
    messages = [{"role": "system", "content": AI_SYSTEM_PROMPT}] + history
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                GROQ_API_BASE,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 180}
            )
            data = safe_json(r)
            reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not reply:
                err = data.get("error", {}).get("message", "Unknown error")
                return f"❌ No AI response. Error: {err}"
            history.append({"role": "assistant", "content": reply})
            _ai_history[uid] = history[-16:]
            return reply
    except Exception as e:
        return f"❌ AI error: {str(e)[:200]}"


async def _send_ai_powered_response(update: Update, uid: str, users: dict, user_message: str):
    """Send the full AI powered response including tool results to the user."""
    sent = await update.message.reply_text("⚡ <i>AI is working...</i>", parse_mode="HTML")

    result = await ai_groq_powered(uid, user_message, users, update)

    try:
        # If there's a tool result, show it first
        if result.get("tool_result_html"):
            tool_name = result.get("tool_name", "")
            credit_note = " <i>(1cr)</i>" if result.get("credit_spent") else " <i>(free)</i>"

            # Check if it's an image generation tool
            if result.get("is_image_tool"):
                prompt = result.get("image_prompt", "")
                img_url = f"{POLLINATIONS_BASE}/{urllib.parse.quote(prompt)}?width=1024&height=1024&nologo=true&model=flux"
                try:
                    async with httpx.AsyncClient(timeout=60) as client:
                        img_r = await client.get(img_url)
                    if img_r.status_code == 200 and img_r.headers.get("content-type", "").startswith("image"):
                        await sent.delete()
                        photo_sent = await update.message.reply_photo(
                            photo=img_r.content,
                            caption=f"🎨 <b>AI Image</b>\n<i>{h(prompt[:200])}</i>\n\n👺 @Shuvobhai",
                            parse_mode="HTML"
                        )
                        schedule_delete(photo_sent)
                        if result.get("text"):
                            ai_sent = await update.message.reply_text(
                                f"🤖 <b>SHUVO AI</b>{credit_note}\n\n{fmt_ai(result['text'])}",
                                parse_mode="HTML"
                            )
                            schedule_delete(ai_sent)
                        return
                except Exception:
                    pass

            # Show tool result
            await sent.edit_text(result["tool_result_html"], parse_mode="HTML")
            schedule_delete(sent)

            # Show AI commentary (short, styled, no blockquote)
            if result.get("text"):
                ai_sent = await update.message.reply_text(
                    f"🤖 <b>SHUVO AI</b>{credit_note}\n\n{fmt_ai(result['text'])}",
                    parse_mode="HTML"
                )
                schedule_delete(ai_sent)
        else:
            # Pure text AI response — no blockquote, just styled text
            await sent.edit_text(
                f"🤖 <b>SHUVO AI</b>\n\n{fmt_ai(result['text'])}",
                parse_mode="HTML"
            )
            schedule_delete(sent)
    except Exception as e:
        try:
            await sent.edit_text(
                f"🤖 <b>SHUVO AI</b>\n\n{fmt_ai(result.get('text', 'Error occurred.'))}",
                parse_mode="HTML"
            )
            schedule_delete(sent)
        except Exception:
            pass


def build_menu_page(page: int, is_admin: bool) -> InlineKeyboardMarkup:
    pages = [
        # ── Page 0 · Quick Access ──
        [
            [InlineKeyboardButton("🎁✨  Daily Claim  ✨🎁",   callback_data="daily_claim")],
            [InlineKeyboardButton("🤖💬  AI Chat",             callback_data="service_ai"),
             InlineKeyboardButton("🎨🖼️  Image Gen",          callback_data="service_imagegen")],
            [InlineKeyboardButton("📞🔎  TG ID → Num",         callback_data="service_tgid"),
             InlineKeyboardButton("🔍👤  User → Num",          callback_data="service_tguser")],
            [InlineKeyboardButton("🪪✨  Make Aadhaar Card",   callback_data="service_makeaadhar")],
        ],
        # ── Page 1 · OSINT Tools ──
        [
            [InlineKeyboardButton("☎️🇮🇳  IND Num",           callback_data="service_indinfo"),
             InlineKeyboardButton("🎯🔥  FF Stats",            callback_data="service_ffstats")],
            [InlineKeyboardButton("📸💜  Instagram",           callback_data="service_instainfo"),
             InlineKeyboardButton("🎬⬇️  Vid Download",        callback_data="service_viddown")],
            [InlineKeyboardButton("📮🗺️  Pincode",            callback_data="service_pincode"),
             InlineKeyboardButton("🏦💰  IFSC",                callback_data="service_ifsc")],
            [InlineKeyboardButton("🌐🖥️  IP Info",            callback_data="service_ipinfo"),
             InlineKeyboardButton("📧⚡  Email Rep",           callback_data="service_emailrep")],
        ],
        # ── Page 2 · Info & Discovery ──
        [
            [InlineKeyboardButton("🚀🌟  NASA APOD",           callback_data="service_nasa_apod"),
             InlineKeyboardButton("🌍🛸  NASA EPIC",           callback_data="service_nasa_epic")],
            [InlineKeyboardButton("🚗💨  Vehicle",             callback_data="service_vehicle"),
             InlineKeyboardButton("⛅🌤️  Weather",            callback_data="service_weather")],
            [InlineKeyboardButton("🎓📚  University",          callback_data="service_university"),
             InlineKeyboardButton("👤🎲  Rand User",           callback_data="service_randomuser")],
            [InlineKeyboardButton("🌏🗺️  Country",            callback_data="service_country"),
             InlineKeyboardButton("🗄️💾  Databases",          callback_data="service_databases")],
        ],
        # ── Page 3 · India / Pak ──
        [
            [InlineKeyboardButton("🪪🇮🇳  Aadhar",            callback_data="service_aadhar"),
             InlineKeyboardButton("💼📊  GST",                 callback_data="service_gst")],
            [InlineKeyboardButton("📋🪪  PAN",                 callback_data="service_pan"),
             InlineKeyboardButton("📱🇵🇰  Pak Num",           callback_data="service_paknum")],
            [InlineKeyboardButton("🚘📝  Vehicle RC",          callback_data="service_vehicle_rc"),
             InlineKeyboardButton("💳💸  UPI",                 callback_data="service_upi")],
            [InlineKeyboardButton("🪪✨  Make Aadhar Card",    callback_data="service_makeaadhar")],
        ],
        # ── Page 4 · AI Media Studio ──
        [
            [InlineKeyboardButton("🎵🎧  Music Gen",           callback_data="service_musicgen"),
             InlineKeyboardButton("🎞️🎬  Video Gen",          callback_data="service_videogen")],
            [InlineKeyboardButton("👾🕹️  Sprite Gen",         callback_data="service_sprite"),
             InlineKeyboardButton("🧊✨  3D Model",            callback_data="service_model3d")],
            [InlineKeyboardButton("🖌️🎨  Edit Image",         callback_data="service_editimage"),
             InlineKeyboardButton("🎙️🔊  Voice TTS",          callback_data="service_voice")],
        ],
    ]
    page_titles = ["⚡ Quick Access", "🕵️ OSINT Tools", "🌐 Info & Discovery", "🇮🇳 India / Pak Lookup", "🎬 AI Media Studio"]
    total = len(pages)
    rows = pages[page][:]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️  Back", callback_data=f"menu_page_{page-1}"))
    nav.append(InlineKeyboardButton(f"• {page+1}/{total} •", callback_data=f"menu_page_{page}"))
    if page < total - 1:
        nav.append(InlineKeyboardButton("Next  ➡️", callback_data=f"menu_page_{page+1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("💰  Balance",  callback_data="check_balance"),
                 InlineKeyboardButton("❓  Help",     callback_data="service_help")])
    return InlineKeyboardMarkup(rows)

def main_menu_text(user, uid=""):
    uname = f"@{user.get('username')}" if user.get("username") else "—"
    role  = get_role(user, uid)
    cred  = credit_display(user)
    try:
        total_users = len(load_users())
    except Exception:
        total_users = "?"
    return (
        f"╔══════════════════════════╗\n"
        f"      ⚡ <b>SHUVO BOT</b> ⚡\n"
        f"   <i>AI • OSINT • Media • Tools</i>\n"
        f"╚══════════════════════════╝\n\n"
        f"<blockquote>"
        f"🆔 <b>ID</b>       ›  <code>{h(uid)}</code>\n"
        f"👤 <b>User</b>     ›  {h(uname)}\n"
        f"🎭 <b>Role</b>     ›  {role}\n"
        f"💰 <b>Credits</b>  ›  <b>{cred}</b>\n"
        f"👥 <b>Members</b>  ›  <b>{total_users}</b>"
        f"</blockquote>\n\n"
        f"🗂 <b>5 Pages</b> of features — swipe ➡️ to explore\n"
        f"💡 <i>Tip: /ai does everything automatically!</i>\n"
        f"<i>━━━━━━━━ 👺 DEV @Shuvobhai ━━━━━━━━</i>"
    )

def after_result_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 TG ID",     callback_data="service_tgid"),
         InlineKeyboardButton("👤 Username",  callback_data="service_tguser")],
        [InlineKeyboardButton("📮 Pincode",   callback_data="service_pincode"),
         InlineKeyboardButton("🏦 IFSC",      callback_data="service_ifsc")],
        [InlineKeyboardButton("🌐 IP Info",   callback_data="service_ipinfo"),
         InlineKeyboardButton("📊 FF Stats",  callback_data="service_ffstats")],
        [InlineKeyboardButton("🚀 NASA APOD", callback_data="service_nasa_apod"),
         InlineKeyboardButton("🌍 NASA EPIC", callback_data="service_nasa_epic")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="back_home")],
    ])


async def _send_menu_photo(target, user, uid, extra="", reply_markup=None):
    markup = reply_markup or build_menu_page(0, user["is_admin"])
    caption = main_menu_text(user, uid) + extra
    try:
        with open(BANNER_FILE, "rb") as f:
            if hasattr(target, "reply_photo"):
                return await target.reply_photo(photo=f, caption=caption, reply_markup=markup, parse_mode="HTML")
            else:
                return await target.message.reply_photo(photo=f, caption=caption, reply_markup=markup, parse_mode="HTML")
    except Exception:
        if hasattr(target, "reply_text"):
            return await target.reply_text(caption, reply_markup=markup, parse_mode="HTML")
        else:
            return await target.message.reply_text(caption, reply_markup=markup, parse_mode="HTML")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    tg_user = update.effective_user
    is_new_user = str(tg_user.id) not in users
    user, uid = get_user(
        users, tg_user.id,
        username=tg_user.username or "",
        first_name=tg_user.first_name or ""
    )
    if user["banned"]:
        sent = await update.message.reply_text(bq("⛔ You are banned from using this bot."), parse_mode="HTML")
        schedule_delete(sent); return

    if not user.get("is_admin") and str(tg_user.id) != str(ADMIN_ID):
        unjoined = await check_force_join(context.bot, tg_user.id)
        if unjoined:
            names = "\n".join(f"  🔹 <b>{h(ch['title'])}</b>" for ch in unjoined)
            sent = await update.message.reply_text(
                bq(
                    f"📢 <b>Join Required!</b>\n\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"To use <b>SHUVO BOT</b> you must join:\n\n"
                    f"{names}\n\n"
                    f"After joining all channels/groups,\n"
                    f"tap <b>✅ Verify</b> below to unlock the bot."
                ),
                reply_markup=force_join_keyboard(unjoined),
                parse_mode="HTML"
            )
            schedule_delete(sent)
            return

    now = datetime.now()
    last = user.get("last_claim")
    claimed = False
    extra_note = ""

    if is_new_user:
        user["last_claim"] = now.isoformat()
        save_users(users)
        name = tg_user.first_name or "User"
        extra_note = (
            f"\n\n<blockquote>"
            f"🎊 <b>Welcome, {h(name)}!</b>\n"
            f"🎁 <b>+3 Welcome Credits</b> added!\n"
            f"📅 Claim <b>+3</b> more every 24h via /start\n"
            f"💡 <b>Tip:</b> /ai handles everything!"
            f"</blockquote>"
        )
        write_log(f"NEW USER: {uid} (@{tg_user.username or 'N/A'} | {tg_user.first_name or ''}) joined")
    elif last:
        last_dt = datetime.fromisoformat(last)
        if (now - last_dt).total_seconds() >= 86400:
            user["credits"] += 3
            user["last_claim"] = now.isoformat()
            claimed = True
            save_users(users)
    else:
        user["last_claim"] = now.isoformat()
        save_users(users)

    if claimed:
        extra_note = (
            f"\n\n<blockquote>"
            f"✅ <b>Daily Claim!</b>  🎁 <b>+3 Credits</b> added!\n"
            f"⏰ Come back in <b>24 hours</b> for more"
            f"</blockquote>"
        )

    context.user_data["pending"] = PENDING_NONE
    sent = await _send_menu_photo(update.message, user, uid, extra=extra_note)
    schedule_delete(sent)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = bq(
        "╔══════════════════════════╗\n"
        "   📋 <b>SHUVO BOT — ALL COMMANDS</b>\n"
        "╚══════════════════════════╝\n\n"

        "🤖 <b>AI TOOLS</b>  <i>(Always FREE)</i>\n"
        "┣ /ai — Super AI agent · does everything\n"
        "┣ /image — AI image generator (FREE)\n"
        "┣ /nasaapod — NASA pic of the day (FREE)\n"
        "┗ /nasaepic — NASA Earth live view (FREE)\n\n"

        "🎨 <b>AI CREATION STUDIO</b>  <i>(Credits)</i>\n"
        "┣ /imagegen — HD AI image  <code>3cr</code>\n"
        "┣ /music — AI music generator  <code>5cr</code>\n"
        "┣ /videogen — AI video  <code>50cr</code>\n"
        "┣ /sprite — Game sprite gen  <code>3cr</code>\n"
        "┣ /model3d — 3D model gen  <code>190cr</code>\n"
        "┣ /editimage — Edit photo w/ AI  <code>10cr</code>\n"
        "┗ /voice — Text to speech  <code>1cr</code>\n\n"

        "🕵️ <b>OSINT TOOLS</b>  <i>(1cr each)</i>\n"
        "┣ /userid — TG User ID → Phone number\n"
        "┣ /usernum — TG Username → Phone number\n"
        "┣ /indinfo — Indian phone number info\n"
        "┣ /instainfo — Instagram profile info\n"
        "┣ /ipinfo — IP address lookup\n"
        "┣ /emailrep — Email reputation check\n"
        "┣ /ffstats — Free Fire player stats\n"
        "┗ /download — Video downloader\n\n"

        "🇮🇳 <b>INDIA / PAK LOOKUP</b>  <i>(1cr each)</i>\n"
        "┣ /aadhar — Aadhaar number info\n"
        "┣ /makeaadhar — 🪪 Make Aadhaar Card\n"
        "┣ /gst — GST number info\n"
        "┣ /pan — PAN card lookup\n"
        "┣ /pincode — Pincode area info\n"
        "┣ /ifsc — Bank IFSC lookup\n"
        "┣ /vehicle — Vehicle info\n"
        "┣ /vehiclerc — Vehicle RC lookup\n"
        "┣ /upi — UPI ID info\n"
        "┗ /paknum — Pakistan number info\n\n"

        "🌐 <b>INFO & DISCOVERY</b>  <i>(1cr each)</i>\n"
        "┣ /weather — Weather by city\n"
        "┣ /university — University search\n"
        "┣ /country — Country info\n"
        "┗ /randomuser — Random person gen\n\n"

        "💰 <b>ACCOUNT</b>\n"
        "┣ /start — Daily claim (+3 credits)\n"
        "┣ /balance — Profile &amp; credits\n"
        "┗ /redeem — Redeem gift code\n\n"

        "🛠 <b>ADMIN ONLY</b>\n"
        "┣ /admin — Admin panel\n"
        "┣ /gen — Add credits to user\n"
        "┣ /ban  /unban — Ban/unban user\n"
        "┣ /broadcast — Broadcast message\n"
        "┗ /gencode — Create redeem code\n\n"

        "👥 <b>GROUP TOOLS</b>\n"
        "┣ /clearmsg on/off — Auto-delete msgs\n"
        "┗ /blacklist  /unblacklist\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>Tip:</b> /ai handles everything automatically!\n"
        "<i>Example: \"check IP 8.8.8.8\" • \"FF stats 1234\" • \"make aadhaar card\"</i>\n\n"
        "👺 DEV @Shuvobhai ✅"
    )
    sent = await update.message.reply_text(text, parse_mode="HTML")
    schedule_delete(sent)


async def bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    uname = f"@{user.get('username')}" if user.get("username") else f"<code>{h(uid)}</code>"
    last = user.get("last_claim")
    next_claim = "Now!" if not last else (
        "Now!" if (datetime.now() - datetime.fromisoformat(last)).total_seconds() >= 86400
        else str(timedelta(seconds=int(86400 - (datetime.now() - datetime.fromisoformat(last)).total_seconds())))
    )
    role = get_role(user, uid)
    cred = credit_display(user)
    sent = await update.message.reply_text(
        bq(
            f"👤 <b>Your Profile</b>\n\n"
            f"🆔 ID: <code>{h(uid)}</code>\n"
            f"👤 Username: {uname}\n"
            f"🎭 Role: {role}\n"
            f"💰 Credits: <b>{cred}</b>\n"
            f"⏰ Next claim: <b>{next_claim}</b>\n\n"
            f"👺 DEV @Shuvobhai ✅"
        ),
        parse_mode="HTML"
    )
    schedule_delete(sent)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Also clear any pending dm reply
    _pending_dm_reply.pop(str(update.effective_user.id), None)
    context.user_data["pending"] = PENDING_NONE
    sent = await update.message.reply_text(bq("✅ Cancelled."), parse_mode="HTML")
    schedule_delete(sent)


async def cmd_loghere(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        sent = await update.message.reply_text(
            bq("❌ Run this command <b>inside the group</b> you want as the log group."),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return
    cfg = load_config()
    cfg["log_group_id"] = str(chat.id)
    save_config(cfg)
    try:
        await update.message.delete()
    except Exception:
        pass
    sent = await update.message.reply_text(
        bq(
            f"✅ <b>Log Group Set!</b>\n\n"
            f"📨 This group is now the <b>User Logs</b> destination.\n"
            f"Group ID: <code>{chat.id}</code>\n\n"
            f"All user DM activity and bot interactions\n"
            f"will be logged here with a 💬 DM button."
        ),
        parse_mode="HTML"
    )
    schedule_delete(sent)
    write_log(f"LOG_GROUP set to {chat.id} ({chat.title})")


async def cmd_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "tgid"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_USERID
    sent = await update.message.reply_text(bq("🔎 <b>TG ID → Phone</b>\n\nSend Telegram user ID:\nExample: <code>123456789</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_usernum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "tguser"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_USERNUM
    sent = await update.message.reply_text(bq("👤 <b>Username → Phone</b>\n\nSend Telegram username:\nExample: <code>username</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_indinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "indinfo"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_INDINFO
    sent = await update.message.reply_text(bq("📱 <b>Indian Number Info</b>\n\nSend Indian phone number:\nExample: <code>9876543210</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_instainfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "instainfo"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_INSTAINFO
    sent = await update.message.reply_text(bq("📸 <b>Instagram Info</b>\n\nSend Instagram username:\nExample: <code>cristiano</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "viddown"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_DOWNLOAD
    sent = await update.message.reply_text(bq("📥 <b>Video Download</b>\n\nSend YouTube/TikTok/Instagram URL:\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_pincode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "pincode"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_PINCODE
    sent = await update.message.reply_text(bq("📮 <b>Pincode Lookup</b>\n\nSend 6-digit Indian pincode:\nExample: <code>110001</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_ifsc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "ifsc"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_IFSC
    sent = await update.message.reply_text(bq("🏦 <b>IFSC Lookup</b>\n\nSend bank IFSC code:\nExample: <code>SBIN0001234</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_ipinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "ipinfo"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_IPINFO
    sent = await update.message.reply_text(bq("🌐 <b>IP Info</b>\n\nSend IP address:\nExample: <code>8.8.8.8</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_ffstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "ffstats"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_FFSTATS
    sent = await update.message.reply_text(bq("📊 <b>FF Stats</b>\n\nSend FF UID:\nExample: <code>11959685790</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_emailrep(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "emailrep"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_EMAILREP
    sent = await update.message.reply_text(bq("📧 <b>Email Reputation</b>\n\nSend email address:\nExample: <code>user@example.com</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_vehicle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "vehicle"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_VEHICLE
    sent = await update.message.reply_text(bq("🚗 <b>Vehicle RC Info</b>\n\nSend RC number:\nExample: <code>MH12AB1234</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "weather"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_WEATHER
    sent = await update.message.reply_text(bq("🌤 <b>Weather Info</b>\n\nSend city name:\nExample: <code>Dhaka</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_university(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "university"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_UNIVERSITY
    sent = await update.message.reply_text(bq("🎓 <b>University Search</b>\n\nSend country name:\nExample: <code>Bangladesh</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "country"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_COUNTRY
    sent = await update.message.reply_text(bq("🌍 <b>Country Info</b>\n\nSend country name:\nExample: <code>Bangladesh</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_aadhar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "aadhar"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_AADHAR
    sent = await update.message.reply_text(bq("🪪 <b>Aadhar Info Lookup</b>\n\nSend 12-digit Aadhar number:\nExample: <code>123456789012</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_gst(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "gst"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_GST
    sent = await update.message.reply_text(bq("💼 <b>GST Info Lookup</b>\n\nSend GSTIN number:\nExample: <code>10DJCPK4351Q1Z5</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_pan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "pan"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_PAN
    sent = await update.message.reply_text(bq("🪪 <b>PAN Card Info Lookup</b>\n\nSend PAN number:\nExample: <code>AAMTS3432L</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_paknum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "paknum"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_PAKNUM
    sent = await update.message.reply_text(bq("🇵🇰 <b>Pakistan Number Lookup</b>\n\nSend Pakistan mobile number:\nExample: <code>03001234567</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_vehicle_rc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "vehicle_rc"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_VEHICLE_RC
    sent = await update.message.reply_text(bq("🚗 <b>Vehicle RC Lookup</b>\n\nSend vehicle RC (registration) number:\nExample: <code>MH12AB1234</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)

async def cmd_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "upi"): return
    if await _check_credits(update, user): return
    context.user_data["pending"] = PENDING_UPI
    sent = await update.message.reply_text(bq("💳 <b>UPI Info Lookup</b>\n\nSend UPI ID:\nExample: <code>name@paytm</code>\n\n/cancel to go back."), parse_mode="HTML")
    schedule_delete(sent)


# ──────────────────────────────────────────────────────────────
#  FAKE AADHAR CARD GENERATOR
# ──────────────────────────────────────────────────────────────

_FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_NORMAL = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_FONT_SERIF  = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

def _aadhar_font(size: int, bold: bool = False, serif: bool = False) -> ImageFont.ImageFont:
    path = _FONT_SERIF if serif else (_FONT_BOLD if bold else _FONT_NORMAL)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        try:
            return ImageFont.load_default(size=size)
        except Exception:
            return ImageFont.load_default()


def _draw_qr_pattern(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int) -> None:
    """Draw a fake QR-code-like grid pattern."""
    size = x2 - x1
    sq   = max(6, size // 18)
    import random as _rnd
    _rnd.seed(42)
    for r in range(y1 + 2, y2 - 2, sq):
        for c in range(x1 + 2, x2 - 2, sq):
            if _rnd.random() > 0.45:
                draw.rectangle([c, r, c + sq - 2, r + sq - 2], fill=(0, 0, 0))
    # Corner finder patterns (3 corners)
    for cx, cy in [(x1 + 2, y1 + 2), (x2 - 26, y1 + 2), (x1 + 2, y2 - 26)]:
        draw.rectangle([cx, cy, cx + 22, cy + 22], fill=(0, 0, 0))
        draw.rectangle([cx + 3, cy + 3, cx + 19, cy + 19], fill=(255, 255, 255))
        draw.rectangle([cx + 6, cy + 6, cx + 16, cy + 16], fill=(0, 0, 0))


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words, line, lines = text.split(), "", []
    for w in words:
        test = (line + " " + w).strip()
        if len(test) <= max_chars:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines or [""]


def _draw_aadhar_card(name: str, dob: str, number: str, address: str, photo_bytes: bytes, gender: str = "Male") -> BytesIO:
    import math as _math
    import random as _rnd

    # ── Canvas — credit-card ratio at 300dpi ─────────────────────
    W, H = 1016, 638

    # Official UIDAI colors
    NAVY      = (0,  63, 136)        # #003F88 — UIDAI header blue
    NAVY_LT   = (0,  82, 165)        # lighter navy for accents
    SAFFRON   = (255, 103, 0)        # #FF6700 — tricolor saffron
    GREEN_IND = (19, 136, 8)         # #138808 — tricolor green
    WHITE     = (255, 255, 255)
    CREAM     = (252, 252, 248)      # card body
    LIGHT_BLU = (235, 242, 254)      # number bar bg
    TEXT_DK   = (20,  20,  40)       # primary text
    TEXT_MD   = (70,  90, 130)       # label text
    TEXT_LT   = (120, 140, 170)      # secondary text
    NUM_BLU   = (10,  40, 120)       # aadhaar number
    GOLD      = (200, 158,  10)      # gold accent
    ORANGE_BR = (236,  93,  41)      # Aadhaar brand orange
    HEADER_H  = 100
    STRIP_W   = 14                   # tricolor strip width

    img  = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # ── Outer card border (thin shadow effect) ────────────────────
    draw.rectangle([0, 0, W - 1, H - 1], outline=(180, 190, 210), width=2)

    # ── Tricolor left strip (vertical) ───────────────────────────
    draw.rectangle([0, 0,          STRIP_W, H // 3],       fill=SAFFRON)
    draw.rectangle([0, H // 3,     STRIP_W, 2 * H // 3],   fill=WHITE)
    draw.rectangle([0, 2 * H // 3, STRIP_W, H],            fill=GREEN_IND)
    # thin separator lines between strips
    draw.line([(0, H // 3), (STRIP_W, H // 3)],       fill=(220,220,220), width=1)
    draw.line([(0, 2*H//3), (STRIP_W, 2*H//3)],       fill=(220,220,220), width=1)

    # ── Header background ─────────────────────────────────────────
    draw.rectangle([STRIP_W, 0, W, HEADER_H], fill=NAVY)

    # Subtle grid texture on header
    for gx in range(STRIP_W, W, 18):
        draw.line([(gx, 0), (gx, HEADER_H)], fill=(255,255,255,8), width=1)

    # Gold + saffron divider under header
    draw.rectangle([STRIP_W, HEADER_H,     W, HEADER_H + 5], fill=GOLD)
    draw.rectangle([STRIP_W, HEADER_H + 5, W, HEADER_H + 8], fill=SAFFRON)

    # ── Ashoka Chakra Emblem ──────────────────────────────────────
    ex, ey = STRIP_W + 54, HEADER_H // 2
    er_outer, er_mid, er_inner = 38, 25, 9

    # Outer decorative ring (double)
    draw.ellipse([ex-er_outer, ey-er_outer, ex+er_outer, ey+er_outer],
                 outline=(255, 215, 80), width=3)
    draw.ellipse([ex-er_outer+4, ey-er_outer+4, ex+er_outer-4, ey+er_outer-4],
                 outline=(255, 215, 80), width=1)
    # Middle wheel (chakra)
    draw.ellipse([ex-er_mid, ey-er_mid, ex+er_mid, ey+er_mid],
                 outline=(255, 215, 80), width=2)
    # Centre hub
    draw.ellipse([ex-er_inner, ey-er_inner, ex+er_inner, ey+er_inner],
                 fill=(255, 215, 80))
    draw.ellipse([ex-er_inner+3, ey-er_inner+3, ex+er_inner-3, ey+er_inner-3],
                 fill=NAVY)

    # 24 Ashoka chakra spokes
    for deg in range(0, 360, 15):
        ang = _math.radians(deg)
        x_inner = int(ex + (er_inner + 1) * _math.cos(ang))
        y_inner = int(ey + (er_inner + 1) * _math.sin(ang))
        x_outer = int(ex + (er_mid - 2) * _math.cos(ang))
        y_outer = int(ey + (er_mid - 2) * _math.sin(ang))
        draw.line([(x_inner, y_inner), (x_outer, y_outer)],
                  fill=(255, 215, 80), width=2)
    # Outer decorative ticks
    for deg in range(0, 360, 15):
        ang = _math.radians(deg)
        x_a = int(ex + (er_mid + 3) * _math.cos(ang))
        y_a = int(ey + (er_mid + 3) * _math.sin(ang))
        x_b = int(ex + (er_outer - 6) * _math.cos(ang))
        y_b = int(ey + (er_outer - 6) * _math.sin(ang))
        draw.line([(x_a, y_a), (x_b, y_b)], fill=(255, 215, 80), width=1)

    # Lions base silhouette (trapezoid below emblem)
    base_x1, base_y  = ex - 22, ey + er_outer
    base_x2, base_y2 = ex + 22, ey + er_outer + 12
    draw.polygon([(base_x1, base_y), (base_x2, base_y),
                  (base_x2 + 6, base_y2), (base_x1 - 6, base_y2)],
                 fill=(255, 215, 80))
    draw.rectangle([base_x1 - 6, base_y2, base_x2 + 6, base_y2 + 4], fill=(255, 215, 80))

    # "Satyameva Jayate" under emblem
    draw.text((ex - 28, base_y2 + 5), "Satyameva Jayate",
              font=_aadhar_font(7, serif=True), fill=(255, 215, 80))

    # ── Header text (centre) ──────────────────────────────────────
    htext_x = STRIP_W + 116
    draw.text((htext_x,  7), "Government of India",
              font=_aadhar_font(16, bold=True), fill=(255, 215, 80))
    draw.text((htext_x, 27), "UNIQUE IDENTIFICATION AUTHORITY OF INDIA",
              font=_aadhar_font(11, bold=True), fill=WHITE)
    draw.text((htext_x, 44), "Issued under The Aadhaar (Targeted Delivery) Act, 2016",
              font=_aadhar_font(9), fill=(170, 200, 245))
    draw.text((htext_x, 57), "uidai.gov.in  |  resident.uidai.gov.in  |  Helpline: 1947  |  help@uidai.gov.in",
              font=_aadhar_font(8), fill=(130, 170, 220))
    # Devanagari line
    draw.text((htext_x, 72), "mAadhaar  |  Digitally Verified  |  Resident Copy",
              font=_aadhar_font(9, bold=True), fill=(200, 225, 255))

    # ── AADHAAR brand (right of header) ──────────────────────────
    bx = W - 195
    draw.text((bx,  4), "आधार",    font=_aadhar_font(38, bold=True), fill=ORANGE_BR)
    draw.text((bx, 48), "AADHAAR", font=_aadhar_font(20, bold=True), fill=WHITE)
    draw.text((bx, 73), "Resident Copy",
              font=_aadhar_font(10), fill=(160, 200, 255))
    # small orange bar under AADHAAR text
    draw.rectangle([bx, 69, bx + 145, 72], fill=ORANGE_BR)

    # ── Card body ─────────────────────────────────────────────────
    draw.rectangle([STRIP_W, HEADER_H + 8, W, H], fill=CREAM)

    # ── UIDAI diagonal watermark ──────────────────────────────────
    try:
        wm_img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        wm_draw = ImageDraw.Draw(wm_img)
        wm_font = _aadhar_font(48, bold=True)
        for wx in range(80, W, 280):
            for wy in range(HEADER_H + 50, H - 50, 170):
                wm_draw.text((wx, wy), "UIDAI", font=wm_font,
                             fill=(0, 63, 136, 14))
        img  = Image.alpha_composite(img.convert("RGBA"), wm_img).convert("RGB")
        draw = ImageDraw.Draw(img)
    except Exception:
        pass

    # ── Photo box ────────────────────────────────────────────────
    PX  = STRIP_W + 18
    PY  = HEADER_H + 18
    PW  = 170
    PH_ = 210
    # Shadow effect
    draw.rectangle([PX + 4, PY + 4, PX + PW + 4, PY + PH_ + 4],
                   fill=(200, 210, 230))
    # Navy border (outer)
    draw.rectangle([PX - 3, PY - 3, PX + PW + 3, PY + PH_ + 3], fill=NAVY)
    # Gold inner border
    draw.rectangle([PX - 1, PY - 1, PX + PW + 1, PY + PH_ + 1],
                   outline=GOLD, width=1)
    try:
        pil_photo = Image.open(BytesIO(photo_bytes)).convert("RGB")
        pw2, ph2  = pil_photo.size
        side = min(pw2, ph2)
        pil_photo = pil_photo.crop(((pw2-side)//2, (ph2-side)//2,
                                    (pw2+side)//2, (ph2+side)//2))
        pil_photo = pil_photo.resize((PW, PH_), Image.LANCZOS)
        img.paste(pil_photo, (PX, PY))
        draw = ImageDraw.Draw(img)
    except Exception:
        draw.rectangle([PX, PY, PX + PW, PY + PH_], fill=(165, 190, 220))
        draw.text((PX + 38, PY + 85), "PHOTO", font=_aadhar_font(22, bold=True), fill=WHITE)
        draw.text((PX + 28, PY + 112), "AFFIX HERE", font=_aadhar_font(11), fill=(200, 215, 235))

    # "MY AADHAAR" strip below photo
    strip_y  = PY + PH_ + 3
    draw.rectangle([PX - 3, strip_y, PX + PW + 3, strip_y + 22], fill=NAVY)
    draw.text((PX + 10, strip_y + 4), "MY AADHAAR",
              font=_aadhar_font(12, bold=True), fill=(255, 215, 80))

    # Fingerprint icon area below MY AADHAAR strip
    fp_y = strip_y + 26
    draw.rectangle([PX - 3, fp_y, PX + PW + 3, fp_y + 46],
                   fill=LIGHT_BLU, outline=(180, 200, 235), width=1)
    # Draw simple fingerprint arc lines
    fcx, fcy = PX + PW // 2, fp_y + 23
    for r in range(6, 28, 5):
        draw.arc([fcx - r, fcy - r, fcx + r, fcy + r], 200, 340,
                 fill=TEXT_MD, width=1)
    draw.text((PX + 42, fp_y + 30), "SCAN", font=_aadhar_font(8, bold=True), fill=TEXT_LT)

    # ── Personal Details ──────────────────────────────────────────
    DX = PX + PW + 26
    DY = HEADER_H + 14
    RW = W - DX - 148          # available width (leave space for QR)

    f_lbl  = _aadhar_font(10)
    f_val  = _aadhar_font(16, bold=True)
    f_val2 = _aadhar_font(13, bold=True)
    f_addr = _aadhar_font(11)

    # Thin top rule
    draw.rectangle([DX, DY, DX + RW, DY + 1], fill=(200, 215, 235))
    DY += 6

    # ── Name ─────────────────────────────────────────────────────
    draw.text((DX, DY),      "Name / नाम", font=f_lbl, fill=TEXT_MD)
    draw.text((DX, DY + 13), name.upper()[:40], font=f_val, fill=TEXT_DK)
    DY += 42

    # ── DOB + Gender (same row) ───────────────────────────────────
    draw.text((DX, DY),      "Date of Birth / जन्म तिथि", font=f_lbl, fill=TEXT_MD)
    draw.text((DX, DY + 13), dob, font=f_val2, fill=TEXT_DK)

    gender_hi = {"Male":"पुरुष","Female":"महिला","Transgender":"ट्रांसजेंडर"}.get(gender,"पुरुष")
    gx = DX + 200
    draw.text((gx, DY),      "Gender / लिंग", font=f_lbl, fill=TEXT_MD)
    draw.text((gx, DY + 13), f"{gender} / {gender_hi}", font=f_val2, fill=TEXT_DK)
    DY += 42

    # ── Address ───────────────────────────────────────────────────
    draw.text((DX, DY),      "Address / पता", font=f_lbl, fill=TEXT_MD)
    addr_lines = _wrap_text(address, 48)
    for i, ln in enumerate(addr_lines[:4]):
        draw.text((DX, DY + 13 + i * 16), ln, font=f_addr, fill=TEXT_DK)
    DY += 85

    # ── QR Code ───────────────────────────────────────────────────
    QW  = 130
    qx1 = W - QW - 14
    qy1 = HEADER_H + 14
    qx2 = qx1 + QW
    qy2 = qy1 + QW
    draw.rectangle([qx1 - 4, qy1 - 4, qx2 + 4, qy2 + 4], fill=NAVY)
    draw.rectangle([qx1,     qy1,     qx2,     qy2],     fill=WHITE)
    # Data-seeded QR pattern (unique per Aadhaar number)
    clean_num = re.sub(r"\D", "", number) or "000000000000"
    _rnd.seed(int(clean_num) % 999983)
    sq = max(5, QW // 20)
    for qr in range(qy1 + 2, qy2 - 2, sq):
        for qc in range(qx1 + 2, qx2 - 2, sq):
            if _rnd.random() > 0.42:
                draw.rectangle([qc, qr, qc + sq - 2, qr + sq - 2], fill=(0, 0, 0))
    # Corner finder squares (3)
    for (fx, fy) in [(qx1+2, qy1+2), (qx2-26, qy1+2), (qx1+2, qy2-26)]:
        draw.rectangle([fx,   fy,   fx+22, fy+22], fill=(0,0,0))
        draw.rectangle([fx+3, fy+3, fx+19, fy+19], fill=WHITE)
        draw.rectangle([fx+6, fy+6, fx+16, fy+16], fill=(0,0,0))
    draw.text((qx1 + 8, qy2 + 5), "Scan & Verify",
              font=_aadhar_font(9, bold=True), fill=TEXT_LT)

    # ── Number bar divider ────────────────────────────────────────
    nb_div = H - 185
    draw.rectangle([STRIP_W, nb_div, W, nb_div + 2], fill=(190, 205, 230))

    # ── Aadhaar Number Bar ────────────────────────────────────────
    nb_y = nb_div + 2
    nb_h = 82
    draw.rectangle([STRIP_W, nb_y, W, nb_y + nb_h], fill=LIGHT_BLU)
    # left accent stripe
    draw.rectangle([STRIP_W, nb_y, STRIP_W + 6, nb_y + nb_h], fill=NAVY)

    clean_fmt = clean_num.ljust(12)[:12]
    fmt_num   = f"{clean_fmt[:4]}  {clean_fmt[4:8]}  {clean_fmt[8:12]}"

    draw.text((STRIP_W + 20, nb_y + 6),
              "Aadhaar No. / आधार संख्या",
              font=_aadhar_font(11), fill=TEXT_MD)
    draw.text((STRIP_W + 20, nb_y + 22), fmt_num,
              font=_aadhar_font(42, bold=True), fill=NUM_BLU)

    # VID (Virtual ID) on right of number bar
    _rnd.seed(int(clean_num) % 888877 + 1)
    vid     = "".join([str(_rnd.randint(0, 9)) for _ in range(16)])
    vid_fmt = f"{vid[:4]} {vid[4:8]} {vid[8:12]} {vid[12:]}"
    vx = W - 310
    draw.text((vx, nb_y + 6),  "VID / वर्चुअल आईडी",
              font=_aadhar_font(10), fill=TEXT_LT)
    draw.text((vx, nb_y + 22), vid_fmt,
              font=_aadhar_font(13, bold=True), fill=TEXT_MD)

    # ── Footer ───────────────────────────────────────────────────
    foot_y = nb_y + nb_h
    draw.rectangle([STRIP_W, foot_y, W, H], fill=WHITE)
    draw.rectangle([STRIP_W, foot_y, W, foot_y + 2], fill=(190, 205, 230))

    _rnd.seed(hash(name + dob) % 99991)
    part_a = f"{_rnd.randint(1000,9999)}"
    part_b = f"{_rnd.randint(10000,99999)}"
    part_c = f"{_rnd.randint(10000,99999)}"
    enrol  = f"{part_a}/{part_b}/{part_c}"

    draw.text((STRIP_W + 14, foot_y + 5),
              f"Enrolment No: {enrol}   |   Issue Date: {dob}   |   Last Update: {dob}",
              font=_aadhar_font(10), fill=TEXT_MD)
    draw.text((STRIP_W + 14, foot_y + 20),
              "Issued by UIDAI under The Aadhaar (Targeted Delivery of Financial) Subsidies, Benefits and Services Act, 2016.",
              font=_aadhar_font(8), fill=TEXT_LT)
    draw.text((STRIP_W + 14, foot_y + 33),
              "Verify at resident.uidai.gov.in  |  Download mAadhaar App  |  Toll Free: 1947  |  help@uidai.gov.in",
              font=_aadhar_font(8), fill=TEXT_LT)

    # Hologram sticker (bottom-right)
    hcx, hcy = W - 58, foot_y + 28
    draw.ellipse([hcx-28, hcy-28, hcx+28, hcy+28],
                 fill=(228, 238, 255), outline=NAVY, width=2)
    draw.ellipse([hcx-21, hcy-21, hcx+21, hcy+21],
                 outline=GOLD, width=1)
    draw.ellipse([hcx-14, hcy-14, hcx+14, hcy+14],
                 outline=ORANGE_BR, width=1)
    draw.text((hcx - 18, hcy - 8), "UIDAI",
              font=_aadhar_font(11, bold=True), fill=NAVY)

    # ── Tricolor bottom strip ─────────────────────────────────────
    draw.rectangle([STRIP_W, H - 12, W, H],       fill=SAFFRON)
    draw.rectangle([STRIP_W, H - 24, W, H - 12],  fill=WHITE)
    draw.rectangle([STRIP_W, H - 36, W, H - 24],  fill=GREEN_IND)

    out = BytesIO()
    img.save(out, format="PNG", dpi=(300, 300), optimize=True)
    out.seek(0)
    return out


async def cmd_makeaadhar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "makeaadhar"): return
    if await _check_credits(update, user): return
    _makeaadhar_state[uid] = {}
    context.user_data["pending"] = PENDING_MAKEAADHAR_NAME
    sent = await update.message.reply_text(
        bq(
            "🪪 <b>Aadhaar Card Generator</b>\n\n"
            "┌─────────────────────────┐\n"
            "│  Step <b>1 / 6</b> — Full Name  │\n"
            "└─────────────────────────┘\n\n"
            "Person er <b>full name</b> likho:\n"
            "Example: <code>Rahul Kumar</code>\n\n"
            "/cancel to go back."
        ),
        parse_mode="HTML"
    )
    schedule_delete(sent)


async def _handle_makeaadhar_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, uid: str, users: dict):
    """Final step: receive photo and generate the Aadhar card image."""
    photo_file = await update.message.photo[-1].get_file()
    photo_buf  = BytesIO()
    await photo_file.download_to_memory(photo_buf)
    photo_bytes = photo_buf.getvalue()

    data = _makeaadhar_state.get(uid, {})
    name    = data.get("name", "N/A")
    dob     = data.get("dob",  "N/A")
    number  = data.get("number", "0000 0000 0000")
    address = data.get("address", "N/A")

    if not spend_credit(users, uid):
        sent = await update.message.reply_text(bq("❌ Insufficient credits.\n\n💡 Claim daily credits via /start."), parse_mode="HTML")
        schedule_delete(sent)
        _makeaadhar_state.pop(uid, None)
        context.user_data["pending"] = PENDING_NONE
        return

    context.user_data["pending"] = PENDING_NONE
    _makeaadhar_state.pop(uid, None)

    sent = await update.message.reply_text(bq("⏳ Generating Aadhaar Card..."), parse_mode="HTML")

    gender = data.get("gender", "Male")

    try:
        card_buf = await asyncio.get_event_loop().run_in_executor(
            None, _draw_aadhar_card, name, dob, number, address, photo_bytes, gender
        )
        await sent.delete()
        caption = bq(
            f"🪪 <b>Aadhaar Card</b>\n\n"
            f"👤 Name    : <b>{h(name)}</b>\n"
            f"📅 DOB     : <b>{h(dob)}</b>\n"
            f"⚧ Gender  : <b>{h(gender)}</b>\n"
            f"🔢 No      : <code>{h(number)}</code>\n"
            f"🏠 Address : {h(address[:60])}\n\n"
            f"👺 DEV @Shuvobhai ✅"
        )
        await update.message.reply_photo(
            photo=card_buf,
            caption=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🪪 Make Another", callback_data="service_makeaadhar"),
                InlineKeyboardButton("🏠 Home",          callback_data="back_home"),
            ]])
        )
    except Exception as e:
        await sent.edit_text(bq(f"❌ Card generate kora jacchena: <code>{h(str(e))}</code>"), parse_mode="HTML")
        schedule_delete(sent)


async def _generate_voice(text: str, voice: str, out_path: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

async def _send_voice_reply(update: Update, text: str, voice: str):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    try:
        await _generate_voice(text, voice, tmp)
        with open(tmp, "rb") as audio:
            await update.message.reply_voice(voice=audio)
    finally:
        try:
            os.unlink(tmp)
        except Exception:
            pass

async def cmd_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "voice"): return
    if not user.get("is_admin") and user.get("credits", 0) <= 0:
        sent = await update.message.reply_text(bq("❌ Insufficient credits.\n\n💡 Claim daily credits via /start."), parse_mode="HTML")
        schedule_delete(sent); return

    args      = context.args or []
    lang_code = ""
    text_parts= []

    for a in args:
        if a.lower() in VOICE_MAP and not lang_code:
            lang_code = a.lower()
        else:
            text_parts.append(a)

    voice     = VOICE_MAP.get(lang_code, VOICE_DEFAULT)
    text      = " ".join(text_parts).strip()

    if not text and update.message.reply_to_message:
        rp = update.message.reply_to_message
        text = (rp.text or rp.caption or "").strip()

    if not text:
        lang_list = "bn/bd · en · hi · ar · fr · de · ja · ko · zh · ru · es · tr · ur · ta · te · pt · it"
        sent = await update.message.reply_text(
            bq(
                "🎙 <b>Voice Convert</b>\n\n"
                "Usage:\n"
                "• <code>/voice Hello world</code> — Bangla voice (default)\n"
                "• <code>/voice en Hello world</code> — English voice\n"
                "• Reply any message with <code>/voice bd</code>\n\n"
                f"🌍 Language codes: <code>{lang_list}</code>\n\n"
                "/cancel to go back."
            ),
            parse_mode="HTML"
        )
        context.user_data["pending"]      = PENDING_VOICE
        context.user_data["voice_lang"]   = lang_code
        schedule_delete(sent)
        return

    if not spend_credit(users, uid):
        sent = await update.message.reply_text(bq("❌ Insufficient credits."), parse_mode="HTML")
        schedule_delete(sent); return

    sent = await update.message.reply_text(bq("🎙 Converting to voice..."), parse_mode="HTML")
    try:
        await _send_voice_reply(update, text, voice)
        await sent.delete()
    except Exception as e:
        await sent.edit_text(bq(f"❌ Voice convert failed: {h(str(e)[:200])}\n\n👺 DEV @Shuvobhai ✅"), parse_mode="HTML")
        schedule_delete(sent)

async def cmd_randomuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "randomuser"): return
    if not spend_credit(users, uid):
        sent = await update.message.reply_text(bq("❌ Insufficient credits. Use /start to claim daily credits."), parse_mode="HTML"); schedule_delete(sent); return
    sent = await update.message.reply_text(bq("⏳ Generating random user..."), parse_mode="HTML")
    await _do_randomuser(sent)

async def _do_randomuser(sent):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(RANDOMUSER_API_BASE)
            data = safe_json(r)
            res_list = data.get("results", [{}])
            u = res_list[0] if res_list else {}
            name = u.get("name", {})
            full_name = f"{name.get('first','')} {name.get('last','')}".strip()
            loc = u.get("location", {})
            result = bq(
                f"🎲 <b>Random User</b>\n\n"
                f"👤 Name: <b>{h(full_name)}</b>\n"
                f"🚻 Gender: {h(u.get('gender','N/A').title())}\n"
                f"📧 Email: <code>{h(u.get('email','N/A'))}</code>\n"
                f"📱 Phone: <code>{h(u.get('phone','N/A'))}</code>\n"
                f"🏙 City: {h(loc.get('city','N/A'))}\n"
                f"🌍 Country: {h(loc.get('country','N/A'))}\n"
                f"🎂 Age: {h(u.get('dob',{}).get('age','N/A'))}\n\n"
                f"👺 DEV @Shuvobhai ✅"
            )
            await sent.edit_text(result, parse_mode="HTML")
    except Exception as e:
        await sent.edit_text(bq(f"❌ Error: {h(str(e)[:200])}"), parse_mode="HTML")
    schedule_delete(sent)


async def cmd_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "ai_chat"): return

    prompt = " ".join(context.args).strip() if context.args else ""
    if not prompt:
        sent = await update.message.reply_text(
            bq(
                "🤖 <b>SHUVO SUPER AI</b>\n\n"
                "I can do EVERYTHING for you!\n\n"
                "💡 <b>Examples:</b>\n"
                "• <code>/ai check IP 8.8.8.8</code>\n"
                "• <code>/ai weather in Dhaka</code>\n"
                "• <code>/ai lookup TG ID 123456789</code>\n"
                "• <code>/ai Instagram info cristiano</code>\n"
                "• <code>/ai generate image sunset over ocean</code>\n"
                "• <code>/ai IFSC SBIN0001234</code>\n\n"
                "Or just send any message in private chat!\n\n"
                "👺 DEV @Shuvobhai ✅"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    await _send_ai_powered_response(update, uid, users, prompt)


async def cmd_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "imagegen"): return
    prompt = " ".join(context.args).strip() if context.args else ""
    if not prompt:
        sent = await update.message.reply_text(
            bq("🎨 <b>AI Image Generator</b>\n\nSend a prompt!\nExample: <code>/image a cat in space, digital art</code>"),
            parse_mode="HTML"
        )
        schedule_delete(sent); return
    sent = await update.message.reply_text(bq("🎨 Generating image..."), parse_mode="HTML")
    try:
        encoded = urllib.parse.quote(prompt)
        img_url = f"{POLLINATIONS_BASE}/{encoded}?width=1024&height=1024&nologo=true&model=flux"
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(img_url)
        if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
            await sent.delete()
            photo_sent = await update.message.reply_photo(
                photo=r.content,
                caption=bq(f"🎨 <b>AI Generated Image</b>\n\n📝 Prompt: {h(prompt[:200])}\n\n👺 DEV @Shuvobhai ✅"),
                parse_mode="HTML"
            )
            schedule_delete(photo_sent)
        else:
            await sent.edit_text(bq("❌ Could not generate image. Please try again."), parse_mode="HTML")
            schedule_delete(sent)
    except Exception as e:
        await sent.edit_text(bq(f"❌ Error: {h(str(e)[:200])}"), parse_mode="HTML")
        schedule_delete(sent)


async def _do_nasa_apod(sent):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(NASA_APOD_BASE, params={"api_key": NASA_API_KEY})
            data = safe_json(r)
            title = data.get("title", "N/A")
            explanation = data.get("explanation", "")[:500]
            url = data.get("url", "")
            await sent.edit_text(
                bq(
                    f"🚀 <b>NASA — Astronomy Picture of the Day</b>\n\n"
                    f"📸 <b>{h(title)}</b>\n\n"
                    f"📝 {h(explanation)}...\n\n"
                    f"🔗 <a href='{url}'>View Image</a>\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                ),
                parse_mode="HTML"
            )
    except Exception as e:
        await sent.edit_text(bq(f"❌ Error: {h(str(e)[:200])}"), parse_mode="HTML")
    schedule_delete(sent)


async def _do_nasa_epic(sent):
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(NASA_EPIC_BASE, params={"api_key": NASA_API_KEY})
            data = safe_json(r, [])
            if data:
                ep = data[0]
                img_name = ep.get("image", "")
                date_str = ep.get("date", "")[:10].replace("-", "/")
                img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{date_str}/png/{img_name}.png"
                await sent.edit_text(
                    bq(
                        f"🌍 <b>NASA EPIC — Earth from Space</b>\n\n"
                        f"📅 Date: {h(ep.get('date','N/A')[:10])}\n"
                        f"🏷 Caption: {h(ep.get('caption','N/A')[:300])}\n"
                        f"🔗 <a href='{img_url}'>View Photo</a>\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    ),
                    parse_mode="HTML"
                )
            else:
                await sent.edit_text(bq("🌍 <b>NASA EPIC</b>\n\n❌ No photos available.\n\n👺 DEV @Shuvobhai ✅"), parse_mode="HTML")
    except Exception as e:
        await sent.edit_text(bq(f"❌ Error: {h(str(e)[:200])}"), parse_mode="HTML")
    schedule_delete(sent)


async def cmd_nasa_apod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "nasa"): return
    sent = await update.message.reply_text(bq("🚀 Fetching NASA APOD..."), parse_mode="HTML")
    await _do_nasa_apod(sent)

async def cmd_nasa_epic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "nasa"): return
    sent = await update.message.reply_text(bq("🌍 Fetching NASA EPIC..."), parse_mode="HTML")
    await _do_nasa_epic(sent)


async def cmd_diagnose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if not user.get("is_admin"):
        sent = await update.message.reply_text(bq("⛔ Admin only."), parse_mode="HTML")
        schedule_delete(sent); return
    if not _error_log:
        sent = await update.message.reply_text(bq("✅ No error logs found. Bot is running fine!"), parse_mode="HTML")
        schedule_delete(sent); return
    errors_text = "\n".join(_error_log[-20:])
    sent = await update.message.reply_text(bq("🔍 AI is analyzing errors..."), parse_mode="HTML")
    diagnosis = await ai_groq(uid, f"Analyze these recent bot error logs. Explain what is going wrong and HOW TO FIX each issue. Be specific and actionable:\n\n{errors_text}")
    await sent.edit_text(bq(f"🔍 <b>Bot Diagnosis</b>\n\n{h(diagnosis)}"), parse_mode="HTML")
    schedule_delete(sent)


async def cmd_aiclear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    _ai_history.pop(uid, None)
    sent = await update.message.reply_text(bq("🗑 AI conversation history cleared."), parse_mode="HTML")
    schedule_delete(sent)


async def cmd_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply to any message with /sticker to convert text into a sticker."""
    if not update.message:
        return
    reply = update.message.reply_to_message
    if not reply:
        sent = await update.message.reply_text(
            bq("↩️ <b>Reply to a message</b> with /sticker to turn it into a sticker!"),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return
    text = (reply.text or reply.caption or "").strip()
    if not text:
        sent = await update.message.reply_text(
            bq("❌ That message has no text to convert."), parse_mode="HTML"
        )
        schedule_delete(sent)
        return

    sender      = reply.from_user
    sender_name = (sender.first_name or "User") if sender else "User"

    try:
        from PIL import Image, ImageDraw, ImageFont
        import io, textwrap, math

        FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

        SIZE_NAME = 26
        SIZE_TEXT = 24
        PADDING   = 28
        MAX_W     = 460
        RADIUS    = 22

        try:
            fn = ImageFont.truetype(FONT_BOLD, SIZE_NAME)
            ft = ImageFont.truetype(FONT_REG,  SIZE_TEXT)
        except Exception:
            fn = ft = ImageFont.load_default()

        # ── Wrap text ──────────────────────────────────────────────
        wrapped_lines: list[str] = []
        for raw_line in text.splitlines():
            if not raw_line:
                wrapped_lines.append("")
                continue
            wrapped_lines.extend(textwrap.wrap(raw_line, width=22) or [""])

        # ── Measure sizes ─────────────────────────────────────────
        def text_size(draw: ImageDraw.ImageDraw, txt: str, font):
            bbox = draw.textbbox((0, 0), txt, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]

        tmp = Image.new("RGBA", (1, 1))
        td  = ImageDraw.Draw(tmp)
        name_w, name_h  = text_size(td, sender_name, fn)
        line_h = SIZE_TEXT + 8
        text_block_h    = len(wrapped_lines) * line_h
        max_line_w      = max((text_size(td, l, ft)[0] for l in wrapped_lines if l), default=name_w)

        bubble_w = min(MAX_W, max(name_w, max_line_w) + PADDING * 2 + 8)
        bubble_h = PADDING + name_h + 10 + text_block_h + PADDING

        # ── Canvas (transparent, 512×512 max) ─────────────────────
        CW = 512
        CH = min(512, bubble_h + 48)
        img  = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        bx = (CW - bubble_w) // 2
        by = (CH - bubble_h) // 2

        # Bubble fill (dark Telegram-like)
        BUBBLE  = (36, 36, 56, 240)
        NAME_C  = (110, 168, 254, 255)   # blue accent
        TEXT_C  = (220, 220, 235, 255)
        ACCENT  = (110, 168, 254, 255)

        draw.rounded_rectangle(
            [bx, by, bx + bubble_w, by + bubble_h],
            radius=RADIUS, fill=BUBBLE
        )
        # Left accent bar
        draw.rounded_rectangle(
            [bx, by + 10, bx + 4, by + bubble_h - 10],
            radius=2, fill=ACCENT
        )

        # Sender name
        draw.text((bx + PADDING, by + PADDING // 2), sender_name, font=fn, fill=NAME_C)

        # Message lines
        ty = by + PADDING // 2 + name_h + 10
        for line in wrapped_lines:
            draw.text((bx + PADDING, ty), line, font=ft, fill=TEXT_C)
            ty += line_h

        # ── Export as WebP sticker ─────────────────────────────────
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=90)
        buf.seek(0)

        await update.message.reply_sticker(sticker=buf)
        try:
            await update.message.delete()
        except Exception:
            pass

    except Exception as e:
        sent = await update.message.reply_text(
            bq(f"❌ <b>Sticker creation failed</b>\n<code>{h(str(e))}</code>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)


async def cmd_bypass_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        sent = await update.message.reply_text(
            bq("❌ This command only works <b>inside a group</b>."),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return
    uid = str(update.effective_user.id)
    try:
        member = await context.bot.get_chat_member(chat.id, int(uid))
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
    if not is_admin and uid != str(ADMIN_ID):
        sent = await update.message.reply_text(
            bq("🚫 Only <b>group admins</b> can toggle bypass."),
            parse_mode="HTML"
        )
        schedule_delete(sent)
        return
    args = context.args or []
    arg = args[0].lower() if args else ""
    cid = str(chat.id)
    if arg == "on":
        _bypass_disabled_groups.discard(cid)
        sent = await update.message.reply_text(
            bq("✅ <b>Auto Bypass: ON</b>\n\nNow I'll automatically bypass any link sent in this group.\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
    elif arg == "off":
        _bypass_disabled_groups.add(cid)
        sent = await update.message.reply_text(
            bq("🔴 <b>Auto Bypass: OFF</b>\n\nAuto bypass is now disabled in this group.\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
    else:
        status = "🔴 OFF" if cid in _bypass_disabled_groups else "✅ ON"
        sent = await update.message.reply_text(
            bq(f"🔗 <b>Auto Bypass Status: {status}</b>\n\n"
               f"Use:\n"
               f"• <code>/by on</code> — Enable auto bypass\n"
               f"• <code>/by off</code> — Disable auto bypass\n\n"
               f"👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
    schedule_delete(sent)


# Domains that are already direct/safe — no bypass needed
_SAFE_DOMAINS = {
    # Telegram
    "t.me", "telegram.me", "telegram.org",
    # Google
    "google.com", "gmail.com", "accounts.google.com", "docs.google.com",
    "maps.google.com", "play.google.com", "googleapis.com",
    # YouTube
    "youtube.com", "youtu.be", "yt.be",
    # Social media
    "facebook.com", "fb.com", "instagram.com", "twitter.com", "x.com",
    "whatsapp.com", "wa.me", "linkedin.com", "pinterest.com",
    "reddit.com", "tiktok.com", "snapchat.com",
    # Messaging/community
    "discord.com", "discord.gg", "slack.com",
    # Direct download / file hosts (direct links only — share pages still need bypass)
    "github.com", "raw.githubusercontent.com",
    "archive.org", "wikimedia.org", "wikipedia.org",
    # Common safe sites
    "amazon.com", "flipkart.com", "apple.com", "microsoft.com",
    "stackoverflow.com", "medium.com",
    # CDNs / direct file delivery
    "cdn.discordapp.com", "images-ext-1.discordapp.net",
    "pbs.twimg.com", "abs.twimg.com",
}

def _needs_bypass(url: str) -> bool:
    """Bypass everything EXCEPT known safe/direct domains."""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        host = host.lower().removeprefix("www.")
        # Skip if it's a known safe domain
        if any(host == d or host.endswith("." + d) for d in _SAFE_DOMAINS):
            return False
        return True
    except Exception:
        return False

def _load_bypass_cache() -> dict:
    try:
        with open(BYPASS_CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_bypass_cache(cache: dict):
    try:
        os.makedirs("bot", exist_ok=True)
        with open(BYPASS_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

_bypass_cache: dict = _load_bypass_cache()

def _extract_url(text: str) -> str | None:
    match = re.search(r'https?://[^\s]+', text)
    return match.group(0) if match else None

async def _do_bypass(update: Update, url: str, uid: str, users: dict):
    global _bypass_cache
    user = users.get(uid, {})
    name = (user.get("first_name") or user.get("username") or uid)

    # ── Cache hit: already bypassed before ──
    if url in _bypass_cache:
        t0 = datetime.now()
        cached = _bypass_cache[url]
        elapsed_cache = (datetime.now() - t0).total_seconds()
        msg = (
            f"➿➿➿➿➿➿➿➿➿\n"
            f"💐 <b>SHUVO BOT BYPASS</b> 🌟\n"
            f"➿➿➿➿➿➿➿➿➿\n\n"
            f"🥳 <b>Requested By:</b> {h(name)}\n\n"
            f"➿➿➿➿➿➿➿➿➿\n\n"
            f"⛓ <b>Original :</b>\n<code>{h(url)}</code>\n\n"
            f"🎁 <b>Bypassed :</b>\n<code>{h(cached)}</code>\n\n"
            f"➿➿➿➿➿➿➿➿➿\n\n"
            f"⚡ <b>Time Taken :</b> {elapsed_cache:.2f}s\n"
            f"💾 <b>Served from response.json cache!</b>\n\n"
            f"➿➿➿➿➿➿➿➿➿\n"
            f"🥫 <b>Dev :</b> @Shuvobhai 🌟\n"
            f"➿➿➿➿➿➿➿➿➿"
        )
        await update.message.reply_text(bq(msg), parse_mode="HTML")
        return

    sent = await update.message.reply_text(
        bq("🔗 <b>Bypass in progress...</b>\n⏳ Please wait..."),
        parse_mode="HTML"
    )
    start_t = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(FELIX_BYPASS_API.format(urllib.parse.quote(url, safe='')))
            data = safe_json(resp, {})
    except Exception as e:
        await sent.edit_text(bq(f"❌ <b>Bypass Failed!</b>\n\n<code>{h(str(e))}</code>"), parse_mode="HTML")
        return
    elapsed = (datetime.now() - start_t).total_seconds()
    status  = data.get("status", False)
    bypassed = data.get("response", {}).get("bypassed_link", "")
    original = data.get("request", {}).get("original_link", url)
    stats    = data.get("stats", {})
    usage    = stats.get("total_requests", "—")
    if not status or not bypassed:
        err = data.get("message") or data.get("error") or "Unknown error"
        await sent.edit_text(
            bq(f"❌ <b>Bypass Failed!</b>\n\n🔗 Link: <code>{h(url)}</code>\n💬 Reason: <code>{h(str(err))}</code>\n\n👺 DEV @Shuvobhai ✅"),
            parse_mode="HTML"
        )
        return

    # ── Save to cache ──
    _bypass_cache[url] = bypassed
    _save_bypass_cache(_bypass_cache)

    msg = (
        f"➿➿➿➿➿➿➿➿➿\n"
        f"💐 <b>SHUVO BOT BYPASS</b> 🌟\n"
        f"➿➿➿➿➿➿➿➿➿\n\n"
        f"🥳 <b>Requested By:</b> {h(name)}\n\n"
        f"➿➿➿➿➿➿➿➿➿\n\n"
        f"⛓ <b>Original :</b>\n<code>{h(original)}</code>\n\n"
        f"🎁 <b>Bypassed :</b>\n<code>{h(bypassed)}</code>\n\n"
        f"➿➿➿➿➿➿➿➿➿\n\n"
        f"⏰ <b>Time Taken :</b> {elapsed:.2f}s\n"
        f"🥳 <b>Usage      :</b> {usage} Times\n\n"
        f"➿➿➿➿➿➿➿➿➿\n"
        f"🥫 <b>Dev :</b> @Shuvobhai 🌟\n"
        f"➿➿➿➿➿➿➿➿➿"
    )
    await sent.edit_text(bq(msg), parse_mode="HTML")


async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    if is_paused() and str(update.effective_user.id) != str(ADMIN_ID):
        sent = await update.message.reply_text("🔧 Bot is under maintenance. Please try again later.")
        schedule_delete(sent)
        return
    pending = context.user_data.get("pending", PENDING_NONE)
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")

    if user["banned"]: return

    # ── Admin DM reply mode ──
    admin_key = str(update.effective_user.id)
    if admin_key in _pending_dm_reply and update.effective_chat.type == "private":
        target_uid = _pending_dm_reply.pop(admin_key)
        try:
            await context.bot.copy_message(
                chat_id=int(target_uid),
                from_chat_id=update.message.chat_id,
                message_id=update.message.message_id
            )
            sent = await update.message.reply_text(
                f"✅ <b>Message Delivered!</b>\n\n"
                f"📤 Sent to user <code>{target_uid}</code>.",
                parse_mode="HTML"
            )
        except Exception as e:
            sent = await update.message.reply_text(
                f"❌ <b>Failed to send:</b> <code>{e}</code>",
                parse_mode="HTML"
            )
        schedule_delete(sent)
        return

    if not user.get("is_admin") and str(update.effective_user.id) != str(ADMIN_ID):
        if update.effective_chat.type == "private" and pending == PENDING_NONE:
            unjoined = await check_force_join(context.bot, update.effective_user.id)
            if unjoined:
                names = "\n".join(f"  🔹 <b>{h(ch['title'])}</b>" for ch in unjoined)
                sent = await update.message.reply_text(
                    bq(
                        f"📢 <b>Join Required!</b>\n\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"To use <b>SHUVO BOT</b> you must join:\n\n"
                        f"{names}\n\n"
                        f"Tap <b>✅ Verify</b> after joining."
                    ),
                    reply_markup=force_join_keyboard(unjoined),
                    parse_mode="HTML"
                )
                schedule_delete(sent)
                return

    chat_type = update.effective_chat.type
    text_raw = update.message.text or ""

    # ── Group/Supergroup: AI responds when mentioned or replied to ──
    if chat_type in ("group", "supergroup"):
        if pending == PENDING_NONE:
            is_mention = _bot_username and f"@{_bot_username}" in text_raw.lower()
            is_reply_to_bot = (
                update.message.reply_to_message is not None and
                update.message.reply_to_message.from_user is not None and
                update.message.reply_to_message.from_user.id == context.bot.id
            )
            if not is_mention and not is_reply_to_bot:
                detected_url = _extract_url(text_raw)
                if detected_url and _needs_bypass(detected_url) and str(update.effective_chat.id) not in _bypass_disabled_groups:
                    await _do_bypass(update, detected_url, uid, users)
                return
            ai_text = text_raw
            if is_mention and _bot_username:
                ai_text = re.sub(rf"@{_bot_username}", "", ai_text, flags=re.IGNORECASE).strip()
            if not ai_text:
                return
            # Use powered AI in groups too
            await _send_ai_powered_response(update, uid, users, ai_text)
            return

    if pending == PENDING_BROADCAST:
        context.user_data["pending"] = PENDING_NONE
        sent_count = 0
        from_chat = update.message.chat_id
        msg_id    = update.message.message_id
        for user_id, u in users.items():
            if not u["banned"]:
                try:
                    await context.bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=from_chat,
                        message_id=msg_id
                    )
                    sent_count += 1
                except Exception:
                    pass
        sent = await update.message.reply_text(bq(f"✅ Broadcast sent to <b>{sent_count}</b> users.\n📋 Formatting preserved ✅"), parse_mode="HTML")
        schedule_delete(sent); return

    # ── Aadhar Card Generator: accept photo on final step ──
    if update.message.photo and pending == PENDING_MAKEAADHAR_PHOTO:
        await _handle_makeaadhar_photo(update, context, uid, users)
        return

    if update.message.text is None:
        if pending == PENDING_MAKEAADHAR_PHOTO:
            sent = await update.message.reply_text(bq("📸 Photo pathao — photo message patha! Camera/gallery theke select koro.\n\n/cancel to cancel."), parse_mode="HTML")
        else:
            sent = await update.message.reply_text(bq("❌ Text only — photo/sticker/voice pathabo na."), parse_mode="HTML")
        schedule_delete(sent); return

    text = update.message.text.strip()

    if pending == PENDING_MKCODE_CREDITS:
        try:
            credits = int(text)
            if credits <= 0: raise ValueError
        except ValueError:
            sent = await update.message.reply_text(bq("❌ Send a valid number (e.g. <code>10</code>)."), parse_mode="HTML")
            schedule_delete(sent); return
        _mkcode_state[uid] = {"credits": credits}
        context.user_data["pending"] = PENDING_MKCODE_USERS
        sent = await update.message.reply_text(
            bq(
                f"✅ Credits set: <b>{credits}</b>\n\n"
                f"👥 <b>Max users?</b>\n"
                f"How many people can use this code?\n"
                f"<code>0</code> = unlimited"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    if pending == PENDING_MKCODE_USERS:
        try:
            max_users = int(text)
            if max_users < 0: raise ValueError
        except ValueError:
            sent = await update.message.reply_text(bq("❌ Send a valid number (e.g. <code>10</code> or <code>0</code> for unlimited)."), parse_mode="HTML")
            schedule_delete(sent); return
        _mkcode_state[uid]["max_users"] = max_users
        context.user_data["pending"] = PENDING_MKCODE_DAYS
        sent = await update.message.reply_text(
            bq(
                f"✅ Max users: <b>{'Unlimited ∞' if max_users == 0 else max_users}</b>\n\n"
                f"📅 <b>Expiry in days?</b>\n"
                f"How many days until this code expires?\n"
                f"<code>0</code> = never expires"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    if pending == PENDING_MKCODE_DAYS:
        try:
            days = int(text)
            if days < 0: raise ValueError
        except ValueError:
            sent = await update.message.reply_text(bq("❌ Send a valid number (e.g. <code>7</code> or <code>0</code> for never)."), parse_mode="HTML")
            schedule_delete(sent); return
        context.user_data["pending"] = PENDING_NONE
        state = _mkcode_state.pop(uid, {})
        credits = state.get("credits", 5)
        max_users = state.get("max_users", 0)
        chars = string.ascii_uppercase + string.digits
        suffix = "".join(random.choices(chars, k=4)) + "-" + "".join(random.choices(chars, k=4))
        code_str = f"SHUVO_{suffix}"
        expires_at = (datetime.now() + timedelta(days=days)).isoformat() if days > 0 else None
        codes = load_codes()
        codes[code_str] = {
            "credits": credits,
            "max_users": max_users,
            "expires_at": expires_at,
            "used_by": [],
            "created_by": uid,
            "created_at": datetime.now().isoformat(),
        }
        save_codes(codes)
        exp_text = f"{days} day{'s' if days != 1 else ''}" if days > 0 else "♾️ Never"
        max_text = f"{max_users} users" if max_users > 0 else "♾️ Unlimited"
        bar = "█" * min(credits // 10, 10) + "░" * max(0, 10 - credits // 10)
        sent = await update.message.reply_text(
            bq(
                f"🎫 <b>CODE CREATED!</b>\n\n"
                f"🔑 <code>{h(code_str)}</code>\n\n"
                f"💎 Credits  : <b>{credits}</b>  [{bar}]\n"
                f"👥 Max Users: <b>{max_text}</b>\n"
                f"⏳ Expires  : <b>{exp_text}</b>\n\n"
                f"📢 /redeem <code>{h(code_str)}</code>\n\n"
                f"👺 SHUVO BOT ✅"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    # ── Menu-triggered AI generation prompts ──
    if pending == "imagegen_prompt":
        context.user_data["pending"] = PENDING_NONE
        context.args = text.split()
        await cmd_image_p2(update, context)
        return

    if pending == "music_prompt":
        context.user_data["pending"] = PENDING_NONE
        context.args = text.split()
        await cmd_music(update, context)
        return

    if pending == "videogen_prompt":
        context.user_data["pending"] = PENDING_NONE
        context.args = text.split()
        await cmd_video_gen(update, context)
        return

    if pending == "sprite_prompt":
        context.user_data["pending"] = PENDING_NONE
        context.args = text.split()
        await cmd_sprite(update, context)
        return

    if pending == "model3d_prompt":
        context.user_data["pending"] = PENDING_NONE
        context.args = text.split()
        await cmd_model3d(update, context)
        return

    # ── Aadhar Card Generator: multi-step text flow ──
    if pending == PENDING_MAKEAADHAR_NAME:
        if len(text.strip()) < 2:
            sent = await update.message.reply_text(bq("❌ Valid name likho (min 2 chars).\n\n/cancel to cancel."), parse_mode="HTML")
            schedule_delete(sent); return
        _makeaadhar_state[uid] = {"name": text.strip()}
        context.user_data["pending"] = PENDING_MAKEAADHAR_DOB
        sent = await update.message.reply_text(
            bq(
                f"✅ Name: <b>{h(text.strip())}</b>\n\n"
                "┌──────────────────────────────┐\n"
                "│  Step <b>2 / 6</b> — Date of Birth  │\n"
                "└──────────────────────────────┘\n\n"
                "Date of birth pathao:\n"
                "Example: <code>01/01/1995</code>\n\n"
                "/cancel to cancel."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    if pending == PENDING_MAKEAADHAR_DOB:
        _makeaadhar_state.setdefault(uid, {})["dob"] = text.strip()
        context.user_data["pending"] = PENDING_MAKEAADHAR_GENDER
        sent = await update.message.reply_text(
            bq(
                f"✅ DOB: <b>{h(text.strip())}</b>\n\n"
                "┌──────────────────────────┐\n"
                "│  Step <b>3 / 6</b> — Gender / লিঙ্গ  │\n"
                "└──────────────────────────┘\n\n"
                "Gender select koro:"
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("👨 Male",        callback_data="aadhar_gen_Male"),
                    InlineKeyboardButton("👩 Female",      callback_data="aadhar_gen_Female"),
                    InlineKeyboardButton("⚧ Transgender", callback_data="aadhar_gen_Transgender"),
                ]
            ])
        )
        schedule_delete(sent); return

    if pending == PENDING_MAKEAADHAR_GENDER:
        g = text.strip().capitalize()
        if g not in ("Male", "Female", "Transgender"):
            g = "Male"
        _makeaadhar_state.setdefault(uid, {})["gender"] = g
        context.user_data["pending"] = PENDING_MAKEAADHAR_NUM
        sent = await update.message.reply_text(
            bq(
                f"✅ Gender: <b>{h(g)}</b>\n\n"
                "┌───────────────────────────────────┐\n"
                "│  Step <b>4 / 6</b> — Aadhaar Card Number  │\n"
                "└───────────────────────────────────┘\n\n"
                "12-digit Aadhaar number pathao:\n"
                "Example: <code>1234 5678 9012</code>\n\n"
                "/cancel to cancel."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    if pending == PENDING_MAKEAADHAR_NUM:
        clean = re.sub(r"\D", "", text)
        if len(clean) != 12:
            sent = await update.message.reply_text(bq("❌ 12-digit number pathao.\nExample: <code>1234 5678 9012</code>\n\n/cancel to cancel."), parse_mode="HTML")
            schedule_delete(sent); return
        fmt = f"{clean[:4]} {clean[4:8]} {clean[8:12]}"
        _makeaadhar_state.setdefault(uid, {})["number"] = fmt
        context.user_data["pending"] = PENDING_MAKEAADHAR_ADDR
        sent = await update.message.reply_text(
            bq(
                f"✅ Number: <code>{h(fmt)}</code>\n\n"
                "┌───────────────────────────────┐\n"
                "│  Step <b>5 / 6</b> — Address / ঠিকানা  │\n"
                "└───────────────────────────────┘\n\n"
                "Full address pathao:\n"
                "Example: <code>123 Main St, New Delhi 110001</code>\n\n"
                "/cancel to cancel."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    if pending == PENDING_MAKEAADHAR_ADDR:
        _makeaadhar_state.setdefault(uid, {})["address"] = text.strip()
        context.user_data["pending"] = PENDING_MAKEAADHAR_PHOTO
        sent = await update.message.reply_text(
            bq(
                f"✅ Address saved!\n\n"
                "┌──────────────────────────┐\n"
                "│  Step <b>6 / 6</b> — 📸 Photo  │\n"
                "└──────────────────────────┘\n\n"
                "Person er <b>photo</b> pathao (gallery / camera theke).\n"
                "Photo ta card-e paste hobe!\n\n"
                "/cancel to cancel."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent); return

    # ── Private chat with no pending: check URL first, then SUPER AI ──
    if pending == PENDING_NONE:
        detected_url = _extract_url(text_raw)
        if detected_url and _needs_bypass(detected_url):
            await _do_bypass(update, detected_url, uid, users)
            return
        if chat_type == "private":
            await _send_ai_powered_response(update, uid, users, text)
        return

    context.user_data["pending"] = PENDING_NONE

    if not spend_credit(users, uid):
        sent = await update.message.reply_text(bq("❌ Insufficient credits. Use /start to claim daily credits.\n\n💡 Or use /ai — I can do it for you!"), parse_mode="HTML")
        schedule_delete(sent); return

    sent = await update.message.reply_text(bq("⏳ Processing..."), parse_mode="HTML")

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            if pending == PENDING_USERID:
                clean_id = re.sub(r'\D', '', text)
                info = await _fetch_userid_info(client, clean_id, is_username=False)
                all_recs = info.get("all_records", [])
                lines = [f"🔎 <b>TG ID Lookup</b>\n\n🆔 ID: <code>{h(text)}</code>"]
                if all_recs:
                    lines.append(f"📊 Results: <b>{len(all_recs)}</b>\n")
                    for i, rec in enumerate(all_recs, 1):
                        cc   = rec.get("country_code", "")
                        num  = rec.get("phone", "")
                        full = f"{cc}{num}" if cc and not num.startswith(cc.lstrip("+")) else num
                        lines.append(f"<b>#{i}</b>")
                        lines.append(f"📱 Phone: <code>{h(full)}</code>")
                        if cc:    lines.append(f"🔢 Country Code: <b>{h(cc)}</b>")
                        cntry = rec.get("country", "")
                        if cntry: lines.append(f"🌍 Country: <b>{h(cntry)}</b>")
                        fn = rec.get("first_name", "")
                        if fn:    lines.append(f"👤 Name: {h(fn)}")
                        tg = rec.get("total_groups")
                        if tg:    lines.append(f"👥 Groups: {h(str(tg))}")
                        if i < len(all_recs): lines.append("")
                else:
                    lines.append("\n📱 Phone: <b>Not found in database</b>")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                result = bq("\n".join(lines))

            elif pending == PENDING_USERNUM:
                uname = text.lstrip("@")
                info = await _fetch_userid_info(client, uname, is_username=True)
                all_recs = info.get("all_records", [])
                lines = [f"👤 <b>Username Lookup</b>\n\n👤 @{h(uname)}"]
                if all_recs:
                    lines.append(f"📊 Results: <b>{len(all_recs)}</b>\n")
                    for i, rec in enumerate(all_recs, 1):
                        cc   = rec.get("country_code", "")
                        num  = rec.get("phone", "")
                        full = f"{cc}{num}" if cc and not num.startswith(cc.lstrip("+")) else num
                        lines.append(f"<b>#{i}</b>")
                        lines.append(f"📱 Phone: <code>{h(full)}</code>")
                        if cc:    lines.append(f"🔢 Country Code: <b>{h(cc)}</b>")
                        cntry = rec.get("country", "")
                        if cntry: lines.append(f"🌍 Country: <b>{h(cntry)}</b>")
                        fn = rec.get("first_name", "")
                        if fn:    lines.append(f"👤 Name: {h(fn)}")
                        if i < len(all_recs): lines.append("")
                else:
                    lines.append("\n📱 Phone: <b>Not found</b>")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                result = bq("\n".join(lines))

            elif pending == PENDING_INDINFO:
                clean_num = re.sub(r'\D', '', text)
                META_KEYS  = {'status','success','error','message','msg','developer','dev','key','apikey','numbere','number','query','_raw','time','result','count','total','type','n','credit','searched_userid','response_time','code'}
                EMPTY_VALS = (None, '', 'N/A', 'None', 'null', 'undefined', 'false', 'False', 0)

                async def _ind_shadow():
                    try:
                        r2 = await client.get(PHONE_API_URL.format(clean_num), headers={"User-Agent": "Mozilla/5.0"})
                        return safe_json(r2, {})
                    except Exception:
                        return {}

                async def _ind_hitek():
                    try:
                        r2 = await client.get(HITEK_NUM_INFO_API_URL.format(clean_num), headers={"User-Agent": "Mozilla/5.0"})
                        return safe_json(r2, {})
                    except Exception:
                        return {}

                sd, hd = await asyncio.gather(_ind_shadow(), _ind_hitek())

                def _ind_extract(data):
                    inner = data.get("result") or {}
                    recs = []
                    if isinstance(inner, dict):
                        recs = inner.get("results") or inner.get("data") or []
                    if not recs:
                        recs = data.get("data") or []
                    if isinstance(recs, dict):
                        recs = [recs]
                    return [rec for rec in recs if isinstance(rec, dict) and any(
                        str(k).lower() not in META_KEYS and v not in EMPTY_VALS
                        for k, v in rec.items() if not isinstance(v, (dict, list))
                    )]

                real = _ind_extract(sd) + _ind_extract(hd)
                lines = [f"📱 <b>Indian Number Info</b>\n\n📞 Number: <code>{h(text)}</code>"]
                if real:
                    lines.append(f"📊 Records: <b>{len(real)}</b>\n")
                    for i, rec in enumerate(real[:5], 1):
                        lines.append(f"\n<b>Record {i}:</b>")
                        for k, v in rec.items():
                            if str(k).lower() not in META_KEYS and v not in EMPTY_VALS and not isinstance(v, (dict, list)):
                                lines.append(f"• {h(str(k).replace('_',' ').title())}: <b>{h(str(v))}</b>")
                else:
                    lines.append("❌ No data found.")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                result = bq("\n".join(lines))

            elif pending == PENDING_INSTAINFO:
                uname = text.lstrip("@")
                r = await client.get(INSTA_API_URL.format(uname), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                d = data.get("data") or data
                if isinstance(d, list) and d: d = d[0]
                if not isinstance(d, dict): d = data
                name     = d.get("name") or d.get("full_name") or ""
                bio      = d.get("bio") or ""
                followers= d.get("followers") or 0
                following= d.get("following") or 0
                posts    = d.get("posts") or 0
                private  = bool(d.get("private") or d.get("is_private"))
                verified = bool(d.get("verified"))
                pic      = d.get("pic") or ""
                result = bq(
                    f"📸 <b>Instagram Info</b>\n\n"
                    f"👤 @{h(uname)}\n"
                    f"📛 Name: <b>{h(name) if name else 'N/A'}</b>\n"
                    f"📝 Bio: {h(bio[:200]) if bio else 'N/A'}\n"
                    f"👥 Followers: <b>{h(str(followers))}</b>\n"
                    f"➡️ Following: <b>{h(str(following))}</b>\n"
                    f"📷 Posts: <b>{h(str(posts))}</b>\n"
                    f"🔒 Private: {'Yes' if private else 'No'}\n"
                    f"✅ Verified: {'Yes' if verified else 'No'}\n"
                    + (f"🖼 Pic: <a href='{pic}'>View</a>\n" if pic else "")
                    + f"\n👺 DEV @Shuvobhai ✅"
                )

            elif pending == PENDING_DOWNLOAD:
                r = await client.post(
                    "https://api.cobalt.tools/",
                    json={"url": text},
                    headers={"Accept": "application/json", "Content-Type": "application/json"}
                )
                data = safe_json(r)
                url = data.get("url") or data.get("audio")
                if url:
                    result = bq(f"📥 <b>Video Download</b>\n\n🔗 <a href='{url}'>Click to Download</a>\n\n👺 DEV @Shuvobhai ✅")
                else:
                    result = bq(f"❌ Could not fetch download link.\n\nResponse: {h(str(data)[:300])}\n\n👺 DEV @Shuvobhai ✅")

            elif pending == PENDING_PINCODE:
                r = await client.get(PINCODE_API_URL.format(text), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                post_offices = data.get("PostOffice") or []
                if post_offices:
                    po = post_offices[0]
                    result = bq(
                        f"📮 <b>Pincode Info</b>\n\n"
                        f"📌 Pincode: <code>{h(text)}</code>\n"
                        f"🏙 District: <b>{h(po.get('District','N/A'))}</b>\n"
                        f"🗺 State: <b>{h(po.get('State','N/A'))}</b>\n"
                        f"🏘 Area: <b>{h(po.get('Name','N/A'))}</b>\n"
                        f"📯 Division: {h(po.get('Division','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                else:
                    result = bq(f"❌ No data for pincode <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")

            elif pending == PENDING_IFSC:
                r = await client.get(IFSC_API_URL.format(text.upper()), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                if isinstance(data, dict) and (data.get("BANK") or data.get("bank")):
                    result = bq(
                        f"🏦 <b>IFSC Info</b>\n\n"
                        f"🔑 IFSC: <code>{h(data.get('IFSC') or text.upper())}</code>\n"
                        f"🏦 Bank: <b>{h(data.get('BANK') or data.get('bank','N/A'))}</b>\n"
                        f"🏢 Branch: {h(data.get('BRANCH') or data.get('branch','N/A'))}\n"
                        f"🏙 City: {h(data.get('CITY') or data.get('city','N/A'))}\n"
                        f"🗺 State: {h(data.get('STATE') or data.get('state','N/A'))}\n"
                        f"📍 Address: {h(data.get('ADDRESS') or data.get('address','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                else:
                    result = bq(f"❌ Invalid IFSC: <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")

            elif pending == PENDING_IPINFO:
                r = await client.get(f"{IP_API_BASE}/{text}")
                data = safe_json(r)
                result = bq(
                    f"🌐 <b>IP Info</b>\n\n"
                    f"🖥 IP: <code>{h(text)}</code>\n"
                    f"🌍 Country: <b>{h(data.get('country','N/A'))}</b>\n"
                    f"🏙 City: {h(data.get('city','N/A'))}\n"
                    f"🌐 ISP: {h(data.get('isp','N/A'))}\n"
                    f"🕐 Timezone: {h(data.get('timezone','N/A'))}\n"
                    f"📍 Lat/Lon: {h(data.get('lat','N/A'))}, {h(data.get('lon','N/A'))}\n\n"
                    f"👺 DEV @Shuvobhai ✅"
                )

            elif pending == PENDING_FFSTATS:
                ff_uid = re.sub(r'\D', '', text.split()[0])
                r = await client.get(f"{FFSTATS_API_BASE}?uid={ff_uid}", headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                basic = data.get("basicInfo", {})
                if not basic:
                    result = bq(f"📊 <b>FF Stats</b>\n\n🆔 UID: <code>{h(ff_uid)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                else:
                    result = bq(
                        f"📊 <b>FF Stats</b>\n\n"
                        f"🆔 UID: <code>{h(ff_uid)}</code>\n"
                        f"👤 Name: <b>{h(basic.get('nickname','N/A'))}</b>\n"
                        f"⭐ Level: {h(basic.get('level','N/A'))}\n"
                        f"🏆 Rank: {h(basic.get('rank','N/A'))}\n"
                        f"🌍 Region: {h(basic.get('region','N/A'))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )

            elif pending == PENDING_EMAILREP:
                r = await client.get(EMAIL_API_URL.format(urllib.parse.quote(text, safe="")), headers={"User-Agent": "Mozilla/5.0"})
                data = safe_json(r, {})
                SKIP_EM = {"success", "developer", "dev", "query", "email", "status", "key"}
                lines = [f"📧 <b>Email Lookup</b>\n\n📨 Email: <code>{h(text)}</code>"]
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k in SKIP_EM or isinstance(v, (dict, list)): continue
                        if v and str(v) not in ("None", "null", "N/A", "", "false", "False"):
                            lines.append(f"• {h(str(k).replace('_',' ').title())}: <b>{h(str(v))}</b>")
                if len(lines) == 1:
                    lines.append("❌ No data found for this email.")
                lines.append("\n👺 DEV @Shuvobhai ✅")
                result = bq("\n".join(lines))

            elif pending == PENDING_VEHICLE:
                clean_rc = re.sub(r'\s+', '', text).upper()
                if len(clean_rc) < 6:
                    result = bq(f"❌ Invalid RC number. Send like: <code>MH12AB1234</code>\n\n👺 DEV @Shuvobhai ✅")
                else:
                    r = await client.get(f"{VEHICLE_RC_API_BASE}/", params={"key": VEHICLE_RC_API_KEY, "rc": clean_rc})
                    data = safe_json(r, {})
                    if not data or data.get("error") or str(data.get("success", "true")).lower() == "false":
                        result = bq(f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(clean_rc)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                    else:
                        merged = {}
                        nested = data.get("data") or data.get("vehicle_data") or data.get("result") or {}
                        if isinstance(nested, dict): merged.update(nested)
                        SKIP_RC = {"data","vehicle_data","result","success","status","error","message","msg","developer","dev","key","n"}
                        for k, v in data.items():
                            if k not in SKIP_RC and not isinstance(v, (dict, list)): merged.setdefault(k, v)
                        FIELD_MAP = {"ownername":"Owner Name","number":"RC Number","address":"Address","makermodel":"Make/Model","modelname":"Model","fueltype":"Fuel Type","regdate":"Reg. Date","registeredrto":"RTO","class":"Vehicle Class","insurancecompany":"Insurance","insuranceupto":"Insurance Upto","fitnessupto":"Fitness Upto","taxupto":"Tax Upto","city":"City"}
                        lines = [f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(clean_rc)}</code>\n"]
                        for k, v in merged.items():
                            if v and str(v) not in ("None", "null", "N/A", ""):
                                label = FIELD_MAP.get(str(k).lower(), str(k).replace("_"," ").title())
                                lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        lines.append("\n👺 DEV @Shuvobhai ✅")
                        result = bq("\n".join(lines))

            elif pending == PENDING_WEATHER:
                geo_r = await client.get(GEOCODING_API_BASE, params={"name": text, "count": 1})
                geo_data = safe_json(geo_r).get("results", [])
                if not geo_data:
                    result = bq(f"❌ City not found: <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")
                else:
                    lat = geo_data[0]["latitude"]
                    lon = geo_data[0]["longitude"]
                    w_r = await client.get(WEATHER_API_BASE, params={
                        "latitude": lat, "longitude": lon,
                        "current_weather": True, "timezone": "auto"
                    })
                    w = safe_json(w_r).get("current_weather", {})
                    result = bq(
                        f"🌤 <b>Weather</b>\n\n"
                        f"🏙 City: <b>{h(geo_data[0].get('name',''))}, {h(geo_data[0].get('country',''))}</b>\n"
                        f"🌡 Temp: <b>{h(w.get('temperature','N/A'))}°C</b>\n"
                        f"💨 Wind: {h(w.get('windspeed','N/A'))} km/h\n"
                        f"🧭 Direction: {h(w.get('winddirection','N/A'))}°\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )

            elif pending == PENDING_UNIVERSITY:
                r = await client.get(UNIVERSITY_API_BASE, params={"country": text})
                data = safe_json(r, [])
                if data:
                    lines = [f"🎓 <b>Universities in {h(text)}</b>\n"]
                    for uni in data[:10]:
                        lines.append(f"• {h(uni.get('name',''))}")
                    if len(data) > 10:
                        lines.append(f"\n...and {len(data)-10} more")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))
                else:
                    result = bq(f"❌ No results for: <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")

            elif pending == PENDING_COUNTRY:
                r = await client.get(f"{COUNTRY_API_BASE}/{text}")
                data = safe_json(r, [])
                if isinstance(data, list) and data:
                    c = data[0]
                    cap = ", ".join(c.get("capital", ["N/A"]))
                    langs = ", ".join(c.get("languages", {}).values())
                    result = bq(
                        f"🌍 <b>Country Info</b>\n\n"
                        f"🏳 Name: <b>{h(c.get('name',{}).get('common','N/A'))}</b>\n"
                        f"🗺 Region: {h(c.get('region','N/A'))}\n"
                        f"🏙 Capital: {h(cap)}\n"
                        f"👥 Population: {h('{:,}'.format(c.get('population',0)))}\n"
                        f"🗣 Languages: {h(langs)}\n"
                        f"💰 Currency: {h(', '.join(c.get('currencies',{}).keys()))}\n"
                        f"🌐 TLD: {h(', '.join(c.get('tld',['N/A'])))}\n\n"
                        f"👺 DEV @Shuvobhai ✅"
                    )
                else:
                    result = bq(f"❌ Country not found: <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")

            elif pending == PENDING_AADHAR:
                clean_aadhar = re.sub(r'\s+', '', text)
                if not re.match(r'^\d{12}$', clean_aadhar):
                    result = bq(f"❌ Invalid Aadhar number. Must be 12 digits.\n\n👺 DEV @Shuvobhai ✅")
                else:
                    r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "aadhar", "query": clean_aadhar, "key": SHADOW_API_KEY})
                    data = safe_json(r, {})
                    results_obj = data.get("results") or {}
                    records = (results_obj.get("data") or []) if isinstance(results_obj, dict) else []
                    if not records:
                        result = bq(f"🪪 <b>Aadhar Info</b>\n\n📋 Aadhar: <code>{h(clean_aadhar)}</code>\n❌ No records found.\n\n👺 DEV @Shuvobhai ✅")
                    else:
                        lines = [f"🪪 <b>Aadhar Info</b>\n\n📋 Aadhar: <code>{h(clean_aadhar)}</code>\n📊 Records: <b>{len(records)}</b>\n"]
                        for i, rec in enumerate(records[:3], 1):
                            if isinstance(rec, dict):
                                lines.append(f"\n<b>Record {i}:</b>")
                                for k, v in rec.items():
                                    if v and str(v) not in ("None", "null", "N/A", ""):
                                        lines.append(f"• {h(str(k).replace('_',' ').title())}: <b>{h(str(v))}</b>")
                        lines.append("\n👺 DEV @Shuvobhai ✅")
                        result = bq("\n".join(lines))

            elif pending == PENDING_GST:
                clean_gst = text.upper().strip()
                r = await client.get(f"{GST_API_BASE}/", params={"number": clean_gst, "key": GST_API_KEY})
                data = safe_json(r, {})
                if isinstance(data, list): data = data[0] if data else {}
                if not data or data.get("error") or str(data.get("status", "")).lower() in ("error", "fail"):
                    result = bq(f"💼 <b>GST Info</b>\n\n🔎 GSTIN: <code>{h(clean_gst)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                else:
                    SKIP_GST = {"success","developer","dev","msg","message","n","gstin","gstNumber"}
                    KEY_MAP = {"legalNameOfBusiness":"Legal Name","tradeName":"Trade Name","registrationDate":"Reg. Date","taxPayerType":"Taxpayer","gstStatus":"Status","constitutionOfBusiness":"Biz Type","principalPlaceOfBusiness":"Address","stateJurisdiction":"State","pan":"PAN"}
                    lines = [f"💼 <b>GST Info</b>\n\n🔎 GSTIN: <code>{h(clean_gst)}</code>\n"]
                    for k, v in data.items():
                        if k.lower() in {s.lower() for s in SKIP_GST} or isinstance(v, (dict, list)): continue
                        if v and str(v) not in ("None", "null", "N/A", ""):
                            label = KEY_MAP.get(k, str(k).replace("_"," ").title())
                            lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))

            elif pending == PENDING_PAN:
                clean_pan = text.upper().strip()
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "pan", "query": clean_pan, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                name = data.get("fullname") or data.get("name") or ""
                if not name:
                    result = bq(f"🪪 <b>PAN Info</b>\n\n📋 PAN: <code>{h(clean_pan)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                else:
                    lines = [f"🪪 <b>PAN Info</b>\n\n📋 PAN: <code>{h(clean_pan)}</code>\n👤 Name: <b>{h(name)}</b>"]
                    SKIP_PAN = {"fullname","name","pan","success","message","developer","dev"}
                    for k, v in data.items():
                        if k in SKIP_PAN: continue
                        if v and str(v) not in ("None", "null", "N/A", ""):
                            lines.append(f"• {h(str(k).replace('_',' ').title())}: <b>{h(str(v))}</b>")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))

            elif pending == PENDING_PAKNUM:
                clean_num = re.sub(r'[^\d]', '', text)
                r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "pak_num", "query": clean_num, "key": SHADOW_API_KEY})
                data = safe_json(r, {})
                records = data.get("data") or []
                if not records:
                    result = bq(f"🇵🇰 <b>Pakistan Number Info</b>\n\n📱 Number: <code>{h(clean_num)}</code>\n❌ No records found.\n\n👺 DEV @Shuvobhai ✅")
                else:
                    lines = [f"🇵🇰 <b>Pakistan Number Info</b>\n\n📱 Number: <code>{h(clean_num)}</code>\n📊 Records: <b>{len(records)}</b>\n"]
                    for i, rec in enumerate(records[:3], 1):
                        if isinstance(rec, dict):
                            lines.append(f"\n<b>Record {i}:</b>")
                            for k, v in rec.items():
                                if v and str(v) not in ("None", "null", "N/A", "", "0"):
                                    lines.append(f"• {h(str(k).replace('_',' ').title())}: <b>{h(str(v))}</b>")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))

            elif pending == PENDING_VEHICLE_RC:
                clean_rc = re.sub(r'\s+', '', text).upper()
                if len(clean_rc) < 8:
                    result = bq(f"❌ Invalid RC number: <code>{h(text)}</code>\n\n👺 DEV @Shuvobhai ✅")
                else:
                    r = await client.get(f"{VEHICLE_RC_API_BASE}/", params={"key": VEHICLE_RC_API_KEY, "rc": clean_rc})
                    data = safe_json(r, {})
                    if not data or data.get("error") or str(data.get("success", "true")).lower() == "false":
                        result = bq(f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(clean_rc)}</code>\n❌ No data found.\n\n👺 DEV @Shuvobhai ✅")
                    else:
                        merged = {}
                        nested = data.get("data") or data.get("vehicle_data") or data.get("result") or {}
                        if isinstance(nested, dict): merged.update(nested)
                        SKIP_RC = {"data","vehicle_data","result","success","status","error","message","msg","developer","dev","key","n"}
                        for k, v in data.items():
                            if k not in SKIP_RC and not isinstance(v, (dict, list)): merged.setdefault(k, v)
                        FIELD_MAP = {"ownername":"Owner Name","number":"RC Number","address":"Address","makermodel":"Make/Model","modelname":"Model","fueltype":"Fuel Type","regdate":"Reg. Date","registeredrto":"RTO","class":"Vehicle Class","insurancecompany":"Insurance","insuranceupto":"Insurance Upto","fitnessupto":"Fitness Upto","taxupto":"Tax Upto","city":"City"}
                        lines = [f"🚗 <b>Vehicle RC Info</b>\n\n🔎 RC: <code>{h(clean_rc)}</code>\n"]
                        for k, v in merged.items():
                            if v and str(v) not in ("None", "null", "N/A", ""):
                                label = FIELD_MAP.get(str(k).lower(), str(k).replace("_"," ").title())
                                lines.append(f"• {h(label)}: <b>{h(str(v))}</b>")
                        lines.append("\n👺 DEV @Shuvobhai ✅")
                        result = bq("\n".join(lines))

            elif pending == PENDING_UPI:
                upi = text.strip()
                if "@" not in upi:
                    result = bq(f"❌ Invalid UPI ID. Example: <code>name@paytm</code>\n\n👺 DEV @Shuvobhai ✅")
                else:
                    r = await client.get(f"{SHADOW_API_BASE}/", params={"type": "upi", "query": upi, "key": SHADOW_API_KEY})
                    data = safe_json(r, {})
                    res      = data.get("result") or {}
                    primary  = res.get("primary") or {}
                    secondary= res.get("secondary") or {}
                    user_det = secondary.get("user_details") or {}
                    name     = primary.get("recipientBankAccountName") or user_det.get("name") or ""
                    vpa      = primary.get("recipientVpa") or user_det.get("vpa") or upi
                    valid    = "✅ Valid" if primary.get("validVpa") else "❌ Invalid"
                    merchant = "✅ Yes" if primary.get("isMerchant") else "❌ No"
                    ifsc     = res.get("extracted_ifsc") or user_det.get("ifsc") or ""
                    acc_type = primary.get("accountType") or ""
                    lines = [
                        f"💳 <b>UPI Info</b>\n",
                        f"📋 UPI ID: <code>{h(vpa)}</code>",
                        f"👤 Name: <b>{h(name) if name else 'N/A'}</b>",
                        f"✅ Status: <b>{valid}</b>",
                        f"🏪 Merchant: <b>{merchant}</b>",
                    ]
                    if acc_type: lines.append(f"🏦 Account Type: <b>{h(acc_type)}</b>")
                    if ifsc:     lines.append(f"🏦 IFSC: <code>{h(ifsc)}</code>")
                    lines.append("\n👺 DEV @Shuvobhai ✅")
                    result = bq("\n".join(lines))

            elif pending == PENDING_VOICE:
                lang_code = context.user_data.pop("voice_lang", "")
                voice     = VOICE_MAP.get(lang_code, VOICE_DEFAULT)
                if not text:
                    await sent.edit_text(bq("❌ No text found."), parse_mode="HTML")
                    schedule_delete(sent); return
                await sent.edit_text(bq("🎙 Converting to voice..."), parse_mode="HTML")
                try:
                    await _send_voice_reply(update, text, voice)
                    await sent.delete()
                except Exception as e:
                    await sent.edit_text(bq(f"❌ Voice convert failed: {h(str(e)[:200])}\n\n👺 DEV @Shuvobhai ✅"), parse_mode="HTML")
                    schedule_delete(sent)
                return

            else:
                result = bq("❓ Unknown action.")

        await sent.edit_text(result, parse_mode="HTML", reply_markup=after_result_keyboard())
    except Exception as e:
        _error_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {pending}: {str(e)[:200]}")
        if len(_error_log) > 50:
            _error_log.pop(0)
        await sent.edit_text(bq(f"❌ Error: {h(str(e)[:300])}\n\n💡 Try /ai to ask me to fix this!\n\n👺 DEV @Shuvobhai ✅"), parse_mode="HTML")

    schedule_delete(sent)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user, _ = get_user(users, update.effective_user.id)
    if not user["is_admin"]:
        sent = await update.message.reply_text(bq("⛔ Admin only."), parse_mode="HTML")
        schedule_delete(sent); return
    sent = await update.message.reply_text(bq("🛠 <b>Admin Panel</b>"), reply_markup=admin_keyboard(), parse_mode="HTML")
    schedule_delete(sent)

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast",   callback_data="admin_broadcast")],
        [InlineKeyboardButton("💎 Gen Credits", callback_data="admin_gen")],
        [InlineKeyboardButton("🎫 Make Code",   callback_data="admin_mkcode")],
        [InlineKeyboardButton("⛔ Ban",          callback_data="admin_ban"),
         InlineKeyboardButton("✅ Unban",        callback_data="admin_unban")],
        [InlineKeyboardButton("👑 Add Admin",   callback_data="admin_addadmin")],
    ])

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user, _ = get_user(users, update.effective_user.id)
    if not user["is_admin"]: return
    if not context.args:
        sent = await update.message.reply_text(bq("Usage: /broadcast &lt;message&gt;"), parse_mode="HTML")
        schedule_delete(sent); return
    text = " ".join(context.args)
    admin_uid = str(update.effective_user.id)
    sent_count = 0
    for uid, u in users.items():
        if not u["banned"]:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 {text}")
                sent_count += 1
            except Exception:
                pass
    write_log(f"[BROADCAST] Admin {admin_uid} sent broadcast to {sent_count} users: {text[:80]}")
    sent = await update.message.reply_text(bq(f"✅ Broadcast sent to <b>{sent_count}</b> users."), parse_mode="HTML")
    schedule_delete(sent)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if user["banned"]:
        sent = await update.message.reply_text(bq("⛔ You are banned."), parse_mode="HTML"); schedule_delete(sent); return
    if not context.args:
        sent = await update.message.reply_text(bq("Usage: /redeem &lt;code&gt;\nExample: <code>/redeem SHUVO_abc123</code>"), parse_mode="HTML")
        schedule_delete(sent); return
    code_str = context.args[0].strip()
    codes = load_codes()
    if code_str not in codes:
        sent = await update.message.reply_text(bq("❌ Invalid code."), parse_mode="HTML"); schedule_delete(sent); return
    code = codes[code_str]
    if code.get("expires_at"):
        if datetime.now() > datetime.fromisoformat(code["expires_at"]):
            sent = await update.message.reply_text(bq("❌ This code has expired."), parse_mode="HTML"); schedule_delete(sent); return
    if uid in code.get("used_by", []):
        sent = await update.message.reply_text(bq("❌ You have already used this code."), parse_mode="HTML"); schedule_delete(sent); return
    credits = code["credits"]
    user["credits"] += credits
    code.setdefault("used_by", []).append(uid)
    save_users(users)
    save_codes(codes)
    write_log(f"[REDEEM] User {uid} redeemed code {code_str} for +{credits} credits (balance: {user['credits']})")
    sent = await update.message.reply_text(
        bq(f"✅ <b>Code redeemed!</b>\n🎁 +{credits} credits added.\n💰 Balance: <b>{user['credits']}</b>\n\n👺 DEV @Shuvobhai ✅"),
        parse_mode="HTML"
    )
    schedule_delete(sent)

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    admin, _ = get_user(users, update.effective_user.id)
    if not admin["is_admin"]: return
    if len(context.args) < 2:
        sent = await update.message.reply_text(bq("Usage: /gen &lt;user_id or @username&gt; &lt;amount&gt;"), parse_mode="HTML")
        schedule_delete(sent); return
    raw_target = context.args[0]
    try:
        amount = int(context.args[1])
    except ValueError:
        sent = await update.message.reply_text(bq("❌ Amount must be a number."), parse_mode="HTML"); schedule_delete(sent); return
    if raw_target.startswith("@") or not raw_target.isdigit():
        target, target_id = find_user_by_username(users, raw_target)
        if target is None:
            sent = await update.message.reply_text(bq("❌ User not found."), parse_mode="HTML"); schedule_delete(sent); return
    else:
        target_id = raw_target
        target, _ = get_user(users, target_id)
    target["credits"] += amount
    save_users(users)
    write_log(f"[GEN] Admin {str(update.effective_user.id)} added {amount} credits to user {target_id} (balance: {target['credits']})")
    sent = await update.message.reply_text(bq(f"✅ Added <b>{amount}</b> credits.\n💰 New balance: <b>{target['credits']}</b>"), parse_mode="HTML")
    schedule_delete(sent)

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    admin, admin_uid = get_user(users, update.effective_user.id)
    if not admin["is_admin"]: return
    if not context.args:
        sent = await update.message.reply_text(bq("Usage: /ban &lt;user_id&gt;"), parse_mode="HTML"); schedule_delete(sent); return
    target_id = context.args[0]
    target, _ = get_user(users, target_id)
    target["banned"] = True
    save_users(users)
    write_log(f"[BAN] Admin {admin_uid} banned user {target_id}")
    sent = await update.message.reply_text(bq(f"⛔ User <code>{h(target_id)}</code> banned."), parse_mode="HTML")
    schedule_delete(sent)

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    admin, admin_uid = get_user(users, update.effective_user.id)
    if not admin["is_admin"]: return
    if not context.args:
        sent = await update.message.reply_text(bq("Usage: /unban &lt;user_id&gt;"), parse_mode="HTML"); schedule_delete(sent); return
    target_id = context.args[0]
    target, _ = get_user(users, target_id)
    target["banned"] = False
    save_users(users)
    write_log(f"[UNBAN] Admin {admin_uid} unbanned user {target_id}")
    sent = await update.message.reply_text(bq(f"✅ User <code>{h(target_id)}</code> unbanned."), parse_mode="HTML")
    schedule_delete(sent)

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    admin, admin_uid = get_user(users, update.effective_user.id)
    if not admin["is_admin"]: return
    if not context.args:
        sent = await update.message.reply_text(bq("Usage: /addadmin &lt;user_id&gt;"), parse_mode="HTML"); schedule_delete(sent); return
    target_id = context.args[0]
    target, _ = get_user(users, target_id)
    target["is_admin"] = True
    save_users(users)
    write_log(f"[ADDADMIN] Admin {admin_uid} promoted user {target_id} to admin")
    sent = await update.message.reply_text(bq(f"👑 User <code>{h(target_id)}</code> is now admin."), parse_mode="HTML")
    schedule_delete(sent)


def _db_page_text(page: int) -> str:
    dbs = load_databases()
    total = len(dbs)
    total_pages = max(1, (total + DB_PAGE_SIZE - 1) // DB_PAGE_SIZE)
    start = page * DB_PAGE_SIZE
    end   = min(start + DB_PAGE_SIZE, total)
    lines = [f"🗄 <b>Available Databases</b>  [{page+1}/{total_pages}]",
             f"📊 Total: <b>{total:,}</b>\n"]
    dbs_list = dbs if isinstance(dbs, list) else list(dbs.values())
    for i, db in enumerate(dbs_list[start:end], start=start+1):
        title = db.get("title") or db.get("name") or str(db)[:50] if isinstance(db, dict) else str(db)[:50]
        lines.append(f"<b>{i}.</b> {h(title)}")
    return "\n".join(lines)

def _db_page_keyboard(page: int) -> InlineKeyboardMarkup:
    dbs = load_databases()
    dbs_list = dbs if isinstance(dbs, list) else list(dbs.values())
    total_pages = max(1, (len(dbs_list) + DB_PAGE_SIZE - 1) // DB_PAGE_SIZE)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"db_page_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"db_page_{page+1}"))
    rows = []
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🏠 Main Menu", callback_data="back_home")])
    return InlineKeyboardMarkup(rows)

async def databases_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent = await update.message.reply_text(bq(_db_page_text(0)), parse_mode="HTML", reply_markup=_db_page_keyboard(0))
    schedule_delete(sent)


async def app_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    user, _ = get_user(users, update.effective_user.id)
    if not user["is_admin"]:
        sent = await update.message.reply_text(bq("⛔ Admin only."), parse_mode="HTML"); schedule_delete(sent); return
    if not context.args or context.args[0].lower() not in ("on", "off"):
        sent = await update.message.reply_text(bq("Usage: <code>/app on</code> or <code>/app off</code>"), parse_mode="HTML")
        schedule_delete(sent); return
    chat_id = str(update.effective_chat.id)
    action  = context.args[0].lower()
    cfg     = load_config()
    chats   = cfg.get("autoapprove_chats", [])
    if action == "on":
        if chat_id not in chats: chats.append(chat_id)
        cfg["autoapprove_chats"] = chats; save_config(cfg)
        sent = await update.message.reply_text(bq(f"✅ <b>Auto-Approve ON</b>\n🆔 Chat: <code>{chat_id}</code>"), parse_mode="HTML")
    else:
        if chat_id in chats: chats.remove(chat_id)
        cfg["autoapprove_chats"] = chats; save_config(cfg)
        sent = await update.message.reply_text(bq(f"🔴 <b>Auto-Approve OFF</b>\n🆔 Chat: <code>{chat_id}</code>"), parse_mode="HTML")
    schedule_delete(sent)


async def auto_approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_autoapprove(update.chat_join_request.chat.id):
        asyncio.create_task(_do_approve(update.chat_join_request))

async def _do_approve(req):
    try:
        await req.approve()
    except Exception:
        pass


_SERVICE_FEATURE_MAP = {
    "service_tgid":       "tgid",
    "service_tguser":     "tguser",
    "service_indinfo":    "indinfo",
    "service_instainfo":  "instainfo",
    "service_viddown":    "viddown",
    "service_pincode":    "pincode",
    "service_ifsc":       "ifsc",
    "service_ipinfo":     "ipinfo",
    "service_ffstats":    "ffstats",
    "service_emailrep":   "emailrep",
    "service_vehicle":    "vehicle",
    "service_weather":    "weather",
    "service_nasa_apod":  "nasa",
    "service_nasa_epic":  "nasa",
    "service_aadhar":     "aadhar",
    "service_gst":        "gst",
    "service_pan":        "pan",
    "service_paknum":     "paknum",
    "service_vehicle_rc": "vehicle_rc",
    "service_upi":        "upi",
    "service_makeaadhar": "makeaadhar",
    "service_imagegen":   "imagegen",
    "service_musicgen":   "music",
    "service_videogen":   "videogen",
    "service_sprite":     "sprite",
    "service_model3d":    "model3d",
    "service_editimage":  "editimage",
    "service_ai":         "ai_chat",
    "service_voice":      "voice",
    "daily_claim":        "daily_claim",
}

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data  = query.data
    users = load_users()
    user, uid = get_user(users, query.from_user.id, query.from_user.username or "")

    if is_paused() and not user.get("is_admin"):
        await query.answer("🔧 Bot under maintenance.", show_alert=True)
        return

    if data in _SERVICE_FEATURE_MAP and not user.get("is_admin"):
        feat = _SERVICE_FEATURE_MAP[data]
        if not is_enabled(feat):
            await query.answer("❌ This feature is currently disabled.", show_alert=True)
            return

    if data.startswith("log_dm_"):
        await query.answer()
        if str(query.from_user.id) != str(ADMIN_ID):
            await query.answer("❌ Only bot owner can do this.", show_alert=True)
            return
        target_uid = data[7:]
        _pending_dm_reply[str(query.from_user.id)] = target_uid
        try:
            await context.bot.send_message(
                chat_id=int(ADMIN_ID),
                text=(
                    f"💬 <b>DM Reply Mode Active</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📤 Your next message will be sent to:\n"
                    f"🆔 User ID: <code>{target_uid}</code>\n\n"
                    f"➤ Send your message now.\n"
                    f"➤ Or /cancel to abort."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        await query.answer("✅ Go to bot DM and send your message!", show_alert=True)
        return

    if data == "back_home":
        await query.answer()
        context.user_data["pending"] = PENDING_NONE
        try:
            await query.message.delete()
        except Exception:
            pass
        sent = await _send_menu_photo(query, user, uid)
        schedule_delete(sent)

    elif data == "daily_claim":
        now = datetime.now()
        last = user.get("last_claim")
        if last:
            diff = (now - datetime.fromisoformat(last)).total_seconds()
            if diff < 86400:
                rem = int(86400 - diff)
                h_rem = rem // 3600
                m_rem = (rem % 3600) // 60
                await query.answer(f"⏳ Next claim in {h_rem}h {m_rem}m", show_alert=True)
                return
        users = load_users()
        user, uid = get_user(users, query.from_user.id, query.from_user.username or "")
        user["credits"] += 3
        user["last_claim"] = now.isoformat()
        save_users(users)
        await query.answer("🎁 +3 credits claimed!", show_alert=True)
        try:
            await query.edit_message_caption(
                caption=main_menu_text(user, uid) + "\n\n🎁 <b>+3 credits claimed!</b>",
                reply_markup=build_menu_page(0, user["is_admin"]),
                parse_mode="HTML"
            )
        except Exception:
            pass

    elif data.startswith("menu_page_"):
        page = int(data.split("_")[-1])
        await query.answer()
        try:
            await query.edit_message_reply_markup(reply_markup=build_menu_page(page, user["is_admin"]))
        except Exception:
            pass

    elif data == "check_balance":
        cred = credit_display(user)
        role = get_role(user, uid)
        await query.answer(f"{role}\n💰 Credits: {cred}", show_alert=True)

    elif data.startswith("db_page_"):
        page = int(data.split("_")[-1])
        await query.answer()
        try:
            await query.edit_message_text(bq(_db_page_text(page)), parse_mode="HTML", reply_markup=_db_page_keyboard(page))
        except Exception:
            pass

    elif data == "service_databases":
        await query.answer()
        try:
            await query.edit_message_text(bq(_db_page_text(0)), parse_mode="HTML", reply_markup=_db_page_keyboard(0))
        except Exception:
            sent = await query.message.reply_text(bq(_db_page_text(0)), parse_mode="HTML", reply_markup=_db_page_keyboard(0))
            schedule_delete(sent)

    elif data == "service_aadhar":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_AADHAR
        sent = await query.message.reply_text(bq("🪪 <b>Aadhar Info Lookup</b>\n\nSend 12-digit Aadhar number:\nExample: <code>123456789012</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_gst":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_GST
        sent = await query.message.reply_text(bq("💼 <b>GST Info Lookup</b>\n\nSend GSTIN number:\nExample: <code>10DJCPK4351Q1Z5</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_pan":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_PAN
        sent = await query.message.reply_text(bq("🪪 <b>PAN Card Info Lookup</b>\n\nSend PAN number:\nExample: <code>AAMTS3432L</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_paknum":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_PAKNUM
        sent = await query.message.reply_text(bq("🇵🇰 <b>Pakistan Number Lookup</b>\n\nSend Pakistan mobile number:\nExample: <code>03001234567</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_vehicle_rc":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_VEHICLE_RC
        sent = await query.message.reply_text(bq("🚗 <b>Vehicle RC Lookup</b>\n\nSend vehicle RC number:\nExample: <code>MH12AB1234</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_upi":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        context.user_data["pending"] = PENDING_UPI
        sent = await query.message.reply_text(bq("💳 <b>UPI Info Lookup</b>\n\nSend UPI ID:\nExample: <code>name@paytm</code>\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)

    elif data == "service_makeaadhar":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] <= 0:
            await query.answer("❌ Insufficient credits.", show_alert=True); return
        _makeaadhar_state[str(query.from_user.id)] = {}
        context.user_data["pending"] = PENDING_MAKEAADHAR_NAME
        sent = await query.message.reply_text(
            bq(
                "🪪 <b>Aadhaar Card Generator</b>\n\n"
                "┌─────────────────────────┐\n"
                "│  Step <b>1 / 6</b> — Full Name  │\n"
                "└─────────────────────────┘\n\n"
                "Person er <b>full name</b> likho:\n"
                "Example: <code>Rahul Kumar</code>\n\n"
                "/cancel to go back."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data.startswith("aadhar_gen_"):
        await query.answer()
        gender_val = data.replace("aadhar_gen_", "")
        uid2 = str(query.from_user.id)
        _makeaadhar_state.setdefault(uid2, {})["gender"] = gender_val
        context.user_data["pending"] = PENDING_MAKEAADHAR_NUM
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        sent = await query.message.reply_text(
            bq(
                f"✅ Gender: <b>{gender_val}</b>\n\n"
                "┌───────────────────────────────────┐\n"
                "│  Step <b>4 / 6</b> — Aadhaar Card Number  │\n"
                "└───────────────────────────────────┘\n\n"
                "12-digit Aadhaar number pathao:\n"
                "Example: <code>1234 5678 9012</code>\n\n"
                "/cancel to cancel."
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_nasa_apod":
        await query.answer()
        if user["banned"]: return
        sent = await query.message.reply_text(bq("🚀 Fetching NASA APOD..."), parse_mode="HTML")
        await _do_nasa_apod(sent)

    elif data == "service_nasa_epic":
        await query.answer()
        if user["banned"]: return
        sent = await query.message.reply_text(bq("🌍 Fetching NASA EPIC..."), parse_mode="HTML")
        await _do_nasa_epic(sent)

    elif data == "admin_panel":
        await query.answer()
        if not user["is_admin"]:
            await query.answer("Access denied.", show_alert=True); return
        try:
            await query.edit_message_text(bq("🛠 <b>Admin Panel</b>"), reply_markup=admin_keyboard(), parse_mode="HTML")
        except Exception:
            pass

    elif data == "service_imagegen":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 3:
            await query.answer("❌ Need 3 credits. Check /balance.", show_alert=True); return
        context.user_data["pending"] = "imagegen_prompt"
        sent = await query.message.reply_text(
            bq("🌈 <b>AI Image Generation</b>\n\nSend a prompt:\n<i>Example: a cyberpunk city at night</i>\n\nCost: <b>3 Credits</b>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_musicgen":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 5:
            await query.answer("❌ Need 5+ credits.", show_alert=True); return
        context.user_data["pending"] = "music_prompt"
        sent = await query.message.reply_text(
            bq("🎧 <b>AI Music Generation</b>\n\nSend a prompt:\n<i>Example: epic battle orchestral --sec 30</i>\n\nCost: <b>5+ Credits</b> (based on duration)"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_videogen":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 50:
            await query.answer("❌ Need 50 credits.", show_alert=True); return
        context.user_data["pending"] = "videogen_prompt"
        sent = await query.message.reply_text(
            bq("🎞️ <b>AI Video Generation</b>\n\nSend a prompt:\n<i>Example: a dragon flying over mountains</i>\n\nCost: <b>50 Credits</b>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_sprite":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 3:
            await query.answer("❌ Need 3 credits.", show_alert=True); return
        context.user_data["pending"] = "sprite_prompt"
        sent = await query.message.reply_text(
            bq("👾 <b>Sprite Generation</b>\n\nSend a prompt:\n<i>Example: pixel art warrior facing right</i>\n\nCost: <b>3 Credits</b>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_model3d":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 190:
            await query.answer("❌ Need 190 credits.", show_alert=True); return
        context.user_data["pending"] = "model3d_prompt"
        sent = await query.message.reply_text(
            bq("🧊 <b>3D Model Generation</b>\n\nSend a prompt:\n<i>Example: a medieval castle tower</i>\n\nCost: <b>190 Credits</b>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_editimage":
        await query.answer()
        if user["banned"]: return
        if not user.get("is_admin") and user["credits"] < 10:
            await query.answer("❌ Need 10 credits.", show_alert=True); return
        sent = await query.message.reply_text(
            bq("🖌️ <b>Edit Image</b>\n\nReply to a photo with:\n<code>/editimage make the background sunset</code>\n\nCost: <b>10 Credits</b>"),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "verify_join":
        await query.answer()
        unjoined = await check_force_join(context.bot, query.from_user.id)
        if unjoined:
            names = "\n".join(f"  🔹 <b>{h(ch['title'])}</b>" for ch in unjoined)
            try:
                await query.edit_message_text(
                    bq(
                        f"❌ <b>Not Verified!</b>\n\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"You still haven't joined:\n\n"
                        f"{names}\n\n"
                        f"Please join them all, then tap <b>✅ Verify</b> again."
                    ),
                    reply_markup=force_join_keyboard(unjoined),
                    parse_mode="HTML"
                )
            except Exception:
                pass
        else:
            try:
                await query.message.delete()
            except Exception:
                pass
            users_inner = load_users()
            user_inner, uid_inner = get_user(users_inner, query.from_user.id,
                                             query.from_user.username or "",
                                             query.from_user.first_name or "")
            sent = await _send_menu_photo(query, user_inner, uid_inner,
                                          extra="\n\n<blockquote>✅ <b>Verified!</b> Welcome to SHUVO BOT!</blockquote>")
            schedule_delete(sent)

    elif data == "service_ai":
        await query.answer()
        if user["banned"]: return
        sent = await query.message.reply_text(
            bq(
                "🤖 <b>AI Chat — SHUVO SUPER AI</b>\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "💬  Just type <code>/ai your message</code>\n\n"
                "🔥  <b>What I can do:</b>\n"
                "┣  Answer any question\n"
                "┣  Run OSINT lookups for you\n"
                "┣  Check IPs, TG IDs, weather &amp; more\n"
                "┗  Generate images on command\n\n"
                "💡  <i>Example: /ai check ip 8.8.8.8</i>\n\n"
                "✨  Powered by LLaMA 3.3 70B (Groq)\n"
                "👺 DEV @Shuvobhai ✅"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_voice":
        await query.answer()
        if user["banned"]: return
        sent = await query.message.reply_text(
            bq(
                "🎙️ <b>Voice TTS</b>\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "Convert any text to speech!\n\n"
                "📝  Usage: <code>/voice [lang] text</code>\n\n"
                "🌍  <b>Language codes:</b>\n"
                "┣  <code>en</code> — English\n"
                "┣  <code>bd</code> — Bangla\n"
                "┣  <code>hi</code> — Hindi\n"
                "┣  <code>ar</code> — Arabic\n"
                "┗  <code>ur</code> — Urdu  + more\n\n"
                "💡  <i>Example: /voice bd আমি ভালো আছি</i>\n\n"
                "👺 DEV @Shuvobhai ✅"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "service_help":
        await query.answer()
        users_data = load_users()
        user_obj, uid_str = get_user(users_data, query.from_user.id)
        await help_command.__wrapped__(query, context) if hasattr(help_command, "__wrapped__") else None
        text = bq(
            "╔══════════════════════════╗\n"
            "   📋 <b>SHUVO BOT — ALL FEATURES</b>\n"
            "╚══════════════════════════╝\n\n"
            "🤖 <b>AI TOOLS</b>  <i>(Always FREE)</i>\n"
            "┣ /ai — Super AI agent · does everything\n"
            "┣ /image — AI image gen (free)\n"
            "┣ /nasaapod — NASA pic of the day\n"
            "┗ /nasaepic — NASA Earth live view\n\n"
            "🕵️ <b>OSINT TOOLS</b>  <i>(1 credit each)</i>\n"
            "┣ /userid — TG User ID → Phone\n"
            "┣ /usernum — TG Username → Phone\n"
            "┣ /indinfo — Indian number info\n"
            "┣ /instainfo — Instagram profile\n"
            "┣ /ipinfo — IP address lookup\n"
            "┣ /emailrep — Email reputation\n"
            "┣ /ffstats — Free Fire stats\n"
            "┗ /download — Video downloader\n\n"
            "🇮🇳 <b>INDIA / PAK LOOKUP</b>  <i>(1 credit each)</i>\n"
            "┣ /aadhar — Aadhaar number info\n"
            "┣ /makeaadhar — 🪪 Make Aadhaar Card\n"
            "┣ /gst — GST info  ┃ /pan — PAN info\n"
            "┣ /pincode — Pincode  ┃ /ifsc — IFSC\n"
            "┣ /vehicle — Vehicle  ┃ /vehiclerc — RC\n"
            "┣ /upi — UPI info  ┃ /paknum — Pak Num\n"
            "┗ /weather — Weather by city\n\n"
            "🎨 <b>AI CREATION STUDIO</b>  <i>(Credits)</i>\n"
            "┣ /imagegen <code>3cr</code>  ┃ /music <code>5cr</code>\n"
            "┣ /videogen <code>50cr</code>  ┃ /sprite <code>3cr</code>\n"
            "┣ /model3d <code>190cr</code>  ┃ /editimage <code>10cr</code>\n"
            "┗ /voice <code>1cr</code> — Text to speech\n\n"
            "💰 <b>ACCOUNT</b>\n"
            "┣ /start — Daily +3 credits claim\n"
            "┣ /balance — Profile &amp; credits\n"
            "┗ /redeem — Redeem gift code\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <b>Tip:</b> /ai runs ANY feature for you!\n"
            "<i>Say: \"lookup IP 8.8.8.8\" or \"make aadhaar\"</i>\n\n"
            "👺 DEV @Shuvobhai ✅"
        )
        sent = await query.message.reply_text(text, parse_mode="HTML")
        schedule_delete(sent)

    elif data == "admin_mkcode":
        await query.answer()
        if not user["is_admin"]: return
        context.user_data["pending"] = PENDING_MKCODE_CREDITS
        sent = await query.message.reply_text(
            bq(
                "🎫 <b>Create Redeem Code</b>\n\n"
                "<b>Step 1/3</b> — 💎 Credits\n"
                "How many credits to give?\n\n"
                "<i>Example: <code>10</code></i>"
            ),
            parse_mode="HTML"
        )
        schedule_delete(sent)

    elif data == "admin_broadcast":
        await query.answer()
        if not user["is_admin"]: return
        context.user_data["pending"] = PENDING_BROADCAST
        sent = await query.message.reply_text(bq("📢 <b>Broadcast</b>\n\nType your message:\n\n/cancel to abort."), parse_mode="HTML")
        schedule_delete(sent)
        delete_query_msg(query)

    elif data.startswith("admin_"):
        await query.answer()
        instructions = {
            "admin_gen":      "/gen &lt;user_id or @username&gt; &lt;amount&gt;",
            "admin_ban":      "/ban &lt;user_id&gt;",
            "admin_unban":    "/unban &lt;user_id&gt;",
            "admin_addadmin": "/addadmin &lt;user_id&gt;",
        }
        try:
            await query.edit_message_text(bq(f"📋 Use:\n\n<code>{instructions.get(data, '')}</code>"), parse_mode="HTML")
        except Exception:
            pass

    elif data.startswith("service_"):
        service = data[len("service_"):]
        await query.answer()
        if user["banned"]:
            sent = await query.message.reply_text(bq("⛔ You are banned."), parse_mode="HTML"); schedule_delete(sent); return

        if service == "randomuser":
            if not spend_credit(users, uid):
                sent = await query.message.reply_text(bq("❌ Insufficient credits. Use /start to claim daily credits."), parse_mode="HTML")
                schedule_delete(sent); return
            sent = await query.message.reply_text(bq("⏳ Generating random user..."), parse_mode="HTML")
            await _do_randomuser(sent); return

        service_map = {
            "tgid":      PENDING_USERID,
            "tguser":    PENDING_USERNUM,
            "indinfo":   PENDING_INDINFO,
            "instainfo": PENDING_INSTAINFO,
            "viddown":   PENDING_DOWNLOAD,
            "pincode":   PENDING_PINCODE,
            "ifsc":      PENDING_IFSC,
            "ipinfo":    PENDING_IPINFO,
            "ffstats":   PENDING_FFSTATS,
            "emailrep":  PENDING_EMAILREP,
            "vehicle":   PENDING_VEHICLE,
            "weather":   PENDING_WEATHER,
            "university":PENDING_UNIVERSITY,
            "country":   PENDING_COUNTRY,
        }
        prompts = {
            "tgid":      "🔎 <b>TG ID → Phone</b>\n\nSend Telegram user ID:\nExample: <code>123456789</code>",
            "tguser":    "👤 <b>Username → Phone</b>\n\nSend username:\nExample: <code>username</code>",
            "indinfo":   "📱 <b>Indian Number Info</b>\n\nSend Indian phone number:\nExample: <code>9876543210</code>",
            "instainfo": "📸 <b>Instagram Info</b>\n\nSend Instagram username:\nExample: <code>cristiano</code>",
            "viddown":   "📥 <b>Video Download</b>\n\nSend YouTube/TikTok/Instagram URL:",
            "pincode":   "📮 <b>Pincode Lookup</b>\n\nSend 6-digit Indian pincode:\nExample: <code>110001</code>",
            "ifsc":      "🏦 <b>IFSC Lookup</b>\n\nSend IFSC code:\nExample: <code>SBIN0001234</code>",
            "ipinfo":    "🌐 <b>IP Info</b>\n\nSend IP address:\nExample: <code>8.8.8.8</code>",
            "ffstats":   "📊 <b>FF Stats</b>\n\nSend FF UID:\nExample: <code>11959685790</code>",
            "emailrep":  "📧 <b>Email Reputation</b>\n\nSend email:\nExample: <code>user@example.com</code>",
            "vehicle":   "🚗 <b>Vehicle Specs</b>\n\nSend: <code>Make Year</code>\nExample: <code>Toyota 2020</code>",
            "weather":   "🌤 <b>Weather</b>\n\nSend city name:\nExample: <code>Dhaka</code>",
            "university":"🎓 <b>University Search</b>\n\nSend country name:\nExample: <code>Bangladesh</code>",
            "country":   "🌍 <b>Country Info</b>\n\nSend country name:\nExample: <code>Bangladesh</code>",
        }

        if service not in service_map:
            return
        if not user.get("is_admin") and user["credits"] <= 0:
            sent = await query.message.reply_text(bq("❌ Insufficient credits. Use /start to claim daily credits.\n\n💡 Or use /ai — I can do it for you!"), parse_mode="HTML")
            schedule_delete(sent); return
        context.user_data["pending"] = service_map[service]
        sent = await query.message.reply_text(bq(f"{prompts.get(service,'Send input:')}\n\n/cancel to go back."), parse_mode="HTML")
        schedule_delete(sent)
        delete_query_msg(query)

    else:
        await query.answer()


async def error_handler(update, context):
    err_str = str(context.error)
    print(f"Error: {err_str}")
    if "Forbidden: bot was blocked" not in err_str:
        _error_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {err_str[:300]}")
        if len(_error_log) > 50:
            _error_log.pop(0)


async def post_init(app):
    global _bot_username
    bot_info = await app.bot.get_me()
    _bot_username = (bot_info.username or "").lower()

    from telegram import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
    user_commands = [
        BotCommand("start",      "Main menu"),
        BotCommand("help",       "All commands"),
        BotCommand("balance",    "Balance & profile"),
        BotCommand("sticker",    "Reply to msg → convert to sticker 🎨"),
        BotCommand("redeem",     "Redeem gift code"),
        BotCommand("ai",         "🤖 Super AI — does EVERYTHING (FREE)"),
        BotCommand("image",      "Generate AI image 🎨 (FREE)"),
        BotCommand("aiclear",    "Clear AI chat history"),
        BotCommand("userid",     "TG ID → phone (1 credit)"),
        BotCommand("usernum",    "Username → phone (1 credit)"),
        BotCommand("indinfo",    "Indian number info (1 credit)"),
        BotCommand("instainfo",  "Instagram info (1 credit)"),
        BotCommand("download",   "Download video (1 credit)"),
        BotCommand("pincode",    "Pincode lookup (1 credit)"),
        BotCommand("ifsc",       "IFSC lookup (1 credit)"),
        BotCommand("ipinfo",     "IP address info (1 credit)"),
        BotCommand("ffstats",    "FF stats (1 credit)"),
        BotCommand("emailrep",   "Email reputation (1 credit)"),
        BotCommand("vehicle",    "Vehicle specs (1 credit)"),
        BotCommand("weather",    "Weather info (1 credit)"),
        BotCommand("university", "University search (1 credit)"),
        BotCommand("randomuser", "Random user profile (1 credit)"),
        BotCommand("country",    "Country info (1 credit)"),
        BotCommand("aadhar",     "Aadhar card lookup (1 credit)"),
        BotCommand("gst",        "GST number lookup (1 credit)"),
        BotCommand("pan",        "PAN card lookup (1 credit)"),
        BotCommand("paknum",     "Pakistan number lookup (1 credit)"),
        BotCommand("vehiclerc",  "Vehicle RC lookup (1 credit)"),
        BotCommand("upi",        "UPI ID info (1 credit)"),
        BotCommand("nasaapod",   "NASA Picture of the Day (FREE)"),
        BotCommand("nasaepic",   "NASA Earth photos (FREE)"),
        BotCommand("databases",  "Browse databases"),
        BotCommand("cancel",     "Cancel current action"),
    ]
    admin_commands = user_commands + [
        BotCommand("admin",     "Admin panel"),
        BotCommand("broadcast", "Broadcast to all users"),
        BotCommand("gen",       "Add credits to user"),
        BotCommand("ban",       "Ban a user"),
        BotCommand("unban",     "Unban a user"),
        BotCommand("addadmin",  "Promote to admin"),
        BotCommand("app",       "Toggle auto-approve"),
        BotCommand("diagnose",  "AI diagnose bot errors 🔍"),
    ]
    await app.bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
    try:
        await app.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=int(ADMIN_ID)))
    except Exception:
        pass


# ── /music ──
async def cmd_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    uid = str(update.effective_user.id)
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "music"): return
    args_text = " ".join(context.args).strip()
    if not args_text:
        sent = await update.message.reply_text(
            bq("🎧 <b>AI Music Generation</b>\n\nExample: <code>/music epic battle --sec 30</code>\n\nCost: 5+ credits (based on duration)"),
            parse_mode="HTML")
        schedule_delete(sent); return
    duration = 30
    prompt = args_text
    if "--sec" in args_text:
        parts = args_text.split("--sec")
        prompt = parts[0].strip()
        try:
            duration = min(300, max(10, int(parts[1].strip().split()[0])))
        except Exception:
            duration = 30
    cost = max(5, duration * 140 // 60)
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq(f"❌ Not enough credits! This music costs <b>{cost} credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text(f"🎧 Generating music ({duration}s)... ~1 min wait")
    caption = f"🎧 Music Generated\n\n📝 {prompt}\n⏱ {duration}s\n\nPowered by Player2"
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text("❌ Player2 API connection failed.")
            return
        try:
            result = await mcp_call(client, session_id, "generate_music",
                                    {"prompt": prompt, "duration_seconds": duration, "duration": duration})
            audio_url = (result.get("audio_url") or result.get("url") or
                         result.get("music_url") or result.get("file_url") or "")
            if audio_url:
                await msg.delete()
                await _send_audio_robust(context, update.effective_chat.id, audio_url, caption)
                return
            job_id = result.get("job_id") or result.get("id") or result.get("task_id") or ""
            if not job_id:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"❌ Music API error: {str(result)[:200]}")
                return
            await msg.edit_text("🎧 Generating... Polling.")
            done = await mcp_poll_job(client, session_id, "check_music_job", job_id, 10, 180)
            audio_url = (done.get("audio_url") or done.get("url") or
                         done.get("music_url") or done.get("file_url") or "")
            if audio_url:
                await msg.delete()
                await _send_audio_robust(context, update.effective_chat.id, audio_url, caption)
            else:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"⏳ Music generation {done.get('status','timeout')}. Credits refunded.")
        except Exception as e:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /video ──
async def cmd_video_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "videogen"): return
    prompt = " ".join(context.args).strip()
    if not prompt:
        sent = await update.message.reply_text(bq("🎞️ <b>AI Video Generation</b>\n\nExample: <code>/videogen a dragon flying over mountains</code>\n\nCost: <b>50 credits</b>"), parse_mode="HTML")
        schedule_delete(sent); return
    cost = 50
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq(f"❌ Not enough credits! Video costs <b>50 credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text("🎞️ Generating video... ~2-5 min wait")
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text("❌ Player2 API connection failed.")
            return
        try:
            result = await mcp_call(client, session_id, "generate_video", {"prompt": prompt})
            video_url = result.get("video_url") or result.get("url") or ""
            if video_url:
                await msg.delete()
                caption = f"🎞️ Video Generated\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption)
                return
            job_id = result.get("job_id") or result.get("id") or ""
            if not job_id:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"❌ Video API error: {str(result)[:200]}")
                return
            await msg.edit_text("🎞️ Generating... Polling.")
            done = await mcp_poll_job(client, session_id, "check_video_job", job_id, 15, 300)
            video_url = done.get("video_url") or done.get("url") or ""
            if video_url:
                await msg.delete()
                caption = f"🎞️ Video Generated\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_video(chat_id=update.effective_chat.id, video=video_url, caption=caption)
            else:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text("❌ Video generation failed. Credits refunded.")
        except Exception as e:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /sprite ──
async def cmd_sprite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "sprite"): return
    prompt = " ".join(context.args).strip()
    if not prompt:
        sent = await update.message.reply_text(bq("👾 <b>Sprite Generation</b>\n\nExample: <code>/sprite pixel art warrior facing right</code>\n\nCost: <b>3 credits</b>"), parse_mode="HTML")
        schedule_delete(sent); return
    cost = 3
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq("❌ Not enough credits! Cost: <b>3 credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text("👾 Generating sprite...")
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text("❌ Player2 API connection failed.")
            return
        try:
            result = await mcp_call(client, session_id, "generate_sprite", {"prompt": prompt})
            url = result.get("image_url") or result.get("url") or ""
            if url:
                await msg.delete()
                caption = f"👾 Sprite Generated\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url, caption=caption)
            else:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"❌ Failed: {str(result)[:200]}")
        except Exception as e:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /model3d ──
async def cmd_model3d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "model3d"): return
    prompt = " ".join(context.args).strip()
    if not prompt:
        sent = await update.message.reply_text(bq("🧊 <b>3D Model Generation</b>\n\nExample: <code>/model3d a medieval castle tower</code>\n\nCost: <b>190 credits</b>"), parse_mode="HTML")
        schedule_delete(sent); return
    cost = 190
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq("❌ Not enough credits! Cost: <b>190 credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text("🧊 Generating 3D model... ~3-5 min")
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text("❌ Player2 API connection failed.")
            return
        try:
            result = await mcp_call(client, session_id, "generate_3d_model", {"prompt": prompt})
            glb_url = result.get("glb_url") or result.get("url") or result.get("model_url") or ""
            if glb_url:
                await msg.delete()
                caption = f"🧊 3D Model Generated\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_document(chat_id=update.effective_chat.id, document=glb_url, caption=caption)
                return
            job_id = result.get("job_id") or result.get("id") or ""
            if not job_id:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"❌ 3D API error: {str(result)[:200]}")
                return
            await msg.edit_text("🧊 Generating... Polling.")
            done = await mcp_poll_job(client, session_id, "check_3d_job", job_id, 20, 360)
            glb_url = done.get("glb_url") or done.get("url") or done.get("model_url") or ""
            if glb_url:
                await msg.delete()
                caption = f"🧊 3D Model Generated\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_document(chat_id=update.effective_chat.id, document=glb_url, caption=caption)
            else:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text("❌ 3D generation failed. Credits refunded.")
        except Exception as e:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /editimage ──
async def cmd_editimage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "editimage"): return
    prompt = " ".join(context.args).strip()
    reply = update.message.reply_to_message
    if not reply or not (reply.photo or reply.document):
        sent = await update.message.reply_text(bq("↩️ <b>Reply to a photo</b>, then use:\n<code>/editimage &lt;your changes&gt;</code>\n\nCost: <b>10 credits</b>"), parse_mode="HTML")
        schedule_delete(sent); return
    if not prompt:
        sent = await update.message.reply_text(bq("❌ Give an edit prompt!\nExample: <code>/editimage make it look like night</code>"), parse_mode="HTML")
        schedule_delete(sent); return
    cost = 10
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq("❌ Not enough credits! Cost: <b>10 credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text("🖌️ Editing image...")
    async with httpx.AsyncClient() as client:
        session_id = await mcp_init(client)
        if not session_id:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text("❌ Player2 API connection failed.")
            return
        try:
            if reply.photo:
                file = await reply.photo[-1].get_file()
            else:
                file = await reply.document.get_file()
            result = await mcp_call(client, session_id, "edit_image",
                                    {"image_url": file.file_path, "prompt": prompt})
            url = result.get("image_url") or result.get("url") or ""
            if url:
                await msg.delete()
                caption = f"🖌️ Image Edited\n\n📝 {prompt[:100]}\n\nPowered by Player2"
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url, caption=caption)
            else:
                if not user.get("is_admin"):
                    users[uid]["credits"] += cost
                    save_users(users)
                await msg.edit_text(f"❌ Failed: {str(result)[:200]}")
        except Exception as e:
            if not user.get("is_admin"):
                users[uid]["credits"] += cost
                save_users(users)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /imagegen (Player2 image) ──
async def cmd_image_p2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    if await _check_maintenance(update): return
    users = load_users()
    user, uid = get_user(users, update.effective_user.id, update.effective_user.username or "")
    if await _check_banned(update, user): return
    if await _check_feature(update, "imagegen"): return
    prompt = " ".join(context.args).strip()
    if not prompt:
        sent = await update.message.reply_text(bq("🌈 <b>AI Image Generation</b>\n\nExample: <code>/imagegen a cyberpunk city at night</code>\n\nCost: <b>3 credits</b>"), parse_mode="HTML")
        schedule_delete(sent); return
    cost = 3
    if not user.get("is_admin") and user.get("credits", 0) < cost:
        sent = await update.message.reply_text(bq("❌ Not enough credits! Cost: <b>3 credits</b>.\n\nUse /start to claim daily credits."), parse_mode="HTML")
        schedule_delete(sent); return
    if not user.get("is_admin"):
        users[uid]["credits"] -= cost
        save_users(users)
    msg = await update.message.reply_text("🌈 Generating image...")
    used_fallback = False
    try:
        url = await generate_image_player2(prompt) if PLAYER2_API_KEY else None
        if url == "QUOTA" or url is None:
            used_fallback = True
            url = await generate_image_fallback(prompt)
        source = "🔄 Free fallback (Player2 quota exceeded)" if used_fallback else "⚡ Powered by Player2"
        await msg.delete()
        caption = f"🌈 Image Generated\n\n📝 {prompt[:100]}\n\n{source}"
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=url, caption=caption)
    except Exception as e:
        if not user.get("is_admin"):
            users[uid]["credits"] += cost
            save_users(users)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ── /stats (admin) ──
async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    if not users.get(str(update.effective_user.id), {}).get("is_admin") and str(update.effective_user.id) != str(ADMIN_ID):
        return
    codes = load_codes()
    total = len(users)
    banned = sum(1 for u in users.values() if u.get("banned"))
    admins = sum(1 for u in users.values() if u.get("is_admin"))
    total_codes = len(codes)
    now = datetime.utcnow()
    active = 0
    for c in codes.values():
        exp = c.get("expires_at")
        if not exp:
            active += 1
        else:
            try:
                if now < datetime.fromisoformat(exp):
                    active += 1
            except Exception:
                pass
    await update.message.reply_text(
        f"📊 Bot Statistics\n\n"
        f"👥 Total Users: {total}\n"
        f"🚫 Banned: {banned}\n"
        f"👑 Admins: {admins}\n\n"
        f"🎫 Total Codes: {total_codes}\n"
        f"✅ Active Codes: {active}"
    )


# ── /gencode (admin) ──
async def cmd_gencode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = load_users()
    if not (users.get(uid, {}).get("is_admin") or uid == str(ADMIN_ID)):
        await update.message.reply_text("❌ Admin only command.")
        return
    if not context.args:
        await update.message.reply_text(
            "📋 Usage:\n/gencode <credits> [max_users] [days]\n\n"
            "Examples:\n/gencode 50 — 50 credits, unlimited\n"
            "/gencode 100 10 — max 10 users\n"
            "/gencode 50 5 7 — expires in 7 days"
        )
        return
    try:
        credits_amount = int(context.args[0])
        max_users = int(context.args[1]) if len(context.args) > 1 else 0
        days = int(context.args[2]) if len(context.args) > 2 else 0
    except ValueError:
        await update.message.reply_text("❌ Numbers only. Example: /gencode 50 10 7")
        return
    chars = string.ascii_letters + string.digits
    code = "SHUVO_" + "".join(random.choices(chars, k=8))
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat() if days > 0 else None
    codes = load_codes()
    codes[code] = {
        "credits": credits_amount,
        "max_users": max_users,
        "expires_at": expires_at,
        "used_by": [],
        "created_by": uid,
        "created_at": datetime.utcnow().isoformat(),
    }
    save_codes(codes)
    max_str = str(max_users) if max_users > 0 else "Unlimited"
    exp_str = f"{days} days" if days > 0 else "Never"
    await update.message.reply_text(
        f"✅ Code Generated!\n\n"
        f"🎫 Code: {code}\n"
        f"🔋 Credits: {credits_amount}\n"
        f"👥 Max Users: {max_str}\n"
        f"⏳ Expires: {exp_str}\n\n"
        f"Share: /redeem {code}"
    )


# ── /listcodes (admin) ──
async def cmd_listcodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = load_users()
    if not (users.get(uid, {}).get("is_admin") or uid == str(ADMIN_ID)):
        return
    codes = load_codes()
    if not codes:
        await update.message.reply_text("📭 No codes yet.")
        return
    now = datetime.utcnow()
    lines = [f"📋 Codes ({len(codes)} total):\n"]
    for code, c in list(codes.items())[-20:]:
        used = len(c.get("used_by", []))
        max_u = c.get("max_users", 0)
        max_str = str(max_u) if max_u > 0 else "∞"
        exp = c.get("expires_at")
        if exp:
            try:
                exp_dt = datetime.fromisoformat(exp)
                expired_mark = " ⛔" if now > exp_dt else ""
                exp_str = exp_dt.strftime("%m/%d") + expired_mark
            except Exception:
                exp_str = "?"
        else:
            exp_str = "∞"
        lines.append(f"• {code}\n  💰{c['credits']}cr | 👥{used}/{max_str} | ⏳{exp_str}\n")
    await update.message.reply_text("\n".join(lines))


# ── /delcode (admin) ──
async def cmd_delcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = load_users()
    if not (users.get(uid, {}).get("is_admin") or uid == str(ADMIN_ID)):
        return
    if not context.args:
        await update.message.reply_text("Usage: /delcode <CODE>")
        return
    code = context.args[0].strip()
    codes = load_codes()
    if code not in codes:
        await update.message.reply_text("❌ Code not found.")
        return
    del codes[code]
    save_codes(codes)
    await update.message.reply_text(f"✅ {code} deleted.")


# ── /addcredits (admin) ──
async def cmd_addcredits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    users = load_users()
    if not (users.get(uid, {}).get("is_admin") or uid == str(ADMIN_ID)):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addcredits <user_id> <amount>")
        return
    try:
        target_uid = context.args[0].strip()
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")
        return
    target_user, _ = get_user(users, target_uid)
    new_bal = target_user.get("credits", 0) + amount
    users[target_uid]["credits"] = new_bal
    save_users(users)
    await update.message.reply_text(f"✅ Credits Added!\n👤 {target_uid}\n🔋 +{amount} → Balance: {new_bal}")


# ── /clear (group admin) ──
async def cmd_clear_msgs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    is_admin_user = str(user.id) == str(ADMIN_ID) or load_users().get(str(user.id), {}).get("is_admin")
    if not is_admin_user and chat.type in ("group", "supergroup"):
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin_user = member.status in ("administrator", "creator")
    if not is_admin_user:
        await update.message.reply_text("❌ Admin only command.")
        return
    chat_id = chat.id
    arg = (context.args[0].lower() if context.args else "").strip()
    if arg == "on":
        _clear_chats.add(chat_id)
        await update.message.reply_text("✅ Auto-delete ON!")
    elif arg == "off":
        _clear_chats.discard(chat_id)
        await update.message.reply_text("✅ Auto-delete OFF!")
    else:
        status = "ON ✅" if chat_id in _clear_chats else "OFF ❌"
        await update.message.reply_text(f"Auto-delete: {status}\nUse /clearmsg on or /clearmsg off")


# ── /blacklist /unblacklist (group admin) ──
async def cmd_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    is_admin_user = str(user.id) == str(ADMIN_ID) or load_users().get(str(user.id), {}).get("is_admin")
    if not is_admin_user and chat.type in ("group", "supergroup"):
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin_user = member.status in ("administrator", "creator")
    if not is_admin_user:
        await update.message.reply_text("❌ Admin only command.")
        return
    chat_id = chat.id
    arg = " ".join(context.args).strip().lower()
    if arg == "list":
        words = _blacklist_data.get(chat_id, set())
        if not words:
            await update.message.reply_text("📭 Blacklist is empty.")
        else:
            items = "\n".join(f"• {w}" for w in sorted(words))
            await update.message.reply_text(f"🚫 Blacklisted:\n\n{items}")
        return
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("↩️ Reply to a message, then use /blacklist.")
        return
    text = (reply.text or reply.caption or "").strip().lower()
    if not text:
        await update.message.reply_text("❌ Cannot blacklist an empty message.")
        return
    if chat_id not in _blacklist_data:
        _blacklist_data[chat_id] = set()
    _blacklist_data[chat_id].add(text)
    await update.message.reply_text(f"✅ '{text[:100]}' — blacklisted.")


async def cmd_unblacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    is_admin_user = str(user.id) == str(ADMIN_ID) or load_users().get(str(user.id), {}).get("is_admin")
    if not is_admin_user and chat.type in ("group", "supergroup"):
        member = await context.bot.get_chat_member(chat.id, user.id)
        is_admin_user = member.status in ("administrator", "creator")
    if not is_admin_user:
        await update.message.reply_text("❌ Admin only command.")
        return
    chat_id = chat.id
    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("↩️ Reply to a message, then use /unblacklist.")
        return
    text = (reply.text or reply.caption or "").strip().lower()
    words = _blacklist_data.get(chat_id, set())
    if text in words:
        words.discard(text)
        await update.message.reply_text(f"✅ '{text[:100]}' — removed from blacklist.")
    else:
        await update.message.reply_text("⚠️ This message is not in the blacklist.")


def main():
    os.makedirs("bot", exist_ok=True)

    # Write PID so controller bot can manage this process
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    write_log(f"SHUVO BOT started — PID {os.getpid()}")

    if not os.path.exists(USER_FILE):
        users = {}
        users[ADMIN_ID] = {"credits": 100, "banned": False, "is_admin": True, "last_claim": None, "username": ""}
        save_users(users)

    app = Application.builder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start",      start))
    app.add_handler(CommandHandler("help",       help_command))
    app.add_handler(CommandHandler("balance",    bal))
    app.add_handler(CommandHandler("userid",     cmd_userid))
    app.add_handler(CommandHandler("usernum",    cmd_usernum))
    app.add_handler(CommandHandler("indinfo",    cmd_indinfo))
    app.add_handler(CommandHandler("instainfo",  cmd_instainfo))
    app.add_handler(CommandHandler("download",   cmd_download))
    app.add_handler(CommandHandler("cancel",     cancel))
    app.add_handler(CommandHandler("loghere",    cmd_loghere))
    app.add_handler(CommandHandler("admin",      admin_command))
    app.add_handler(CommandHandler("broadcast",  broadcast))
    app.add_handler(CommandHandler("redeem",     redeem))
    app.add_handler(CommandHandler("gen",        gen))
    app.add_handler(CommandHandler("ban",        ban_cmd))
    app.add_handler(CommandHandler("unban",      unban_cmd))
    app.add_handler(CommandHandler("addadmin",   addadmin))
    app.add_handler(CommandHandler("databases",  databases_command))
    app.add_handler(CommandHandler("app",        app_toggle))
    app.add_handler(CommandHandler("pincode",    cmd_pincode))
    app.add_handler(CommandHandler("ifsc",       cmd_ifsc))
    app.add_handler(CommandHandler("ipinfo",     cmd_ipinfo))
    app.add_handler(CommandHandler("ffstats",    cmd_ffstats))
    app.add_handler(CommandHandler("emailrep",   cmd_emailrep))
    app.add_handler(CommandHandler("vehicle",    cmd_vehicle))
    app.add_handler(CommandHandler("weather",    cmd_weather))
    app.add_handler(CommandHandler("university", cmd_university))
    app.add_handler(CommandHandler("randomuser", cmd_randomuser))
    app.add_handler(CommandHandler("country",    cmd_country))
    app.add_handler(CommandHandler("aadhar",     cmd_aadhar))
    app.add_handler(CommandHandler("gst",        cmd_gst))
    app.add_handler(CommandHandler("pan",        cmd_pan))
    app.add_handler(CommandHandler("paknum",     cmd_paknum))
    app.add_handler(CommandHandler("vehiclerc",  cmd_vehicle_rc))
    app.add_handler(CommandHandler("upi",        cmd_upi))
    app.add_handler(CommandHandler("makeaadhar", cmd_makeaadhar))
    app.add_handler(CommandHandler("voice",      cmd_voice))
    app.add_handler(CommandHandler("nasaapod",   cmd_nasa_apod))
    app.add_handler(CommandHandler("nasaepic",   cmd_nasa_epic))
    app.add_handler(CommandHandler("ai",          cmd_ai))
    app.add_handler(CommandHandler("ask",         cmd_ai))
    app.add_handler(CommandHandler("image",       cmd_image))
    app.add_handler(CommandHandler("imagegen",    cmd_image_p2))
    app.add_handler(CommandHandler("music",       cmd_music))
    app.add_handler(CommandHandler("videogen",    cmd_video_gen))
    app.add_handler(CommandHandler("sprite",      cmd_sprite))
    app.add_handler(CommandHandler("model3d",     cmd_model3d))
    app.add_handler(CommandHandler("editimage",   cmd_editimage))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("gencode",     cmd_gencode))
    app.add_handler(CommandHandler("listcodes",   cmd_listcodes))
    app.add_handler(CommandHandler("delcode",     cmd_delcode))
    app.add_handler(CommandHandler("addcredits",  cmd_addcredits))
    app.add_handler(CommandHandler("clearmsg",    cmd_clear_msgs))
    app.add_handler(CommandHandler("blacklist",   cmd_blacklist))
    app.add_handler(CommandHandler("unblacklist", cmd_unblacklist))
    app.add_handler(CommandHandler("aiclear",     cmd_aiclear))
    app.add_handler(CommandHandler("diagnose",    cmd_diagnose))
    app.add_handler(CommandHandler("by",          cmd_bypass_toggle))
    app.add_handler(CommandHandler("sticker",     cmd_sticker))
    app.add_handler(ChatJoinRequestHandler(auto_approve_request))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, handle_user_input))
    app.add_handler(MessageHandler(filters.ALL, log_all_messages), group=-1)
    app.add_error_handler(error_handler)

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
