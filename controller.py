import json
import os
import sys
import signal
import subprocess
import hashlib
import string
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

CONTROLLER_TOKEN  = "8999526361:AAHiHkjpP5QNxHwX6hm6vd6LmGMyhnyUNmg"
OWNER_ID          = "8600328303"
MAIN_BOT_SCRIPT   = "main.py"

FEATURES_FILE     = "bot/features.json"
CONFIG_FILE       = "bot/config.json"
USER_FILE         = "bot/user.json"
CODES_FILE        = "bot/codes.json"
LOG_FILE          = "bot/shuvo.log"
PID_FILE          = "bot/.main_pid"
PAUSE_FILE        = "bot/.paused"
CTRL_BANNER_FILE  = "bot/controller_banner.png"

_DEFAULT_PASS_HASH = hashlib.sha256("asraful123".encode()).hexdigest()

_authenticated: set = set()

FEATURES = {
    "ai_chat":     "🤖 AI Chat",
    "daily_claim": "🎁 Daily Claim",
    "redeem":      "🎫 Redeem Code",
    "voice":       "🎙️ Voice TTS",
    "imagegen":    "🌈 Image Gen",
    "music":       "🎧 Music Gen",
    "videogen":    "🎞️ Video Gen",
    "sprite":      "👾 Sprite Gen",
    "model3d":     "🧊 3D Model",
    "editimage":   "🖌️ Edit Image",
    "tgid":        "📞 TG ID→Num",
    "tguser":      "🔍 User→Num",
    "indinfo":     "☎️ IND Info",
    "instainfo":   "📸 Instagram",
    "viddown":     "🎬 Vid Download",
    "pincode":     "📮 Pincode",
    "ifsc":        "🏦 IFSC",
    "ipinfo":      "🌐 IP Info",
    "ffstats":     "🎯 FF Stats",
    "emailrep":    "📧 Email Check",
    "vehicle":     "🚗 Vehicle",
    "weather":     "⛅ Weather",
    "nasa":        "🚀 NASA",
    "aadhar":      "🪪 Aadhar",
    "gst":         "💼 GST",
    "pan":         "🪪 PAN",
    "paknum":      "🇵🇰 Pak Num",
    "vehicle_rc":  "🚗 Vehicle RC",
    "upi":         "💳 UPI Info",
    "makeaadhar":  "🪪 Make Aadhar Card",
}


def is_owner(uid):
    return str(uid) == str(OWNER_ID)

def is_authed(uid):
    return str(uid) in _authenticated

def get_pass_hash() -> str:
    cfg = load_config()
    return cfg.get("controller_pass_hash", _DEFAULT_PASS_HASH)

def set_pass_hash(new_hash: str):
    cfg = load_config()
    cfg["controller_pass_hash"] = new_hash
    save_config(cfg)

def check_pass(text: str) -> bool:
    return hashlib.sha256(text.strip().encode()).hexdigest() == get_pass_hash()

