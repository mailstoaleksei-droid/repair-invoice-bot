import telebot
from telebot import types
import os
import sys

# ВАЖНО: Замените на ваш токен от @BotFather
TELEGRAM_BOT_TOKEN = 8127115250:AAHmDuiiRuPSpE6oSwHzmUpSl2-DzVSr3Io
# ВАЖНО: Замените на ваш Telegram ID (можно узнать у @userinfobot)
TELEGRAM_CHAT_ID = 745125435

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Путь к скрипту обработки
SCRIPT_PATH = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\PDF_Processor\process_improved.py"

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_process = types.KeyboardButton('🔄 Обработать PDF')
    btn_status = types.KeyboardButton('📊 Статус')
    markup.add(btn_process, btn_status)
    
    bot.reply_to(message, 
                 "Привет! Я бот для обработки PDF счетов.\n\n"
                 "Доступные команды:\n"
                 "🔄 Обработать PDF - запустить обработку файлов\n"
                 "📊 Статус - показать статистику",
                 reply_markup=markup)

# Обработка кнопок
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == '🔄 Обработать PDF':
        bot.reply_to(message, "⏳ Начинаю обработку PDF файлов...")
        
        try:
            # Запустить скрипт обработки
            import subprocess
            result = subprocess.run(['python', SCRIPT_PATH], 
                                   capture_output=True, 
                                   text=True,
                                   encoding='utf-8')
            
            # Парсим результаты из вывода
            output = result.stdout
            
            # Отправить результаты
            bot.send_message(message.chat.id, 
                           f"✅ Обработка завершена!\n\n"
                           f"Результаты:\n{output[-500:]}")  # Последние 500 символов
            
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при обработке: {e}")
    
    elif message.text == '📊 Статус':
        PDF_FOLDER = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
        
        pdf_count = len([f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')])
        
        bot.reply_to(message, 
                    f"📊 Текущий статус:\n\n"
                    f"📁 Файлов в очереди: {pdf_count}\n"
                    f"📂 Папка: EingangsRG")

# Функция для отправки уведомления
def send_notification(message_text):
    """Отправить уведомление в Telegram"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message_text, parse_mode='HTML')
        return True
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()