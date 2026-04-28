"""
TELEGRAM BOT v2.0
Бот для управления обработкой PDF счетов
С исправленными уведомлениями и расширенным функционалом
"""

import telebot
from telebot import types
import os
import sys
import subprocess
from datetime import datetime

# ===== НАСТРОЙКИ БОТА =====
# ВАЖНО: Замените на ваш токен от @BotFather
TELEGRAM_BOT_TOKEN = "8127115250:AAHmDuiiRuPSpE6oSwHzmUpSl2-DzVSr3Io"
# ВАЖНО: Замените на ваш Telegram ID (можно узнать у @userinfobot)
TELEGRAM_CHAT_ID = "745125435"

# Создаем бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Пути к скриптам и папкам
SCRIPT_PATH = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\PDF_Processor\process_pdf_v2.py"
PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
MANUAL_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG\manual"
PROCESSED_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\RG 2025 Ersatyteile RepRG"

# Глобальная переменная для хранения статуса обработки
processing_status = {
    'is_running': False,
    'start_time': None,
    'last_run': None,
    'last_results': None
}

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
    btn_help = types.KeyboardButton('❓ Помощь')
    btn_test = types.KeyboardButton('🔔 Тест уведомлений')
    
    markup.add(btn_process, btn_status)
    markup.add(btn_stats, btn_manual)
    markup.add(btn_help, btn_test)
    
    welcome_text = (
        "👋 <b>Привет! Я бот для обработки PDF счетов v2.0</b>\n\n"
        "Доступные функции:\n"
        "🔄 <b>Обработать PDF</b> - запустить обработку\n"
        "📊 <b>Статус</b> - текущее состояние\n"
        "📈 <b>Статистика</b> - результаты последней обработки\n"
        "📁 <b>Ручные</b> - файлы требующие ручной обработки\n"
        "❓ <b>Помощь</b> - справка по боту\n"
        "🔔 <b>Тест</b> - проверить уведомления\n\n"
        f"📍 Папка наблюдения: <code>EingangsRG</code>"
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
    
    # Проверка, не запущена ли уже обработка
    if processing_status['is_running']:
        bot.reply_to(
            message, 
            "⚠ Обработка уже запущена!\n"
            f"Начата: {processing_status['start_time'].strftime('%H:%M:%S') if processing_status['start_time'] else 'неизвестно'}"
        )
        return
    
    # Проверка наличия файлов
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
        f"⏱ Ожидайте результаты...",
        parse_mode='HTML'
    )
    
    # Установка статуса
    processing_status['is_running'] = True
    processing_status['start_time'] = datetime.now()
    
    try:
        # Запуск скрипта обработки
        result = subprocess.run(
            ['python', SCRIPT_PATH],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=600  # 10 минут таймаут
        )
        
        # Парсинг результатов из вывода
        output = result.stdout
        
        # Попытка извлечь статистику из вывода
        processed = 0
        duplicates = 0
        manual = 0
        
        # Простой парсинг вывода
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
        
        # Сохранение результатов
        processing_status['last_results'] = {
            'total': pdf_count,
            'processed': processed,
            'duplicates': duplicates,
            'manual': manual,
            'time': datetime.now()
        }
        
        # Время обработки
        processing_time = datetime.now() - processing_status['start_time']
        minutes = int(processing_time.total_seconds() / 60)
        seconds = int(processing_time.total_seconds() % 60)
        
        # Отправка результатов
        result_text = (
            f"✅ <b>Обработка завершена!</b>\n\n"
            f"📊 <b>Результаты:</b>\n"
            f"📄 Всего файлов: {pdf_count}\n"
            f"✓ Успешно обработано: {processed}\n"
            f"⚠ Дубликатов: {duplicates}\n"
            f"❌ Требуют ручной обработки: {manual}\n\n"
            f"⏱ Время обработки: {minutes}:{seconds:02d}\n"
        )
        
        # Добавляем процент успеха
        if pdf_count > 0:
            success_rate = (processed / pdf_count) * 100
            result_text += f"📈 Процент автоматизации: {success_rate:.1f}%\n"
        
        # Проверка оставшихся файлов
        try:
            remaining = len([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')])
            if remaining > 0:
                result_text += f"\n⚠ Осталось файлов: {remaining}"
        except:
            pass
        
        bot.send_message(message.chat.id, result_text, parse_mode='HTML')
        
    except subprocess.TimeoutExpired:
        bot.send_message(
            message.chat.id,
            "⚠ Обработка заняла слишком много времени (>10 минут)\n"
            "Проверьте состояние вручную"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ <b>Ошибка при обработке:</b>\n\n{str(e)}",
            parse_mode='HTML'
        )
    finally:
        # Сброс статуса
        processing_status['is_running'] = False
        processing_status['last_run'] = datetime.now()

@bot.message_handler(func=lambda message: message.text == '📊 Статус')
def show_status(message):
    """Показать текущий статус"""
    
    try:
        # Подсчет файлов
        pdf_count = len([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')])
        manual_count = len([f for f in os.listdir(MANUAL_FOLDER) if f.lower().endswith('.pdf')])
        processed_count = len([f for f in os.listdir(PROCESSED_FOLDER) if f.lower().endswith('.pdf')])
        
        status_text = f"📊 <b>Текущий статус системы</b>\n\n"
        
        # Статус обработки
        if processing_status['is_running']:
            elapsed = datetime.now() - processing_status['start_time']
            status_text += f"🔄 <b>Обработка запущена</b>\n"
            status_text += f"⏱ Идет: {int(elapsed.total_seconds() / 60)}:{int(elapsed.total_seconds() % 60):02d}\n\n"
        else:
            status_text += f"✅ <b>Система готова</b>\n\n"
        
        # Статистика папок
        status_text += f"📁 <b>Состояние папок:</b>\n"
        status_text += f"📥 Входящие: {pdf_count} файлов\n"
        status_text += f"✋ Ручная обработка: {manual_count} файлов\n"
        status_text += f"✅ Обработанные: {processed_count} файлов\n\n"
        
        # Последний запуск
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
        f"⚠ Дубликатов: {results['duplicates']}\n"
        f"❌ Ручная обработка: {results['manual']}\n\n"
    )
    
    # Процент успеха
    if results['total'] > 0:
        success_rate = (results['processed'] / results['total']) * 100
        stats_text += f"📈 Процент автоматизации: {success_rate:.1f}%\n"
        
        # Оценка результата
        if success_rate >= 90:
            stats_text += "🎯 Отличный результат!"
        elif success_rate >= 70:
            stats_text += "👍 Хороший результат"
        elif success_rate >= 50:
            stats_text += "📊 Средний результат"
        else:
            stats_text += "⚠ Требуется оптимизация"
    
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
        
        # Группировка по типам
        manual_types = {
            'manual_': '❌ Не распознан',
            'error_': '⚠ Ошибка обработки',
            'duplicate_': '📋 Дубликат'
        }
        
        for prefix, description in manual_types.items():
            files = [f for f in manual_files if f.startswith(prefix)]
            if files:
                response_text += f"\n{description} ({len(files)}):\n"
                for file in files[:5]:  # Показываем первые 5
                    # Убираем префикс для читабельности
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
        "❓ <b>Справка по боту PDF Processor v2.0</b>\n\n"
        
        "<b>🔄 Обработка PDF:</b>\n"
        "Автоматически обрабатывает все PDF файлы в папке EingangsRG:\n"
        "• Извлекает данные (номер счета, дата, сумма, машина)\n"
        "• Определяет поставщика\n"
        "• Добавляет в Excel\n"
        "• Перемещает обработанные файлы\n\n"
        
        "<b>📊 Поддерживаемые поставщики:</b>\n"
        "• Vital Projekt (шины)\n"
        "• MAN Truck & Bus\n"
        "• Euromaster\n"
        "• DEKRA\n"
        "• TIP Trailer Services\n"
        "• Auto Compass\n"
        "• Groo GmbH\n"
        "• И другие...\n\n"
        
        "<b>📁 Структура папок:</b>\n"
        "• <code>EingangsRG</code> - входящие PDF\n"
        "• <code>manual</code> - требуют ручной обработки\n"
        "• <code>processed</code> - обработанные файлы\n\n"
        
        "<b>🎯 Особенности v2.0:</b>\n"
        "• Улучшенное определение номеров машин\n"
        "• Расширенная поддержка поставщиков\n"
        "• Детальная статистика\n"
        "• Telegram уведомления\n\n"
        
        "<b>💡 Совет:</b>\n"
        "Для лучшего распознавания называйте файлы в формате:\n"
        "<code>checked_XXX - Поставщик Номер.pdf</code>\n"
        "где XXX - номер машины\n\n"
        
        "📞 Поддержка: @your_username"
    )
    
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text == '🔔 Тест уведомлений')
def test_notification(message):
    """Тестовое уведомление"""
    
    test_text = (
        "🔔 <b>Тест уведомлений</b>\n\n"
        "✅ Бот работает корректно!\n"
        f"📍 Ваш ID: {message.chat.id}\n"
        f"👤 Имя: {message.from_user.first_name}\n"
        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
        "Если вы видите это сообщение - уведомления настроены правильно!"
    )
    
    bot.send_message(message.chat.id, test_text, parse_mode='HTML')

# ===== ФУНКЦИЯ ДЛЯ ОТПРАВКИ УВЕДОМЛЕНИЙ =====

def send_notification(message_text):
    """Отправить уведомление в Telegram"""
    try:
        # Добавляем временную метку
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
    print("TELEGRAM BOT v2.0 - PDF PROCESSOR")
    print("="*50)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Бот запущен и ожидает команды...")
    print("\nДля остановки нажмите Ctrl+C")
    print("="*50)
    
    # Отправка уведомления о запуске
    send_notification(
        "🚀 <b>Бот PDF Processor v2.0 запущен!</b>\n\n"
        "Готов к обработке счетов.\n"
        "Используйте /start для начала работы"
    )
    
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n\nБот остановлен пользователем")
        send_notification("⛔ Бот остановлен")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        send_notification(f"❌ Критическая ошибка бота:\n{e}")