def load_users():
    try:
        with open(USER_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(data):
    os.makedirs("bot", exist_ok=True)
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_codes():
    try:
        with open(CODES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_codes(data):
    os.makedirs("bot", exist_ok=True)
    with open(CODES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def esc(t):
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def load_features():
    os.makedirs("bot", exist_ok=True)
    try:
        with open(FEATURES_FILE) as f:
            data = json.load(f)
    except Exception:
        data = {}
    for k in FEATURES:
        if k not in data:
            data[k] = True
    return data

def save_features(data):
    os.makedirs("bot", exist_ok=True)
    with open(FEATURES_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(data):
    os.makedirs("bot", exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_channel_link(link: str) -> str:
    link = link.strip()
    if "t.me/" in link:
        part = link.split("t.me/")[-1].strip("/").split("?")[0]
        if part.startswith("+") or part.lower().startswith("joinchat"):
            return link
        return "@" + part
    elif link.startswith("@"):
        return link
    elif link.startswith("-") or link.lstrip("-").isdigit():
        return link
    else:
        return "@" + link.lstrip("@")

MAX_CHANNELS = 5

def channels_panel_text():
    cfg      = load_config()
    channels = cfg.get("required_channels", [])
    count    = len(channels)
    if not channels:
        return (
            f"📢 <b>Force Join Manager</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Total Added : <b>0 / {MAX_CHANNELS}</b>\n\n"
            f"No channels or groups added yet.\n"
            f"Users can freely use the bot.\n\n"
            f"Tap <b>➕ Add</b> to require membership.\n"
            f"You can add up to <b>{MAX_CHANNELS}</b> channels/groups."
        )
    lines = "\n".join(
        f"  {i+1}. {ch['title']}  »  <code>{ch['username']}</code>"
        for i, ch in enumerate(channels)
    )
    status = "🔴 Limit reached!" if count >= MAX_CHANNELS else f"🟢 {MAX_CHANNELS - count} slot(s) remaining"
    return (
        f"📢 <b>Force Join Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total Added : <b>{count} / {MAX_CHANNELS}</b>  —  {status}\n\n"
        f"<b>Required Channels/Groups:</b>\n"
        f"{lines}\n\n"
        f"⚠️ Users must join <b>all</b> of these before using the bot."
    )

def channels_keyboard():
    cfg      = load_config()
    channels = cfg.get("required_channels", [])
    count    = len(channels)
    rows     = []
    for i, ch in enumerate(channels):
        label = ch['title'][:24]
        rows.append([InlineKeyboardButton(f"🗑 Remove  {i+1}. {label}", callback_data=f"c_remove_ch_{i}")])
    if count < MAX_CHANNELS:
        rows.append([InlineKeyboardButton("➕ Add Channel / Group", callback_data="c_add_channel")])
    else:
        rows.append([InlineKeyboardButton(f"🚫 Max {MAX_CHANNELS} reached — Remove one to add", callback_data="c_channels")])
    rows.append([
        InlineKeyboardButton(f"📊 Total: {count}/{MAX_CHANNELS}", callback_data="c_channels"),
        InlineKeyboardButton("🔁 Refresh",                         callback_data="c_channels"),
    ])
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="c_home")])
    return InlineKeyboardMarkup(rows)

def userlogs_panel_text():
    cfg = load_config()
    log_grp = cfg.get("log_group_id")
    if not log_grp:
        return (
            "📝 <b>User Logs System</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📴 Status : <b>Disabled</b>\n\n"
            "When enabled, every message users send to the bot\n"
            "will be logged to your chosen group, with a\n"
            "<b>💬 DM</b> button to reply directly to any user.\n\n"
            "Tap <b>➕ Set Log Group</b> to activate."
        )
    return (
        f"📝 <b>User Logs System</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🟢 Status    : <b>Active</b>\n"
        f"📨 Log Group : <code>{log_grp}</code>\n\n"
        f"All user messages &amp; commands are being logged.\n"
        f"Use the <b>💬 DM</b> button in any log entry to\n"
        f"send a message directly to that user."
    )


def userlogs_keyboard():
    cfg = load_config()
    log_grp = cfg.get("log_group_id")
    rows = []
    if log_grp:
        rows.append([InlineKeyboardButton("🗑 Remove Log Group", callback_data="c_clear_loggroup")])
    else:
        rows.append([InlineKeyboardButton("➕ Set Log Group",    callback_data="c_set_loggroup")])
    rows.append([
        InlineKeyboardButton("🔁 Refresh", callback_data="c_userlogs"),
        InlineKeyboardButton("🏠 Home",    callback_data="c_home"),
    ])
    return InlineKeyboardMarkup(rows)


# ─────────────────── USER MANAGER ───────────────────

USERS_PAGE_SIZE = 8

def users_list_text(page=0):
    users  = load_users()
    items  = sorted(users.items(), key=lambda x: x[1].get("first_name","").lower())
    total  = len(items)
    start  = page * USERS_PAGE_SIZE
    chunk  = items[start:start + USERS_PAGE_SIZE]
    lines  = []
    for uid, u in chunk:
        name   = esc(u.get("first_name","") + " " + u.get("last_name","")).strip() or "Unknown"
        uname  = f"@{u.get('username')}" if u.get("username") else "—"
        banned = " 🚫" if u.get("banned") else ""
        admin  = " 👑" if u.get("is_admin") else ""
        cr     = u.get("credits", 0)
        lines.append(f"  <code>{uid}</code>  {esc(name)}{admin}{banned}\n"
                     f"  └ {uname}  •  💰 {cr} credits")
    body = "\n".join(lines) if lines else "  No users found."
    pages = max(1, (total + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE)
    return (
        f"👤 <b>User Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total: <b>{total}</b>  •  Page <b>{page+1}/{pages}</b>\n\n"
        f"{body}\n\n"
        f"🔍 Tap <b>Search</b> to look up a specific user."
    )

def users_list_keyboard(page=0):
    users  = load_users()
    total  = len(users)
    pages  = max(1, (total + USERS_PAGE_SIZE - 1) // USERS_PAGE_SIZE)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"c_users_{page-1}"))
    nav.append(InlineKeyboardButton(f"• {page+1}/{pages} •", callback_data="c_noop"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"c_users_{page+1}"))
    return InlineKeyboardMarkup([
        nav,
        [InlineKeyboardButton("🔍 Search User",  callback_data="c_user_search"),
         InlineKeyboardButton("🔁 Refresh",       callback_data=f"c_users_{page}")],
        [InlineKeyboardButton("🏠 Home",          callback_data="c_home")],
    ])

def user_profile_text(uid, u):
    name   = esc((u.get("first_name","") + " " + u.get("last_name","")).strip()) or "Unknown"
    uname  = f"@{esc(u.get('username'))}" if u.get("username") else "—"
    cr     = u.get("credits", 0)
    banned = "🚫 Yes" if u.get("banned") else "✅ No"
    admin  = "👑 Yes" if u.get("is_admin") else "—"
    joined = esc(u.get("joined_at", "—"))
    last   = esc(u.get("last_seen", "—"))
    return (
        f"👤 <b>User Profile</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 User ID   : <code>{uid}</code>\n"
        f"📛 Name      : {name}\n"
        f"🔗 Username  : {uname}\n"
        f"💰 Credits   : <b>{cr:,}</b>\n"
        f"🚫 Banned    : {banned}\n"
        f"👑 Admin     : {admin}\n"
        f"📅 Joined    : {joined}\n"
        f"🕐 Last seen : {last}"
    )

def user_profile_keyboard(uid, u):
    ban_btn = (
        InlineKeyboardButton("✅ Unban",  callback_data=f"c_unban_{uid}")
        if u.get("banned") else
        InlineKeyboardButton("🚫 Ban",    callback_data=f"c_ban_{uid}")
    )
    adm_btn = (
        InlineKeyboardButton("👑 Remove Admin", callback_data=f"c_deadmin_{uid}")
        if u.get("is_admin") else
        InlineKeyboardButton("👑 Make Admin",   callback_data=f"c_mkadmin_{uid}")
    )
    return InlineKeyboardMarkup([
        [ban_btn, adm_btn],
        [InlineKeyboardButton("💰 Add Credits",    callback_data=f"c_addcr_{uid}"),
         InlineKeyboardButton("💸 Remove Credits", callback_data=f"c_remcr_{uid}")],
        [InlineKeyboardButton("🗑 Delete User",    callback_data=f"c_deluser_{uid}"),
         InlineKeyboardButton("🔁 Refresh",        callback_data=f"c_viewuser_{uid}")],
        [InlineKeyboardButton("◀️ Back",            callback_data="c_users_0"),
         InlineKeyboardButton("🏠 Home",            callback_data="c_home")],
    ])


# ─────────────────── CODE MANAGER ───────────────────

def codes_list_text():
    codes = load_codes()
    if not codes:
        return (
            "🎫 <b>Code Manager</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📭 No redeem codes found.\n\n"
            "Tap <b>➕ Create Code</b> to generate a new one."
        )
    lines = []
    for code, info in list(codes.items())[:20]:
        cr  = info.get("credits", 0)
        lim = info.get("limit", "∞")
        used= info.get("used", 0)
        exp = info.get("expires", "Never")
        lines.append(f"  🎫 <code>{esc(code)}</code>\n"
                     f"  └ 💰 {cr} cr  •  Used: {used}/{lim}  •  Exp: {esc(exp)}")
    body = "\n".join(lines)
    shown = min(len(codes), 20)
    return (
        f"🎫 <b>Code Manager</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 Total Codes: <b>{len(codes)}</b>"
        + (f"  (showing first {shown})" if len(codes) > 20 else "") +
        f"\n\n{body}"
    )

def codes_keyboard():
    codes = load_codes()
    rows  = []
    for code in list(codes.keys())[:8]:
        rows.append([InlineKeyboardButton(
            f"🗑 Delete  {code[:20]}", callback_data=f"c_delcode_{code}"
        )])
    rows.append([
        InlineKeyboardButton("➕ Create Code",  callback_data="c_createcode"),
        InlineKeyboardButton("🗑 Clear All",    callback_data="c_clearallcodes"),
    ])
    rows.append([
        InlineKeyboardButton("🔁 Refresh",      callback_data="c_codes"),
        InlineKeyboardButton("🏠 Home",          callback_data="c_home"),
    ])
    return InlineKeyboardMarkup(rows)


# ─────────────────── DM USER ───────────────────

def dm_user_text():
    return (
        "💬 <b>DM User</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Send a private message to any bot user directly.\n\n"
        "Tap <b>➕ Send DM</b> and enter the User ID first."
    )

def dm_user_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Send DM",  callback_data="c_dm_start")],
        [InlineKeyboardButton("🏠 Home",     callback_data="c_home")],
    ])


def get_main_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None

def process_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def bot_status_line():
    pid    = get_main_pid()
    paused = os.path.exists(PAUSE_FILE)
    if pid and process_alive(pid):
        state = f"🟢 Running  (PID {pid})"
    elif pid:
        state = f"🔴 Dead     (stale PID {pid})"
    else:
        state = "⚪ Unknown  (no PID file)"
    mode = "⏸️ PAUSED" if paused else "▶️ Active"
    return state, mode

def panel_text():
    feats       = load_features()
    on          = sum(1 for v in feats.values() if v)
    tot         = len(feats)
    state, mode = bot_status_line()
    now         = datetime.now().strftime("%d %b  %H:%M:%S")
    cfg         = load_config()
    ch_count    = len(cfg.get("required_channels", []))
    return (
        f"╔━━━━━━━━━━━━━━━━━━━━╗\n"
        f"   🎛 <b>SHUVO BOT CONTROLLER</b>\n"
        f"╚━━━━━━━━━━━━━━━━━━━━╝\n\n"
        f"<blockquote>"
        f"🤖 <b>Status</b>   ›  {state}\n"
        f"🕹 <b>Mode</b>     ›  {mode}\n"
        f"🔧 <b>Features</b> ›  <b>{on}/{tot}</b> enabled\n"
        f"📢 <b>Force Join</b> ›  <b>{ch_count}/5</b>\n"
        f"🕐 <b>Time</b>     ›  {now}"
        f"</blockquote>"
    )

def main_keyboard():
    cfg      = load_config()
    channels = cfg.get("required_channels", [])
    log_grp  = cfg.get("log_group_id")
    n        = len(channels)
    fj_label = f"📢🔗  Force Join  •  {n}/5" if channels else "📢🔗  Force Join"
    ul_label = f"📝👁️  User Logs  •  ON ✅" if log_grp else "📝👁️  User Logs"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️🔧  Features",       callback_data="c_feat_0"),
         InlineKeyboardButton("📋🖥️  Live Logs",      callback_data="c_logs")],
        [InlineKeyboardButton("📊📈  Stats",           callback_data="c_stats"),
         InlineKeyboardButton("🔁✅  Refresh",         callback_data="c_home")],
        [InlineKeyboardButton(fj_label,                callback_data="c_channels"),
         InlineKeyboardButton(ul_label,                callback_data="c_userlogs")],
        [InlineKeyboardButton("👤🔍  User Manager",   callback_data="c_users_0"),
         InlineKeyboardButton("📣📡  Broadcast",       callback_data="c_broadcast")],
        [InlineKeyboardButton("🎫💎  Code Manager",   callback_data="c_codes"),
         InlineKeyboardButton("💬📤  DM User",         callback_data="c_dm_user")],
        [InlineKeyboardButton("⏸️🔴  Pause Bot",      callback_data="c_pause"),
         InlineKeyboardButton("▶️💚  Resume Bot",      callback_data="c_resume")],
        [InlineKeyboardButton("🔄⚡  Restart Bot",    callback_data="c_restart"),
         InlineKeyboardButton("💀🛑  Kill Process",   callback_data="c_kill")],
        [InlineKeyboardButton("⚡🚀  Spawn Process",  callback_data="c_spawn"),
         InlineKeyboardButton("🗑🧹  Clear Logs",      callback_data="c_clearlogs")],
        [InlineKeyboardButton("🔑🔐  Change Password", callback_data="c_changepass"),
         InlineKeyboardButton("📁💾  Backup Files",    callback_data="c_backup")],
        [InlineKeyboardButton("🔒🚪  Logout",          callback_data="c_logout")],
    ])

