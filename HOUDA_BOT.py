# -*- coding: utf-8 -*-
# ============================================================
#   مصنع تليثون الموحد - HOUDA FACTORY (نسخة مدمجة ومُصلحة)
# ============================================================
#  هذا الملف هو دمج كامل للمصنعين في مصنع واحد بملف واحد:
#   1) سورس تليثون خاص بالمطور حودا
#   2) سورس مصنع تليثون
#  جميع الميزات موجودة بدون حذف أي ميزة، مع إصلاح الأخطاء.
#
#  الميزات المدمجة بالكامل:
#  [سورس الحساب - Userbot]
#   - الردود التلقائية المخصصة (اضافة رد / حذف رد / الردود)
#   - رد الترحيب (هلا) + الرد التلقائي العام (الرد التلقائي / ايقاف الرد التلقائي)
#   - العد التنازلي (وقت) + ايقاف
#   - تغيير الاسم (اسم) + الوقت الحي في الاسم (تفعيل الوقت / تعطيل الوقت)
#   - مسح الرسائل / نشر في المجموعات / حذف المنشورة / الرسائل
#   - كتم مستخدم / المكتومين / الغاء الكتم (يعمل بالمجموعات والقنوات الكبرى)
#   - نقل عضو مع الكتم التلقائي في المجموعة الجديدة
#   - تفعيل الكليشة (تبليغ تليجرام) / الغاء تفعيل الكليشة
#   - معلوماتي / الاشتراك الاجباري / الغاء الاشتراك الاجباري / اضافة قناة
#   - اذاعه للمستخدمين / النشر التلقائي في المجموعات / ايقاف النشر التلقائي
#  [المصنع - بوت الإدارة]
#   - /start مع اشتراك اجباري في قناة المصنع @SorSesshouda والتحقق من كل مستخدم جديد
#   - اضافه حساب (رقم + كود + تحقق بخطوتين) + ادارة تليثون (تفعيل/ايقاف السورس)
#   - لوحة الأدمن: اذاعة برسالة + الوضع المدفوع + جميع الحسابات المسجله
#     + الحسابات النشطه + تنظيف الجلسات المنتهيه + سحب حساب (مراقبة 777000 حية)
#   - إشعارات الأدمن: مستخدم جديد + تسجيل دخول جديد
#
#  المطور: @H_P_P02 | القناة: @sorsehoda | قناة الاشتراك الاجباري للمصنع: @SorSesshouda
#  الإصدار: أزرار بألوان حقيقية من تليجرام (Bot API 9.4+): primary أزرق / success أخضر / danger أحمر
# ============================================================

import os
import sys
import subprocess
import asyncio
import json
import pickle
import re
import datetime
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from telethon.sync import TelegramClient, events
from telethon import utils
# تم تصحيح مسارات الاستيراد وإضافة خاصية نقل العضو
from telethon.tl.functions.account import UpdateProfileRequest, ReportPeerRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantsRequest, GetParticipantRequest
from telethon.tl.functions.messages import DeleteMessagesRequest
from telethon.errors.rpcerrorlist import (MessageNotModifiedError, FloodWaitError,
    SessionPasswordNeededError, UserNotParticipantError, AuthKeyUnregisteredError,
    UserAlreadyParticipantError, ChatAdminRequiredError)
# تم تصحيح اسم كلاس الإبلاغ هنا
from telethon.tl.types import (ChannelParticipantCreator, ChannelParticipantAdmin,
    InputReportReasonSpam, InputPeerUser, ChannelParticipantsSearch)
from telethon.tl.custom import Button
import pytz

# ==========================================
# إعدادات البوت والمصنع
# ==========================================
API_ID = 20257283
API_HASH = 'dc89a0cea4e184cc2175eed7149efff0'
BOT_TOKEN = '8307133240:AAGBxNnhYPAJhTIp6nQOJsDIpi_qFKsvGJQ'
ADMIN_ID = 8529218230
DEVELOPER_LINK = "https://t.me/H_P_P02"
CHANNEL_LINK = "https://t.me/sorsehoda"
FORCE_SUB_CHANNEL = 'SorSesshouda'

# نص زر لوحة المفاتيح (القائمة الرئيسية) - ويُقبل النص القديم أيضاً للتوافق
HOME_KEYBOARD_TEXT = '🏠 القائمة الرئيسية'

# المجلدات
SESSIONS_FOLDER = 'Sessions'
DATA_FOLDER = 'Data'
Path(SESSIONS_FOLDER).mkdir(exist_ok=True)
Path(DATA_FOLDER).mkdir(exist_ok=True)

# ملفات البيانات
USERS_DB_FILE = os.path.join(DATA_FOLDER, 'users_db.json')
ACCOUNTS_DB_FILE = os.path.join(DATA_FOLDER, 'accounts_db.json')
SETTINGS_FILE = os.path.join(DATA_FOLDER, 'settings.json')

# تجمع خيوط (Thread Pool) لعمليات الملفات
executor = ThreadPoolExecutor(max_workers=10)

# أقفال لتجنب تعارض الكتابة
db_lock = asyncio.Lock()

# قاموس لتخزين مهام المراقبة (Monitor 777000)
monitoring_tasks = {}

# إصلاح: جدول تحويل حقيقي للأرقام السفلية (Superscript) بدل علامات الاستفهام المكسورة
SUPERSCRIPT_TABLE = str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')


def load_json(file):
    if os.path.exists(file):
        try:
            return json.load(open(file, 'r', encoding='utf-8'))
        except Exception as e:
            print(f"Error loading json {file}: {e}")
            return {}
    return {}

def sync_save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def save_json(file, data):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, sync_save_json, file, data)

users_db = load_json(USERS_DB_FILE)
accounts_db = load_json(ACCOUNTS_DB_FILE)
settings = load_json(SETTINGS_FILE)

temp_login_data = {}

# ==========================================
# دوال مساعدة للإشعارات والميزات الجديدة
# ==========================================
async def send_admin_notification(text, buttons=None):
    """إرسال إشعار للأدمن"""
    try:
        await bot_client.send_message(ADMIN_ID, text, buttons=buttons)
    except Exception as e:
        print(f"Error sending admin notification: {e}")

