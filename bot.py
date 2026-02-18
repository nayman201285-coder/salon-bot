import os
import asyncio
import logging
import time
import http.server
import socketserver
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import Database

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 926112462  # Твой ID напрямую, без os.getenv

logging.basicConfig(level=logging.INFO)

# Инициализация
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()

# Состояния для FSM
class BookingStates(StatesGroup):
    choosing_language = State()
    choosing_master = State()
    choosing_service = State()
    entering_phone = State()
    choosing_date = State()
    choosing_time = State()
    confirmation = State()
    choosing_another_master = State()

class AdminStates(StatesGroup):
    admin_menu = State()
    viewing_appointments = State()
    adding_note = State()
    deleting_note = State()
    waiting_for_date = State()
    manual_booking = State()
    manual_master = State()
    manual_service = State()
    manual_client_name = State()
    manual_client_phone = State()
    manual_date = State()
    manual_time = State()
    manual_confirm = State()
    editing_note = State()
    editing_note_date = State()
    editing_note_time = State()
    editing_note_text = State()

# ==================== ТЕКСТЫ НА ТРЕХ ЯЗЫКАХ ====================

TEXTS = {
    'ru': {
        'welcome': "👋 Добро пожаловать в салон красоты 'Преображение'!\n\nВыберите язык:",
        'main_menu': "Главное меню:",
        'choose_master': "👩‍🎨 Выберите мастера:",
        'choose_service': "💅 Выберите услугу (цены от ${} до ${}):",
        'enter_phone': "📱 Введите ваш номер телефона для связи:\n(например: +7 999 123-45-67)",
        'choose_date': "📅 Выберите дату:",
        'choose_time': "⏰ Выберите свободное время:",
        'confirm': "✅ Подтвердите запись:\n\nМастер: {}\nУслуга: {}\nЦена: ${}-${}\nДата: {}\nВремя: {}\nТелефон: {}",
        'confirmed': "✅ Запись подтверждена! Ждем вас в салоне!",
        'cancelled': "❌ Запись отменена",
        'no_slots': "❌ На это время нет свободных слотов",
        'no_slots_for_date': "❌ На выбранную дату нет свободного времени у этого мастера",
        'booking_success': "✅ Вы успешно записаны! Номер записи: {}",
        'back': "🔙 Назад",
        'cancel': "❌ Отмена",
        'confirm_btn': "✅ Подтвердить",
        'masters': "Наши мастера:",
        'services': "Наши услуги:",
        'price_from': "от ${}",
        'price_to': "до ${}",
        'book': "📝 Записаться",
        'my_bookings': "📋 Мои записи",
        'admin_panel': "👑 Админ-панель",
        'address': "📍 Наш адрес",
        'no_bookings': "У вас пока нет записей",
        'booking_info': "Запись #{}\nМастер: {}\nУслуга: {}\nДата: {}\nВремя: {}\nСтатус: {}",
        'status_pending': "Ожидает подтверждения",
        'status_confirmed': "Подтверждено",
        'status_cancelled': "Отменено",
        'status_completed': "Выполнено",
        'try_another_master': "🤔 Попробовать другого мастера?",
        'choose_another_master': "👩‍🎨 Выберите другого мастера:",
        'different_master': "🔄 Выбрать другого мастера",
        'change_master': "🔄 Сменить мастера",
        'back_to_masters': "🔙 К выбору мастеров",
        'need_callback': "📞 Нужен звонок",
        'callback_requested': "✅ Запрос на звонок отправлен. Администратор свяжется с вами!",
        'language': "🇷🇺 Русский",
        'select_language': "Выберите язык:",
        'our_address': '📍 **Наш адрес:**\n\nг. Алматы, ул. Абая 123\nБЦ "Алатау", 5 этаж, офис 501\n\n🕐 Режим работы:\nПн-Сб: 10:00 - 20:00\nВс: Выходной\n\n📞 Телефон: +7 (727) 123-45-67\n\nМы находимся в центре города, рядом с метро!',
        'enter_booking_number': "📝 **Для отмены записи отправьте номер записи:**\n\nНомер записи можно найти в разделе 'Мои записи'\nНапример: #123",
        'booking_not_found': "❌ Запись с таким номером не найдена.",
        'already_cancelled': "❌ Запись #{} уже отменена.",
        'already_completed': "❌ Запись #{} уже выполнена.",
        'confirm_cancel': "⚠️ **Вы уверены, что хотите отменить запись #{}?**\n\nДата: {}\nВремя: {}",
        'cancelled_success': "✅ **Запись #{} успешно отменена!**",
        'cancel_aborted': "✅ Отмена отменена. Запись сохраняется.",
        'admin_notes': "📝 Управление заметками",
        'add_note': "➕ Добавить заметку",
        'edit_note': "✏️ Редактировать заметку",
        'delete_note': "❌ Удалить заметку",
        'view_notes': "👁 Просмотреть заметки",
        'manual_booking': "📝 Ручная запись клиента",
        'enter_client_name': "👤 Введите имя клиента:",
        'enter_client_phone': "📞 Введите телефон клиента:",
        'select_master': "👩‍🎨 Выберите мастера:",
        'select_service': "💅 Выберите услугу:",
        'select_date': "📅 Выберите дату:",
        'select_time': "⏰ Выберите время:",
        'confirm_manual': "✅ Подтвердите ручную запись:\n\nКлиент: {}\nТелефон: {}\nМастер: {}\nУслуга: {}\nДата: {}\nВремя: {}",
        'manual_success': "✅ Ручная запись #{} успешно создана!",
        'note_added': "✅ Заметка добавлена",
        'note_edited': "✅ Заметка отредактирована",
        'note_deleted': "✅ Заметка удалена",
        'enter_note_text': "📝 Введите текст заметки:",
        'enter_note_date': "📅 Введите дату (ДД.ММ.ГГГГ):",
        'enter_note_time': "⏰ Введите время (ЧЧ:ММ) или 'весь день':",
        'block_day': "🚫 Заблокировать весь день",
        'unblock_day': "✅ Разблокировать весь день",
    },
    'en': {
        'welcome': "👋 Welcome to the beauty salon 'Preobrazhenie'!\n\nChoose language:",
        'main_menu': "Main menu:",
        'choose_master': "👩‍🎨 Choose a master:",
        'choose_service': "💅 Choose a service (prices from ${} to ${}):",
        'enter_phone': "📱 Enter your phone number:\n(e.g.: +7 999 123-45-67)",
        'choose_date': "📅 Choose a date:",
        'choose_time': "⏰ Choose available time:",
        'confirm': "✅ Confirm booking:\n\nMaster: {}\nService: {}\nPrice: ${}-${}\nDate: {}\nTime: {}\nPhone: {}",
        'confirmed': "✅ Booking confirmed! We're waiting for you!",
        'cancelled': "❌ Booking cancelled",
        'no_slots': "❌ No available slots for this time",
        'no_slots_for_date': "❌ No available time slots for this master on selected date",
        'booking_success': "✅ You have successfully booked! Booking number: {}",
        'back': "🔙 Back",
        'cancel': "❌ Cancel",
        'confirm_btn': "✅ Confirm",
        'masters': "Our masters:",
        'services': "Our services:",
        'price_from': "from ${}",
        'price_to': "to ${}",
        'book': "📝 Book now",
        'my_bookings': "📋 My bookings",
        'admin_panel': "👑 Admin panel",
        'address': "📍 Our address",
        'no_bookings': "You have no bookings yet",
        'booking_info': "Booking #{}\nMaster: {}\nService: {}\nDate: {}\nTime: {}\nStatus: {}",
        'status_pending': "Pending",
        'status_confirmed': "Confirmed",
        'status_cancelled': "Cancelled",
        'status_completed': "Completed",
        'try_another_master': "🤔 Try another master?",
        'choose_another_master': "👩‍🎨 Choose another master:",
        'different_master': "🔄 Choose different master",
        'change_master': "🔄 Change master",
        'back_to_masters': "🔙 Back to masters",
        'need_callback': "📞 Need a callback",
        'callback_requested': "✅ Callback request sent. Administrator will contact you!",
        'language': "🇬🇧 English",
        'select_language': "Choose language:",
        'our_address': '📍 **Our address:**\n\nAlmaty, Abay street 123\n"Alatau" Business Center, 5th floor, office 501\n\n🕐 Working hours:\nMon-Sat: 10:00 - 20:00\nSun: Closed\n\n📞 Phone: +7 (727) 123-45-67\n\nWe are located in the city center, near the metro!',
        'enter_booking_number': "📝 **To cancel a booking, send the booking number:**\n\nYou can find the number in 'My bookings'\nExample: #123",
        'booking_not_found': "❌ Booking not found.",
        'already_cancelled': "❌ Booking #{} is already cancelled.",
        'already_completed': "❌ Booking #{} is already completed.",
        'confirm_cancel': "⚠️ **Are you sure you want to cancel booking #{}?**\n\nDate: {}\nTime: {}",
        'cancelled_success': "✅ **Booking #{} successfully cancelled!**",
        'cancel_aborted': "✅ Cancellation aborted. Booking preserved.",
        'admin_notes': "📝 Notes Management",
        'add_note': "➕ Add note",
        'edit_note': "✏️ Edit note",
        'delete_note': "❌ Delete note",
        'view_notes': "👁 View notes",
        'manual_booking': "📝 Manual client booking",
        'enter_client_name': "👤 Enter client name:",
        'enter_client_phone': "📞 Enter client phone:",
        'select_master': "👩‍🎨 Select master:",
        'select_service': "💅 Select service:",
        'select_date': "📅 Select date:",
        'select_time': "⏰ Select time:",
        'confirm_manual': "✅ Confirm manual booking:\n\nClient: {}\nPhone: {}\nMaster: {}\nService: {}\nDate: {}\nTime: {}",
        'manual_success': "✅ Manual booking #{} created successfully!",
        'note_added': "✅ Note added",
        'note_edited': "✅ Note edited",
        'note_deleted': "✅ Note deleted",
        'enter_note_text': "📝 Enter note text:",
        'enter_note_date': "📅 Enter date (DD.MM.YYYY):",
        'enter_note_time': "⏰ Enter time (HH:MM) or 'all day':",
        'block_day': "🚫 Block all day",
        'unblock_day': "✅ Unblock all day",
    },
    'kz': {
        'welcome': "👋 'Преображение' сұлулық салонына қош келдіңіз!\n\nТілді таңдаңыз:",
        'main_menu': "Негізгі мәзір:",
        'choose_master': "👩‍🎨 Шеберді таңдаңыз:",
        'choose_service': "💅 Қызметті таңдаңыз (бағасы ${} бастап ${} дейін):",
        'enter_phone': "📱 Байланыс үшін телефон нөміріңізді енгізіңіз:\n(мысалы: +7 999 123-45-67)",
        'choose_date': "📅 Күнді таңдаңыз:",
        'choose_time': "⏰ Бос уақытты таңдаңыз:",
        'confirm': "✅ Жазбаны растаңыз:\n\nШебер: {}\nҚызмет: {}\nБағасы: ${}-${}\nКүні: {}\nУақыты: {}\nТелефон: {}",
        'confirmed': "✅ Жазба расталды! Салонда күтеміз!",
        'cancelled': "❌ Жазба болдырылмады",
        'no_slots': "❌ Бұл уақытқа бос орын жоқ",
        'no_slots_for_date': "❌ Бұл шеберде таңдалған күнге бос уақыт жоқ",
        'booking_success': "✅ Сәтті жазылдыңыз! Жазба нөмірі: {}",
        'back': "🔙 Артқа",
        'cancel': "❌ Болдырмау",
        'confirm_btn': "✅ Растау",
        'masters': "Біздің шеберлер:",
        'services': "Біздің қызметтер:",
        'price_from': "${} бастап",
        'price_to': "${} дейін",
        'book': "📝 Жазылу",
        'my_bookings': "📋 Менің жазбаларым",
        'admin_panel': "👑 Админ-панель",
        'address': "📍 Біздің мекенжай",
        'no_bookings': "Сізде әзірге жазбалар жоқ",
        'booking_info': "Жазба #{}\nШебер: {}\nҚызмет: {}\nКүні: {}\nУақыты: {}\nСтатус: {}",
        'status_pending': "Растауды күтуде",
        'status_confirmed': "Расталды",
        'status_cancelled': "Болдырылмады",
        'status_completed': "Орындалды",
        'try_another_master': "🤔 Басқа шеберді сынап көру?",
        'choose_another_master': "👩‍🎨 Басқа шеберді таңдаңыз:",
        'different_master': "🔄 Басқа шеберді таңдау",
        'change_master': "🔄 Шеберді ауыстыру",
        'back_to_masters': "🔙 Шеберлер таңдауға оралу",
        'need_callback': "📞 Қоңырау керек",
        'callback_requested': "✅ Қоңырау сұрау жіберілді. Администратор сізге хабарласады!",
        'language': "🇰🇿 Қазақша",
        'select_language': "Тілді таңдаңыз:",
        'our_address': '📍 **Біздің мекенжай:**\n\nАлматы қ., Абай к-сі 123\n"Алатау" БО, 5-қабат, 501-кеңсе\n\n🕐 Жұмыс уақыты:\nДс-Сб: 10:00 - 20:00\nЖс: Демалыс\n\n📞 Телефон: +7 (727) 123-45-67\n\nБіз қала орталығында, метро жанында орналасқанбыз!',
        'enter_booking_number': "📝 **Жазбаны болдырмау үшін жазба нөмірін жіберіңіз:**\n\nЖазба нөмірін 'Менің жазбаларым' бөлімінен табуға болады\nМысалы: #123",
        'booking_not_found': "❌ Жазба табылмады.",
        'already_cancelled': "❌ #{} жазбасы бұрыннан болдырылмаған.",
        'already_completed': "❌ #{} жазбасы бұрыннан орындалған.",
        'confirm_cancel': "⚠️ **#{} жазбасын болдырмағыңыз келе ме?**\n\nКүні: {}\nУақыты: {}",
        'cancelled_success': "✅ **#{} жазбасы сәтті болдырылмады!**",
        'cancel_aborted': "✅ Болдырмау тоқтатылды. Жазба сақталды.",
        'admin_notes': "📝 Ескертпелерді басқару",
        'add_note': "➕ Ескертпе қосу",
        'edit_note': "✏️ Ескертпені өңдеу",
        'delete_note': "❌ Ескертпені жою",
        'view_notes': "👁 Ескертпелерді көру",
        'manual_booking': "📝 Қолмен жазу",
        'enter_client_name': "👤 Клиенттің атын енгізіңіз:",
        'enter_client_phone': "📞 Клиенттің телефонын енгізіңіз:",
        'select_master': "👩‍🎨 Шеберді таңдаңыз:",
        'select_service': "💅 Қызметті таңдаңыз:",
        'select_date': "📅 Күнді таңдаңыз:",
        'select_time': "⏰ Уақытты таңдаңыз:",
        'confirm_manual': "✅ Қолмен жазуды растаңыз:\n\nКлиент: {}\nТелефон: {}\nШебер: {}\nҚызмет: {}\nКүні: {}\nУақыты: {}",
        'manual_success': "✅ Қолмен жазу #{} сәтті жасалды!",
        'note_added': "✅ Ескертпе қосылды",
        'note_edited': "✅ Ескертпе өңделді",
        'note_deleted': "✅ Ескертпе жойылды",
        'enter_note_text': "📝 Ескертпе мәтінін енгізіңіз:",
        'enter_note_date': "📅 Күнді енгізіңіз (КК.АА.ЖЖЖЖ):",
        'enter_note_time': "⏰ Уақытты енгізіңіз (СС:ММ) немесе 'бүкіл күн':",
        'block_day': "🚫 Бүкіл күнді бұғаттау",
        'unblock_day': "✅ Бүкіл күнді бұғаттау",
    }
}

