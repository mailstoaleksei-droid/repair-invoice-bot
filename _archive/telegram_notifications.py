"""
TELEGRAM NOTIFICATIONS MODULE
Унифицированная система уведомлений для PDF Processor
Версия: 1.0
"""

import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import threading


class NotificationThrottler:
    """
    Механизм throttling для предотвращения спама уведомлений
    """
    
    def __init__(self, min_interval: float = 2.0):
        """
        Инициализация throttler
        
        Args:
            min_interval: Минимальный интервал между сообщениями (секунды)
        """
        self.min_interval = min_interval
        self.last_send_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Подождать если нужно перед отправкой следующего сообщения"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_send_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            
            self.last_send_time = time.time()


class TelegramNotifier:
    """
    Класс для отправки уведомлений в Telegram
    """
    
    def __init__(self, bot, chat_id: str, throttle_interval: float = 2.0):
        """
        Инициализация notifier
        
        Args:
            bot: Экземпляр telebot
            chat_id: ID чата для отправки
            throttle_interval: Интервал throttling (секунды)
        """
        self.bot = bot
        self.chat_id = chat_id
        self.throttler = NotificationThrottler(throttle_interval)
        self.message_queue = []
        self.stats = {
            'sent': 0,
            'failed': 0,
            'throttled': 0
        }
    
    def send(self, message: str, parse_mode: str = 'HTML', disable_notification: bool = False) -> bool:
        """
        Отправить уведомление с throttling
        
        Args:
            message: Текст сообщения
            parse_mode: Режим парсинга (HTML/Markdown)
            disable_notification: Отключить звук уведомления
            
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # Throttling
            self.throttler.wait_if_needed()
            
            # Отправка
            self.bot.send_message(
                self.chat_id,
                message,
                parse_mode=parse_mode,
                disable_notification=disable_notification
            )
            
            self.stats['sent'] += 1
            return True
            
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
            self.stats['failed'] += 1
            return False
    
    def notify_processing_start(self, filename: str) -> bool:
        """
        Уведомление о начале обработки файла
        
        Args:
            filename: Имя файла
            
        Returns:
            bool: True если отправлено
        """
        message = (
            f"⏳ <b>Обработка начата</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
        )
        return self.send(message, disable_notification=True)
    
    def notify_success(self, data: Dict[str, Any], filename: str, excel_row: Optional[int] = None) -> bool:
        """
        Уведомление об успешной обработке
        
        Args:
            data: Извлеченные данные
            filename: Имя файла
            excel_row: Номер строки в Excel (опционально)
            
        Returns:
            bool: True если отправлено
        """
        message = (
            f"✅ <b>Обработан успешно!</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🏢 Поставщик: {data.get('seller', 'N/A')}\n"
            f"🔢 Счет: <b>{data.get('invoice', 'N/A')}</b>\n"
            f"📅 Дата: {data.get('date', 'N/A')}\n"
            f"💰 Сумма: {self._format_amount(data.get('total_price', data.get('amount', 0)))} EUR\n"
            f"🚛 Машина: {data.get('truck', 'N/A')}\n"
        )
        
        if excel_row:
            message += f"✅ Добавлен в Excel, строка {excel_row}\n"
        
        message += f"📂 Перемещен в: <code>processed/</code>"
        
        return self.send(message)
    
    def notify_duplicate(self, filename: str, invoice_number: str, existing_date: Optional[str] = None) -> bool:
        """
        Уведомление о дубликате
        
        Args:
            filename: Имя файла
            invoice_number: Номер счета
            existing_date: Дата существующего счета
            
        Returns:
            bool: True если отправлено
        """
        message = (
            f"⚠️ <b>ДУБЛИКАТ ОБНАРУЖЕН!</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🔢 Счет: <b>{invoice_number}</b> уже существует\n"
        )
        
        if existing_date:
            message += f"📅 Оригинал от: {existing_date}\n"
        
        message += f"\n📂 Перемещен в: <code>duplicate_{filename}</code>"
        
        return self.send(message)
    
    def notify_manual(self, filename: str, reason: str, supplier: Optional[str] = None) -> bool:
        """
        Уведомление о файле требующем ручной обработки
        
        Args:
            filename: Имя файла
            reason: Причина отправки в manual
            supplier: Определенный поставщик (опционально)
            
        Returns:
            bool: True если отправлено
        """
        # Определить emoji по причине
        reason_emoji = {
            'Не удалось извлечь': '❌',
            'PDF пустой': '📭',
            'Не удалось извлечь номер счета': '🔢',
            'Не удалось извлечь дату': '📅',
            'Не удалось извлечь сумму': '💰',
            'Не определен номер машины': '🚛',
            'Ошибка обработки': '⚠️',
        }
        
        emoji = '❌'
        for key, value in reason_emoji.items():
            if key in reason:
                emoji = value
                break
        
        message = (
            f"{emoji} <b>Требует ручной обработки</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"⚠️ Причина: {reason}\n"
        )
        
        if supplier:
            message += f"🏢 Поставщик: {supplier}\n"
        
        message += f"\n📂 Перемещен в: <code>manual/</code>\n"
        message += f"\n💡 Проверьте файл вручную и при необходимости обработайте"
        
        return self.send(message)
    
    def notify_error(self, filename: str, error_message: str) -> bool:
        """
        Уведомление об ошибке обработки
        
        Args:
            filename: Имя файла
            error_message: Сообщение об ошибке
            
        Returns:
            bool: True если отправлено
        """
        message = (
            f"🔴 <b>Ошибка обработки</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"⚠️ Ошибка: <code>{error_message[:200]}</code>\n"
            f"\n📂 Перемещен в: <code>manual/error_{filename}</code>"
        )
        
        return self.send(message)
    
    def notify_summary(self, summary: Dict[str, Any]) -> bool:
        """
        Отправить финальную сводку обработки
        
        Args:
            summary: Словарь со статистикой
            
        Returns:
            bool: True если отправлено
        """
        total = summary.get('total', 0)
        processed = summary.get('processed', 0)
        duplicates = summary.get('duplicates', 0)
        manual = summary.get('manual', 0)
        
        message = (
            f"📊 <b>ОБРАБОТКА ЗАВЕРШЕНА</b>\n\n"
            f"📄 Всего файлов: {total}\n"
            f"✅ Успешно: {processed}\n"
            f"⚠️ Дубликатов: {duplicates}\n"
            f"❌ Ручная обработка: {manual}\n\n"
        )
        
        # Процент автоматизации
        if total > 0:
            success_rate = (processed / total) * 100
            message += f"📈 Процент автоматизации: {success_rate:.1f}%\n\n"
            
            # Оценка результата
            if success_rate >= 90:
                message += "🎯 Отличный результат!"
            elif success_rate >= 70:
                message += "👍 Хороший результат"
            elif success_rate >= 50:
                message += "📊 Средний результат"
            else:
                message += "⚠️ Требуется оптимизация"
        
        # Детали по файлам
        if summary.get('processed_files'):
            message += f"\n\n✅ <b>Обработанные ({len(summary['processed_files'])}):</b>\n"
            for file in summary['processed_files'][:5]:  # Первые 5
                message += f"  • {file}\n"
            if len(summary['processed_files']) > 5:
                message += f"  ... и еще {len(summary['processed_files']) - 5}\n"
        
        if summary.get('duplicate_files'):
            message += f"\n⚠️ <b>Дубликаты ({len(summary['duplicate_files'])}):</b>\n"
            for file in summary['duplicate_files'][:5]:
                message += f"  • {file}\n"
            if len(summary['duplicate_files']) > 5:
                message += f"  ... и еще {len(summary['duplicate_files']) - 5}\n"
        
        if summary.get('manual_files'):
            message += f"\n❌ <b>Ручная обработка ({len(summary['manual_files'])}):</b>\n"
            for file in summary['manual_files'][:5]:
                message += f"  • {file}\n"
            if len(summary['manual_files']) > 5:
                message += f"  ... и еще {len(summary['manual_files']) - 5}\n"
        
        return self.send(message)
    
    def _format_amount(self, amount: float) -> str:
        """
        Форматировать сумму
        
        Args:
            amount: Сумма
            
        Returns:
            str: Отформатированная сумма
        """
        if amount == 0:
            return "0.00"
        return f"{amount:,.2f}".replace(',', ' ')
    
    def get_stats(self) -> Dict[str, int]:
        """
        Получить статистику отправки уведомлений
        
        Returns:
            dict: Статистика
        """
        return self.stats.copy()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def create_notifier(bot, chat_id: str) -> TelegramNotifier:
    """
    Создать экземпляр TelegramNotifier
    
    Args:
        bot: Экземпляр telebot
        chat_id: ID чата
        
    Returns:
        TelegramNotifier: Настроенный notifier
    """
    return TelegramNotifier(bot, chat_id, throttle_interval=2.0)


def format_file_list(files: List[str], max_files: int = 5) -> str:
    """
    Форматировать список файлов для отображения
    
    Args:
        files: Список имен файлов
        max_files: Максимум файлов для отображения
        
    Returns:
        str: Отформатированный список
    """
    result = ""
    for i, file in enumerate(files[:max_files], 1):
        result += f"{i}. {file}\n"
    
    if len(files) > max_files:
        result += f"... и еще {len(files) - max_files} файлов\n"
    
    return result


# ===== ТЕСТИРОВАНИЕ =====

if __name__ == "__main__":
    # Пример использования
    print("Модуль telegram_notifications.py")
    print("Для использования импортируйте в process_pdf_v2.py")
    
    # Пример создания notifier
    # from telegram_notifications import TelegramNotifier
    # notifier = TelegramNotifier(bot, CHAT_ID)
    # notifier.notify_success(data, filename)
