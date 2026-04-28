"""
UNIFIED TELEGRAM MODULE v1.0
Единый модуль для всех Telegram операций

Возможности:
- Отправка всех типов уведомлений
- Throttling (контроль частоты)
- Форматирование сообщений
- Обработка ошибок
- Статистика отправки

Использование:
    from unified_telegram import TelegramClient
    
    client = TelegramClient(bot_token, chat_id)
    client.notify_success(data, filename)
    client.notify_duplicate(filename, invoice)
    client.notify_summary(summary)
"""

import os
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List


# ===== THROTTLE MANAGER =====

class ThrottleManager:
    """
    Менеджер контроля частоты отправки сообщений
    Предотвращает блокировку бота Telegram
    """
    
    def __init__(self, min_interval: float = 2.0):
        """
        Args:
            min_interval: Минимальный интервал между сообщениями (секунды)
        """
        self.min_interval = min_interval
        self.last_send_time = 0
        self.lock = threading.Lock()
        self.stats = {
            'total_waits': 0,
            'total_wait_time': 0.0
        }
    
    def wait_if_needed(self):
        """Подождать если нужно перед отправкой следующего сообщения"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_send_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
                
                self.stats['total_waits'] += 1
                self.stats['total_wait_time'] += sleep_time
            
            self.last_send_time = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику throttling"""
        return self.stats.copy()


# ===== NOTIFICATION FORMATTER =====