# ==================== КЛАВИАТУРЫ ====================

def get_language_keyboard():
    """Клавиатура выбора языка (3 языка)"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kz")
    )
    return keyboard

def get_main_menu(lang='ru'):
    """Главное меню"""
    texts = TEXTS[lang]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton(text=texts['book']),
        KeyboardButton(text=texts['my_bookings'])
    )
    keyboard.add(
        KeyboardButton(text=texts['cancel_booking']),
        KeyboardButton(text=texts['address'])
    )
    keyboard.add(KeyboardButton(text="🇷🇺/🇬🇧/🇰🇿 Language"))
    if ADMIN_ID:
        keyboard.add(KeyboardButton(text=texts['admin_panel']))
    return keyboard

def get_masters_keyboard(lang='ru'):
    """Клавиатура с мастерами"""
    masters = db.get_masters(lang)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for master_id, name, spec in masters:
        keyboard.add(
            InlineKeyboardButton(text=f"{name} - {spec}", callback_data=f"master_{master_id}")
        )
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['back'], callback_data="back_to_main")
    )
    return keyboard

def get_services_keyboard(lang='ru'):
    """Клавиатура с услугами"""
    services = db.get_services(lang)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for service_id, name, price_from, price_to in services:
        text = f"{name} (${price_from}-${price_to})"
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"service_{service_id}")
        )
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['back'], callback_data="back_to_masters")
    )
    return keyboard

def get_dates_keyboard(lang='ru'):
    """Клавиатура с датами (ближайшие 7 дней)"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        day_name = date.strftime("%A")
        
        if lang == 'ru':
            days = {
                'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
                'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
            }
            day_short = days.get(day_name, day_name[:2])
            text = f"{date_str} ({day_short})"
        elif lang == 'kz':
            days = {
                'Monday': 'Дс', 'Tuesday': 'Сс', 'Wednesday': 'Ср',
                'Thursday': 'Бс', 'Friday': 'Жм', 'Saturday': 'Сб', 'Sunday': 'Жс'
            }
            day_short = days.get(day_name, day_name[:2])
            text = f"{date_str} ({day_short})"
        else:
            text = f"{date_str} ({day_name[:3]})"
        
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"date_{date_str}")
        )
    
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['change_master'], callback_data="change_master")
    )
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['back'], callback_data="back_to_services")
    )
    return keyboard

