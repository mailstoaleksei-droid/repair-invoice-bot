"""
TELEGRAM BOT v3.0 - С АВТОМАТИЧЕСКИМ МОНИТОРИНГОМ
Бот для управления обработкой PDF счетов с автоматическим отслеживанием новых файлов
"""

import telebot
from telebot import types
import os
import sys
import subprocess
import threading
from datetime import datetime

# Импорт модуля мониторинга
try:
    from file_monitor import FileMonitor, format_file_size, get_file_info
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    print("⚠️ Модуль file_monitor.py не найден. Автомониторинг недоступен.")

# ===== НАСТРОЙКИ БОТА =====
TELEGRAM_BOT_TOKEN = "8127115250:AAHmDuiiRuPSpE6oSwHzmUpSl2-DzVSr3Io"
TELEGRAM_CHAT_ID = "745125435"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Пути к скриптам и папкам
SCRIPT_PATH = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\PDF_Processor\process_pdf_v4.py"
PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
MANUAL_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG\manual"
PROCESSED_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\RG 2025 Ersatyteile RepRG"

# Глобальные переменные
processing_status = {
    'is_running': False,
    'start_time': None,
    'last_run': None,
    'last_results': None
}

# Мониторинг файлов
file_monitor = None
monitor_settings = {
    'enabled': False,
    'auto_process': False  # Автоматически обрабатывать новые файлы
}

# ===== ФУНКЦИИ МОНИТОРИНГА =====

def init_file_monitor():
    """Инициализировать мониторинг файлов"""
    global file_monitor
    
    if not MONITOR_AVAILABLE:
        return False
    
    try:
        if file_monitor is None:
            file_monitor = FileMonitor(PDF_FOLDER, on_new_file_detected)
        return True
    except Exception as e:
        print(f"Ошибка инициализации мониторинга: {e}")
        return False

def on_new_file_detected(file_path, filename, file_size):
    """
    Callback функция при обнаружении нового файла
    """
    try:
        # Форматировать размер
        size_str = format_file_size(file_size)
        
        # Создать сообщение
        message_text = (
            f"📥 <b>Новый файл обнаружен!</b>\n\n"
            f"📄 <b>Имя:</b> <code>{filename}</code>\n"
            f"📊 <b>Размер:</b> {size_str}\n"
            f"⏰ <b>Время:</b> {datetime.now().strftime('%H:%M:%S')}\n"
        )
        
        # Кнопки действий
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("🚀 Обработать сейчас", callback_data=f"process_file:{filename}"),
            types.InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_file")
        )
        
        # Отправить уведомление
        bot.send_message(
            TELEGRAM_CHAT_ID,
            message_text,
            reply_markup=markup,
            parse_mode='HTML'
        )
        
        # Если включена автообработка - запустить
        if monitor_settings.get('auto_process', False):
            # Небольшая задержка
            threading.Timer(3.0, lambda: trigger_processing()).start()
        
    except Exception as e:
        print(f"Ошибка в on_new_file_detected: {e}")

def start_monitoring():
    """Запустить мониторинг"""
    global file_monitor, monitor_settings
    
    if not init_file_monitor():
        return False
    
    if file_monitor.start():
        monitor_settings['enabled'] = True
        return True
    return False

def stop_monitoring():
    """Остановить мониторинг"""
    global file_monitor, monitor_settings
    
    if file_monitor and file_monitor.stop():
        monitor_settings['enabled'] = False
        return True
    return False