class NotificationFormatter:
    """
    Форматирование уведомлений для Telegram
    Единообразный стиль для всех типов сообщений
    """
    
    @staticmethod
    def format_amount(amount: float) -> str:
        """Форматировать сумму"""
        if amount == 0:
            return "0.00"
        return f"{amount:,.2f}".replace(',', ' ')
    
    @staticmethod
    def format_file_list(files: List[str], max_files: int = 5) -> str:
        """Форматировать список файлов"""
        result = ""
        for file in files[:max_files]:
            result += f"  • {file}\n"
        
        if len(files) > max_files:
            result += f"  ... и еще {len(files) - max_files}\n"
        
        return result

    @staticmethod
    def humanize_reason_code(code: str) -> str:
        """Convert internal reason code to a human-friendly Russian label."""
        reason_labels = {
            'pdf_read_error': 'ne udalos prochitat PDF',
            'empty_pdf': 'PDF bez izvlekaemogo teksta',
            'unknown_supplier': 'ne opredelen prodavec ili postavshik',
            'extract_failed': 'ne udalos izvlech dannye iz scheta',
            'excel_write_error': 'ne udalos sokhranit dannye v Excel',
            'processing_error': 'oshibka obrabotki',
            'duplicate': 'dublikat v master Excel',
        }
        return reason_labels.get(code, code or 'drugaya prichina')

    @staticmethod
    def humanize_field_code(code: str) -> str:
        """Convert missing field code to a human-friendly Russian label."""
        field_labels = {
            'invoice': 'ne naiden nomer scheta',
            'date': 'ne naidena data',
            'truck': 'ne naiden nomer mashiny',
            'seller': 'ne naiden prodavec',
            'buyer': 'ne naiden pokupatel',
            'name': 'ne naideno nazvanie remontnykh rabot',
            'total_price': 'ne naidena NETTO summa',
        }
        return field_labels.get(code, code or 'drugoe pole')

    @staticmethod
    def format_breakdown(
        breakdown: Dict[str, int],
        humanize_func,
        max_items: int = 8,
    ) -> str:
        """Format a breakdown dictionary as a Telegram-friendly list."""
        if not breakdown:
            return ""

        lines = []
        items = sorted(breakdown.items(), key=lambda item: (-item[1], item[0]))
        for code, count in items[:max_items]:
            lines.append(f"• {humanize_func(code)}: {count}")

        remaining = len(items) - max_items
        if remaining > 0:
            lines.append(f"• eshche kategorii: {remaining}")

        return "\n".join(lines)
    
    @staticmethod
    def format_processing_start(filename: str) -> str:
        """Уведомление о начале обработки"""
        return (
            f"⏳ <b>Обработка начата</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    @staticmethod
    def format_success(data: Dict[str, Any], filename: str, excel_row: Optional[int] = None) -> str:
        """Уведомление об успешной обработке"""
        message = (
            f"✅ <b>Обработан успешно!</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🏢 Поставщик: {data.get('seller', 'N/A')}\n"
            f"🔢 Счет: <b>{data.get('invoice', 'N/A')}</b>\n"
            f"📅 Дата: {data.get('date', 'N/A')}\n"
            f"💰 Сумма: {NotificationFormatter.format_amount(data.get('total_price', data.get('amount', 0)))} EUR\n"
            f"🚛 Машина: {data.get('truck', 'N/A')}\n"
        )
        
        if excel_row:
            message += f"✅ Добавлен в Excel, строка {excel_row}\n"
        
        message += f"📂 Перемещен в: <code>processed/</code>"
        
        return message
    
    @staticmethod
    def format_duplicate(filename: str, invoice_number: str, existing_date: Optional[str] = None) -> str:
        """Уведомление о дубликате"""
        message = (
            f"⚠️ <b>ДУБЛИКАТ ОБНАРУЖЕН!</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"🔢 Счет: <b>{invoice_number}</b> уже существует\n"
        )
        
        if existing_date:
            message += f"📅 Оригинал от: {existing_date}\n"
        
        message += f"\n📂 Перемещен в: <code>duplicate_{filename}</code>"
        
        return message
    
    @staticmethod
    def format_manual(filename: str, reason: str, supplier: Optional[str] = None) -> str:
        """Уведомление о файле требующем ручной обработки"""
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
        
        return message
    
    @staticmethod
    def format_error(filename: str, error_message: str) -> str:
        """Уведомление об ошибке"""
        return (
            f"🔴 <b>Ошибка обработки</b>\n\n"
            f"📄 Файл: <code>{filename}</code>\n"
            f"⚠️ Ошибка: <code>{error_message[:200]}</code>\n"
            f"\n📂 Перемещен в: <code>manual/error_{filename}</code>"
        )
    
    @staticmethod
    def format_summary(summary: Dict[str, Any]) -> str:
        """Финальная сводка обработки"""
        total = summary.get('total', 0)
        processed = summary.get('processed', 0)
        processed_full = summary.get('processed_full', processed)
        partial = summary.get('partial', max(processed - processed_full, 0))
        duplicates = summary.get('duplicates', 0)
        manual = summary.get('manual', 0)
        ai_count = summary.get('ai', 0)
        reason_breakdown = summary.get('reason_breakdown', {})
        partial_breakdown = summary.get('partial_breakdown', {})
        report_path = summary.get('report_path')
        
        message = (
            f"📊 <b>ОБРАБОТКА ЗАВЕРШЕНА</b>\n\n"
            f"📄 Всего файлов: {total}\n"
            f"✅ Обработано: {processed}\n"
            f"🟡 Частично: {partial}\n"
            f"🟢 Полностью: {processed_full}\n"
            f"⚠️ Дубликатов: {duplicates}\n"
            f"🤖 AI помог: {ai_count}\n"
            f"❌ Не обработано: {manual}\n\n"
        )
        
        if total > 0:
            extracted_rate = (processed / total) * 100
            full_rate = (processed_full / total) * 100
            message += f"📈 Avtoizvlechenie: {extracted_rate:.1f}%\n"
            message += f"🎯 Polnostyu korrektno: {full_rate:.1f}%\n"

        if partial_breakdown:
            message += "\n\n🟡 <b>Chastichno obrabotano:</b>\n"
            message += NotificationFormatter.format_breakdown(
                partial_breakdown,
                NotificationFormatter.humanize_field_code,
            )

        if reason_breakdown:
            message += "\n\n❌ <b>Prichiny neudachnoi obrabotki:</b>\n"
            message += NotificationFormatter.format_breakdown(
                reason_breakdown,
                NotificationFormatter.humanize_reason_code,
            )

        if report_path:
            message += f"\n\n📁 Otchet: <code>{os.path.basename(report_path)}</code>"
        
        return message
    
    @staticmethod
    def format_processing_batch(file_count: int) -> str:
        """Уведомление о начале обработки пакета файлов"""
        return (
            f"⏳ <b>Начинаю обработку...</b>\n\n"
            f"📄 Файлов к обработке: {file_count}\n"
            f"⏰ Время начала: {datetime.now().strftime('%H:%M:%S')}\n"
            f"⏱️ Ожидайте результаты..."
        )
    
    @staticmethod
    def format_new_file(filename: str, size: int, timestamp: str) -> str:
        """Уведомление о новом файле (мониторинг)"""
        size_kb = size / 1024
        return (
            f"🆕 <b>Новый файл обнаружен!</b>\n\n"
            f"📄 Имя: <code>{filename}</code>\n"
            f"📊 Размер: {size_kb:.1f} KB\n"
            f"⏰ Время: {timestamp}"
        )


# ===== TELEGRAM CLIENT =====

class TelegramClient:
    """
    Единый клиент для всех Telegram операций
    
    Использование:
        client = TelegramClient(bot_token, chat_id)
        client.notify_success(data, filename)
    """
    
    def __init__(self, bot, chat_id: str, throttle_interval: float = 2.0):
        """
        Args:
            bot: Экземпляр telebot.TeleBot
            chat_id: ID чата для отправки
            throttle_interval: Интервал между сообщениями (секунды)
        """
        self.bot = bot
        self.chat_id = chat_id
        self.throttler = ThrottleManager(throttle_interval)
        self.formatter = NotificationFormatter()
        
        self.stats = {
            'sent': 0,
            'failed': 0,
            'by_type': {}
        }
    
    def send(self, message: str, parse_mode: str = 'HTML', disable_notification: bool = False) -> bool:
        """
        Базовая отправка сообщения с throttling
        
        Args:
            message: Текст сообщения
            parse_mode: Режим парсинга (HTML/Markdown)
            disable_notification: Отключить звук
            
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
            print(f"❌ Ошибка отправки: {e}")
            self.stats['failed'] += 1
            return False
    
    # ===== УВЕДОМЛЕНИЯ О ОБРАБОТКЕ =====
    
    def notify_processing_start(self, filename: str) -> bool:
        """Уведомление о начале обработки файла"""
        message = self.formatter.format_processing_start(filename)
        self._track_type('processing_start')
        return self.send(message, disable_notification=True)
    
    def notify_success(self, data: Dict[str, Any], filename: str, excel_row: Optional[int] = None) -> bool:
        """Уведомление об успешной обработке"""
        message = self.formatter.format_success(data, filename, excel_row)
        self._track_type('success')
        return self.send(message)
    
    def notify_duplicate(self, filename: str, invoice_number: str, existing_date: Optional[str] = None) -> bool:
        """Уведомление о дубликате"""
        message = self.formatter.format_duplicate(filename, invoice_number, existing_date)
        self._track_type('duplicate')
        return self.send(message)
    
    def notify_manual(self, filename: str, reason: str, supplier: Optional[str] = None) -> bool:
        """Уведомление о файле требующем ручной обработки"""
        message = self.formatter.format_manual(filename, reason, supplier)
        self._track_type('manual')
        return self.send(message)
    
    def notify_error(self, filename: str, error_message: str) -> bool:
        """Уведомление об ошибке"""
        message = self.formatter.format_error(filename, error_message)
        self._track_type('error')
        return self.send(message)
    
    def notify_summary(self, summary: Dict[str, Any]) -> bool:
        """Финальная сводка обработки"""
        message = self.formatter.format_summary(summary)
        self._track_type('summary')
        return self.send(message)
    
    def notify_processing_batch(self, file_count: int) -> bool:
        """Уведомление о начале обработки пакета"""
        message = self.formatter.format_processing_batch(file_count)
        self._track_type('batch_start')
        return self.send(message, disable_notification=True)
    
    # ===== УВЕДОМЛЕНИЯ О МОНИТОРИНГЕ =====
    
    def notify_new_file(self, filename: str, size: int, timestamp: str) -> bool:
        """Уведомление о новом файле (мониторинг)"""
        message = self.formatter.format_new_file(filename, size, timestamp)
        self._track_type('new_file')
        return self.send(message, disable_notification=True)
    
    # ===== СТАТИСТИКА =====
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику отправки
        
        Returns:
            dict: Статистика с детализацией по типам
        """
        return {
            'sent': self.stats['sent'],
            'failed': self.stats['failed'],
            'by_type': self.stats['by_type'].copy(),
            'throttle': self.throttler.get_stats()
        }
    
    def _track_type(self, msg_type: str):
        """Трекинг по типам сообщений"""
        if msg_type not in self.stats['by_type']:
            self.stats['by_type'][msg_type] = 0
        self.stats['by_type'][msg_type] += 1


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def create_client(bot_token: str, chat_id: str, throttle_interval: float = 2.0) -> TelegramClient:
    """
    Создать TelegramClient с инициализацией бота
    
    Args:
        bot_token: Токен Telegram бота
        chat_id: ID чата
        throttle_interval: Интервал между сообщениями
        
    Returns:
        TelegramClient: Настроенный клиент
        
    Example:
        client = create_client(TOKEN, CHAT_ID)
        client.notify_success(data, filename)
    """
    import telebot
    bot = telebot.TeleBot(bot_token)
    return TelegramClient(bot, chat_id, throttle_interval)


# ===== ПРИМЕР ИСПОЛЬЗОВАНИЯ =====

if __name__ == "__main__":
    print("="*60)
    print("UNIFIED TELEGRAM MODULE v1.0")
    print("="*60)
    print("\nДля использования импортируйте в ваш скрипт:")
    print("\n  from unified_telegram import TelegramClient")
    print("  client = TelegramClient(bot, CHAT_ID)")
    print("  client.notify_success(data, filename)")
    print("\nИли используйте create_client:")
    print("\n  from unified_telegram import create_client")
    print("  client = create_client(TOKEN, CHAT_ID)")
    print("="*60)