def features_keyboard(page=0):
    feats      = load_features()
    items      = list(FEATURES.items())
    per        = 8
    start      = page * per
    chunk      = items[start:start + per]
    rows       = []
    for i in range(0, len(chunk), 2):
        row = []
        for key, label in chunk[i:i+2]:
            icon = "✅" if feats.get(key, True) else "❌"
            row.append(InlineKeyboardButton(f"{icon} {label}", callback_data=f"cf_{key}"))
        rows.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"c_feat_{page-1}"))
    total_pages = (len(items) + per - 1) // per
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"c_feat_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([
        InlineKeyboardButton("🔛 All ON",  callback_data="c_allon"),
        InlineKeyboardButton("🔕 All OFF", callback_data="c_alloff"),
    ])
    rows.append([InlineKeyboardButton("🏠 Home", callback_data="c_home")])
    return InlineKeyboardMarkup(rows)

def feat_panel_text():
    feats = load_features()
    on    = sum(1 for v in feats.values() if v)
    tot   = len(feats)
    return f"🔧 <b>Feature Toggle</b>\n✅ Enabled: <b>{on}/{tot}</b>\n\nTap any feature to toggle it:"


async def _send_banner_panel(target, caption: str, keyboard, parse_mode="HTML"):
    """Send banner photo + caption. target = update.message or query.message"""
    try:
        if os.path.exists(CTRL_BANNER_FILE):
            with open(CTRL_BANNER_FILE, "rb") as f:
                await target.reply_photo(photo=f, caption=caption,
                                         reply_markup=keyboard, parse_mode=parse_mode)
            return
    except Exception:
        pass
    await target.reply_text(caption, reply_markup=keyboard, parse_mode=parse_mode)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_owner(uid):
        try:
            with open(CTRL_BANNER_FILE, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption="🚫 <b>Access Denied</b>\n\nThis is a private controller bot.",
                    parse_mode="HTML"
                )
        except Exception:
            await update.message.reply_text("🚫 Unauthorized.")
        return

    if is_authed(uid):
        await _send_banner_panel(update.message, panel_text(), main_keyboard())
        return

    context.user_data["awaiting_pass"] = True
    login_text = (
        "🔐 <b>SHUVO BOT Controller</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛡️ Owner-only access panel\n"
        "🔑 Enter your <b>password</b> to continue:"
    )
    try:
        if os.path.exists(CTRL_BANNER_FILE):
            with open(CTRL_BANNER_FILE, "rb") as f:
                await update.message.reply_photo(photo=f, caption=login_text, parse_mode="HTML")
            return
    except Exception:
        pass
    await update.message.reply_text(login_text, parse_mode="HTML")