# ===== КОМАНДЫ БОТА =====

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение и меню"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    # Кнопки меню
    btn_process = types.KeyboardButton('🔄 Обработать PDF')
    btn_status = types.KeyboardButton('📊 Статус')
    btn_stats = types.KeyboardButton('📈 Статистика')
    btn_manual = types.KeyboardButton('📁 Ручные')
    btn_monitor = types.KeyboardButton('🔍 Мониторинг')
    btn_help = types.KeyboardButton('❓ Помощь')
    
    markup.add(btn_process, btn_status)
    markup.add(btn_stats, btn_manual)
    markup.add(btn_monitor, btn_help)
    
    welcome_text = (
        "👋 <b>Привет! Я бот для обработки PDF счетов v3.0</b>\n\n"
        "🆕 <b>Новое в v3.0:</b>\n"
        "✨ Автоматический мониторинг новых файлов\n"
        "✨ Мгновенные уведомления (в течение 5 сек)\n"
        "✨ Опция автообработки\n\n"
        
        "<b>Доступные функции:</b>\n"
        "🔄 <b>Обработать PDF</b> - запустить обработку\n"
        "📊 <b>Статус</b> - текущее состояние\n"
        "📈 <b>Статистика</b> - результаты обработки\n"
        "📁 <b>Ручные</b> - файлы для ручной обработки\n"
        "🔍 <b>Мониторинг</b> - управление автомониторингом\n"
        "❓ <b>Помощь</b> - справка по боту\n\n"
        
        f"📍 Папка: <code>EingangsRG</code>\n"
        f"🔍 Мониторинг: {'✅ Включен' if monitor_settings['enabled'] else '⏸️ Выключен'}"
    )
    
    bot.send_message(
        message.chat.id, 
        welcome_text,
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.message_handler(func=lambda message: message.text == '🔄 Обработать PDF')
def process_pdfs(message):
    """Запустить обработку PDF"""
    
    if processing_status['is_running']:
        bot.reply_to(
            message, 
            "⚠️ Обработка уже запущена!\n"
            f"Начата: {processing_status['start_time'].strftime('%H:%M:%S') if processing_status['start_time'] else 'неизвестно'}"
        )
        return
    
    try:
        pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
        pdf_count = len(pdf_files)
        
        if pdf_count == 0:
            bot.reply_to(
                message,
                "📭 Нет файлов для обработки\n\n"
                "Папка пуста, добавьте PDF файлы в папку EingangsRG"
            )
            return
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка доступа к папке: {e}")
        return
    
    # Начинаем обработку
    bot.send_message(
        message.chat.id,
        f"⏳ <b>Начинаю обработку...</b>\n\n"
        f"📄 Файлов к обработке: {pdf_count}\n"
        f"⏰ Время начала: {datetime.now().strftime('%H:%M:%S')}\n\n"
        f"⏱️ Ожидайте результаты...",
        parse_mode='HTML'
    )
    
    processing_status['is_running'] = True
    processing_status['start_time'] = datetime.now()
    
    try:
        result = subprocess.run(
            ['python', SCRIPT_PATH],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600
        )
        
        output = result.stdout
        
        # Парсинг результатов
        processed = 0
        duplicates = 0
        manual = 0
        
        for line in output.split('\n'):
            if 'Обработано успешно:' in line:
                try:
                    processed = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Дубликатов:' in line:
                try:
                    duplicates = int(line.split(':')[1].strip())
                except:
                    pass
            elif 'Требуют ручной обработки:' in line:
                try:
                    manual = int(line.split(':')[1].strip())
                except:
                    pass
        
        processing_status['last_results'] = {
            'total': pdf_count,
            'processed': processed,
            'duplicates': duplicates,
            'manual': manual,
            'time': datetime.now()
        }
        
        processing_time = datetime.now() - processing_status['start_time']
        minutes = int(processing_time.total_seconds() / 60)
        seconds = int(processing_time.total_seconds() % 60)
        
        result_text = (
            f"✅ <b>Обработка завершена!</b>\n\n"
            f"📊 <b>Результаты:</b>\n"
            f"📄 Всего файлов: {pdf_count}\n"
            f"✓ Успешно обработано: {processed}\n"
            f"⚠️ Дубликатов: {duplicates}\n"
            f"❌ Требуют ручной обработки: {manual}\n\n"
            f"⏱️ Время обработки: {minutes}:{seconds:02d}\n"
        )
        
        if pdf_count > 0:
            success_rate = (processed / pdf_count) * 100
            result_text += f"📈 Процент автоматизации: {success_rate:.1f}%\n"
        
        try:
            remaining = len([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')])
            if remaining > 0:
                result_text += f"\n⚠️ Осталось файлов: {remaining}"
        except:
            pass
        
        bot.send_message(message.chat.id, result_text, parse_mode='HTML')
        
    except subprocess.TimeoutExpired:
        bot.send_message(
            message.chat.id,
            "⚠️ Обработка заняла слишком много времени (>10 минут)\n"
            "Проверьте состояние вручную"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ <b>Ошибка при обработке:</b>\n\n{str(e)}",
            parse_mode='HTML'
        )
    finally:
        processing_status['is_running'] = False
        processing_status['last_run'] = datetime.now()

@bot.message_handler(func=lambda message: message.text == '📊 Статус')
def show_status(message):
    """Показать текущий статус"""
    
    try:
        pdf_count = len([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')])
        manual_count = len([f for f in os.listdir(MANUAL_FOLDER) if f.lower().endswith('.pdf')])
        processed_count = len([f for f in os.listdir(PROCESSED_FOLDER) if f.lower().endswith('.pdf')])
        
        status_text = f"📊 <b>Текущий статус системы</b>\n\n"
        
        if processing_status['is_running']:
            elapsed = datetime.now() - processing_status['start_time']
            minutes = int(elapsed.total_seconds() / 60)
            status_text += f"⏳ <b>Обработка запущена</b>\n"
            status_text += f"Прошло времени: {minutes} мин.\n\n"
        else:
            status_text += f"✅ <b>Система готова</b>\n\n"
        
        status_text += f"📁 <b>Состояние папок:</b>\n"
        status_text += f"📥 Входящие: {pdf_count} файлов\n"
        status_text += f"✋ Ручная обработка: {manual_count} файлов\n"
        status_text += f"✅ Обработанные: {processed_count} файлов\n\n"
        
        # Статус мониторинга
        status_text += f"🔍 <b>Мониторинг:</b>\n"
        if monitor_settings['enabled']:
            if file_monitor:
                mon_status = file_monitor.get_status()
                uptime_min = int(mon_status['uptime_seconds'] / 60)
                status_text += f"✅ Включен ({uptime_min} мин.)\n"
                status_text += f"📊 Обнаружено файлов: {mon_status['files_detected']}\n"
                status_text += f"🤖 Автообработка: {'✅ Вкл' if monitor_settings['auto_process'] else '⏸️ Выкл'}\n"
        else:
            status_text += f"⏸️ Выключен\n"
        
        status_text += f"\n"
        
        if processing_status['last_run']:
            time_ago = datetime.now() - processing_status['last_run']
            hours = int(time_ago.total_seconds() / 3600)
            minutes = int((time_ago.total_seconds() % 3600) / 60)
            
            status_text += f"🕐 <b>Последний запуск:</b>\n"
            if hours > 0:
                status_text += f"{hours} ч. {minutes} мин. назад\n"
            else:
                status_text += f"{minutes} мин. назад\n"
        else:
            status_text += f"🕐 Еще не запускался\n"
        
        bot.send_message(message.chat.id, status_text, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка получения статуса: {e}")

@bot.message_handler(func=lambda message: message.text == '🔍 Мониторинг')
def show_monitoring_menu(message):
    """Показать меню управления мониторингом"""
    
    if not MONITOR_AVAILABLE:
        bot.reply_to(
            message,
            "❌ <b>Мониторинг недоступен</b>\n\n"
            "Модуль file_monitor.py не найден.\n"
            "Установите библиотеку: pip install watchdog",
            parse_mode='HTML'
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    
    if monitor_settings['enabled']:
        markup.add(
            types.InlineKeyboardButton("⏸️ Остановить мониторинг", callback_data="monitor_stop")
        )
        
        # Кнопка автообработки
        if monitor_settings['auto_process']:
            markup.add(
                types.InlineKeyboardButton("🤖 Выключить автообработку", callback_data="monitor_auto_off")
            )
        else:
            markup.add(
                types.InlineKeyboardButton("🤖 Включить автообработку", callback_data="monitor_auto_on")
            )
    else:
        markup.add(
            types.InlineKeyboardButton("▶️ Запустить мониторинг", callback_data="monitor_start")
        )
    
    markup.add(
        types.InlineKeyboardButton("📊 Статус мониторинга", callback_data="monitor_status")
    )
    
    # Текст сообщения
    mon_text = f"🔍 <b>Управление мониторингом файлов</b>\n\n"
    
    if monitor_settings['enabled']:
        mon_text += f"✅ Статус: <b>Включен</b>\n"
        if file_monitor:
            mon_status = file_monitor.get_status()
            uptime_min = int(mon_status['uptime_seconds'] / 60)
            mon_text += f"⏱️ Работает: {uptime_min} мин.\n"
            mon_text += f"📊 Обнаружено: {mon_status['files_detected']} файлов\n"
        mon_text += f"🤖 Автообработка: {'✅ Включена' if monitor_settings['auto_process'] else '⏸️ Выключена'}\n\n"
        mon_text += f"📍 Папка: <code>EingangsRG</code>\n"
        mon_text += f"⚡ Обнаружение: в течение 5 секунд\n"
    else:
        mon_text += f"⏸️ Статус: <b>Выключен</b>\n\n"
        mon_text += f"Включите мониторинг для автоматического отслеживания новых файлов.\n"
    
    bot.send_message(
        message.chat.id,
        mon_text,
        reply_markup=markup,
        parse_mode='HTML'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('monitor_'))
def handle_monitor_callback(call):
    """Обработка кнопок мониторинга"""
    
    action = call.data.replace('monitor_', '')
    
    if action == 'start':
        if start_monitoring():
            bot.answer_callback_query(call.id, "✅ Мониторинг запущен!")
            bot.send_message(
                call.message.chat.id,
                "✅ <b>Мониторинг запущен</b>\n\n"
                "Теперь вы будете получать уведомления о новых PDF файлах в папке EingangsRG.\n"
                "Обнаружение происходит в течение 5 секунд после добавления файла.",
                parse_mode='HTML'
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка запуска мониторинга")
    
    elif action == 'stop':
        if stop_monitoring():
            bot.answer_callback_query(call.id, "⏸️ Мониторинг остановлен")
            bot.send_message(
                call.message.chat.id,
                "⏸️ <b>Мониторинг остановлен</b>\n\n"
                "Автоматическое отслеживание новых файлов отключено.",
                parse_mode='HTML'
            )
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка остановки")
    
    elif action == 'auto_on':
        monitor_settings['auto_process'] = True
        bot.answer_callback_query(call.id, "🤖 Автообработка включена")
        bot.send_message(
            call.message.chat.id,
            "🤖 <b>Автообработка включена</b>\n\n"
            "Новые файлы будут автоматически обрабатываться через 3 секунды после обнаружения.",
            parse_mode='HTML'
        )
    
    elif action == 'auto_off':
        monitor_settings['auto_process'] = False
        bot.answer_callback_query(call.id, "⏸️ Автообработка выключена")
        bot.send_message(
            call.message.chat.id,
            "⏸️ <b>Автообработка выключена</b>\n\n"
            "Новые файлы будут только обнаруживаться, без автоматической обработки.",
            parse_mode='HTML'
        )
    
    elif action == 'status':
        if file_monitor and monitor_settings['enabled']:
            mon_status = file_monitor.get_status()
            uptime_min = int(mon_status['uptime_seconds'] / 60)
            
            status_msg = (
                f"📊 <b>Статус мониторинга</b>\n\n"
                f"✅ Включен\n"
                f"⏱️ Работает: {uptime_min} мин.\n"
                f"📊 Обнаружено файлов: {mon_status['files_detected']}\n"
                f"🤖 Автообработка: {'✅ Вкл' if monitor_settings['auto_process'] else '⏸️ Выкл'}\n"
                f"📍 Папка: <code>{mon_status['folder_path']}</code>\n"
                f"🚀 Запущен: {mon_status['start_time']}"
            )
        else:
            status_msg = "⏸️ Мониторинг выключен"
        
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, status_msg, parse_mode='HTML')
    
    # Обновить меню
    show_monitoring_menu(call.message)

@bot.callback_query_handler(func=lambda call: call.data.startswith('process_file:'))
def handle_process_file(call):
    """Обработать конкретный файл"""
    filename = call.data.replace('process_file:', '')
    
    bot.answer_callback_query(call.id, f"🚀 Запуск обработки...")
    bot.send_message(
        call.message.chat.id,
        f"🚀 Запускаю обработку файла: <code>{filename}</code>",
        parse_mode='HTML'
    )
    
    # Триггер обработки
    trigger_processing()

@bot.callback_query_handler(func=lambda call: call.data == 'skip_file')
def handle_skip_file(call):
    """Пропустить файл"""
    bot.answer_callback_query(call.id, "⏭️ Файл пропущен")

def trigger_processing():
    """Триггер для запуска обработки"""
    # Создать фейковое сообщение для вызова обработки
    class FakeMessage:
        def __init__(self):
            self.chat = type('obj', (object,), {'id': TELEGRAM_CHAT_ID})
            self.text = '🔄 Обработать PDF'
    
    process_pdfs(FakeMessage())

@bot.message_handler(func=lambda message: message.text == '📈 Статистика')
def show_statistics(message):
    """Показать статистику последней обработки"""
    
    if not processing_status['last_results']:
        bot.reply_to(
            message,
            "📊 Нет данных о последней обработке\n\n"
            "Запустите обработку с помощью кнопки '🔄 Обработать PDF'"
        )
        return
    
    results = processing_status['last_results']
    time_str = results['time'].strftime('%d.%m.%Y %H:%M')
    
    stats_text = (
        f"📈 <b>Статистика последней обработки</b>\n\n"
        f"📅 Время: {time_str}\n\n"
        f"📊 <b>Результаты:</b>\n"
        f"📄 Всего файлов: {results['total']}\n"
        f"✓ Обработано: {results['processed']}\n"
        f"⚠️ Дубликатов: {results['duplicates']}\n"
        f"❌ Ручная обработка: {results['manual']}\n\n"
    )
    
    if results['total'] > 0:
        success_rate = (results['processed'] / results['total']) * 100
        stats_text += f"📈 Процент автоматизации: {success_rate:.1f}%\n"
        
        if success_rate >= 90:
            stats_text += "🎯 Отличный результат!"
        elif success_rate >= 70:
            stats_text += "👍 Хороший результат"
        elif success_rate >= 50:
            stats_text += "📊 Средний результат"
        else:
            stats_text += "⚠️ Требуется оптимизация"
    
    bot.send_message(message.chat.id, stats_text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '📁 Ручные')
def show_manual_files(message):
    """Показать файлы требующие ручной обработки"""
    
    try:
        manual_files = [f for f in os.listdir(MANUAL_FOLDER) if f.lower().endswith('.pdf')]
        count = len(manual_files)
        
        if count == 0:
            bot.reply_to(
                message,
                "✅ Нет файлов для ручной обработки!\n\n"
                "Все счета обработаны автоматически"
            )
            return
        
        response_text = f"📁 <b>Файлы для ручной обработки ({count}):</b>\n\n"
        
        manual_types = {
            'manual_': '❌ Не распознан',
            'error_': '⚠️ Ошибка обработки',
            'duplicate_': '📋 Дубликат'
        }
        
        for prefix, description in manual_types.items():
            files = [f for f in manual_files if f.startswith(prefix)]
            if files:
                response_text += f"\n{description} ({len(files)}):\n"
                for file in files[:5]:
                    clean_name = file.replace(prefix, '').replace('_', ' ')
                    response_text += f"  • {clean_name}\n"
                
                if len(files) > 5:
                    response_text += f"  ... и еще {len(files) - 5}\n"
        
        response_text += f"\n📂 Папка: <code>manual</code>"
        
        bot.send_message(message.chat.id, response_text, parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка чтения папки manual: {e}")

@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def show_help(message):
    """Показать справку"""
    
    help_text = (
        "❓ <b>Справка по боту PDF Processor v3.0</b>\n\n"
        
        "<b>🆕 Новое в версии 3.0:</b>\n"
        "• 🔍 Автоматический мониторинг папки\n"
        "• ⚡ Уведомления о новых файлах (5 сек)\n"
        "• 🤖 Опция автообработки\n"
        "• 📊 Расширенная статистика\n\n"
        
        "<b>🔄 Обработка PDF:</b>\n"
        "Автоматически обрабатывает все PDF файлы в папке EingangsRG:\n"
        "• Извлекает данные (номер счета, дата, сумма, машина)\n"
        "• Определяет поставщика\n"
        "• Добавляет в Excel\n"
        "• Перемещает обработанные файлы\n\n"
        
        "<b>🔍 Мониторинг:</b>\n"
        "• Включить/выключить автоматическое отслеживание\n"
        "• Мгновенные уведомления о новых файлах\n"
        "• Автообработка новых файлов (опционально)\n"
        "• Статистика обнаруженных файлов\n\n"
        
        "<b>📊 Поддерживаемые поставщики:</b>\n"
        "• Vital Projekt (шины)\n"
        "• MAN Truck & Bus\n"
        "• Euromaster\n"
        "• DEKRA\n"
        "• TIP Trailer Services\n"
        "• Auto Compass\n"
        "• Groo GmbH\n"
        "• И другие...\n\n"
        
        "<b>💡 Совет:</b>\n"
        "Включите мониторинг для автоматического отслеживания новых файлов!\n\n"
        
        "📞 Поддержка: @your_username"
    )
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

# ===== ФУНКЦИЯ ДЛЯ ОТПРАВКИ УВЕДОМЛЕНИЙ =====

def send_notification(message_text):
    """Отправить уведомление в Telegram"""
    try:
        timestamp = datetime.now().strftime('%H:%M')
        full_message = f"{message_text}\n\n🕐 {timestamp}"
        
        bot.send_message(
            TELEGRAM_CHAT_ID, 
            full_message, 
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

# ===== ЗАПУСК БОТА =====

if __name__ == '__main__':
    print("="*50)
    print("TELEGRAM BOT v3.0 - PDF PROCESSOR")
    print("="*50)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Мониторинг файлов: {'✅ Доступен' if MONITOR_AVAILABLE else '❌ Недоступен'}")
    print("Бот запущен и ожидает команды...")
    print("\nДля остановки нажмите Ctrl+C")
    print("="*50)
    
    # Отправка уведомления о запуске
    send_notification(
        "🚀 <b>Бот PDF Processor v3.0 запущен!</b>\n\n"
        "✨ Новое: Автоматический мониторинг файлов\n"
        "Готов к обработке счетов.\n"
        "Используйте /start для начала работы"
    )
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n\n⏸️ Остановка бота...")
        if file_monitor and monitor_settings['enabled']:
            stop_monitoring()
        print("✅ Бот остановлен")
        send_notification("⛔ Бот остановлен")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        if file_monitor and monitor_settings['enabled']:
            stop_monitoring()
        send_notification(f"❌ Критическая ошибка бота:\n{e}")
