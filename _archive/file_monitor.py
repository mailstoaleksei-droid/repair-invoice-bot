"""
FILE MONITOR MODULE
Автоматическое отслеживание папки EingangsRG для обнаружения новых PDF файлов
Версия: 1.0
"""

import os
import time
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFFileHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы для PDF файлов
    """
    
    def __init__(self, callback_function, debounce_time=5):
        """
        Инициализация обработчика
        
        Args:
            callback_function: Функция для вызова при обнаружении нового файла
            debounce_time: Время ожидания после создания файла (секунды)
        """
        super().__init__()
        self.callback = callback_function
        self.debounce_time = debounce_time
        self.pending_files = {}  # filename: timestamp
        self.processed_files = set()  # Уже обработанные файлы
        
        # Запустить фоновый поток для debounce
        self.debounce_thread = threading.Thread(target=self._process_pending_files, daemon=True)
        self.debounce_thread.start()
        
    def on_created(self, event):
        """
        Вызывается при создании нового файла
        """
        if event.is_directory:
            return
            
        file_path = event.src_path
        filename = os.path.basename(file_path)
        
        # Проверить что это PDF
        if not filename.lower().endswith('.pdf'):
            return
            
        # Игнорировать временные файлы
        if filename.startswith('~') or filename.startswith('.'):
            return
            
        logger.info(f"Обнаружен новый файл: {filename}")
        
        # Добавить в очередь pending с временной меткой
        self.pending_files[file_path] = time.time()
    
    def _process_pending_files(self):
        """
        Фоновый процесс для обработки pending файлов с debounce
        """
        while True:
            try:
                current_time = time.time()
                files_to_process = []
                
                # Найти файлы, которые готовы к обработке
                for file_path, timestamp in list(self.pending_files.items()):
                    if current_time - timestamp >= self.debounce_time:
                        files_to_process.append(file_path)
                
                # Обработать готовые файлы
                for file_path in files_to_process:
                    if file_path not in self.processed_files:
                        # Проверить что файл действительно существует и доступен
                        if os.path.exists(file_path) and self._is_file_ready(file_path):
                            filename = os.path.basename(file_path)
                            file_size = os.path.getsize(file_path)
                            
                            logger.info(f"Обработка файла: {filename} ({file_size} bytes)")
                            
                            # Вызвать callback
                            try:
                                self.callback(file_path, filename, file_size)
                                self.processed_files.add(file_path)
                            except Exception as e:
                                logger.error(f"Ошибка в callback для {filename}: {e}")
                        
                        # Удалить из pending
                        del self.pending_files[file_path]
                
                # Спать 1 секунду
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в _process_pending_files: {e}")
                time.sleep(5)
    
    def _is_file_ready(self, file_path, timeout=10):
        """
        Проверить что файл полностью записан и доступен для чтения
        
        Args:
            file_path: Путь к файлу
            timeout: Максимальное время ожидания (секунды)
            
        Returns:
            bool: True если файл готов
        """
        start_time = time.time()
        last_size = -1
        
        while time.time() - start_time < timeout:
            try:
                # Попробовать открыть файл
                with open(file_path, 'rb') as f:
                    current_size = os.path.getsize(file_path)
                    
                    # Если размер не изменился за последнюю секунду - файл готов
                    if current_size == last_size:
                        return True
                    
                    last_size = current_size
                    time.sleep(1)
                    
            except (IOError, OSError):
                # Файл еще записывается
                time.sleep(1)
                continue
        
        # Таймаут - вернуть False
        logger.warning(f"Таймаут ожидания готовности файла: {file_path}")
        return False


class FileMonitor:
    """
    Менеджер мониторинга файлов
    """
    
    def __init__(self, folder_path, notification_callback):
        """
        Инициализация монитора
        
        Args:
            folder_path: Путь к папке для мониторинга
            notification_callback: Функция для отправки уведомлений
                Сигнатура: callback(file_path, filename, file_size)
        """
        self.folder_path = folder_path
        self.notification_callback = notification_callback
        self.observer = None
        self.is_running = False
        self.start_time = None
        self.files_detected = 0
        
        # Проверить что папка существует
        if not os.path.exists(folder_path):
            raise ValueError(f"Папка не существует: {folder_path}")
        
        logger.info(f"FileMonitor инициализирован для папки: {folder_path}")
    
    def start(self):
        """
        Запустить мониторинг
        """
        if self.is_running:
            logger.warning("Мониторинг уже запущен")
            return False
        
        try:
            # Создать обработчик событий
            event_handler = PDFFileHandler(
                callback_function=self._on_file_detected,
                debounce_time=5
            )
            
            # Создать observer
            self.observer = Observer()
            self.observer.schedule(event_handler, self.folder_path, recursive=False)
            
            # Запустить
            self.observer.start()
            self.is_running = True
            self.start_time = datetime.now()
            self.files_detected = 0
            
            logger.info(f"✅ Мониторинг запущен: {self.folder_path}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска мониторинга: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """
        Остановить мониторинг
        """
        if not self.is_running:
            logger.warning("Мониторинг не запущен")
            return False
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.is_running = False
            
            logger.info(f"⛔ Мониторинг остановлен")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка остановки мониторинга: {e}")
            return False
    
    def get_status(self):
        """
        Получить текущий статус мониторинга
        
        Returns:
            dict: Словарь со статусом
        """
        status = {
            'is_running': self.is_running,
            'folder_path': self.folder_path,
            'files_detected': self.files_detected,
            'start_time': self.start_time.strftime('%d.%m.%Y %H:%M:%S') if self.start_time else None,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
        return status
    
    def _on_file_detected(self, file_path, filename, file_size):
        """
        Внутренний обработчик обнаружения нового файла
        
        Args:
            file_path: Полный путь к файлу
            filename: Имя файла
            file_size: Размер файла в байтах
        """
        self.files_detected += 1
        
        logger.info(f"📥 Новый файл #{self.files_detected}: {filename} ({file_size} bytes)")
        
        # Вызвать callback для уведомления
        try:
            self.notification_callback(file_path, filename, file_size)
        except Exception as e:
            logger.error(f"Ошибка в notification_callback: {e}")
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.stop()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def format_file_size(size_bytes):
    """
    Отформатировать размер файла в человекочитаемый вид
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Отформатированный размер (например, "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_info(file_path):
    """
    Получить информацию о файле
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        dict: Словарь с информацией о файле
    """
    try:
        stat = os.stat(file_path)
        
        return {
            'filename': os.path.basename(file_path),
            'size': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'path': file_path
        }
    except Exception as e:
        logger.error(f"Ошибка получения информации о файле {file_path}: {e}")
        return None


# ===== ТЕСТИРОВАНИЕ =====

if __name__ == "__main__":
    # Тест мониторинга
    def test_callback(file_path, filename, file_size):
        print(f"\n🎉 ОБНАРУЖЕН НОВЫЙ ФАЙЛ!")
        print(f"   Имя: {filename}")
        print(f"   Размер: {format_file_size(file_size)}")
        print(f"   Путь: {file_path}")
    
    # Путь для теста (замените на реальный)
    test_folder = r"C:\Users\Aleksei Samosvat\Groo GmbH\Intranet - Groo GmbH - Dokumente\Auto Compass GmbH\AC - Fahrzeuge\Ablage\Eingangs Rechnungen\EingangsRG"
    
    if os.path.exists(test_folder):
        print(f"🔍 Запуск мониторинга папки: {test_folder}")
        print("Добавьте PDF файл в папку для теста...")
        print("Нажмите Ctrl+C для остановки\n")
        
        try:
            with FileMonitor(test_folder, test_callback) as monitor:
                # Мониторинг будет работать пока не нажмут Ctrl+C
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n✅ Мониторинг остановлен")
    else:
        print(f"❌ Папка не найдена: {test_folder}")