async def cmd_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    _authenticated.discard(uid)
    context.user_data["awaiting_pass"] = False
    await update.message.reply_text("🔒 Logged out. Send /start to log in again.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not is_owner(uid):
        return

    text = (update.message.text or "").strip()

    # ── Log Group ID input ──
    if context.user_data.get("awaiting_loggroup"):
        try:
            await update.message.delete()
        except Exception:
            pass
        context.user_data["awaiting_loggroup"] = False
        raw = text.strip()
        if not raw.lstrip("-").isdigit():
            await update.message.reply_text(
                "❌ <b>Invalid Group ID!</b>\n\n"
                "Group IDs are numbers, e.g. <code>-1001234567890</code>\n\n"
                "Try again with <b>➕ Set Log Group</b>.",
                reply_markup=userlogs_keyboard(),
                parse_mode="HTML"
            )
            return
        cfg = load_config()
        cfg["log_group_id"] = raw
        save_config(cfg)
        await update.message.reply_text(
            f"✅ <b>Log Group Set!</b>\n\n"
            f"📨 Group ID: <code>{raw}</code>\n\n"
            f"User logs are now <b>active</b>.\n"
            f"Every message users send to the bot will appear there\n"
            f"with a <b>💬 DM</b> button to reply directly.",
            reply_markup=userlogs_keyboard(),
            parse_mode="HTML"
        )
        return

    # ── Channel link input ──
    if context.user_data.get("awaiting_channel"):
        try:
            await update.message.delete()
        except Exception:
            pass
        context.user_data["awaiting_channel"] = False

        username = parse_channel_link(text)
        title    = username.lstrip("@") if username.startswith("@") else username

        cfg      = load_config()
        channels = cfg.get("required_channels", [])
        if any(ch["username"].lower() == username.lower() for ch in channels):
            await update.message.reply_text(
                "⚠️ <b>Already added!</b>\n\nThis channel/group is already in the list.",
                reply_markup=channels_keyboard(),
                parse_mode="HTML"
            )
            return

        channels.append({"title": title, "link": text, "username": username})
        cfg["required_channels"] = channels
        save_config(cfg)

        await update.message.reply_text(
            f"✅ <b>Added Successfully!</b>\n\n"
            f"📢 <code>{username}</code>\n\n"
            f"Users must now join this to use the bot.",
            reply_markup=channels_keyboard(),
            parse_mode="HTML"
        )
        return

    # ── User lookup ──
    if context.user_data.get("awaiting_user_lookup"):
        context.user_data["awaiting_user_lookup"] = False
        query_val = text.strip().lstrip("@")
        users = load_users()
        found_uid, found_u = None, None
        if query_val.isdigit():
            found_uid = query_val
            found_u   = users.get(query_val)
        else:
            for u_id, u_data in users.items():
                if (u_data.get("username") or "").lower() == query_val.lower():
                    found_uid, found_u = u_id, u_data
                    break
        if found_u is None:
            await update.message.reply_text(
                f"❌ <b>User not found</b>\n\n<code>{esc(text)}</code>\n\n"
                f"Make sure the user has started the bot.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="c_users_0")]]),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                user_profile_text(found_uid, found_u),
                reply_markup=user_profile_keyboard(found_uid, found_u),
                parse_mode="HTML"
            )
        return

    # ── Credits input ──
    if context.user_data.get("awaiting_credits_uid"):
        c_uid  = context.user_data.pop("awaiting_credits_uid")
        c_mode = context.user_data.pop("awaiting_credits_mode", "add")
        try:
            amount = int(text.strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            await update.message.reply_text(
                "❌ <b>Invalid amount!</b>\n\nSend a positive number (e.g. <code>100</code>).",
                parse_mode="HTML"
            )
            return
        users = load_users()
        if c_uid not in users:
            await update.message.reply_text("❌ User not found.", parse_mode="HTML")
            return
        old_cr = users[c_uid].get("credits", 0)
        if c_mode == "add":
            users[c_uid]["credits"] = old_cr + amount
            verb = f"➕ Added <b>{amount}</b> credits"
        else:
            users[c_uid]["credits"] = max(0, old_cr - amount)
            verb = f"➖ Removed <b>{amount}</b> credits"
        save_users(users)
        new_cr = users[c_uid]["credits"]
        await update.message.reply_text(
            f"💰 <b>Credits Updated!</b>\n\n"
            f"User: <code>{c_uid}</code>\n"
            f"{verb}\n"
            f"Before: <b>{old_cr:,}</b>  →  After: <b>{new_cr:,}</b>",
            reply_markup=user_profile_keyboard(c_uid, users[c_uid]),
            parse_mode="HTML"
        )
        return

    # ── Delete user confirmation ──
    if context.user_data.get("awaiting_confirm_deluser"):
        target_uid = context.user_data.pop("awaiting_confirm_deluser")
        if text.strip() == "CONFIRM":
            users = load_users()
            users.pop(target_uid, None)
            save_users(users)
            await update.message.reply_text(
                f"🗑 <b>User Deleted!</b>\n\nUser <code>{target_uid}</code> has been removed.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👤 User Manager", callback_data="c_users_0"),
                     InlineKeyboardButton("🏠 Home",         callback_data="c_home")],
                ]),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ Cancelled. Type <code>CONFIRM</code> exactly to delete, or go back.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Back", callback_data="c_users_0")]]),
                parse_mode="HTML"
            )
        return

    # ── Broadcast ──
    if context.user_data.get("awaiting_broadcast"):
        context.user_data["awaiting_broadcast"] = False
        users = load_users()
        total   = len(users)
        success = 0
        fail    = 0
        prog_msg = await update.message.reply_text(
            f"📣 <b>Broadcasting…</b>\n\n0 / {total} sent…",
            parse_mode="HTML"
        )
        broadcast_text = (
            f"📣 <b>Message from Bot Owner</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{text}"
        )
        for i, u_id in enumerate(users):
            try:
                await context.bot.send_message(chat_id=int(u_id), text=broadcast_text, parse_mode="HTML")
                success += 1
            except Exception:
                fail += 1
            if (i + 1) % 20 == 0:
                try:
                    await prog_msg.edit_text(
                        f"📣 <b>Broadcasting…</b>\n\n{i+1} / {total} sent…",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
        await prog_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"📊 Sent : <b>{success}</b>\n"
            f"❌ Failed: <b>{fail}</b>\n"
            f"👥 Total : <b>{total}</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="c_home")]]),
            parse_mode="HTML"
        )
        return

    # ── DM User — step 1: get UID ──
    if context.user_data.get("awaiting_dm_uid"):
        context.user_data["awaiting_dm_uid"] = False
        dm_target = text.strip()
        if not dm_target.isdigit():
            await update.message.reply_text(
                "❌ <b>Invalid User ID!</b>\n\nUser IDs are numbers only (e.g. <code>123456789</code>).",
                parse_mode="HTML"
            )
            return
        context.user_data["awaiting_dm_msg"] = dm_target
        await update.message.reply_text(
            f"💬 <b>DM User</b>\n\n"
            f"Target: <code>{dm_target}</code>\n\n"
            f"Now send the <b>message</b> you want to send to this user:",
            parse_mode="HTML"
        )
        return

    # ── DM User — step 2: send message ──
    if context.user_data.get("awaiting_dm_msg"):
        dm_target = context.user_data.pop("awaiting_dm_msg")
        try:
            await context.bot.send_message(
                chat_id=int(dm_target),
                text=f"💬 <b>Message from Bot Owner</b>\n━━━━━━━━━━━━━━━━━━━━━\n\n{text}",
                parse_mode="HTML"
            )
            await update.message.reply_text(
                f"✅ <b>Message Sent!</b>\n\nDelivered to user <code>{dm_target}</code>.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Send Another", callback_data="c_dm_start"),
                     InlineKeyboardButton("🏠 Home",          callback_data="c_home")],
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ <b>Failed to send!</b>\n\nUser <code>{dm_target}</code> may have blocked the bot.\n\nError: {esc(str(e))}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="c_home")]]),
                parse_mode="HTML"
            )
        return

    # ── Code Create — multi-step ──
    if context.user_data.get("awaiting_code_create"):
        step = context.user_data.get("code_create_step", "credits")

        if step == "credits":
            try:
                cr = int(text.strip())
                if cr <= 0: raise ValueError
            except ValueError:
                await update.message.reply_text("❌ Send a positive number for credits (e.g. <code>100</code>).", parse_mode="HTML")
                return
            context.user_data["code_create_credits"] = cr
            context.user_data["code_create_step"]    = "limit"
            await update.message.reply_text(
                f"🎫 <b>Create Code — Step 2/3</b>\n\n"
                f"Credits: <b>{cr}</b>\n\n"
                f"How many times can this code be used?\n"
                f"📌 Send a number, or <code>0</code> for unlimited:",
                parse_mode="HTML"
            )

        elif step == "limit":
            try:
                lim = int(text.strip())
                if lim < 0: raise ValueError
            except ValueError:
                await update.message.reply_text("❌ Send 0 for unlimited, or a positive number.", parse_mode="HTML")
                return
            context.user_data["code_create_limit"] = lim
            context.user_data["code_create_step"]  = "code"
            await update.message.reply_text(
                f"🎫 <b>Create Code — Step 3/3</b>\n\n"
                f"Credits: <b>{context.user_data['code_create_credits']}</b>\n"
                f"Limit  : <b>{'Unlimited' if lim == 0 else lim}</b>\n\n"
                f"Send the <b>code text</b>, or send <code>AUTO</code> to generate one automatically:",
                parse_mode="HTML"
            )

        elif step == "code":
            cr  = context.user_data.pop("code_create_credits", 0)
            lim = context.user_data.pop("code_create_limit", 0)
            context.user_data.pop("awaiting_code_create", None)
            context.user_data.pop("code_create_step", None)

            if text.strip().upper() == "AUTO":
                code_text = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
            else:
                code_text = text.strip().upper()

            codes = load_codes()
            if code_text in codes:
                await update.message.reply_text(
                    f"❌ Code <code>{esc(code_text)}</code> already exists!\n\nTry a different name.",
                    parse_mode="HTML"
                )
                return
            codes[code_text] = {
                "credits": cr,
                "limit":   lim if lim > 0 else "unlimited",
                "used":    0,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            save_codes(codes)
            await update.message.reply_text(
                f"✅ <b>Code Created!</b>\n\n"
                f"🎫 Code    : <code>{esc(code_text)}</code>\n"
                f"💰 Credits : <b>{cr}</b>\n"
                f"🔢 Limit   : <b>{'Unlimited' if lim == 0 else lim}</b>\n\n"
                f"Users can redeem it with <code>/redeem {esc(code_text)}</code>",
                reply_markup=codes_keyboard(),
                parse_mode="HTML"
            )
        return

    # ── Clear all codes confirmation ──
    if context.user_data.get("awaiting_confirm_clearall"):
        context.user_data.pop("awaiting_confirm_clearall")
        if text.strip() == "CONFIRM":
            save_codes({})
            await update.message.reply_text(
                "🗑 <b>All Codes Cleared!</b>\n\nAll redeem codes have been deleted.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="c_home")]]),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ Cancelled. Type <code>CONFIRM</code> exactly to clear.",
                reply_markup=codes_keyboard(),
                parse_mode="HTML"
            )
        return

    # ── Change Password — step 1: new password ──
    if context.user_data.get("awaiting_new_pass"):
        context.user_data["awaiting_new_pass"]    = False
        context.user_data["awaiting_confirm_pass"] = True
        context.user_data["new_pass_candidate"]    = text.strip()
        try:
            await update.message.delete()
        except Exception:
            pass
        await update.message.reply_text(
            "🔑 <b>Confirm New Password</b>\n\n"
            "Re-enter the new password to confirm:",
            parse_mode="HTML"
        )
        return

    # ── Change Password — step 2: confirm ──
    if context.user_data.get("awaiting_confirm_pass"):
        context.user_data["awaiting_confirm_pass"] = False
        candidate = context.user_data.pop("new_pass_candidate", "")
        try:
            await update.message.delete()
        except Exception:
            pass
        if text.strip() == candidate:
            new_hash = hashlib.sha256(candidate.encode()).hexdigest()
            set_pass_hash(new_hash)
            await update.message.reply_text(
                "✅ <b>Password Changed!</b>\n\n"
                "Your new password is now active.\n"
                "Use it next time you log in.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="c_home")]]),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ <b>Passwords don't match!</b>\n\n"
                "Password was <b>not</b> changed. Try again from Settings.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔑 Try Again", callback_data="c_changepass"),
                     InlineKeyboardButton("🏠 Home",      callback_data="c_home")],
                ]),
                parse_mode="HTML"
            )
        return

    # ── Password input ──
    if not context.user_data.get("awaiting_pass"):
        return

    try:
        await update.message.delete()
    except Exception:
        pass

    if check_pass(text):
        _authenticated.add(uid)
        context.user_data["awaiting_pass"] = False
        await _send_banner_panel(
            update.message,
            "✅ <b>Access Granted!</b>\n\n" + panel_text(),
            main_keyboard()
        )
    else:
        context.user_data["awaiting_pass"] = True
        await update.message.reply_text(
            "❌ <b>Wrong password!</b>\n\nTry again:",
            parse_mode="HTML"
        )