# ==========================================
# كلاس السورس الكامل (Houda Full Source)
# ==========================================
class HoudaSourceFull:
    def __init__(self, client, phone, account_id, owner_uid=None):
        self.client = client
        self.phone = phone
        self.account_id = account_id
        self.owner_uid = owner_uid
        self.is_active = True

        self.folder = os.path.join(DATA_FOLDER, f"acc_{account_id}")
        Path(self.folder).mkdir(exist_ok=True)

        # ملفات السورس
        self.response_file = os.path.join(self.folder, 'responses.pkl')
        self.published_messages_file = os.path.join(self.folder, 'published_messages.pkl')
        self.muted_users_file = os.path.join(self.folder, 'muted_users.pkl')
        self.time_update_status_file = os.path.join(self.folder, 'time_update_status.pkl')
        self.channel_link_file = os.path.join(self.folder, 'channel_link.pkl')

        # ملفات جديدة
        self.auto_reply_file = os.path.join(self.folder, 'auto_reply.pkl')
        self.auto_poster_file = os.path.join(self.folder, 'auto_poster.pkl')

        self.image_path = 'local_image.jpg'

        # المتغيرات الأساسية
        self.responses = {}
        self.published_messages = []
        # الصيغة الجديدة: {user_id: {'username': '', 'groups': [chat_ids]}}
        self.muted_data = {}
        self.time_status = {'enabled': False}
        self.channel_link = None
        self.active_timers = {}
        self.countdown_messages = {}
        self.account_name = None
        self.my_username = None
        self._me_lock = asyncio.Lock()

        # متغيرات الميزات الجديدة
        self.auto_reply_text = None
        self.auto_poster_task = None
        self.auto_poster_active = False
        self.updater_running = False

        # حالة الانتظار للأوامر (Flow states)
        self.admin_states = {}

        # تحميل البيانات (متزامنة)
        self.load_data()

        # إضافة الأحداث
        self.add_handlers()

    # ---------- أدوات مساعدة ----------
    @staticmethod
    def _unmark_id(chat_id):
        """إصلاح مهم: تحويل معرف المحادثة المُعلَّم (-100xxxx / -xxxx) إلى المعرف الخام
        حتى تعمل المقارنة مع المعرفات المخزنة من get_entity في كل أنواع المجموعات."""
        s = str(chat_id)
        if s.startswith('-100'):
            return int(s[4:])
        if s.startswith('-'):
            return int(s[1:])
        try:
            return int(chat_id)
        except Exception:
            return chat_id

    async def get_me_cached(self):
        async with self._me_lock:
            if self.my_username is None:
                try:
                    me = await self.client.get_me()
                    self.my_username = me.username if me.username else "me"
                    if self.account_name is None:
                        self.account_name = me.first_name
                except: pass
        return self.my_username

    def load_data(self):
        try:
            if os.path.exists(self.response_file):
                self.responses = pickle.load(open(self.response_file, 'rb'))
            if os.path.exists(self.published_messages_file):
                self.published_messages = pickle.load(open(self.published_messages_file, 'rb'))

            # إصلاح مشكلة تحويل بيانات الكتم القديمة (set) إلى الجديدة (dict)
            if os.path.exists(self.muted_users_file):
                loaded_muted = pickle.load(open(self.muted_users_file, 'rb'))
                if isinstance(loaded_muted, set):
                    print(f"Found old mute data format (set) for {self.phone}. Resetting to new format (dict).")
                    self.muted_data = {}
                elif isinstance(loaded_muted, dict):
                    self.muted_data = loaded_muted
                else:
                    self.muted_data = {}

            if os.path.exists(self.time_update_status_file):
                self.time_status = pickle.load(open(self.time_update_status_file, 'rb'))
            if os.path.exists(self.channel_link_file):
                self.channel_link = pickle.load(open(self.channel_link_file, 'rb'))
            if os.path.exists(self.auto_reply_file):
                self.auto_reply_text = pickle.load(open(self.auto_reply_file, 'rb'))
            # إصلاح: لم نعد نعبث بمتغير الرد التلقائي من ملف الناشر التلقائي
            if os.path.exists(self.auto_poster_file):
                try:
                    self.auto_poster_state = pickle.load(open(self.auto_poster_file, 'rb'))
                except Exception:
                    self.auto_poster_state = {}
        except Exception as e:
            print(f"Error loading data for {self.phone}: {e}")

    async def save_data_files(self):
        async with db_lock:
            try:
                pickle.dump(self.responses, open(self.response_file, 'wb'))
                pickle.dump(self.published_messages, open(self.published_messages_file, 'wb'))
                pickle.dump(self.muted_data, open(self.muted_users_file, 'wb'))
                pickle.dump(self.time_status, open(self.time_update_status_file, 'wb'))
                if self.channel_link:
                    pickle.dump(self.channel_link, open(self.channel_link_file, 'wb'))
                if self.auto_reply_text is not None:
                    pickle.dump(self.auto_reply_text, open(self.auto_reply_file, 'wb'))
            except Exception as e:
                print(f"Error saving data for {self.phone}: {e}")

    def add_handlers(self):
        self.client.add_event_handler(self.respond_to_greeting, events.NewMessage(incoming=True))
        self.client.add_event_handler(self.check_subscription, events.NewMessage(incoming=True))
        self.client.add_event_handler(self.handle_auto_reply, events.NewMessage(incoming=True))
        # تم تعديل الشرط ليشمل القنوات والمجموعات الكبرى (معالج الكتم الشامل)
        self.client.add_event_handler(self.handle_global_mute, events.NewMessage(incoming=True))

        # أوامر من نفسي (تم تعديلها للعربية + إصلاح تعارض الأوامر بمراسي ^ و $)
        self.client.add_event_handler(self.add_response, events.NewMessage(from_users='me', pattern=r'^اضافة رد'))
        self.client.add_event_handler(self.delete_response, events.NewMessage(from_users='me', pattern=r'^حذف رد'))
        self.client.add_event_handler(self.show_responses, events.NewMessage(from_users='me', pattern=r'^الردود'))
        self.client.add_event_handler(self.countdown_timer, events.NewMessage(from_users='me', pattern=r'^وقت'))
        self.client.add_event_handler(self.stop_timers, events.NewMessage(from_users='me', pattern=r'^ايقاف$'))
        self.client.add_event_handler(self.show_commands, events.NewMessage(from_users='me', pattern=r'^الاوامر'))
        self.client.add_event_handler(self.set_account_name, events.NewMessage(from_users='me', pattern=r'^اسم'))
        self.client.add_event_handler(self.delete_messages, events.NewMessage(from_users='me', pattern=r'^مسح'))
        self.client.add_event_handler(self.publish_message, events.NewMessage(from_users='me', pattern=r'^نشر'))
        self.client.add_event_handler(self.delete_published_messages, events.NewMessage(from_users='me', pattern=r'^حذف$'))
        self.client.add_event_handler(self.show_published_messages, events.NewMessage(from_users='me', pattern=r'^الرسائل'))

        # أوامر الكتم الجديدة
        self.client.add_event_handler(self.cmd_mute_user, events.NewMessage(from_users='me', pattern=r'^كتم'))
        self.client.add_event_handler(self.cmd_unmute_user, events.NewMessage(from_users='me', pattern=r'^المكتومين'))
        self.client.add_event_handler(self.cmd_unmute_all, events.NewMessage(from_users='me', pattern=r'^الغاء الكتم'))
        self.client.add_event_handler(self.cmd_move_user, events.NewMessage(from_users='me', pattern=r'^نقل عضو'))
        self.client.add_event_handler(self.handle_admin_steps, events.NewMessage(from_users='me'))
        self.client.add_event_handler(self.handle_unmute_callback, events.CallbackQuery())

        # أوامر إضافية
        self.client.add_event_handler(self.cmd_report_spam, events.NewMessage(from_users='me', pattern=r'^تفعيل الكليشة'))
        self.client.add_event_handler(self.cmd_cancel_report, events.NewMessage(from_users='me', pattern=r'^الغاء تفعيل الكليشة'))
        self.client.add_event_handler(self.cmd_my_info, events.NewMessage(from_users='me', pattern=r'^معلوماتي'))
        self.client.add_event_handler(self.cmd_disable_force_sub, events.NewMessage(from_users='me', pattern=r'^الغاء الاشتراك الاجباري'))
        self.client.add_event_handler(self.cmd_enable_time, events.NewMessage(from_users='me', pattern=r'^تفعيل الوقت'))
        self.client.add_event_handler(self.cmd_disable_time, events.NewMessage(from_users='me', pattern=r'^تعطيل الوقت'))

        # الرد التلقائي
        self.client.add_event_handler(self.cmd_set_auto_reply, events.NewMessage(from_users='me', pattern=r'^الرد التلقائي'))
        self.client.add_event_handler(self.cmd_stop_auto_reply, events.NewMessage(from_users='me', pattern=r'^ايقاف الرد التل(ف|ق)ائي'))

        # الإذاعة والنشر
        self.client.add_event_handler(self.cmd_broadcast_users, events.NewMessage(from_users='me', pattern=r'^اذاعه للمستخدمين'))
        self.client.add_event_handler(self.cmd_auto_poster_groups, events.NewMessage(from_users='me', pattern=r'^النشر التلقائي في المجموعات'))
        self.client.add_event_handler(self.cmd_stop_auto_poster, events.NewMessage(from_users='me', pattern=r'^ايقاف النشر التلقائي'))

        # أوامر قديمة
        self.client.add_event_handler(self.add_channel, events.NewMessage(from_users='me', pattern=r'^اضافة قناة (.+)'))

    # ==========================================
    # دوال السورس الجديدة والمعدلة
    # ==========================================

    async def handle_global_mute(self, event):
        """فحص الرسائل الواردة وحذفها إذا كان المرسل مكتوماً في هذه المجموعة/القناة
        (يعمل في المجموعات العادية والقنوات الكبرى Megagroups)."""
        if not self.is_active: return
        if not (event.is_group or event.is_channel): return

        sender_id = event.sender_id
        chat_id = event.chat_id

        if sender_id in self.muted_data:
            muted_chats = self.muted_data[sender_id].get('groups', [])
            # إصلاح: مقارنة موحدة (المعرف المُعلَّم والمعرف الخام) حتى يعمل الكتم فعلياً
            plain_chat_id = self._unmark_id(chat_id)
            if chat_id in muted_chats or plain_chat_id in muted_chats:
                try:
                    await event.delete()
                except Exception as e:
                    print(f"Error deleting message: {e}")

    async def handle_auto_reply(self, event):
        """الرد التلقائي على الرسائل الواردة (بدون تكرار مع رد الترحيب أو الردود المخصصة)"""
        if not self.is_active or event.is_group: return
        if not self.auto_reply_text: return

        text_lower = (event.raw_text or '').lower()
        # إصلاح: منع الرد المزدوج - رد الترحيب والردود المخصصة لها معالجاتها
        if "هلا" in text_lower:
            return
        for keyword in self.responses:
            if keyword and keyword in text_lower:
                return

        sender = await event.get_sender()
        if not sender or (hasattr(sender, 'bot') and sender.bot): return
        # إصلاح: لا نرد إذا كان المستخدم غير مشترك (الاشتراك الإجباري يتكفل بالرد)
        if self.channel_link and not await self.is_subscribed(event.sender_id):
            return

        try:
            await event.reply(self.auto_reply_text)
        except: pass

    async def cmd_mute_user(self, event):
        """بداية عملية كتم مستخدم - تفاعلي لمنع تكرار الردود"""
        if not self.is_active: return
        # تنظيف أي حالة قديمة
        self.admin_states.pop(event.chat_id, None)

        self.admin_states[event.chat_id] = {'step': 'mute_get_id'}
        await event.edit("👤 **أرسل آيدي المستخدم المراد كتمه:**")

    async def cmd_unmute_user(self, event):
        """عرض قائمة المكتومين"""
        if not self.is_active: return
        if not self.muted_data:
            await event.reply("📭 **لا يوجد مستخدمين مكتومين حالياً.**")
            return

        text = "📋 **قائمة المستخدمين المكتومين:**\n\n"
        buttons = []

        for uid, data in self.muted_data.items():
            username = data.get('username', 'بدون يوزر')
            groups_count = len(data.get('groups', []))
            text += f"🔹 `{uid}` ({username}) - {groups_count} مجموعات\n"
            buttons.append([Button.inline(f"🔓 فك الكتم | {username}", f"unmute_{uid}", style='success')])

        buttons.append([Button.inline("❌ إغلاق القائمة", b"close_list", style='danger')])
        try:
            if event.message.reply_markup:
                await event.edit(text, buttons=buttons)
            else:
                await event.reply(text, buttons=buttons)
        except: await event.reply(text, buttons=buttons)

    async def cmd_unmute_all(self, event):
        """الغاء الكتم بالكامل - أمر جديد"""
        if not self.is_active: return
        # تنظيف الحالة إذا كانت موجودة
        self.admin_states.pop(event.chat_id, None)

        try:
            # استخراج الرقم من النص (يتعامل مع الحروف الإضافية أو التنسيق)
            text = event.raw_text
            parts = text.split(' ', 1)
            if len(parts) < 2:
                await event.reply("⚠️ **يرجى إرسال الآيدي مع الأمر.\nالصيغة: الغاء الكتم (آيدي المستخدم)**")
                return

            uid_str = parts[1]
            # البحث عن الأرقام داخل النص
            numbers = re.findall(r'\d+', uid_str)
            if not numbers:
                await event.reply("❌ **آيدي غير صحيح!**")
                return

            target_id = int(numbers[0])

            if target_id in self.muted_data:
                username = self.muted_data[target_id].get('username', 'غير معروف')
                # حذف المستخدم من القاموس بالكامل
                del self.muted_data[target_id]
                await self.save_data_files()
                # محاولة حذف الرسالة القديمة
                try:
                    await event.delete()
                except: pass
                await event.reply(f"✅ **تم الغاء كتم المستخدم {username} (`{target_id}`) بنجاح وازالته من كل المجموعات.**")
            else:
                # محاولة حذف رسالة الخطأ
                try:
                    await event.delete()
                except: pass
                await event.reply("⚠️ **هذا المستخدم غير موجود في قائمة المكتومين.**")
        except Exception as e:
            print(f"Error in unmute_all: {e}")
            self.admin_states.pop(event.chat_id, None)

    async def cmd_move_user(self, event):
        """بدء عملية نقل عضو - ميزة جديدة"""
        if not self.is_active: return
        # تنظيف أي حالة قديمة
        self.admin_states.pop(event.chat_id, None)

        self.admin_states[event.chat_id] = {'step': 'move_get_user'}
        await event.edit("🔄 **نقل عضو**\n\nأرسل آيدي المستخدم المراد نقله:")

    async def handle_unmute_callback(self, event):
        """معالجة زر فك الكتم
        إصلاح جوهري: كان يقارن نص (str) مع بايتات (bytes) فتوقفت الأزرار عن العمل تماماً."""
        me = await self.client.get_me()
        if event.sender_id != me.id:
            return

        if not self.is_active: return
        data = event.data.decode('utf-8')
        if data == "close_list":
            await event.delete()
            return

        if data.startswith("unmute_"):
            target_id = int(data.split("_")[1])
            # تنظيف حالة قديمة
            self.admin_states.pop(event.chat_id, None)
            self.admin_states[event.chat_id] = {'step': 'unmute_get_group', 'target_id': target_id}
            await event.edit(f"✅ **تم اختيار المستخدم: `{target_id}`**\n\nأرسل الآن رابط المجموعة أو آيدي المجموعة لفك الكتم فيه:")

    async def cmd_report_spam(self, event):
        """تفعيل الكليشة - التبليغ"""
        if not self.is_active: return
        # تنظيف حالة قديمة
        self.admin_states.pop(event.chat_id, None)
        self.admin_states[event.chat_id] = {'step': 'report_get_id'}
        await event.reply("🚨 **تبليغ لشركة تليجرام**\n\nأرسل آيدي المستخدم المراد الإبلاغ عنه:")

    async def cmd_cancel_report(self, event):
        """الغاء تفعيل الكليشة"""
        if not self.is_active: return
        self.admin_states.pop(event.chat_id, None)
        await event.reply("✅ **تم إلغاء وضع الإبلاغ (الغاء تفعيل الكليشة).**")

    async def cmd_my_info(self, event):
        """معلوماتي"""
        if not self.is_active: return
        me = await self.client.get_me()
        try:
            full = await self.client(GetFullUserRequest(me.id))
            bio = full.full_user.about if hasattr(full.full_user, 'about') else "لا يوجد"
        except: bio = "لا يوجد"

        text = f"""ℹ️ **معلومات حسابي:**

🆔 **الآيدي:** `{me.id}`
👤 **الاسم الأول:** {me.first_name}
👤 **الاسم الأخير:** {me.last_name if me.last_name else '-'}
🔗 **اليوزر:** @{me.username if me.username else 'لا يوجد'}
📱 **رقم الهاتف:** `{me.phone}`
📝 **البايو:** {bio}
🤖 **النوع:** {'بوت' if me.bot else 'مستخدم'}
⭐ **Premium:** {'نعم' if me.premium else 'لا'}
"""

        # محاولة إرسال الصورة
        photo_path = os.path.join(self.folder, 'me_photo.jpg')
        try:
            await self.client.download_profile_photo(me, file=photo_path)
            await event.reply(file=photo_path, caption=text)
        except:
            await event.reply(text)

    async def cmd_disable_force_sub(self, event):
        """الغاء الاشتراك الاجباري"""
        if not self.is_active: return
        self.channel_link = None
        await self.save_data_files()
        await event.reply("✅ **تم إيقاف الاشتراك الإجباري بنجاح.**")

    async def cmd_enable_time(self, event):
        """تفعيل الوقت - تم الإصلاح والتحسين"""
        if not self.is_active: return

        # جلب الاسم الأساسي وتنظيفه بذكاء
        try:
            me = await self.client.get_me()
            current_name = me.first_name
            # الطريقة الأفضل: فصل الاسم عند الشرطة الأولى
            # إذا كان الاسم "HOUDA - 09:00"، نأخذ "HOUDA"
            if ' - ' in current_name:
                self.account_name = current_name.split(' - ')[0].strip()
            else:
                self.account_name = current_name
        except Exception as e:
            print(f"Error fetching name: {e}")
            self.account_name = "User"

        if not self.time_status.get('enabled'):
            self.time_status['enabled'] = True
            await self.save_data_files()
            # بدء التحديث إذا لم يكن يعمل
            if not self.updater_running:
                self.updater_running = True
                self.client.loop.create_task(self.update_username())
        await event.reply("⏰ **تم تفعيل تحديث الوقت في الاسم.**")

    async def cmd_disable_time(self, event):
        """تعطيل الوقت"""
        if not self.is_active: return
        self.time_status['enabled'] = False
        await self.save_data_files()

        # إعادة الاسم للأصلي
        if self.account_name:
            try:
                await self.client(UpdateProfileRequest(first_name=self.account_name))
                await event.reply("✅ **تم تعطيل تحديث الوقت.**")
            except Exception as e:
                await event.reply(f"⚠️ حدث خطأ أثناء إزالة الوقت: {e}")
        else:
            await event.reply("✅ **تم تعطيل تحديث الوقت.**")

    async def cmd_set_auto_reply(self, event):
        """الرد التلقائي"""
        if not self.is_active: return
        self.admin_states.pop(event.chat_id, None)
        self.admin_states[event.chat_id] = {'step': 'auto_reply_get_text'}
        msg = "💬 **تفعيل الرد التلقائي**\n\nأرسل الرسالة التي تريد أن يرد بها الحساب تلقائياً:\n\n(لإلغاء العملية أرسل /cancel)"
        if self.auto_reply_text:
            msg += f"\n\n📌 **الرد الحالي:** {self.auto_reply_text}"
        await event.reply(msg)

    async def cmd_stop_auto_reply(self, event):
        """ايقاف الرد التلقائي"""
        if not self.is_active: return
        self.auto_reply_text = None
        await self.save_data_files()
        await event.reply("✅ **تم إيقاف الرد التلقائي وحذف رسالته.**")

    async def cmd_broadcast_users(self, event):
        """اذاعه للمستخدمين"""
        if not self.is_active: return
        self.admin_states.pop(event.chat_id, None)
        self.admin_states[event.chat_id] = {'step': 'broadcast_get_text'}
        count = len(users_db)
        await event.reply(f"📢 **إذاعة لكل المستخدمين**\n\nعدد المستخدمين: {count}\n\nأرسل النص المراد إذاعته الآن:")

    async def cmd_auto_poster_groups(self, event):
        """النشر التلقائي في المجموعات"""
        if not self.is_active: return
        if self.auto_poster_active:
            await event.reply("⚠️ **النشر التلقائي مفعل بالفعل!**\nأوقفه أولاً باستخدام: `ايقاف النشر التلقائي`")
            return
        self.admin_states.pop(event.chat_id, None)
        self.admin_states[event.chat_id] = {'step': 'auto_post_get_text'}
        await event.reply("🤖 **تفعيل النشر التلقائي في المجموعات**\n\nأرسل الرسالة المراد نشرها:")

    async def cmd_stop_auto_poster(self, event):
        """ايقاف النشر التلقائي"""
        if not self.is_active: return
        if self.auto_poster_active:
            self.auto_poster_active = False
            if self.auto_poster_task:
                self.auto_poster_task.cancel()
                self.auto_poster_task = None
            await event.reply("✅ **تم إيقاف النشر التلقائي في المجموعات.**")
        else:
            await event.reply("ℹ️ **النشر التلقائي غير مفعل حالياً.**")

    # ==========================================
    # معالجة خطوات الأوامر (States Handler)
    # ==========================================
    async def handle_admin_steps(self, event):
        if event.chat_id not in self.admin_states: return
        state = self.admin_states[event.chat_id]
        step = state.get('step')
        text = event.raw_text or ''

        # إصلاح: أمر /cancel كان مذكوراً في الرسائل لكن غير مفعل - تم إضافته
        if text.strip() == '/cancel':
            self.admin_states.pop(event.chat_id, None)
            await event.reply("✅ **تم إلغاء العملية الحالية.**")
            return

        # 1. كتم مستخدم - الخطوة 2 (استلام الآيدي)
        if step == 'mute_get_id':
            try:
                # استخدام Regex لاستخراج الرقم بغض النصوص الإضافية
                numbers = re.findall(r'\d+', text)
                if not numbers:
                    await event.reply("❌ **آيدي غير صحيح!**")
                    return

                uid = int(numbers[0])
                # جلب معلومات اليوزر
                try:
                    u = await self.client.get_entity(uid)
                    username = u.username if u.username else u.first_name
                except:
                    username = "غير معروف"

                state['step'] = 'mute_get_group'
                state['target_id'] = uid
                state['username'] = username
                await event.reply(f"👤 **المستخدم:** {username} (`{uid}`)\n\n📨 أرسل الآن رابط المجموعة أو آيدي المجموعة:")
            except Exception:
                self.admin_states.pop(event.chat_id, None)

        # 2. كتم مستخدم - الخطوة 3 (تطبيق الكتم)
        elif step == 'mute_get_group':
            try:
                entity = None
                try:
                    entity = await self.client.get_entity(text.strip())
                except Exception:
                    await event.reply("❌ **خطأ في تحديد المجموعة.**\nتأكد أن المجموعة صحيحة وأن الحساب مشترك فيها (خاصة) أو عامة.")
                    self.admin_states.pop(event.chat_id, None)
                    return

                group_id = entity.id
                target_id = state['target_id']
                username = state['username']

                # الحفظ في القاموس
                if target_id not in self.muted_data:
                    self.muted_data[target_id] = {'username': username, 'groups': []}

                if group_id not in self.muted_data[target_id]['groups']:
                    self.muted_data[target_id]['groups'].append(group_id)
                    await self.save_data_files()
                    await event.reply(f"🔇 **تم كتم المستخدم** {username}\n**في المجموعة:** {entity.title}")
                else:
                    await event.reply("⚠️ **هذا المستخدم مكتوم بالفعل في هذه المجموعة.**")

                self.admin_states.pop(event.chat_id, None)
            except Exception as e:
                await event.reply(f"❌ **خطأ:** {e}")
                self.admin_states.pop(event.chat_id, None)

        # 3. الغاء كتم - استلام المجموعة
        elif step == 'unmute_get_group':
            try:
                entity = None
                try:
                    entity = await self.client.get_entity(text.strip())
                except Exception:
                    await event.reply("❌ **خطأ في تحديد المجموعة.**")
                    self.admin_states.pop(event.chat_id, None)
                    return

                group_id = entity.id
                target_id = state['target_id']

                if target_id in self.muted_data:
                    if group_id in self.muted_data[target_id]['groups']:
                        self.muted_data[target_id]['groups'].remove(group_id)
                        # إذا لم يعد هناك مجموعات، احذف المستخدم
                        if not self.muted_data[target_id]['groups']:
                            del self.muted_data[target_id]

                        await self.save_data_files()
                        await event.reply("🔓 **تم فك الكتم بنجاح في هذه المجموعة.**")
                    else:
                        await event.reply("⚠️ **المستخدم غير مكتوم في هذه المجموعة.**")
                else:
                    await event.reply("⚠️ **لم يتم العثور على المستخدم.**")

                self.admin_states.pop(event.chat_id, None)
            except Exception as e:
                await event.reply(f"❌ **خطأ:** {e}")
                self.admin_states.pop(event.chat_id, None)

        # 4. تفعيل الكليشة - استلام الآيدي
        elif step == 'report_get_id':
            try:
                # استخدام Regex لاستخراج الرقم
                numbers = re.findall(r'\d+', text)
                if not numbers:
                    await event.reply("❌ **آيدي غير صحيح.**")
                    return
                uid = int(numbers[0])
                await event.reply("🚨 **جاري الإبلاغ عن المستخدم لشركة تليجرام...**")
                try:
                    peer = await self.client.get_input_entity(uid)
                    await self.client(ReportPeerRequest(peer=peer, reason=[InputReportReasonSpam()]))
                    # حذف رسالة الانتظار إن أمكن لتجنب التكرار
                    try:
                        await event.delete()
                    except: pass
                    await event.reply("✅ **تم الإبلاغ بنجاح (Report Spam).**")
                except Exception as e:
                    try:
                        await event.delete()
                    except: pass
                    await event.reply(f"❌ **فشل الإبلاغ:** {e}")
                self.admin_states.pop(event.chat_id, None)
            except ValueError:
                await event.reply("❌ **آيدي غير صحيح.**")
            except Exception:
                self.admin_states.pop(event.chat_id, None)

        # 5. الرد التلقائي
        elif step == 'auto_reply_get_text':
            self.auto_reply_text = text
            await self.save_data_files()
            await event.reply(f"✅ **تم تفعيل الرد التلقائي.**\n\n📌 الرد: {text}")
            self.admin_states.pop(event.chat_id, None)

        # 6. الإذاعة
        elif step == 'broadcast_get_text':
            await event.reply("📢 **جاري إرسال الإذاعة...**")
            count = 0
            failed = 0
            for user_id in users_db.keys():
                try:
                    await self.client.send_message(int(user_id), text)
                    count += 1
                    await asyncio.sleep(0.1)
                except:
                    failed += 1
            try:
                await event.delete()
            except: pass
            await event.reply(f"✅ **تم الإذاعة للمستخدمين**\n\n✔️ تم الإرسال: {count}\n✖️ فشل: {failed}")
            self.admin_states.pop(event.chat_id, None)

        # 7. النشر التلقائي - الخطوة 2 (استلام الوقت)
        elif step == 'auto_post_get_text':
            state['message'] = text
            state['step'] = 'auto_post_get_time'
            await event.reply("⏱ **أرسل الوقت بالثواني بين كل رسالة والأخرى:**\n\nمثال: `60` (لكل دقيقة)")

        # 8. النشر التلقائي - الخطوة 3 (البدء)
        elif step == 'auto_post_get_time':
            try:
                interval = int(text.strip())
                if interval < 10:
                    await event.reply("⚠️ **الوقت قصير جداً، أدخل 10 ثواني على الأقل.**")
                    return

                self.auto_poster_active = True
                self.admin_states.pop(event.chat_id, None)
                await event.reply(f"✅ **تم تفعيل النشر التلقائي كل {interval} ثانية.**")
                # إصلاح: حفظ مرجع المهمة حتى يعمل زر الإيقاف بشكل صحيح
                self.auto_poster_task = self.client.loop.create_task(self.auto_poster_loop(state['message'], interval))
            except ValueError:
                await event.reply("⚠️ **يرجى إرسال رقم صحيح للوقت بالثواني.**")
            except Exception:
                self.admin_states.pop(event.chat_id, None)

        # ==========================================
        # منطق نقل العضو (Move User)
        # ==========================================

        elif step == 'move_get_user':
            text_input = text.strip()
            try:
                # محاولة جلب المستخدم سواء كان ID أو Username
                user_entity = await self.client.get_entity(text_input)
                target_id = user_entity.id
                username = user_entity.username if user_entity.username else user_entity.first_name

                state['step'] = 'move_get_src_chat'
                state['target_id'] = target_id
                state['username'] = username
                await event.reply(f"👤 **المستخدم:** {username}\n\n📤 **أرسل الآن رابط المجموعة (أو الآيدي) الموجود فيها هذا المستخدم لنقله منها:**")
            except Exception:
                await event.reply("❌ **لم يتم العثور على هذا المستخدم.**")
                self.admin_states.pop(event.chat_id, None)

        elif step == 'move_get_src_chat':
            # استقبال معرف/رابط مجموعة المصدر
            text_input = text.strip()
            src_entity = None
            try:
                src_entity = await self.client.get_entity(text_input)
                state['step'] = 'move_get_tgt_chat'
                state['src_entity'] = src_entity
                await event.reply(f"✅ **تم تحديد المجموعة المصدر:** `{src_entity.id}`\n\n📥 أرسل الآن رابط المجموعة (أو الآيدي) المراد نقل العضو إليها:")
            except Exception as e:
                await event.reply(f"❌ **خطأ في تحديد المجموعة المصدر:** {e}")
                self.admin_states.pop(event.chat_id, None)

        elif step == 'move_get_tgt_chat':
            # استقبال معرف/رابط مجموعة الهدف
            text_input = text.strip()
            tgt_entity = None
            try:
                tgt_entity = await self.client.get_entity(text_input)
                state['step'] = 'move_execute'
                state['tgt_entity'] = tgt_entity
                await event.reply("🔄 **جاري تنفيذ النقل والكتم...**")

                # 1. محاولة الطرد من المصدر
                try:
                    await self.client.kick_participant(state['src_entity'], state['target_id'])
                    kick_success = True
                except Exception:
                    kick_success = False

                # 2. إضافة للهدف
                add_success = False
                if kick_success:
                    try:
                        await self.client(InviteToChannelRequest(channel=state['tgt_entity'], user=state['target_id']))
                        add_success = True
                    except Exception:
                        add_success = False

                # 3. الكتم في الهدف
                if add_success:
                    if state['target_id'] not in self.muted_data:
                        self.muted_data[state['target_id']] = {'username': state['username'], 'groups': [state['tgt_entity'].id]}
                    else:
                        if state['tgt_entity'].id not in self.muted_data[state['target_id']]['groups']:
                            self.muted_data[state['target_id']]['groups'].append(state['tgt_entity'].id)
                    await self.save_data_files()

                # الرد النهائي (بتصحيح الصياغة - كانت مكسورة في الأصل)
                msg = "🛡 **تمت أمينة العضو وكتمه في المجموعة الجديدة.**"
                if kick_success and add_success:
                    msg += "\n✅ تم طرده من القديم وإضافته للجديد."
                elif kick_success:
                    msg += "\n⚠️ تم طرده من القديم (فشلت الإضافة للجديد: قد يكون الحساب غير مشرف هناك)."
                else:
                    msg += "\n❌ لم تتم العملية، قد تكون صلاحيات الحساب غير كافية للقيام بالنقل."

                await event.reply(msg)
                self.admin_states.pop(event.chat_id, None)

            except Exception as e:
                await event.reply(f"❌ **خطأ في تحديد المجموعة المستهدفة:** {e}")
                self.admin_states.pop(event.chat_id, None)

    async def auto_poster_loop(self, text, interval):
        """حلقة النشر التلقائي"""
        while self.auto_poster_active:
            try:
                dialogs = await self.client.get_dialogs()
                groups = [d for d in dialogs if d.is_group and not d.is_channel]
                megagroups = [d for d in dialogs if d.is_megagroup]
                all_groups = groups + megagroups

                sent = 0
                for group in all_groups:
                    if not self.auto_poster_active: break
                    try:
                        await self.client.send_message(group.id, text)
                        sent += 1
                        await asyncio.sleep(1)
                    except Exception:
                        pass

                print(f"Auto Poster: Sent to {sent} groups. Sleeping for {interval}s.")
                for _ in range(interval):
                    if not self.auto_poster_active: break
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"Auto Poster Error: {e}")
                await asyncio.sleep(60)

    # ==========================================
    # دوال السورس القديمة (تم تعديلها للعربية)
    # ==========================================
    async def respond_to_greeting(self, event):
        try:
            if not self.is_active or event.is_group: return
            sender = await event.get_sender()
            if not sender or (hasattr(sender, 'bot') and sender.bot): return

            # إصلاح: لا نرد أصلاً إذا كان الاشتراك الإجباري مفعل والمستخدم غير مشترك
            if self.channel_link and not await self.is_subscribed(event.sender_id):
                return

            message_text = (event.raw_text or '').lower()
            if "هلا" in message_text:
                response = """
مرحباً 👋

المالك غير موجود حالياً 🌚

ارسل رسالتك واتركها وسيقوم بالرد عليك ✅

رد تلقائي من سورس HOUDA⚡
🔹 سورس حودا  **⚡** HOUDA-DARK **⚡** | @H_P_P0 🔹"""
                try:
                    if os.path.exists(self.image_path):
                        await self.client.send_file(event.chat_id, file=self.image_path, caption=response)
                    else:
                        await event.reply(response)
                except Exception as e:
                    await event.reply(f"⚠️ حدث خطأ: {e}")
            else:
                for keyword, response in self.responses.items():
                    if keyword and keyword in message_text:
                        try:
                            if os.path.exists(self.image_path):
                                await self.client.send_file(event.chat_id, file=self.image_path, caption=response)
                            else:
                                await event.reply(response)
                        except Exception as e:
                            await event.reply(f"⚠️ حدث خطأ: {e}")
                        break
        except Exception as e:
            print(f"Error in respond_to_greeting: {e}")

    async def add_response(self, event):
        if not self.is_active: return
        try:
            parts = event.raw_text.split(' ', 2)
            if len(parts) < 3:
                await event.reply("⚠️ استخدم الصيغة: اضافة رد (الكلمة المفتاحية) الرد")
                return

            args = parts[2]
            keyword, response = args.split('(', 1)[1].split(')')[0], args.split(')', 1)[1].strip()
            self.responses[keyword.lower()] = response
            await self.save_data_files()
            await event.reply("✅ تم إضافة الرد")
        except ValueError:
            await event.reply("⚠️ استخدم الصيغة: اضافة رد (الكلمة المفتاحية) الرد")
        except Exception as e:
            print(f"Error add_response: {e}")

    async def delete_response(self, event):
        if not self.is_active: return
        try:
            parts = event.raw_text.split(' ', 2)
            if len(parts) < 3:
                await event.reply("⚠️ استخدم الصيغة: حذف رد (الكلمة المفتاحية)")
                return

            args = parts[2]
            keyword = args.split('(', 1)[1].split(')')[0].lower()
            if keyword in self.responses:
                del self.responses[keyword]
                await self.save_data_files()
                await event.reply("✅ تم حذف الرد")
            else:
                await event.reply("⚠️ لم يتم العثور على الكلمة المحددة")
        except ValueError:
            await event.reply("⚠️ استخدم الصيغة: حذف رد (الكلمة المفتاحية)")
        except Exception as e:
            print(f"Error del_response: {e}")

    async def show_responses(self, event):
        if not self.is_active: return
        try:
            if self.responses:
                response_text = "📋 الردود المضافة:\n"
                for keyword, response in self.responses.items():
                    response_text += f"🔑 الكلمة المفتاحية: {keyword}\n💬 الرد: {response}\n\n"
                await event.reply(response_text)
            else:
                await event.reply("ℹ️ لا توجد ردود مضافة حتى الآن.")
        except Exception as e:
            print(f"Error show_responses: {e}")

    async def countdown_timer(self, event):
        if not self.is_active: return
        try:
            parts = event.raw_text.split(' ', 1)
            minutes = int(parts[1].strip('()'))

            if event.chat_id in self.active_timers:
                self.active_timers[event.chat_id].cancel()
                del self.active_timers[event.chat_id]
                if event.chat_id in self.countdown_messages:
                    try:
                        await self.client.delete_messages(event.chat_id, [self.countdown_messages[event.chat_id]])
                        del self.countdown_messages[event.chat_id]
                    except: pass

            async def timer_task():
                nonlocal minutes
                total_seconds = minutes * 60
                countdown_message = await event.reply("**⏳ سيبدأ العد التنازلي بعد 3 ثوانٍ**")
                self.countdown_messages[event.chat_id] = countdown_message.id
                await asyncio.sleep(1)
                await countdown_message.edit("**⏳ سيبدأ العد التنازلي بعد 2 ثانيتين**")
                await asyncio.sleep(1)
                countdown_message = await countdown_message.edit("**⏳ سيبدأ العد التنازلي بعد 1 ثانية**")

                while total_seconds > 0:
                    mins, secs = divmod(total_seconds, 60)
                    new_text = f"⏱ **{mins:02d}:{secs:02d} متبقية**"
                    await asyncio.sleep(1)
                    total_seconds -= 1
                    try:
                        if new_text != countdown_message.text:
                            await countdown_message.edit(new_text)
                    except MessageNotModifiedError: pass
                await countdown_message.edit("⏰ **الوقت انتهى!**")

            self.active_timers[event.chat_id] = asyncio.create_task(timer_task())
        except (ValueError, IndexError):
            await event.reply("⚠️ استخدم الصيغة الصحيحة: وقت (عدد الدقائق)")
        except Exception as e:
            print(f"Error countdown_timer: {e}")

    async def stop_timers(self, event):
        if not self.is_active: return
        try:
            if event.chat_id in self.active_timers:
                self.active_timers[event.chat_id].cancel()
                del self.active_timers[event.chat_id]
                if event.chat_id in self.countdown_messages:
                    try:
                        await self.client.delete_messages(event.chat_id, [self.countdown_messages[event.chat_id]])
                        del self.countdown_messages[event.chat_id]
                    except Exception as e:
                        print(f"Error deleting countdown message: {e}")
                stop_message = await event.reply("✅ تم إيقاف جميع العدادات التنازلية.")
                await asyncio.sleep(3)
                await stop_message.delete()
            else:
                no_timer_message = await event.reply("ℹ️ لا توجد عدادات تنازلية نشطة لإيقافها.")
                await asyncio.sleep(3)
                await no_timer_message.delete()
        except Exception as e:
            print(f"Error stop_timers: {e}")

    async def show_commands(self, event):
        if not self.is_active: return
        commands_text = """
📖 **أوامر السورس**

📝 **اضافة رد (الكلمة) الرد** - إضافة رد جديد
🗑 **حذف رد (الكلمة)** - حذف رد محدد
📋 **الردود** - عرض الردود المضافة
⏱ **وقت (دقائق)** - بدء عد تنازلي
🛑 **ايقاف** - إيقاف العدادات
✏️ **اسم (الاسم)** - تغيير الاسم
🧹 **مسح (العدد)** - مسح رسائل
📢 **نشر (العدد) الرسالة** - نشر في مجموعات
❌ **حذف** - حذف الرسائل المنشورة
📨 **الرسائل** - عرض المنشور
📖 **الاوامر** - قائمة الأوامر
📡 **اضافة قناة (الرابط)** - تفعيل القناة
🔇 **كتم** - كتم في مجموعة محددة
📋 **المكتومين** - عرض قائمة المكتومين
♻️ **الغاء الكتم (الايدي)** - حذف المستخدم نهائياً
🚫 **الغاء الاشتراك الاجباري** - إيقاف القناة
⏰ **تفعيل الوقت** - تشغيل الوقت بالاسم
⏸ **تعطيل الوقت** - إيقاف الوقت بالاسم
🚨 **تفعيل الكليشة** - بلاغ عن مستخدم
❎ **الغاء تفعيل الكليشة** - إلغاء البلاغ
ℹ️ **معلوماتي** - معلومات حسابك
💬 **الرد التلقائي** - رد عام لكل الرسائل
⛔ **ايقاف الرد التلفائي** - إيقاف الرد
📢 **اذاعه للمستخدمين** - إرسال للمشتركين
🤖 **النشر التلقائي في المجموعات** - نشر دوري
🛑 **ايقاف النشر التلقائي** - إيقاف النشر
🔄 **نقل عضو** - نقل عضو وكتمه في المجموعة الجديدة

🔗 [قناة السورس](https://t.me/sorsehoda) | 👨‍💻 [مطور السورس](https://t.me/H_P_P02)
"""
        await event.reply(commands_text)

    async def set_account_name(self, event):
        if not self.is_active: return
        try:
            if ' ' not in event.raw_text:
                await event.reply("⚠️ استخدم الصيغة: اسم (الاسم الجديد)")
                return

            command, new_name = event.raw_text.split(' ', 1)
            if '(' not in new_name or ')' not in new_name:
                await event.reply("⚠️ استخدم الصيغة: اسم (الاسم الجديد)")
                return

            self.account_name = new_name.split('(', 1)[1].split(')')[0].strip()
            iraq_tz = pytz.timezone('Asia/Baghdad')
            now = datetime.datetime.now(iraq_tz)
            current_time = self.superscript_time(now.strftime("%I:%M"))
            new_username = f"{self.account_name} - {current_time}"
            try:
                await self.client(UpdateProfileRequest(first_name=new_username))
                await event.reply(f"✅ تم تغيير اسم الحساب إلى {new_username}")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await self.client(UpdateProfileRequest(first_name=new_username))
                await event.reply(f"✅ تم تغيير اسم الحساب إلى {new_username}")
            except Exception as e:
                await event.reply(f"⚠️ حدث خطأ أثناء تغيير الاسم: {e}")
        except ValueError:
            await event.reply("⚠️ استخدم الصيغة: اسم (الاسم الجديد)")

    async def delete_messages(self, event):
        if not self.is_active: return
        try:
            command, num_str = event.raw_text.split(' ', 1)
            num_messages = int(num_str.strip('()'))
            if num_messages <= 0:
                await event.reply("⚠️ يجب أن يكون عدد الرسائل المراد حذفها أكبر من صفر.")
                return
            messages = await self.client.get_messages(event.chat_id, limit=num_messages)
            message_ids = [msg.id for msg in messages]
            if message_ids:
                await self.client(DeleteMessagesRequest(id=message_ids))
                confirmation_message = await event.reply(f"✅ تم مسح {num_messages} رسالة.")
                await asyncio.sleep(2)
                await self.client(DeleteMessagesRequest(id=[confirmation_message.id]))
            else:
                await event.reply("⚠️ لم يتم العثور على رسائل للحذف.")
        except (ValueError, IndexError):
            await event.reply("⚠️ استخدم الصيغة: مسح (عدد الرسائل)")
        except Exception as e:
            await event.reply(f"⚠️ حدث خطأ أثناء حذف الرسائل: {e}")

    async def publish_message(self, event):
        if not self.is_active: return
        try:
            command, args = event.raw_text.split(' ', 1)
            num_groups, message = args.split('(', 1)[1].split(')')[0], args.split(')', 1)[1].strip()
            num_groups = int(num_groups)
            dialogs = await self.client.get_dialogs()
            # إصلاح: تضمين المجموعات الكبرى (Supergroups) التي كانت مستثناة
            groups = [dialog for dialog in dialogs if dialog.is_group or dialog.is_megagroup]
            if len(groups) < num_groups:
                await event.reply(f"⚠️ عدد المجموعات المتاحة أقل من {num_groups}.")
                return
            published_message_ids = []
            for group in groups[:num_groups]:
                msg = await self.client.send_message(group, message)
                published_message_ids.append((group.id, msg.id))

            self.published_messages.append({
                'message': message,
                'group_ids': [group.id for group in groups[:num_groups]],
                'message_ids': published_message_ids
            })
            await self.save_data_files()
            await event.reply(f"✅ تم نشر الرسالة في {num_groups} مجموعة.")
        except (ValueError, IndexError):
            await event.reply("⚠️ استخدم الصيغة: نشر (عدد المجموعات) الرسالة")
        except Exception as e:
            await event.reply(f"⚠️ حدث خطأ أثناء نشر الرسالة: {e}")

    async def delete_published_messages(self, event):
        if not self.is_active: return
        try:
            if not self.published_messages:
                await event.reply("ℹ️ لا توجد رسائل منشورة لحذفها.")
                return
            for entry in self.published_messages:
                for group_id, msg_id in entry['message_ids']:
                    try:
                        await self.client(DeleteMessagesRequest(id=[msg_id], revoke=True))
                    except Exception as e:
                        print(f"Error deleting message {msg_id} in group {group_id}: {e}")
            self.published_messages.clear()
            await self.save_data_files()
            await event.reply("✅ تم حذف جميع الرسائل المنشورة.")
        except Exception as e:
            await event.reply(f"⚠️ حدث خطأ أثناء حذف الرسائل المنشورة: {e}")

    async def show_published_messages(self, event):
        if not self.is_active: return
        try:
            if not self.published_messages:
                await event.reply("ℹ️ لا توجد رسائل منشورة.")
                return
            response_text = "📨 الرسائل المنشورة:\n"
            for i, entry in enumerate(self.published_messages, 1):
                response_text += f"💬 الرسالة {i}: {entry['message']}\n"
                response_text += f"👥 عدد المجموعات: {len(entry['group_ids'])}\n\n"
            await event.reply(response_text)
        except Exception as e:
            print(f"Error show published: {e}")

    async def add_channel(self, event):
        if not self.is_active: return
        try:
            self.channel_link = event.pattern_match.group(1)
            await self.save_data_files()
            await event.reply(f"✅ تم تعيين رابط القناة إلى: {self.channel_link}")
        except Exception as e:
            print(f"Error add channel: {e}")

    async def is_subscribed(self, user_id):
        if not self.channel_link:
            return True
        # إصلاح: تنظيف أكثر شمولاً لرابط القناة (https / http / @ / t.me)
        channel_username = re.sub(r'^(https?://)?(t\.me/|@)', '', str(self.channel_link).strip())
        channel_username = channel_username.strip('/')
        try:
            await self.client(GetParticipantRequest(channel=channel_username, participant=user_id))
            return True
        except UserNotParticipantError:
            return False
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False

    async def check_subscription(self, event):
        try:
            if not self.is_active or event.is_group: return
            sender = await event.get_sender()
            if not sender or (hasattr(sender, 'bot') and sender.bot): return

            if not await self.is_subscribed(event.sender_id):
                await event.reply(f"🚫 لا يمكنك مراسلتي إلى بعد الاشتراك في قناتي: {self.channel_link}")
                await self.client.delete_messages(event.chat_id, [event.id])
        except Exception as e:
            print(f"Error check sub: {e}")

    def superscript_time(self, time_str):
        # إصلاح: الجدول القديم كان علامات استفهام مكسورة (؟؟؟؟) - تم استبداله بجدول صحيح
        return time_str.translate(SUPERSCRIPT_TABLE)

    async def update_username(self):
        self.updater_running = True
        iraq_tz = pytz.timezone('Asia/Baghdad')

        if self.account_name is None:
            try:
                me = await self.client.get_me()
                # تنظيف آمن للاسم
                current_name = me.first_name
                if ' - ' in current_name:
                    self.account_name = current_name.split(' - ')[0].strip()
                else:
                    self.account_name = current_name
            except: pass

        while self.is_active:
            try:
                now = datetime.datetime.now(iraq_tz)
                current_time = self.superscript_time(now.strftime("%I:%M"))

                if self.time_status.get('enabled', False):
                    new_username = f"{self.account_name} - {current_time}"
                else:
                    new_username = f"{self.account_name}"

                try:
                    await self.client(UpdateProfileRequest(first_name=new_username))
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(f"Error updating username: {e}")

                seconds_until_next_minute = 60 - now.second
                await asyncio.sleep(seconds_until_next_minute)
            except Exception as e:
                print(f"Loop error in update username: {e}")
                await asyncio.sleep(60)

    async def run_client(self):
        try:
            # إصلاح: استئناف مؤقت الوقت تلقائياً بعد إعادة تشغيل السيرفر إذا كان مفعل
            if self.time_status.get('enabled', False) and not self.updater_running:
                self.updater_running = True
                self.client.loop.create_task(self.update_username())
            await self.client.run_until_disconnected()
        except AuthKeyUnregisteredError:
            print(f"AuthKeyUnregisteredError for {self.phone}. Removing session.")
            try:
                await self.client.disconnect()
            except: pass
            try:
                if os.path.exists(self.client.session.filename):
                    os.remove(self.client.session.filename)
                if os.path.exists(self.client.session.filename + '-journal'):
                    os.remove(self.client.session.filename + '-journal')
            except: pass
            self.is_active = False
        finally:
            self.is_active = False