def get_times_keyboard(available_times, lang='ru'):
    """Клавиатура с доступным временем"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for time in available_times:
        buttons.append(
            InlineKeyboardButton(text=time, callback_data=f"time_{time}")
        )
    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['change_master'], callback_data="change_master")
    )
    keyboard.add(
        InlineKeyboardButton(text=TEXTS[lang]['back'], callback_data="back_to_dates")
    )
    return keyboard

def get_no_slots_keyboard(lang='ru'):
    """Клавиатура когда нет свободных слотов"""
    texts = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=texts['change_master'], callback_data="change_master"),
        InlineKeyboardButton(text=texts['back'], callback_data="back_to_dates")
    )
    return keyboard

def get_confirmation_keyboard(lang='ru'):
    """Клавиатура подтверждения с кнопкой звонка"""
    texts = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text=texts['confirm_btn'], callback_data="confirm_yes"),
        InlineKeyboardButton(text=texts['need_callback'], callback_data="need_callback")
    )
    keyboard.add(
        InlineKeyboardButton(text=texts['cancel'], callback_data="confirm_no")
    )
    return keyboard

def get_admin_keyboard(lang='ru'):
    """Админ-клавиатура"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="📅 Записи на сегодня", callback_data="admin_view_today"),
        InlineKeyboardButton(text="📅 Выбрать дату", callback_data="admin_view_date"),
        InlineKeyboardButton(text="📊 Статистика за 2 месяца", callback_data="admin_stats"),
        InlineKeyboardButton(text="💰 Финансы", callback_data="admin_finance"),
        InlineKeyboardButton(text="📝 Управление заметками", callback_data="admin_notes_menu"),
        InlineKeyboardButton(text="📝 Ручная запись", callback_data="admin_manual_booking"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )
    return keyboard

def get_notes_menu_keyboard(lang='ru'):
    """Клавиатура управления заметками"""
    texts = TEXTS[lang]
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text=texts['add_note'], callback_data="admin_add_note"),
        InlineKeyboardButton(text=texts['view_notes'], callback_data="admin_view_notes"),
        InlineKeyboardButton(text=texts['edit_note'], callback_data="admin_edit_note"),
        InlineKeyboardButton(text=texts['delete_note'], callback_data="admin_delete_note"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    return keyboard

def get_masters_for_admin(lang='ru', action='note'):
    """Клавиатура с мастерами для админа"""
    masters = db.get_masters(lang)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for master_id, name, spec in masters:
        keyboard.add(
            InlineKeyboardButton(text=name, callback_data=f"admin_{action}_master_{master_id}")
        )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
    )
    return keyboard

def get_notes_list_keyboard(notes, date, master_id, action='view'):
    """Клавиатура со списком заметок"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    for note in notes:
        time, text, is_blocked = note
        status = "🔴" if is_blocked else "📝"
        keyboard.add(
            InlineKeyboardButton(
                text=f"{status} {time} - {text[:20]}...",
                callback_data=f"note_{action}_{date}_{master_id}_{time}"
            )
        )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
    )
    return keyboard

def get_manual_masters_keyboard(lang='ru'):
    """Клавиатура для ручной записи - выбор мастера"""
    masters = db.get_masters(lang)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for master_id, name, spec in masters:
        keyboard.add(
            InlineKeyboardButton(text=f"{name}", callback_data=f"manual_master_{master_id}")
        )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    return keyboard

def get_manual_services_keyboard(master_id, lang='ru'):
    """Клавиатура для ручной записи - выбор услуги"""
    services = db.get_services(lang)
    keyboard = InlineKeyboardMarkup(row_width=1)
    for service_id, name, price_from, price_to in services:
        text = f"{name} (${price_from}-${price_to})"
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"manual_service_{service_id}")
        )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    return keyboard

def get_manual_dates_keyboard(lang='ru'):
    """Клавиатура для ручной записи - выбор даты"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i in range(14):
        date = datetime.now() + timedelta(days=i)
        date_str = date.strftime("%d.%m.%Y")
        day_name = date.strftime("%A")
        
        if lang == 'ru':
            days = {'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср',
                    'Thursday': 'Чт', 'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'}
            day_short = days.get(day_name, day_name[:2])
            text = f"{date_str} ({day_short})"
        else:
            text = f"{date_str} ({day_name[:3]})"
        
        keyboard.add(
            InlineKeyboardButton(text=text, callback_data=f"manual_date_{date_str}")
        )
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    return keyboard

def get_manual_times_keyboard(available_times, lang='ru'):
    """Клавиатура для ручной записи - выбор времени"""
    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = []
    for time in available_times:
        buttons.append(
            InlineKeyboardButton(text=time, callback_data=f"manual_time_{time}")
        )
    keyboard.add(*buttons)
    keyboard.add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    )
    return keyboard

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
    await BookingStates.choosing_language.set()
    await message.answer(
        TEXTS['ru']['select_language'],
        reply_markup=get_language_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith('lang_'), state='*')