async def safe_edit(query, text, reply_markup=None, parse_mode="HTML"):
    """Works whether the message is a photo (caption) or plain text."""
    try:
        await query.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            await safe_edit(query, text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            pass

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = str(query.from_user.id)

    if not is_owner(uid):
        await query.answer("🚫 Unauthorized.", show_alert=True)
        return

    if not is_authed(uid):
        await query.answer("🔒 Session expired. Send /start to log in.", show_alert=True)
        return

    data = query.data
    await query.answer()

    if data in ("c_home", "c_refresh"):
        try:
            await query.edit_message_caption(
                caption=panel_text(), reply_markup=main_keyboard(), parse_mode="HTML"
            )
        except Exception:
            try:
                await safe_edit(query, panel_text(), reply_markup=main_keyboard(), parse_mode="HTML")
            except Exception:
                pass

    elif data == "c_userlogs":
        await safe_edit(query, userlogs_panel_text(), reply_markup=userlogs_keyboard(), parse_mode="HTML")

    elif data == "c_set_loggroup":
        context.user_data["awaiting_loggroup"] = True
        await safe_edit(query, 
            "📝 <b>Set Log Group</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Send the <b>Group ID</b> where user logs should be sent.\n\n"
            "<b>How to get Group ID:</b>\n"
            "┣ Add the main bot to your group\n"
            "┣ Forward any message from that group to\n"
            "┃   @userinfobot — it shows the chat ID\n"
            "┗ Group IDs usually start with <code>-100</code>\n\n"
            "📌 <b>Send the group ID now:</b>",
            parse_mode="HTML"
        )

    elif data == "c_clear_loggroup":
        cfg = load_config()
        cfg.pop("log_group_id", None)
        save_config(cfg)
        await safe_edit(query, 
            "🗑 <b>Log Group Removed</b>\n\n"
            "User logs are now disabled.\n"
            "Users' messages will no longer be forwarded.",
            reply_markup=userlogs_keyboard(),
            parse_mode="HTML"
        )

    elif data == "c_channels":
        await safe_edit(query, channels_panel_text(), reply_markup=channels_keyboard(), parse_mode="HTML")

    elif data == "c_add_channel":
        cfg      = load_config()
        channels = cfg.get("required_channels", [])
        if len(channels) >= MAX_CHANNELS:
            await query.answer(f"🚫 Limit reached! Max {MAX_CHANNELS} channels allowed.", show_alert=True)
            await safe_edit(query, channels_panel_text(), reply_markup=channels_keyboard(), parse_mode="HTML")
            return
        context.user_data["awaiting_channel"] = True
        await safe_edit(query, 
            f"📢 <b>Add Channel / Group</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 Slots used: <b>{len(channels)} / {MAX_CHANNELS}</b>\n\n"
            f"Send the channel or group link/username:\n\n"
            f"<b>Accepted formats:</b>\n"
            f"┣ <code>https://t.me/username</code>\n"
            f"┣ <code>@username</code>\n"
            f"┗ <code>username</code>\n\n"
            f"⚠️ Bot must be <b>admin</b> in that channel/group to verify members.",
            parse_mode="HTML"
        )

    elif data.startswith("c_remove_ch_"):
        idx = int(data.split("c_remove_ch_")[-1])
        cfg      = load_config()
        channels = cfg.get("required_channels", [])
        if 0 <= idx < len(channels):
            removed = channels.pop(idx)
            cfg["required_channels"] = channels
            save_config(cfg)
            await safe_edit(query, 
                f"🗑 <b>Removed!</b>\n\n"
                f"<code>{removed['username']}</code> removed from required channels.\n\n"
                f"{channels_panel_text()}",
                reply_markup=channels_keyboard(),
                parse_mode="HTML"
            )
        else:
            await safe_edit(query, channels_panel_text(), reply_markup=channels_keyboard(), parse_mode="HTML")

    elif data == "c_logout":
        _authenticated.discard(uid)
        context.user_data["awaiting_pass"] = False
        await safe_edit(query, 
            "🔒 <b>Logged out.</b>\n\nSend /start to log in again.",
            parse_mode="HTML"
        )

    elif data.startswith("c_feat_"):
        page = int(data.split("_")[-1])
        await safe_edit(query, feat_panel_text(), reply_markup=features_keyboard(page), parse_mode="HTML")

    elif data.startswith("cf_"):
        key   = data[3:]
        feats = load_features()
        feats[key] = not feats.get(key, True)
        save_features(feats)
        await safe_edit(query, feat_panel_text(), reply_markup=features_keyboard(0), parse_mode="HTML")

    elif data == "c_allon":
        save_features({k: True for k in FEATURES})
        await safe_edit(query, feat_panel_text(), reply_markup=features_keyboard(0), parse_mode="HTML")

    elif data == "c_alloff":
        save_features({k: False for k in FEATURES})
        await safe_edit(query, feat_panel_text(), reply_markup=features_keyboard(0), parse_mode="HTML")

    elif data == "c_logs":
        try:
            with open(LOG_FILE, encoding="utf-8") as f:
                lines = f.readlines()[-50:]
            log_text = "".join(lines).strip() or "No logs yet."
        except FileNotFoundError:
            log_text = "📭 No log file found yet."
        if len(log_text) > 3500:
            log_text = "…" + log_text[-3500:]
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Refresh", callback_data="c_logs"),
             InlineKeyboardButton("🗑 Clear",   callback_data="c_clearlogs")],
            [InlineKeyboardButton("🏠 Home",    callback_data="c_home")],
        ])
        await safe_edit(query, 
            f"📋 <b>Live Logs</b> (last 50 lines)\n\n<pre>{log_text}</pre>",
            reply_markup=kb, parse_mode="HTML"
        )

    elif data == "c_clearlogs":
        try:
            open(LOG_FILE, "w").close()
            msg = "🗑 Log file cleared."
        except Exception as e:
            msg = f"❌ Could not clear: {e}"
        await safe_edit(query, msg, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="c_home")]
        ]))

    elif data == "c_pause":
        os.makedirs("bot", exist_ok=True)
        with open(PAUSE_FILE, "w") as f:
            f.write(datetime.now().isoformat())
        await safe_edit(query, 
            "⏸️ <b>Bot Paused</b>\n\nAll user commands are blocked.\nUsers will see a maintenance message.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Resume", callback_data="c_resume"),
                 InlineKeyboardButton("🏠 Home",   callback_data="c_home")],
            ]), parse_mode="HTML"
        )

    elif data == "c_resume":
        try:
            os.remove(PAUSE_FILE)
        except FileNotFoundError:
            pass
        await safe_edit(query, 
            "▶️ <b>Bot Resumed</b>\n\nAll commands are active again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="c_home")]
            ]), parse_mode="HTML"
        )

    elif data == "c_restart":
        pid = get_main_pid()
        if pid and process_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                result = f"🔄 SIGTERM sent to PID {pid}\nWorkflow will auto-restart the bot."
            except Exception as e:
                result = f"❌ Failed: {e}"
        else:
            result = "⚠️ Process not found. Use Spawn to start it manually."
        await safe_edit(query, result, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="c_home")]
        ]))

    elif data == "c_kill":
        pid = get_main_pid()
        if pid and process_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
                result = f"🛑 SIGKILL sent to PID {pid}\nProcess forcefully terminated."
            except Exception as e:
                result = f"❌ Failed: {e}"
        else:
            result = "⚠️ No running process found."
        await safe_edit(query, result, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="c_home")]
        ]))

    elif data == "c_spawn":
        try:
            proc = subprocess.Popen(
                [sys.executable, MAIN_BOT_SCRIPT],
                stdout=open(LOG_FILE, "a"),
                stderr=subprocess.STDOUT
            )
            result = f"🟢 Spawned new bot process\nPID: <b>{proc.pid}</b>"
        except Exception as e:
            result = f"❌ Failed to spawn: {e}"
        await safe_edit(query, result, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="c_home")]
        ]), parse_mode="HTML")

    elif data == "c_noop":
        pass

    # ──── USER MANAGER ────
    elif data.startswith("c_users_"):
        page = int(data.split("c_users_")[-1])
        await safe_edit(query, users_list_text(page), reply_markup=users_list_keyboard(page), parse_mode="HTML")

    elif data == "c_user_search":
        context.user_data["awaiting_user_lookup"] = True
        await safe_edit(query, 
            "🔍 <b>Search User</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Send the <b>User ID</b> or <b>@username</b> to look up:\n\n"
            "📌 User IDs are numeric (e.g. <code>123456789</code>)\n"
            "📌 Usernames start with @ (e.g. <code>@john</code>)",
            parse_mode="HTML"
        )

    elif data.startswith("c_viewuser_"):
        uid2 = data.split("c_viewuser_")[-1]
        users = load_users()
        u = users.get(uid2)
        if not u:
            await query.answer("❌ User not found.", show_alert=True)
            return
        await safe_edit(query, user_profile_text(uid2, u), reply_markup=user_profile_keyboard(uid2, u), parse_mode="HTML")

    elif data.startswith("c_ban_"):
        uid2 = data.split("c_ban_")[-1]
        users = load_users()
        if uid2 not in users:
            await query.answer("❌ User not found.", show_alert=True); return
        users[uid2]["banned"] = True
        save_users(users)
        await safe_edit(query, user_profile_text(uid2, users[uid2]), reply_markup=user_profile_keyboard(uid2, users[uid2]), parse_mode="HTML")
        await query.answer("✅ User banned!", show_alert=True)

    elif data.startswith("c_unban_"):
        uid2 = data.split("c_unban_")[-1]
        users = load_users()
        if uid2 not in users:
            await query.answer("❌ User not found.", show_alert=True); return
        users[uid2]["banned"] = False
        save_users(users)
        await safe_edit(query, user_profile_text(uid2, users[uid2]), reply_markup=user_profile_keyboard(uid2, users[uid2]), parse_mode="HTML")
        await query.answer("✅ User unbanned!", show_alert=True)

    elif data.startswith("c_mkadmin_"):
        uid2 = data.split("c_mkadmin_")[-1]
        users = load_users()
        if uid2 not in users:
            await query.answer("❌ User not found.", show_alert=True); return
        users[uid2]["is_admin"] = True
        save_users(users)
        await safe_edit(query, user_profile_text(uid2, users[uid2]), reply_markup=user_profile_keyboard(uid2, users[uid2]), parse_mode="HTML")
        await query.answer("👑 Made admin!", show_alert=True)

    elif data.startswith("c_deadmin_"):
        uid2 = data.split("c_deadmin_")[-1]
        users = load_users()
        if uid2 not in users:
            await query.answer("❌ User not found.", show_alert=True); return
        users[uid2]["is_admin"] = False
        save_users(users)
        await safe_edit(query, user_profile_text(uid2, users[uid2]), reply_markup=user_profile_keyboard(uid2, users[uid2]), parse_mode="HTML")
        await query.answer("✅ Admin removed!", show_alert=True)

    elif data.startswith("c_addcr_"):
        uid2 = data.split("c_addcr_")[-1]
        context.user_data["awaiting_credits_uid"]  = uid2
        context.user_data["awaiting_credits_mode"] = "add"
        await safe_edit(query, 
            f"💰 <b>Add Credits</b>\n\n"
            f"Adding credits to user <code>{uid2}</code>\n\n"
            f"Send the <b>amount</b> to add (e.g. <code>500</code>):",
            parse_mode="HTML"
        )

    elif data.startswith("c_remcr_"):
        uid2 = data.split("c_remcr_")[-1]
        context.user_data["awaiting_credits_uid"]  = uid2
        context.user_data["awaiting_credits_mode"] = "remove"
        await safe_edit(query, 
            f"💸 <b>Remove Credits</b>\n\n"
            f"Removing credits from user <code>{uid2}</code>\n\n"
            f"Send the <b>amount</b> to remove (e.g. <code>200</code>):",
            parse_mode="HTML"
        )

    elif data.startswith("c_deluser_"):
        uid2 = data.split("c_deluser_")[-1]
        users = load_users()
        if uid2 not in users:
            await query.answer("❌ User not found.", show_alert=True); return
        context.user_data["awaiting_confirm_deluser"] = uid2
        await safe_edit(query, 
            f"⚠️ <b>Delete User?</b>\n\n"
            f"User ID: <code>{uid2}</code>\n\n"
            f"This will permanently remove this user and all their data.\n"
            f"This action <b>cannot be undone.</b>\n\n"
            f"Type <code>CONFIRM</code> to proceed:",
            parse_mode="HTML"
        )

    # ──── BROADCAST ────
    elif data == "c_broadcast":
        context.user_data["awaiting_broadcast"] = True
        await safe_edit(query, 
            "📣 <b>Broadcast Message</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Send your message below and it will be forwarded to <b>ALL</b> bot users.\n\n"
            "✅ Supports: Text, Bold, Italic, Links\n"
            "✅ You can include emojis\n\n"
            "⚠️ This cannot be undone — send carefully!\n\n"
            "📌 Send your broadcast message now:",
            parse_mode="HTML"
        )

    # ──── CODE MANAGER ────
    elif data == "c_codes":
        await safe_edit(query, codes_list_text(), reply_markup=codes_keyboard(), parse_mode="HTML")

    elif data == "c_createcode":
        context.user_data["awaiting_code_create"] = True
        context.user_data["code_create_step"]     = "credits"
        await safe_edit(query, 
            "🎫 <b>Create Redeem Code</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>Step 1/3</b> — How many credits should this code give?\n\n"
            "📌 Send a number (e.g. <code>100</code>):",
            parse_mode="HTML"
        )

    elif data.startswith("c_delcode_"):
        code = data[len("c_delcode_"):]
        codes = load_codes()
        if code in codes:
            codes.pop(code)
            save_codes(codes)
            await query.answer(f"🗑 Code '{code}' deleted!", show_alert=True)
        else:
            await query.answer("❌ Code not found.", show_alert=True)
        await safe_edit(query, codes_list_text(), reply_markup=codes_keyboard(), parse_mode="HTML")

    elif data == "c_clearallcodes":
        context.user_data["awaiting_confirm_clearall"] = True
        await safe_edit(query, 
            "⚠️ <b>Clear All Codes?</b>\n\n"
            "This will delete <b>ALL</b> redeem codes permanently.\n\n"
            "Type <code>CONFIRM</code> to proceed:",
            parse_mode="HTML"
        )

    # ──── DM USER ────
    elif data == "c_dm_user":
        await safe_edit(query, dm_user_text(), reply_markup=dm_user_keyboard(), parse_mode="HTML")

    elif data == "c_dm_start":
        context.user_data["awaiting_dm_uid"] = True
        await safe_edit(query, 
            "💬 <b>DM User</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Send the <b>User ID</b> of the user you want to message:\n\n"
            "📌 Example: <code>123456789</code>",
            parse_mode="HTML"
        )

    # ──── CHANGE PASSWORD ────
    elif data == "c_changepass":
        context.user_data["awaiting_new_pass"]    = True
        context.user_data["awaiting_confirm_pass"] = False
        context.user_data["new_pass_candidate"]    = None
        await safe_edit(query, 
            "🔑 <b>Change Password</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "All current sessions will remain active.\n"
            "You'll need the new password next time you log in.\n\n"
            "📌 Send your <b>new password</b>:",
            parse_mode="HTML"
        )

    # ──── BACKUP FILES ────
    elif data == "c_backup":
        files_to_send = [
            (USER_FILE,     "👥 user.json — user data & credits"),
            (CODES_FILE,    "🎫 codes.json — redeem codes"),
            (CONFIG_FILE,   "⚙️ config.json — bot configuration"),
            (FEATURES_FILE, "🔧 features.json — feature flags"),
            (LOG_FILE,      "📋 shuvo.log — runtime log"),
        ]
        await safe_edit(query, 
            "📁 <b>Backup Files</b>\n\n"
            "Sending all data files now…",
            parse_mode="HTML"
        )
        sent = 0
        for fpath, label in files_to_send:
            if os.path.exists(fpath):
                try:
                    with open(fpath, "rb") as fp:
                        await context.bot.send_document(
                            chat_id=uid,
                            document=fp,
                            filename=os.path.basename(fpath),
                            caption=f"📦 {label}"
                        )
                    sent += 1
                except Exception as e:
                    await context.bot.send_message(chat_id=uid, text=f"❌ Could not send {fpath}: {e}")
        await context.bot.send_message(
            chat_id=uid,
            text=f"✅ <b>Backup Complete!</b>\n\nSent <b>{sent}</b> files.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="c_home")]]),
            parse_mode="HTML"
        )

    elif data == "c_stats":
        try:
            with open("bot/user.json") as f:
                users = json.load(f)
            total    = len(users)
            active   = sum(1 for u in users.values() if not u.get("banned"))
            banned   = total - active
            admins   = sum(1 for u in users.values() if u.get("is_admin"))
            tot_cr   = sum(u.get("credits", 0) for u in users.values())
            has_uname= sum(1 for u in users.values() if u.get("username"))
        except Exception:
            total = active = banned = admins = tot_cr = has_uname = 0
        try:
            with open("bot/codes.json") as f:
                codes = json.load(f)
            n_codes = len(codes)
        except Exception:
            n_codes = 0
        try:
            log_size = os.path.getsize(LOG_FILE) // 1024
        except Exception:
            log_size = 0
        cfg     = load_config()
        ch_cnt  = len(cfg.get("required_channels", []))
        log_grp = "✅ Set" if cfg.get("log_group_id") else "❌ Not set"
        state, mode = bot_status_line()
        feats   = load_features()
        on_cnt  = sum(1 for v in feats.values() if v)
        off_cnt = len(feats) - on_cnt
        now     = datetime.now().strftime("%d %b %Y  %H:%M:%S")
        await safe_edit(query, 
            f"📊 <b>SHUVO BOT — Full Stats</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 <b>Users</b>\n"
            f"   ┣ Total       : <b>{total}</b>\n"
            f"   ┣ Active      : <b>{active}</b>\n"
            f"   ┣ Banned      : <b>{banned}</b>\n"
            f"   ┣ Admins      : <b>{admins}</b>\n"
            f"   ┗ With @user  : <b>{has_uname}</b>\n\n"
            f"💰 <b>Economy</b>\n"
            f"   ┣ Total Credits : <b>{tot_cr:,}</b>\n"
            f"   ┗ Redeem Codes  : <b>{n_codes}</b>\n\n"
            f"🔧 <b>Features</b>\n"
            f"   ┣ Enabled  : <b>{on_cnt}</b>  ✅\n"
            f"   ┗ Disabled : <b>{off_cnt}</b>  ❌\n\n"
            f"⚙️ <b>Config</b>\n"
            f"   ┣ Force Join  : <b>{ch_cnt}/5</b> channels\n"
            f"   ┣ User Logs   : {log_grp}\n"
            f"   ┗ Log Size    : <b>{log_size} KB</b>\n\n"
            f"🤖 <b>Process</b>\n"
            f"   ┣ {state}\n"
            f"   ┗ {mode}\n\n"
            f"🕐 <b>Checked</b>: {now}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Refresh", callback_data="c_stats"),
                 InlineKeyboardButton("🏠 Home",    callback_data="c_home")],
            ]), parse_mode="HTML"
        )


def main():
    print("Controller bot starting...")
    app = Application.builder().token(CONTROLLER_TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("logout", cmd_logout))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Controller bot running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