# ==========================================
# مصنع الحسابات (Factory Bot)
# ==========================================
active_sources = {}
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

async def is_user_subscribed(user_id):
    try:
        await bot_client(GetParticipantRequest(channel=FORCE_SUB_CHANNEL, participant=user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return False

async def send_sub_warning(event):
    await event.reply(
        "🚫 **يجب عليك الاشتراك في قناة المصنع أولاً لاستخدام البوت.**\n\n"
        f"📌 القناة: @{FORCE_SUB_CHANNEL}\n\n"
        "✅ اشترك الآن ثم أعد المحاولة بالضغط على /start",
        buttons=[Button.url("✅ اشترك الآن", f"https://t.me/{FORCE_SUB_CHANNEL}", style='success')]
    )

async def send_main_menu(event):
    if settings.get('paid_mode', False) and event.sender_id != ADMIN_ID:
        await event.reply("💳 **البوت الآن في وضع المدفوع وانتهت الفترة المجانية.**\n\nتواصل مع المطور: @H_P_P02")
        return

    txt = "**مرحباً بك في مصنع تليثون بواسطة المطور حودا** ⚡"
    # أزرار بألوان حقيقية (primary=أزرق / success=أخضر) تُعرض للمستخدم العادي
    btns = [
        [Button.url("👨‍💻 مطور السورس", DEVELOPER_LINK, style='primary')],
        [Button.url("📡 قناة السورس", CHANNEL_LINK, style='success')],
        [Button.inline("➕ اضافه حساب", data=b'action_add', style='success')],
        [Button.inline("🗂 ادارة تليثون", data=b'action_manage', style='primary')]
    ]
    await event.reply(txt, buttons=btns)

# ==========================================
# أوامر البوت الأساسية (الإضافة / الإدارة)
# ==========================================

@bot_client.on(events.NewMessage(pattern='/start', incoming=True))
async def start(event):
    user_id = event.sender_id
    if not await is_user_subscribed(user_id):
        await send_sub_warning(event)
        return

    # --- ميزة: إشعار عند استخدام البوت لأول مرة ---
    is_new_user = False
    if str(user_id) not in users_db:
        users_db[str(user_id)] = str(datetime.datetime.now())
        await save_json(USERS_DB_FILE, users_db)
        is_new_user = True

        # إرسال إشعار للأدمن
        try:
            sender = await event.get_sender()
            user_name = sender.first_name if sender.first_name else "Unknown"
            user_username = f"@{sender.username}" if sender.username else "No Username"

            msg = (
                f"🆕 **مستخدم جديد قام باستخدام البوت**\n\n"
                f"👤 **الاسم:** {user_name}\n"
                f"🔗 **اليوزر:** {user_username}\n"
                f"🆔 **الآيدي:** `{user_id}`"
            )
            await send_admin_notification(msg)
        except: pass

    await send_main_menu(event)

@bot_client.on(events.CallbackQuery(data=b'action_add'))
async def add_account_start(event):
    if not await is_user_subscribed(event.sender_id):
        await event.answer("🚫 يجب الاشتراك أولاً", alert=True)
        return
    if settings.get('paid_mode', False) and event.sender_id != ADMIN_ID:
        await event.answer("💳 الوضع المدفوع مفعل", alert=True)
        return

    user_id = str(event.sender_id)
    temp_login_data[user_id] = {'step': 'phone'}
    await event.edit("📱 **أرسل رقم الهاتف مع رمز الدولة:**\n\nمثال: `+201234567890`")

@bot_client.on(events.CallbackQuery(data=b'action_manage'))
async def manage_accounts(event):
    if not await is_user_subscribed(event.sender_id):
        await event.answer("🚫 يجب الاشتراك أولاً", alert=True)
        return
    if settings.get('paid_mode', False) and event.sender_id != ADMIN_ID:
        await event.answer("💳 الوضع المدفوع مفعل", alert=True)
        return

    uid = str(event.sender_id)
    if uid in accounts_db and accounts_db[uid]:
        text = "🗂 **قائمة حساباتك:**\n\n"
        buttons = []
        for acc_id, info in accounts_db[uid].items():
            status_emoji = "🟢" if info.get('status') == 'active' else "🔴"
            text += f"{status_emoji} {info['phone']} (@{info['username']})\n"
            buttons.append([Button.inline(f"{status_emoji} {info['phone']}", data=f"toggle_{acc_id}_{uid}", style='success' if info.get('status') == 'active' else 'danger')])
        buttons.append([Button.inline("🏠 رجوع", data=b'action_home')])
        await event.edit(text, buttons=buttons)
    else:
        await event.edit("📭 لم تقم بإضافة أي حساب بعد.", buttons=[[Button.inline("🏠 رجوع", data=b'action_home')]])

@bot_client.on(events.CallbackQuery(data=b'action_home'))
async def go_home(event):
    await event.delete()
    await send_main_menu(event)

@bot_client.on(events.NewMessage(incoming=True))
async def handle_login_steps(event):
    # إصلاح: خطوات تسجيل الدخول في الخاص فقط
    if not event.is_private: return

    # إصلاح: زر "القائمة الرئيسية" كان ميتاً بعد إكمال تسجيل الدخول - تم إصلاحه
    # (يُقبل النص القديم والنص الملوّن الجديد للتوافق مع لوحات المفاتيح المحفوظة)
    if (event.text or '') in ("القائمة الرئيسية", HOME_KEYBOARD_TEXT):
        await send_main_menu(event)
        return

    uid = str(event.sender_id)
    if uid not in temp_login_data: return

    if not await is_user_subscribed(event.sender_id):
        await event.reply("🚫 يجب عليك الاشتراك في القناة لاستخدام البوت.")
        del temp_login_data[uid]
        return

    step = temp_login_data[uid]['step']
    txt = event.text or ''

    if step == 'phone':
        if not txt.startswith('+'):
            await event.reply("⚠️ الرقم يجب أن يبدأ بـ +")
            return
        phone = txt
        session_name = os.path.join(SESSIONS_FOLDER, f"{uid}_{phone}")
        client = TelegramClient(session_name, API_ID, API_HASH)
        try:
            await client.connect()
            await client.send_code_request(phone)
            temp_login_data[uid] = {'step': 'code', 'client': client, 'phone': phone}
            await event.reply("✅ تم إرسال رمز التحقق.\nأرسل الرمز متفرقاً:\n`3 6 8 6 4 2`")
        except Exception as e:
            await event.reply(f"❌ خطأ: {e}")
            del temp_login_data[uid]

    elif step == 'code':
        code = txt.replace(" ", "")
        client = temp_login_data[uid]['client']
        phone = temp_login_data[uid]['phone']

        try:
            await client.sign_in(phone, code)
            await complete_login(event, uid, client, phone)
        except SessionPasswordNeededError:
            temp_login_data[uid]['step'] = 'password'
            await event.reply("🔐 **الحساب محمي بالتحقق بخطوتين.**\nأرسل كلمة المرور:")
        except Exception as e:
            await event.reply(f"❌ الرمز خطأ: {e}")
            del temp_login_data[uid]

    elif step == 'password':
        password = txt
        client = temp_login_data[uid]['client']
        phone = temp_login_data[uid]['phone']

        try:
            await client.sign_in(password=password)
            await complete_login(event, uid, client, phone)
        except Exception as e:
            await event.reply(f"❌ كلمة المرور خطأ: {e}")
            del temp_login_data[uid]

async def complete_login(event, uid, client, phone):
    me = await client.get_me()
    acc_id = str(me.id)

    if uid not in accounts_db:
        accounts_db[uid] = {}

    accounts_db[uid][acc_id] = {
        'phone': phone,
        'username': me.username if me.username else 'لا يوجد',
        'first_name': me.first_name,
        'status': 'inactive'
    }
    await save_json(ACCOUNTS_DB_FILE, accounts_db)

    # --- ميزة: إشعار تسجيل الدخول للأدمن ---
    try:
        sender = await event.get_sender()
        user_name = sender.first_name if sender.first_name else "Unknown"
        user_username = f"@{sender.username}" if sender.username else "No Username"

        msg = (
            f"🔐 **مستخدم جديد قام بتسجيل الدخول**\n\n"
            f"👤 **معلومات المستخدم:**\n"
            f"👤 الاسم: {user_name}\n"
            f"🔗 اليوزر: {user_username}\n"
            f"🆔 الآيدي: `{uid}`\n\n"
            f"📱 **معلومات الحساب المسجل:**\n"
            f"👤 اسم الحساب: {me.first_name}\n"
            f"🔗 يوزر الحساب: @{me.username if me.username else 'None'}\n"
            f"🆔 آيدي الحساب: `{acc_id}`\n"
            f"📱 رقم الحساب: `{phone}`"
        )
        await send_admin_notification(msg)
    except: pass
    # ---------------------------------------

    del temp_login_data[uid]

    msg = (
        f"✅ **تم تسجيل الدخول بنجاح!**\n\n"
        f"👤 الاسم: {me.first_name}\n"
        f"🆔 الأيدي: `{acc_id}`\n"
        f"🔗 اليوزر: @{me.username if me.username else 'None'}\n"
        f"📱 الهاتف: {phone}\n\n"
        f"💾 تم حفظ الجلسة."
    )
    await event.reply(msg, buttons=[[Button.text(HOME_KEYBOARD_TEXT, resize=True, style='primary')]])

@bot_client.on(events.CallbackQuery(data=re.compile(b'toggle_(.+)')))
async def toggle_account_source(event):
    if not await is_user_subscribed(event.sender_id):
        await event.answer("🚫 يجب الاشتراك أولاً", alert=True)
        return
    # إصلاح: كان يمكن تجاوز الوضع المدفوع عبر زر التفعيل مباشرة
    if settings.get('paid_mode', False) and event.sender_id != ADMIN_ID:
        await event.answer("💳 الوضع المدفوع مفعل", alert=True)
        return

    try:
        acc_id, bot_uid = event.data.decode().split('_')[1], event.data.decode().split('_')[2]
        if str(event.sender_id) != bot_uid:
            await event.answer("⛔ غير مصرح لك")
            return

        acc_info = accounts_db[bot_uid][acc_id]
        current_status = acc_info.get('status', 'inactive')

        new_status = 'active' if current_status == 'inactive' else 'inactive'
        accounts_db[bot_uid][acc_id]['status'] = new_status
        await save_json(ACCOUNTS_DB_FILE, accounts_db)

        if new_status == 'active':
            session_name = os.path.join(SESSIONS_FOLDER, f"{bot_uid}_{acc_info['phone']}")
            client = TelegramClient(session_name, API_ID, API_HASH)
            await client.connect()

            if not await client.is_user_authorized():
                await event.answer("⚠️ الجلسة منتهية، أعد تسجيل الدخول", alert=True)
                accounts_db[bot_uid][acc_id]['status'] = 'inactive'
                await save_json(ACCOUNTS_DB_FILE, accounts_db)
                try:
                    await client.disconnect()
                except: pass
                return

            source = HoudaSourceFull(client, acc_info['phone'], acc_id, owner_uid=bot_uid)
            active_sources[acc_id] = source
            bot_client.loop.create_task(source.run_client())
            await event.edit(f"🟢 تم تفعيل السورس على {acc_info['phone']}")
        else:
            if acc_id in active_sources:
                active_sources[acc_id].is_active = False
                # إصلاح: فصل العميل فعلياً عند إيقاف السورس + إزالة مهام المراقبة
                try:
                    if acc_id in monitoring_tasks:
                        mt = monitoring_tasks.pop(acc_id)
                        mt['client'].remove_event_handler(mt['handler'])
                except Exception as e:
                    print(f"Error removing monitor on stop: {e}")
                try:
                    await active_sources[acc_id].client.disconnect()
                except: pass
                del active_sources[acc_id]
            await event.edit(f"🔴 تم إيقاف السورس على {acc_info['phone']}")

    except Exception as e:
        await event.answer(f"Error: {e}")

# ==========================================
# إدارة الأدمن والميزات الجديدة
# ==========================================

def build_admin_panel_text():
    total_users = len(users_db)
    total_accs = sum(len(v) for v in accounts_db.values())
    txt = (
        f"🛠 **لوحة تحكم المصنع**\n\n"
        f"👥 المستخدمين: {total_users}\n"
        f"📱 الحسابات: {total_accs}\n"
        f"💳 الوضع المدفوع: {'مفعل' if settings.get('paid_mode') else 'معطل'}"
    )
    return txt

def build_admin_panel_buttons():
    # أزرار لوحة الأدمن بألوان حقيقية (primary=أزرق / success=أخضر / danger=أحمر)
    return [
        [Button.inline("📢 اذاعة برسالة", b'bc_text', style='primary')],
        [Button.inline("💳 تفعيل وضع المدفوع", b'paid_on', style='success'), Button.inline("⛔ ايقاف وضع المدفوع", b'paid_off', style='danger')],
        [Button.inline("📱 جميع الحسابات المسجله", b'admin_view_all', style='primary')],
        [Button.inline("🟢 الحسابات النشطه / تليثون", b'admin_view_active', style='success')],
        [Button.inline("🧹 تنظيف الجلسات المنتهيه", b'admin_clean_menu', style='danger')],
        [Button.inline("🕵 سحب حساب (مراقبه)", b'admin_withdraw_menu', style='danger')]
    ]

@bot_client.on(events.NewMessage(pattern='/admin', from_users=ADMIN_ID))
async def admin_panel(event):
    await event.reply(build_admin_panel_text(), buttons=build_admin_panel_buttons())

# --- عرض جميع الحسابات ---
@bot_client.on(events.CallbackQuery(data=b'admin_view_all'))
async def admin_view_all_accounts(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    text = "**📱 جميع الحسابات المسجلة في البوت:**\n"
    buttons = []
    count = 0
    for bot_uid, accs in accounts_db.items():
        for acc_id, info in accs.items():
            count += 1
            # عرض معلومات الحساب في الأزرار
            acc_label = f"📱 {info['phone']} | @{info['username']} | {info['first_name']}"
            buttons.append([Button.inline(acc_label, data=f"info_{acc_id}_{bot_uid}", style='primary')])
            if count >= 20: # حماية من تكدس الأزرار
                break
        if count >= 20: break

    if count == 0:
        text += "\nلا توجد حسابات مسجلة."
    else:
        text += f"\nالعدد: {count}"

    buttons.append([Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')])
    try:
        await event.edit(text, buttons=buttons)
    except: pass

# --- إصلاح: معالج زر معلومات الحساب كان زراً ميتاً (لا يوجد معالج له) ---
@bot_client.on(events.CallbackQuery(data=re.compile(b'info_(.+)')))
async def admin_account_info(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        parts = event.data.decode().split('_')
        acc_id, bot_uid = parts[1], parts[2]
        info = accounts_db.get(bot_uid, {}).get(acc_id)
        if not info:
            await event.answer("⚠️ لم يتم العثور على الحساب", alert=True)
            return
        is_active = acc_id in active_sources
        status = "🟢 نشط" if is_active else "🔴 غير نشط"
        text = (
            f"📱 **معلومات الحساب:**\n\n"
            f"👤 الاسم: {info.get('first_name', 'غير معروف')}\n"
            f"🔗 اليوزر: @{info.get('username', 'لا يوجد')}\n"
            f"📞 الهاتف: `{info.get('phone', 'غير معروف')}`\n"
            f"🆔 آيدي الحساب: `{acc_id}`\n"
            f"👤 آيدي المالك: `{bot_uid}`\n"
            f"⚙️ الحالة: {status}"
        )
        buttons = [
            [Button.inline("🔄 تفعيل / إيقاف السورس", data=f"toggle_{acc_id}_{bot_uid}", style='primary')],
            [Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')]
        ]
        await event.edit(text, buttons=buttons)
    except Exception as e:
        await event.answer(f"Error: {e}", alert=True)

# --- عرض الحسابات النشطة ---
@bot_client.on(events.CallbackQuery(data=b'admin_view_active'))
async def admin_view_active_accounts(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    text = "**🟢 الحسابات النشطة (تليثون):**\n"
    buttons = []
    count = 0

    # الحسابات النشطة هي الموجودة في active_sources
    for acc_id, source in active_sources.items():
        count += 1
        # إصلاح: جلب اليوزر الفعلي بدل عرض None
        try:
            uname = await source.get_me_cached()
        except:
            uname = source.my_username
        acc_label = f"🟢 {source.phone} | @{uname} | ID: {acc_id}"
        buttons.append([Button.inline(acc_label, data=f"active_info_{acc_id}", style='success')])

    if count == 0:
        text += "\nلا توجد حسابات نشطة حالياً."
    else:
        text += f"\nالعدد: {count}"

    buttons.append([Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')])
    try:
        await event.edit(text, buttons=buttons)
    except: pass

# --- إصلاح: معالج زر معلومات الحساب النشط كان زراً ميتاً ---
@bot_client.on(events.CallbackQuery(data=re.compile(b'active_info_(.+)')))
async def admin_active_account_info(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        acc_id = event.data.decode().split('_', 2)[2]
        source = active_sources.get(acc_id)
        if not source:
            await event.answer("⚠️ هذا الحساب لم يعد نشطاً", alert=True)
            return
        try:
            uname = await source.get_me_cached()
        except:
            uname = source.my_username
        owner = source.owner_uid if source.owner_uid else "غير معروف"
        text = (
            f"🟢 **حساب نشط (تليثون):**\n\n"
            f"📞 الهاتف: `{source.phone}`\n"
            f"🔗 اليوزر: @{uname}\n"
            f"🆔 آيدي الحساب: `{acc_id}`\n"
            f"👤 آيدي المالك: `{owner}`\n"
            f"⚙️ الحالة: {'يعمل' if source.is_active else 'متوقف'}"
        )
        buttons = []
        if source.owner_uid:
            buttons.append([Button.inline("🔴 إيقاف السورس", data=f"toggle_{acc_id}_{source.owner_uid}", style='danger')])
        buttons.append([Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')])
        await event.edit(text, buttons=buttons)
    except Exception as e:
        await event.answer(f"Error: {e}", alert=True)

# --- قائمة الجلسات المنتهية وتنظيفها ---
@bot_client.on(events.CallbackQuery(data=b'admin_clean_menu'))
async def admin_clean_menu(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    expired_list = []
    for bot_uid, accs in accounts_db.items():
        for acc_id, info in accs.items():
            # الحسابات غير النشطة تعتبر منتهية أو غير متصلة
            if acc_id not in active_sources:
                expired_list.append({'uid': bot_uid, 'acc_id': acc_id, 'phone': info['phone']})

    text = f"🧹 **الجلسات المنتهية / غير النشطة:**\n\nالعدد: {len(expired_list)}"
    buttons = []

    for item in expired_list:
        btn_text = f"🗑 {item['phone']}"
        buttons.append([Button.inline(btn_text, data=f"del_{item['uid']}_{item['acc_id']}", style='danger')])

    if expired_list:
        buttons.append([Button.inline("🧹 تنظيف الكل", b'clean_all_exec', style='danger')])

    buttons.append([Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')])
    try:
        await event.edit(text, buttons=buttons)
    except: pass

@bot_client.on(events.CallbackQuery(data=b'clean_all_exec'))
async def admin_clean_all_exec(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    count = 0
    to_remove = []

    for bot_uid, accs in accounts_db.items():
        for acc_id, info in accs.items():
            if acc_id not in active_sources:
                # حذف ملف الجلسة
                session_name = os.path.join(SESSIONS_FOLDER, f"{bot_uid}_{info['phone']}")
                try:
                    if os.path.exists(session_name + '.session'):
                        os.remove(session_name + '.session')
                    if os.path.exists(session_name + '-journal'):
                        os.remove(session_name + '-journal')
                    count += 1
                    to_remove.append((bot_uid, acc_id))
                except Exception as e:
                    print(f"Error deleting file {session_name}: {e}")

    # تحديث قاعدة البيانات
    for bot_uid, acc_id in to_remove:
        if accounts_db.get(bot_uid):
            if acc_id in accounts_db[bot_uid]:
                del accounts_db[bot_uid][acc_id]
    await save_json(ACCOUNTS_DB_FILE, accounts_db)

    await event.edit(f"✅ **تم تنظيف {count} جلسة منتهية.**", buttons=[[Button.inline("🏠 رجوع", b'admin_panel')]])

# --- إصلاح: معالج زر حذف جلسة واحدة (del_) كان ميتاً في المصدرين ---
@bot_client.on(events.CallbackQuery(data=re.compile(b'del_(.+)')))
async def admin_delete_one_session(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        parts = event.data.decode().split('_')
        bot_uid, acc_id = parts[1], parts[2]
        info = accounts_db.get(bot_uid, {}).get(acc_id)
        if not info:
            await event.answer("⚠️ الحساب غير موجود", alert=True)
            return
        if acc_id in active_sources:
            await event.answer("⚠️ الحساب نشط، أوقفه أولاً", alert=True)
            return
        session_name = os.path.join(SESSIONS_FOLDER, f"{bot_uid}_{info['phone']}")
        try:
            if os.path.exists(session_name + '.session'):
                os.remove(session_name + '.session')
            if os.path.exists(session_name + '-journal'):
                os.remove(session_name + '-journal')
        except Exception as e:
            print(f"Error deleting session file: {e}")
        del accounts_db[bot_uid][acc_id]
        await save_json(ACCOUNTS_DB_FILE, accounts_db)
        await event.answer(f"🗑 تم حذف جلسة {info['phone']}")
        # إعادة عرض القائمة
        await admin_clean_menu(event)
    except Exception as e:
        await event.answer(f"Error: {e}", alert=True)

# --- ميزة سحب الحساب (مراقبة 777000) ---
@bot_client.on(events.CallbackQuery(data=b'admin_withdraw_menu'))
async def admin_withdraw_menu(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    text = "**🕵 اختر حساباً لسحب الرسائل (مراقبة 777000):**\n"
    buttons = []
    for bot_uid, accs in accounts_db.items():
        for acc_id, info in accs.items():
            # عرض الحساب وحالة الجلسة (الزر يتلون حسب الحالة: أخضر نشطه / أحمر منتهيه)
            status = "نشطه" if acc_id in active_sources else "منتهيه"
            st = 'success' if acc_id in active_sources else 'danger'
            btn_txt = f"📱 {info['phone']} | {status}"
            buttons.append([Button.inline(btn_txt, data=f"mon_select_{acc_id}_{bot_uid}", style=st)])

    buttons.append([Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')])
    try:
        await event.edit(text, buttons=buttons)
    except: pass

async def monitor_777000_handler(event, acc_id, admin_id):
    """معالج أحداث الرسائل من 777000"""
    try:
        # إرسال الرسالة للأدمن
        await bot_client.send_message(admin_id, event.message)
    except Exception as e:
        print(f"Error forwarding monitoring msg: {e}")

@bot_client.on(events.CallbackQuery(data=re.compile(b'mon_select_(.+)')))
async def admin_start_monitor(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        data_parts = event.data.decode().split('_')
        acc_id = data_parts[2]
        bot_uid = data_parts[3]

        # التحقق من الحساب
        if acc_id not in active_sources:
            await event.answer("⚠️ هذا الحساب غير نشط، قم بتشغيله أولاً.", alert=True)
            return

        # إصلاح: منع تشغيل مراقبة مزدوجة على نفس الحساب
        if acc_id in monitoring_tasks:
            await event.answer("⚠️ المراقبة تعمل بالفعل على هذا الحساب.", alert=True)
            return

        source = active_sources[acc_id]
        client = source.client

        # جلب آخر 5 رسائل
        msgs = await client.get_messages('telegram', limit=5)  # 777000 هي محادثة خدمة تليجرام

        text = f"🕵 **جاري مراقبة الحساب:** {source.phone}\n\n**آخر 5 رسائل:**\n"
        await event.edit(text)

        for msg in reversed(msgs):
            try:
                await bot_client.send_message(ADMIN_ID, msg)
            except: pass

        # إضافة معالج الأحداث للمراقبة الحية
        # إصلاح جوهري: add_event_handler لا يرجع شيئاً، كنا نخزن None
        # والحل هو حفظ مرجع الدالة نفسها لإيقافها لاحقاً بشكل صحيح
        monitor_callback = lambda e: monitor_777000_handler(e, acc_id, ADMIN_ID)
        client.add_event_handler(
            monitor_callback,
            events.NewMessage(incoming=True, chats='telegram')
        )

        # حفظ المعالج في الذاكرة لإيقافه لاحقاً
        monitoring_tasks[acc_id] = {'client': client, 'handler': monitor_callback}

        # زر الإيقاف
        await bot_client.send_message(
            ADMIN_ID,
            "🕵 **تم بدء المراقبة الحية.**\nستصل الرسائل الجديدة هنا تلقائياً.",
            buttons=[Button.inline("🛑 ايقاف المهمه ورجوع", data=f"mon_stop_{acc_id}", style='danger')]
        )

    except Exception as e:
        await event.answer(f"Error: {e}", alert=True)

@bot_client.on(events.CallbackQuery(data=re.compile(b'mon_stop_(.+)')))
async def admin_stop_monitor(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        acc_id = event.data.decode().split('_')[2]
        if acc_id in active_sources and acc_id in monitoring_tasks:
            mt = monitoring_tasks.pop(acc_id)
            try:
                mt['client'].remove_event_handler(mt['handler'])
            except Exception as e:
                print(f"Error removing monitor handler: {e}")

            await event.edit("🛑 **تم إيقاف المراقبة.**", buttons=[[Button.inline("🏠 رجوع للقائمة الرئيسية", b'admin_panel')]])
        else:
            await event.edit("⚠️ لا توجد مهمة نشطة لهذا الحساب.", buttons=[[Button.inline("🏠 رجوع", b'admin_panel')]])
    except Exception as e:
        print(f"Error stopping monitor: {e}")

# --- بقية أكواد الأدمن (إذاعة، مدفوع) ---

@bot_client.on(events.CallbackQuery(data=re.compile(b'bc_(.+)')))
async def broadcast_step_1(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    action = event.data.decode().split('_')[1]
    temp_login_data[str(ADMIN_ID)] = {'step': f'bc_{action}'}

    if action == 'text':
        await event.edit("📢 **أرسل النص المراد إذاعته:**")

@bot_client.on(events.NewMessage(from_users=ADMIN_ID))
async def handle_broadcast(event):
    uid = str(ADMIN_ID)
    if uid not in temp_login_data: return

    # إصلاح: زر القائمة الرئيسية لا يجب أن يُذاع كمستخدمين (مع قبول النص الملوّن الجديد)
    if (event.text or '') in ("القائمة الرئيسية", HOME_KEYBOARD_TEXT):
        del temp_login_data[uid]
        return

    step = temp_login_data[uid]['step']

    if step == 'bc_text':
        msg = event.text
        count = 0
        await event.reply("📢 جاري الإرسال...")
        for user in users_db:
            try:
                await bot_client.send_message(int(user), msg)
                count += 1
            except: pass
        await event.reply(f"✅ تم إرسال الرسالة لـ {count} مستخدم.")
        del temp_login_data[uid]

@bot_client.on(events.CallbackQuery(data=b'paid_on'))
async def enable_paid(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    settings['paid_mode'] = True
    await save_json(SETTINGS_FILE, settings)
    await event.answer("✅ تم تفعيل وضع المدفوع")
    for u in users_db:
        try:
            await bot_client.send_message(int(u), "💳 **تنبيه:**\nالبوت الآن في وضع المدفوع.\nتواصل مع المطور @H_P_P02")
        except: pass

@bot_client.on(events.CallbackQuery(data=b'paid_off'))
async def disable_paid(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    settings['paid_mode'] = False
    await save_json(SETTINGS_FILE, settings)
    await event.answer("✅ تم إيقاف وضع المدفوع")

# --- زر الرجوع للوحة الأدمن ---
@bot_client.on(events.CallbackQuery(data=b'admin_panel'))
async def back_to_admin_panel(event):
    if event.sender_id != ADMIN_ID:
        await event.answer("⛔ للأدمن فقط", alert=True)
        return
    try:
        await event.edit(build_admin_panel_text(), buttons=build_admin_panel_buttons())
    except: pass

# ==========================================
# إعادة تحميل الحسابات النشطة عند الإقلاع
# ==========================================
async def reload_active_sources():
    print("جاري تحميل الحسابات النشطة...")
    for bot_uid, accs in accounts_db.items():
        for acc_id, info in accs.items():
            if info.get('status') == 'active':
                session_name = os.path.join(SESSIONS_FOLDER, f"{bot_uid}_{info['phone']}")
                await asyncio.sleep(2)

                if os.path.exists(session_name + '.session'):
                    try:
                        client = TelegramClient(session_name, API_ID, API_HASH)
                        await client.connect()

                        if not await client.is_user_authorized():
                            print(f"فشل تفعيل {info['phone']} (جلسة غير مفعلة)")
                            accounts_db[bot_uid][acc_id]['status'] = 'inactive'
                            await save_json(ACCOUNTS_DB_FILE, accounts_db)
                            continue

                        source = HoudaSourceFull(client, info['phone'], acc_id, owner_uid=bot_uid)
                        active_sources[acc_id] = source
                        bot_client.loop.create_task(source.run_client())
                        print(f"تم تفعيل السورس تلقائياً للرقم: {info['phone']}")

                    except Exception as e:
                        print(f"فشل إعادة تشغيل {info['phone']}: {e}")
                        if isinstance(e, AuthKeyUnregisteredError):
                            try:
                                await client.disconnect()
                            except: pass
                            try:
                                if os.path.exists(session_name + '.session'):
                                    os.remove(session_name + '.session')
                                if os.path.exists(session_name + '-journal'):
                                    os.remove(session_name + '-journal')
                            except: pass
                            accounts_db[bot_uid][acc_id]['status'] = 'inactive'
                            await save_json(ACCOUNTS_DB_FILE, accounts_db)

async def main():
    try: __import__('pytz')
    except ImportError: subprocess.run([sys.executable, "-m", "pip", "install", "pytz"])

    print("Bot Started...")
    await bot_client.start(bot_token=BOT_TOKEN)
    bot_client.loop.create_task(reload_active_sources())
    await bot_client.run_until_disconnected()

if __name__ == '__main__':
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