async def process_language(callback: types.CallbackQuery, state: FSMContext):
    """Выбор языка"""
    lang = callback.data.split('_')[1]
    await state.update_data(lang=lang)
    await state.finish()
    
    await callback.message.delete()
    await callback.message.answer(
        TEXTS[lang]['main_menu'],
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()

@dp.message_handler(lambda message: message.text in [TEXTS['ru']['address'], TEXTS['en']['address'], TEXTS['kz']['address']])
async def show_address(message: types.Message):
    """Показать адрес салона"""
    if message.text == TEXTS['ru']['address']:
        lang = 'ru'
    elif message.text == TEXTS['en']['address']:
        lang = 'en'
    else:
        lang = 'kz'
    
    await message.answer(
        TEXTS[lang]['our_address'],
        parse_mode="Markdown"
    )

@dp.message_handler(lambda message: message.text == "🇷🇺/🇬🇧/🇰🇿 Language")
async def change_language(message: types.Message, state: FSMContext):
    """Смена языка"""
    await BookingStates.choosing_language.set()
    await message.answer(
        "Выберите язык / Choose language / Тілді таңдаңыз:",
        reply_markup=get_language_keyboard()
    )

@dp.message_handler(lambda message: message.text in [TEXTS['ru']['book'], TEXTS['en']['book'], TEXTS['kz']['book']])
async def book_start(message: types.Message, state: FSMContext):
    """Начало бронирования"""
    if message.text == TEXTS['ru']['book']:
        lang = 'ru'
    elif message.text == TEXTS['en']['book']:
        lang = 'en'
    else:
        lang = 'kz'
    
    await state.update_data(lang=lang)
    await BookingStates.choosing_master.set()
    await message.answer(
        TEXTS[lang]['choose_master'],
        reply_markup=get_masters_keyboard(lang)
    )

@dp.callback_query_handler(lambda c: c.data.startswith('master_'), state=BookingStates.choosing_master)
async def process_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера"""
    master_id = int(callback.data.split('_')[1])
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.update_data(master_id=master_id)
    await BookingStates.choosing_service.set()
    
    master = db.get_master(master_id, lang)
    
    await callback.message.edit_text(
        f"{TEXTS[lang]['masters']} {master[0]}\n\n{TEXTS[lang]['choose_service']}",
        reply_markup=get_services_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "change_master", state='*')
async def change_master(callback: types.CallbackQuery, state: FSMContext):
    """Смена мастера"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await BookingStates.choosing_master.set()
    await callback.message.edit_text(
        TEXTS[lang]['choose_another_master'],
        reply_markup=get_masters_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('service_'), state=BookingStates.choosing_service)
async def process_service(callback: types.CallbackQuery, state: FSMContext):
    """Выбор услуги"""
    service_id = int(callback.data.split('_')[1])
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.update_data(service_id=service_id)
    await BookingStates.entering_phone.set()
    
    await callback.message.edit_text(
        TEXTS[lang]['enter_phone']
    )
    await callback.answer()

@dp.message_handler(state=BookingStates.entering_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Ввод телефона"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.update_data(phone=message.text)
    await BookingStates.choosing_date.set()
    
    await message.answer(
        TEXTS[lang]['choose_date'],
        reply_markup=get_dates_keyboard(lang)
    )

@dp.callback_query_handler(lambda c: c.data.startswith('date_'), state=BookingStates.choosing_date)
async def process_date(callback: types.CallbackQuery, state: FSMContext):
    """Выбор даты"""
    date = callback.data.split('_')[1]
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    master_id = data.get('master_id')
    
    await state.update_data(date=date)
    
    booked = db.get_booked_slots(date, master_id)
    admin_notes = db.get_admin_notes(date, master_id)
    
    all_times = [f"{h:02d}:00" for h in range(10, 20)]
    blocked_times = [note[0] for note in admin_notes if note[2] == 1]
    available_times = [t for t in all_times if t not in booked and t not in blocked_times]
    
    if not available_times:
        await callback.message.edit_text(
            TEXTS[lang]['no_slots_for_date'],
            reply_markup=get_no_slots_keyboard(lang)
        )
        await callback.answer()
        return
    
    await BookingStates.choosing_time.set()
    await callback.message.edit_text(
        TEXTS[lang]['choose_time'],
        reply_markup=get_times_keyboard(available_times, lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('time_'), state=BookingStates.choosing_time)
async def process_time(callback: types.CallbackQuery, state: FSMContext):
    """Выбор времени"""
    time = callback.data.split('_')[1]
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.update_data(time=time)
    
    master = db.get_master(data['master_id'], lang)
    service = db.get_service(data['service_id'], lang)
    
    await BookingStates.confirmation.set()
    await callback.message.edit_text(
        TEXTS[lang]['confirm'].format(
            master[0],
            service[0],
            service[1],
            service[2],
            data['date'],
            time,
            data['phone']
        ),
        reply_markup=get_confirmation_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "need_callback", state=BookingStates.confirmation)
async def request_callback(callback: types.CallbackQuery, state: FSMContext):
    """Запрос на звонок"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    master = db.get_master(data['master_id'], 'ru')
    service = db.get_service(data['service_id'], 'ru')
    
    admin_message = (
        f"📞 **ЗАПРОС НА ЗВОНОК!**\n\n"
        f"👤 Клиент: {callback.from_user.full_name}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💇‍♀️ Мастер: {master[0]}\n"
        f"💅 Услуга: {service[0]}\n"
        f"📅 Желаемая дата: {data.get('date', 'не указана')}\n"
        f"⏰ Желаемое время: {data.get('time', 'не указано')}\n"
        f"🆔 ID пользователя: {callback.from_user.id}"
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode="Markdown"
        )
        print(f"✅ Уведомление о звонке отправлено админу {ADMIN_ID}")
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления о звонке: {e}")
    
    await callback.message.edit_text(
        TEXTS[lang]['callback_requested']
    )
    await state.finish()
    await callback.message.answer(
        TEXTS[lang]['main_menu'],
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "confirm_yes", state=BookingStates.confirmation)
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение записи"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    booked = db.get_booked_slots(data['date'], data['master_id'])
    admin_notes = db.get_admin_notes(data['date'], data['master_id'])
    blocked_times = [note[0] for note in admin_notes if note[2] == 1]
    
    if data['time'] in booked or data['time'] in blocked_times:
        await callback.message.edit_text(
            f"❌ **К сожалению, это время уже занято!**\n\n"
            f"Дата: {data['date']}\n"
            f"Время: {data['time']}\n\n"
            f"Пожалуйста, выберите другое время.",
            reply_markup=get_dates_keyboard(lang)
        )
        await callback.answer()
        return
    
    appointment_id = db.create_appointment(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        user_phone=data['phone'],
        master_id=data['master_id'],
        service_id=data['service_id'],
        date=data['date'],
        time=data['time'],
        lang=lang
    )
    
    master = db.get_master(data['master_id'], 'ru')
    service = db.get_service(data['service_id'], 'ru')
    
    await callback.message.edit_text(
        f"✅ **ЗАПИСЬ ПОДТВЕРЖДЕНА!**\n\n"
        f"📝 Номер записи: #{appointment_id}\n"
        f"👩‍🎨 Мастер: {master[0]}\n"
        f"💅 Услуга: {service[0]}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}\n"
        f"📞 Телефон: {data['phone']}\n\n"
        f"💡 Сохраните номер записи для отмены или изменения.\n"
        f"Ждем вас в салоне! 🌸"
    )
    
    admin_message = (
        f"📝 **НОВАЯ ЗАПИСЬ!**\n\n"
        f"🆔 Номер: #{appointment_id}\n"
        f"👤 Клиент: {callback.from_user.full_name}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💇‍♀️ Мастер: {master[0]}\n"
        f"💅 Услуга: {service[0]}\n"
        f"📅 Дата: {data['date']}\n"
        f"⏰ Время: {data['time']}\n"
        f"🆔 ID пользователя: {callback.from_user.id}\n\n"
        f"Статус: ✅ Подтверждена автоматически"
    )
    
    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode="Markdown"
        )
        print(f"✅ Уведомление о новой записи #{appointment_id} отправлено админу")
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления админу: {e}")
    
    db.update_appointment_status(appointment_id, 'confirmed')
    
    await state.finish()
    await callback.message.answer(
        TEXTS[lang]['main_menu'],
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "confirm_no", state=BookingStates.confirmation)
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    """Отмена записи"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.finish()
    await callback.message.edit_text(TEXTS[lang]['cancelled'])
    await callback.message.answer(
        TEXTS[lang]['main_menu'],
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()

@dp.message_handler(lambda message: message.text in [TEXTS['ru']['my_bookings'], TEXTS['en']['my_bookings'], TEXTS['kz']['my_bookings']])
async def show_my_bookings(message: types.Message):
    """Показать записи пользователя"""
    if message.text == TEXTS['ru']['my_bookings']:
        lang = 'ru'
    elif message.text == TEXTS['en']['my_bookings']:
        lang = 'en'
    else:
        lang = 'kz'
    
    db.cursor.execute('''
        SELECT a.*, m.name_ru, m.name_en, m.name_kz, s.name_ru, s.name_en, s.name_kz 
        FROM appointments a
        LEFT JOIN masters m ON a.master_id = m.id
        LEFT JOIN services s ON a.service_id = s.id
        WHERE a.user_id = ?
        ORDER BY a.date DESC, a.time DESC
        LIMIT 10
    ''', (message.from_user.id,))
    
    appointments = db.cursor.fetchall()
    
    if not appointments:
        await message.answer(TEXTS[lang]['no_bookings'])
        return
    
    for app in appointments:
        if lang == 'ru':
            master_name = app[10]
            service_name = app[13]
        elif lang == 'en':
            master_name = app[11]
            service_name = app[14]
        else:
            master_name = app[12]
            service_name = app[15]
        
        status_map = {
            'pending': TEXTS[lang]['status_pending'],
            'confirmed': TEXTS[lang]['status_confirmed'],
            'cancelled': TEXTS[lang]['status_cancelled'],
            'completed': TEXTS[lang]['status_completed']
        }
        
        text = TEXTS[lang]['booking_info'].format(
            app[0],
            master_name,
            service_name,
            app[6],
            app[7],
            status_map.get(app[8], app[8])
        )
        
        await message.answer(text)

@dp.message_handler(lambda message: message.text in [TEXTS['ru']['cancel_booking'], TEXTS['en']['cancel_booking'], TEXTS['kz']['cancel_booking']])
async def cancel_booking_start(message: types.Message):
    """Начало отмены записи"""
    if message.text == TEXTS['ru']['cancel_booking']:
        lang = 'ru'
    elif message.text == TEXTS['en']['cancel_booking']:
        lang = 'en'
    else:
        lang = 'kz'
    
    await message.answer(TEXTS[lang]['enter_booking_number'])

@dp.message_handler(lambda message: message.text.startswith("#"))
async def process_cancel_booking(message: types.Message):
    """Обработка отмены записи по номеру"""
    try:
        appointment_id = int(message.text.replace("#", "").strip())
        
        db.cursor.execute('''
            SELECT * FROM appointments WHERE id = ? AND user_id = ?
        ''', (appointment_id, message.from_user.id))
        
        appointment = db.cursor.fetchone()
        
        if not appointment:
            await message.answer(TEXTS['ru']['booking_not_found'])
            return
        
        if appointment[8] in ['cancelled', 'completed']:
            status_text = 'отменена' if appointment[8] == 'cancelled' else 'выполнена'
            await message.answer(f"❌ Запись #{appointment_id} уже {status_text}.")
            return
        
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"cancel_confirm_{appointment_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel_abort")
        )
        
        await message.answer(
            f"⚠️ **Вы уверены, что хотите отменить запись #{appointment_id}?**\n\n"
            f"Дата: {appointment[6]}\n"
            f"Время: {appointment[7]}",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer(TEXTS['ru']['enter_booking_number'])

@dp.callback_query_handler(lambda c: c.data.startswith("cancel_confirm_"))
async def confirm_cancel_booking(callback: types.CallbackQuery):
    """Подтверждение отмены записи"""
    appointment_id = int(callback.data.replace("cancel_confirm_", ""))
    
    db.cursor.execute('''
        SELECT a.*, m.name_ru, s.name_ru 
        FROM appointments a
        LEFT JOIN masters m ON a.master_id = m.id
        LEFT JOIN services s ON a.service_id = s.id
        WHERE a.id = ?
    ''', (appointment_id,))
    
    appointment = db.cursor.fetchone()
    
    if not appointment:
        await callback.message.edit_text("❌ Запись не найдена")
        await callback.answer()
        return
    
    db.update_appointment_status(appointment_id, 'cancelled')
    
    admin_message = (
        f"❌ **ЗАПИСЬ ОТМЕНЕНА КЛИЕНТОМ!**\n\n"
        f"🆔 Номер: #{appointment_id}\n"
        f"👤 Клиент: {appointment[2]}\n"
        f"📞 Телефон: {appointment[3]}\n"
        f"💇‍♀️ Мастер: {appointment[13]}\n"
        f"💅 Услуга: {appointment[14]}\n"
        f"📅 Дата: {appointment[6]}\n"
        f"⏰ Время: {appointment[7]}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_message)
    except:
        pass
    
    await callback.message.edit_text(
        f"✅ **Запись #{appointment_id} успешно отменена!**"
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "cancel_abort")
async def abort_cancel(callback: types.CallbackQuery):
    """Отмена отмены записи"""
    await callback.message.edit_text("✅ Отмена отменена. Запись сохраняется.")
    await callback.answer()

# ==================== АДМИН-ПАНЕЛЬ ====================

@dp.message_handler(lambda message: message.text in [TEXTS['ru']['admin_panel'], TEXTS['en']['admin_panel'], TEXTS['kz']['admin_panel']])
async def admin_panel(message: types.Message):
    """Админ-панель"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        return
    
    await message.answer(
        "👑 Админ-панель",
        reply_markup=get_admin_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data == "admin_view_today")
async def admin_view_today(callback: types.CallbackQuery):
    """Просмотр записей на сегодня"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    today = datetime.now().strftime("%d.%m.%Y")
    appointments = db.get_appointments(date=today)
    
    if not appointments:
        await callback.message.edit_text(
            f"📅 На {today} записей нет",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
            )
        )
        await callback.answer()
        return
    
    text = f"📅 **Записи на {today}:**\n\n"
    for app in appointments:
        master = db.get_master(app[4], 'ru')
        service = db.get_service(app[5], 'ru')
        
        status_icon = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'completed': '✔️'
        }.get(app[8], '⏳')
        
        text += f"{status_icon} **{app[7]}** - {app[2]}\n"
        text += f"👤 {app[3]}\n"
        text += f"💇‍♀️ {master[0]} - {service[0]}\n"
        text += f"📞 {app[3]}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
        )
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_view_date")
async def admin_view_date(callback: types.CallbackQuery, state: FSMContext):
    """Выбор даты для просмотра"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.waiting_for_date.set()
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: 25.12.2024"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.waiting_for_date)
async def process_admin_date_input(message: types.Message, state: FSMContext):
    """Обработка введенной даты"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ запрещен")
        await state.finish()
        return
    
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
        date_str = message.text
    except:
        await message.answer(
            "❌ Неправильный формат даты. Попробуйте еще раз:"
        )
        return
    
    appointments = db.get_appointments(date=date_str)
    
    if not appointments:
        await message.answer(
            f"📅 На {date_str} записей нет",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_back")
            )
        )
        await state.finish()
        return
    
    text = f"📅 **Записи на {date_str}:**\n\n"
    for app in appointments:
        master = db.get_master(app[4], 'ru')
        service = db.get_service(app[5], 'ru')
        
        status_icon = {
            'pending': '⏳',
            'confirmed': '✅',
            'cancelled': '❌',
            'completed': '✔️'
        }.get(app[8], '⏳')
        
        text += f"{status_icon} **{app[7]}** - {app[2]}\n"
        text += f"👤 {app[3]}\n"
        text += f"💇‍♀️ {master[0]} - {service[0]}\n"
        text += f"📞 {app[3]}\n\n"
    
    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="🔙 В админ-панель", callback_data="admin_back")
        )
    )
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_stats")
async def admin_show_stats(callback: types.CallbackQuery):
    """Показать полную статистику за 2 месяца"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    db.cursor.execute('''
        SELECT a.*, m.name_ru, s.name_ru 
        FROM appointments a
        LEFT JOIN masters m ON a.master_id = m.id
        LEFT JOIN services s ON a.service_id = s.id
        WHERE a.created_at >= ? OR a.date >= ?
        ORDER BY a.date DESC, a.time DESC
    ''', (two_months_ago, two_months_ago.split(' ')[0]))
    
    appointments = db.cursor.fetchall()
    
    if not appointments:
        await callback.message.edit_text(
            "📊 За последние 2 месяца записей нет",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
            )
        )
        await callback.answer()
        return
    
    total_appointments = len(appointments)
    completed = len([a for a in appointments if a[8] == 'completed'])
    pending = len([a for a in appointments if a[8] == 'pending'])
    cancelled = len([a for a in appointments if a[8] == 'cancelled'])
    confirmed = len([a for a in appointments if a[8] == 'confirmed'])
    
    master_stats = {}
    for app in appointments:
        master_name = app[13]
        if master_name not in master_stats:
            master_stats[master_name] = 0
        master_stats[master_name] += 1
    
    service_stats = {}
    for app in appointments:
        service_name = app[14]
        if service_name not in service_stats:
            service_stats[service_name] = 0
        service_stats[service_name] += 1
    
    daily_stats = {}
    for app in appointments:
        date = app[6]
        if date not in daily_stats:
            daily_stats[date] = 0
        daily_stats[date] += 1
    
    text = "📊 **СТАТИСТИКА ЗА 2 МЕСЯЦА**\n\n"
    text += f"📅 Период: с {(datetime.now() - timedelta(days=60)).strftime('%d.%m.%Y')} по {datetime.now().strftime('%d.%m.%Y')}\n"
    text += "═" * 30 + "\n\n"
    
    text += "**ОБЩАЯ СТАТИСТИКА:**\n"
    text += f"📝 Всего записей: {total_appointments}\n"
    text += f"✅ Выполнено: {completed}\n"
    text += f"📌 Подтверждено: {confirmed}\n"
    text += f"⏳ Ожидает: {pending}\n"
    text += f"❌ Отменено: {cancelled}\n\n"
    
    text += "**СТАТИСТИКА ПО МАСТЕРАМ:**\n"
    for master, count in sorted(master_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_appointments) * 100
        text += f"👩‍🎨 {master}: {count} записей ({percentage:.1f}%)\n"
    
    text += "\n**СТАТИСТИКА ПО УСЛУГАМ:**\n"
    for service, count in sorted(service_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        percentage = (count / total_appointments) * 100
        text += f"💅 {service}: {count} раз ({percentage:.1f}%)\n"
    
    text += "\n**СТАТИСТИКА ПО ДНЯМ (ТОП-10):**\n"
    for date, count in sorted(daily_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        text += f"📅 {date}: {count} записей\n"
    
    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part, reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
                ))
            else:
                await callback.message.answer(part)
    else:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
        ))
    
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_finance")
async def admin_show_finance(callback: types.CallbackQuery):
    """Показать финансовую статистику"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    two_months_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    db.cursor.execute('''
        SELECT a.*, s.price_from, s.price_to, m.name_ru, s.name_ru
        FROM appointments a
        LEFT JOIN services s ON a.service_id = s.id
        LEFT JOIN masters m ON a.master_id = m.id
        WHERE (a.created_at >= ? OR a.date >= ?) AND a.status = 'completed'
    ''', (two_months_ago, two_months_ago.split(' ')[0]))
    
    completed_appointments = db.cursor.fetchall()
    
    total_revenue = 0
    min_revenue = 0
    max_revenue = 0
    avg_revenue = 0
    
    if completed_appointments:
        revenues = []
        for app in completed_appointments:
            price_from = app[15] if app[15] else 0
            price_to = app[16] if app[16] else 0
            avg_price = (price_from + price_to) / 2
            revenues.append(avg_price)
            total_revenue += avg_price
        
        min_revenue = min(revenues)
        max_revenue = max(revenues)
        avg_revenue = total_revenue / len(completed_appointments)
    
    monthly_stats = {}
    for app in completed_appointments:
        month = app[6][:7]
        if month not in monthly_stats:
            monthly_stats[month] = {'count': 0, 'revenue': 0}
        monthly_stats[month]['count'] += 1
        avg_price = (app[15] + app[16]) / 2 if app[15] and app[16] else 0
        monthly_stats[month]['revenue'] += avg_price
    
    text = "💰 **ФИНАНСОВАЯ СТАТИСТИКА**\n\n"
    text += f"📅 Период: с {(datetime.now() - timedelta(days=60)).strftime('%d.%m.%Y')} по {datetime.now().strftime('%d.%m.%Y')}\n"
    text += "═" * 30 + "\n\n"
    
    if completed_appointments:
        text += f"✅ Выполнено записей: {len(completed_appointments)}\n"
        text += f"💵 Общая выручка: ${total_revenue:.2f}\n"
        text += f"📊 Средний чек: ${avg_revenue:.2f}\n"
        text += f"📈 Минимальный чек: ${min_revenue:.2f}\n"
        text += f"📉 Максимальный чек: ${max_revenue:.2f}\n\n"
        
        text += "**СТАТИСТИКА ПО МЕСЯЦАМ:**\n"
        for month, data in sorted(monthly_stats.items()):
            month_name = {
                '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
                '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
                '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
            }.get(month[5:7], month)
            text += f"📅 {month_name}: {data['count']} записей, ${data['revenue']:.2f}\n"
    else:
        text += "❌ Нет завершенных записей за этот период\n"
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")
    ))
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_notes_menu")
async def admin_notes_menu(callback: types.CallbackQuery):
    """Меню управления заметками"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "📝 **Управление заметками**\n\n"
        "Выберите действие:",
        reply_markup=get_notes_menu_keyboard()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_add_note")
async def admin_add_note_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления заметки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.adding_note.set()
    await callback.message.edit_text(
        "Выберите мастера:",
        reply_markup=get_masters_for_admin(action='add')
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("admin_add_master_"), state=AdminStates.adding_note)
async def admin_add_note_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера для добавления заметки"""
    master_id = int(callback.data.split('_')[3])
    await state.update_data(note_master_id=master_id)
    
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: 25.12.2024"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.adding_note)
async def admin_add_note_date(message: types.Message, state: FSMContext):
    """Обработка даты для заметки"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(note_date=message.text)
        await message.answer(
            "Введите время в формате ЧЧ:ММ\n"
            "Например: 14:30\n\n"
            "Или напишите 'весь день' чтобы заблокировать весь день"
        )
    except:
        await message.answer("❌ Неправильный формат даты. Попробуйте еще раз:")

@dp.message_handler(state=AdminStates.adding_note)
async def admin_add_note_time(message: types.Message, state: FSMContext):
    """Обработка времени для заметки"""
    data = await state.get_data()
    
    if message.text.lower() == 'весь день':
        keyboard = InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            InlineKeyboardButton(text="✅ Заблокировать весь день", callback_data="block_whole_day"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_notes_menu")
        )
        await message.answer(
            "Вы уверены, что хотите заблокировать весь день?",
            reply_markup=keyboard
        )
        await state.update_data(block_whole_day=True)
    else:
        try:
            datetime.strptime(message.text, "%H:%M")
            await state.update_data(note_time=message.text)
            await message.answer("Введите текст заметки:")
        except:
            await message.answer("❌ Неправильный формат времени. Попробуйте еще раз:")

@dp.callback_query_handler(lambda c: c.data == "block_whole_day", state=AdminStates.adding_note)
async def block_whole_day(callback: types.CallbackQuery, state: FSMContext):
    """Блокировка всего дня"""
    data = await state.get_data()
    
    for hour in range(10, 20):
        time = f"{hour:02d}:00"
        db.add_admin_note(
            date=data['note_date'],
            time=time,
            master_id=data['note_master_id'],
            note="Весь день заблокирован",
            is_blocked=1
        )
    
    await callback.message.edit_text("✅ Весь день заблокирован")
    await state.finish()
    await callback.answer()

@dp.message_handler(state=AdminStates.adding_note)
async def admin_add_note_save(message: types.Message, state: FSMContext):
    """Сохранение заметки"""
    data = await state.get_data()
    
    if 'block_whole_day' in data:
        await state.finish()
        return
    
    db.add_admin_note(
        date=data['note_date'],
        time=data['note_time'],
        master_id=data['note_master_id'],
        note=message.text,
        is_blocked=0
    )
    
    await message.answer("✅ Заметка добавлена")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_view_notes")
async def admin_view_notes_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало просмотра заметок"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.viewing_appointments.set()
    await callback.message.edit_text(
        "Выберите мастера для просмотра заметок:",
        reply_markup=get_masters_for_admin(action='view')
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("admin_view_master_"), state=AdminStates.viewing_appointments)
async def admin_view_notes_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера для просмотра заметок"""
    master_id = int(callback.data.split('_')[3])
    await state.update_data(view_master_id=master_id)
    
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: 25.12.2024"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.viewing_appointments)
async def admin_view_notes_date(message: types.Message, state: FSMContext):
    """Просмотр заметок по дате"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()
        master_id = data.get('view_master_id')
        
        notes = db.get_admin_notes(message.text, master_id)
        
        if not notes:
            await message.answer(
                f"📝 На {message.text} заметок нет",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
                )
            )
            await state.finish()
            return
        
        text = f"📝 **Заметки на {message.text}:**\n\n"
        for note in notes:
            time, note_text, is_blocked = note
            status = "🔴 ЗАБЛОКИРОВАНО" if is_blocked else "📝 Заметка"
            text += f"{status}\n⏰ {time}\n📌 {note_text}\n\n"
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
            )
        )
        await state.finish()
        
    except ValueError:
        await message.answer("❌ Неправильный формат даты. Попробуйте еще раз:")

@dp.callback_query_handler(lambda c: c.data == "admin_edit_note")
async def admin_edit_note_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования заметки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.editing_note.set()
    await callback.message.edit_text(
        "Выберите мастера:",
        reply_markup=get_masters_for_admin(action='edit')
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("admin_edit_master_"), state=AdminStates.editing_note)
async def admin_edit_note_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера для редактирования"""
    master_id = int(callback.data.split('_')[3])
    await state.update_data(edit_master_id=master_id)
    
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.editing_note)
async def admin_edit_note_date(message: types.Message, state: FSMContext):
    """Обработка даты для редактирования"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()
        master_id = data.get('edit_master_id')
        
        notes = db.get_admin_notes(message.text, master_id)
        
        if not notes:
            await message.answer(
                f"❌ На {message.text} заметок нет",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
                )
            )
            await state.finish()
            return
        
        await state.update_data(edit_date=message.text)
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for note in notes:
            time, note_text, is_blocked = note
            status = "🔴" if is_blocked else "📝"
            keyboard.add(
                InlineKeyboardButton(
                    text=f"{status} {time} - {note_text[:20]}...",
                    callback_data=f"edit_select_{time}"
                )
            )
        
        keyboard.add(
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
        )
        
        await message.answer(
            "Выберите заметку для редактирования:",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer("❌ Неправильный формат даты. Попробуйте еще раз:")

@dp.callback_query_handler(lambda c: c.data.startswith("edit_select_"), state=AdminStates.editing_note)
async def admin_edit_note_select(callback: types.CallbackQuery, state: FSMContext):
    """Выбор заметки для редактирования"""
    time = callback.data.replace("edit_select_", "")
    await state.update_data(edit_time=time)
    
    await callback.message.edit_text("Введите новый текст заметки:")
    await callback.answer()

@dp.message_handler(state=AdminStates.editing_note)
async def admin_edit_note_save(message: types.Message, state: FSMContext):
    """Сохранение отредактированной заметки"""
    data = await state.get_data()
    
    db.update_admin_note(
        date=data['edit_date'],
        time=data['edit_time'],
        master_id=data['edit_master_id'],
        new_note=message.text
    )
    
    await message.answer("✅ Заметка отредактирована")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "admin_delete_note")
async def admin_delete_note_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало удаления заметки"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.deleting_note.set()
    await callback.message.edit_text(
        "Выберите мастера:",
        reply_markup=get_masters_for_admin(action='delete')
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("admin_delete_master_"), state=AdminStates.deleting_note)
async def admin_delete_note_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера для удаления заметки"""
    master_id = int(callback.data.split('_')[3])
    await state.update_data(delete_master_id=master_id)
    
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.deleting_note)
async def admin_delete_note_date(message: types.Message, state: FSMContext):
    """Обработка даты для удаления"""
    try:
        datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()
        master_id = data.get('delete_master_id')
        
        notes = db.get_admin_notes(message.text, master_id)
        
        if not notes:
            await message.answer(
                f"❌ На {message.text} заметок нет",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
                )
            )
            await state.finish()
            return
        
        await state.update_data(delete_date=message.text)
        
        keyboard = InlineKeyboardMarkup(row_width=1)
        for note in notes:
            time, note_text, is_blocked = note
            status = "🔴" if is_blocked else "📝"
            keyboard.add(
                InlineKeyboardButton(
                    text=f"{status} {time} - {note_text[:20]}...",
                    callback_data=f"delete_confirm_{time}"
                )
            )
        
        keyboard.add(
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notes_menu")
        )
        
        await message.answer(
            "Выберите заметку для удаления:",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer("❌ Неправильный формат даты. Попробуйте еще раз:")

@dp.callback_query_handler(lambda c: c.data.startswith("delete_confirm_"), state=AdminStates.deleting_note)
async def admin_delete_note_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления заметки"""
    time = callback.data.replace("delete_confirm_", "")
    data = await state.get_data()
    
    db.delete_admin_note(
        date=data['delete_date'],
        time=time,
        master_id=data['delete_master_id']
    )
    
    await callback.message.edit_text("✅ Заметка удалена")
    await state.finish()
    await callback.answer()

# ==================== РУЧНАЯ ЗАПИСЬ ====================

@dp.callback_query_handler(lambda c: c.data == "admin_manual_booking")
async def admin_manual_booking_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало ручной записи"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await AdminStates.manual_client_name.set()
    await callback.message.edit_text(
        "👤 Введите имя клиента:"
    )
    await callback.answer()

@dp.message_handler(state=AdminStates.manual_client_name)
async def admin_manual_client_name(message: types.Message, state: FSMContext):
    """Ввод имени клиента"""
    await state.update_data(client_name=message.text)
    await AdminStates.manual_client_phone.set()
    await message.answer("📞 Введите телефон клиента:")

@dp.message_handler(state=AdminStates.manual_client_phone)
async def admin_manual_client_phone(message: types.Message, state: FSMContext):
    """Ввод телефона клиента"""
    await state.update_data(client_phone=message.text)
    await AdminStates.manual_master.set()
    await message.answer(
        "Выберите мастера:",
        reply_markup=get_manual_masters_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("manual_master_"), state=AdminStates.manual_master)
async def admin_manual_master(callback: types.CallbackQuery, state: FSMContext):
    """Выбор мастера"""
    master_id = int(callback.data.split('_')[2])
    await state.update_data(manual_master_id=master_id)
    await AdminStates.manual_service.set()
    
    await callback.message.edit_text(
        "Выберите услугу:",
        reply_markup=get_manual_services_keyboard(master_id)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("manual_service_"), state=AdminStates.manual_service)
async def admin_manual_service(callback: types.CallbackQuery, state: FSMContext):
    """Выбор услуги"""
    service_id = int(callback.data.split('_')[2])
    await state.update_data(manual_service_id=service_id)
    await AdminStates.manual_date.set()
    
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=get_manual_dates_keyboard()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("manual_date_"), state=AdminStates.manual_date)
async def admin_manual_date(callback: types.CallbackQuery, state: FSMContext):
    """Выбор даты"""
    date = callback.data.replace("manual_date_", "")
    data = await state.get_data()
    master_id = data.get('manual_master_id')
    
    booked = db.get_booked_slots(date, master_id)
    admin_notes = db.get_admin_notes(date, master_id)
    
    all_times = [f"{h:02d}:00" for h in range(10, 20)]
    blocked_times = [note[0] for note in admin_notes if note[2] == 1]
    available_times = [t for t in all_times if t not in booked and t not in blocked_times]
    
    if not available_times:
        await callback.message.edit_text(
            "❌ На эту дату нет свободного времени",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_manual_booking")
            )
        )
        await callback.answer()
        return
    
    await state.update_data(manual_date=date)
    await AdminStates.manual_time.set()
    
    await callback.message.edit_text(
        "Выберите время:",
        reply_markup=get_manual_times_keyboard(available_times)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data.startswith("manual_time_"), state=AdminStates.manual_time)
async def admin_manual_time(callback: types.CallbackQuery, state: FSMContext):
    """Выбор времени"""
    time = callback.data.replace("manual_time_", "")
    data = await state.get_data()
    master = db.get_master(data['manual_master_id'], 'ru')
    service = db.get_service(data['manual_service_id'], 'ru')
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="manual_confirm_yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
    )
    
    await callback.message.edit_text(
        f"✅ **Подтвердите ручную запись:**\n\n"
        f"👤 Клиент: {data['client_name']}\n"
        f"📞 Телефон: {data['client_phone']}\n"
        f"💇‍♀️ Мастер: {master[0]}\n"
        f"💅 Услуга: {service[0]}\n"
        f"📅 Дата: {data['manual_date']}\n"
        f"⏰ Время: {time}",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "manual_confirm_yes", state=AdminStates.manual_time)
async def admin_manual_confirm(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение ручной записи"""
    data = await state.get_data()
    
    appointment_id = db.create_appointment(
        user_id=ADMIN_ID,
        user_name=data['client_name'],
        user_phone=data['client_phone'],
        master_id=data['manual_master_id'],
        service_id=data['manual_service_id'],
        date=data['manual_date'],
        time=data['manual_time'],
        lang='ru'
    )
    
    db.update_appointment_status(appointment_id, 'confirmed')
    
    await callback.message.edit_text(
        f"✅ **Ручная запись #{appointment_id} успешно создана!**"
    )
    await state.finish()
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    """Возврат в админ-панель"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "👑 Админ-панель",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_main", state='*')
async def back_to_main(callback: types.CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await state.finish()
    await callback.message.delete()
    await callback.message.answer(
        TEXTS[lang]['main_menu'],
        reply_markup=get_main_menu(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_masters", state='*')
async def back_to_masters(callback: types.CallbackQuery, state: FSMContext):
    """Назад к выбору мастера"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await BookingStates.choosing_master.set()
    await callback.message.edit_text(
        TEXTS[lang]['choose_master'],
        reply_markup=get_masters_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_services", state='*')
async def back_to_services(callback: types.CallbackQuery, state: FSMContext):
    """Назад к выбору услуги"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await BookingStates.choosing_service.set()
    await callback.message.edit_text(
        TEXTS[lang]['choose_service'],
        reply_markup=get_services_keyboard(lang)
    )
    await callback.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_dates", state='*')
async def back_to_dates(callback: types.CallbackQuery, state: FSMContext):
    """Назад к выбору даты"""
    data = await state.get_data()
    lang = data.get('lang', 'ru')
    
    await BookingStates.choosing_date.set()
    await callback.message.edit_text(
        TEXTS[lang]['choose_date'],
        reply_markup=get_dates_keyboard(lang)
    )
    await callback.answer()

@dp.message_handler()
async def handle_unknown(message: types.Message):
    """Обработчик неизвестных сообщений"""
    await message.answer(
        "🤔 Я не понимаю эту команду.\n"
        "Используй кнопки меню ниже 👇",
        reply_markup=get_main_menu('ru')
    )

# ==================== ПРОСТОЙ HTTP-СЕРВЕР ДЛЯ RENDER ====================
# Этот сервер нужен только для того, чтобы Render видел открытый порт
# Он не влияет на работу бота

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    def log_message(self, format, *args):
        # Отключаем логи HTTP-сервера, чтобы не засорять консоль
        pass

def run_http_server():
    PORT = int(os.environ.get('PORT', 10000))
    handler = HealthCheckHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"✅ HTTP-сервер запущен на порту {PORT} (для Render)")
        httpd.serve_forever()

# Запускаем HTTP-сервер в отдельном потоке
http_thread = threading.Thread(target=run_http_server, daemon=True)
http_thread.start()

# ==================== ЗАПУСК ====================
import fcntl
import sys

def single_instance():
    """Проверяет, не запущен ли уже бот"""
    lock_file = '/tmp/bot.lock'
    try:
        fh = open(lock_file, 'w')
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except:
        print("❌ Бот уже запущен!")
        sys.exit(1)

if __name__ == "__main__":
    # Проверяем, не запущен ли уже бот
    try:
        single_instance()
    except:
        pass  # Если блокировка не работает на Render, пропускаем
    
    print("=" * 50)
    print("✅ БОТ ДЛЯ САЛОНА КРАСОТЫ 'ПРЕОБРАЖЕНИЕ' ЗАПУСКАЕТСЯ!")
    print("=" * 50)
    print(f"👑 Админ ID: {ADMIN_ID}")
    print("=" * 50)
    
    # Небольшая задержка перед запуском
    time.sleep(2)
    
    # Запуск бота
    executor.start_polling(dp, skip_updates=True, timeout=30)