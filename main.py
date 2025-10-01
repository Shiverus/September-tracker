from data.categories import CAT
from data.config import API_ID, API_HASH, CHANNEL_ID
import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Set, Any
from telethon import TelegramClient
from telethon.tl.types import Channel
import sys
import os

# Добавляем путь к config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
CONFIG = {
    'input_file': '../september/data/messages.json',
    'output_files': {
        'raw_data': '../september/data/budget.xlsx',
        'daily': '../september/data/daily_spendings.xlsx',
        'categorized': '../september/data/category_spendings.xlsx',
        'weekday': '../september/data/weekday_spendings.xlsx',
        'uncategorized': '../september/data/not_used_categories.txt'
    },
    'categories': CAT,
    'holidays': ['01.09.2025', 'any_holidays'],
    'telegram': {
        'days_back': 31
    }
}


class PrivateChannelExporter:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = None

    async def initialize(self):
        """Инициализация клиента"""
        self.client = TelegramClient(
            'private_session', self.api_id, self.api_hash)
        await self.client.start()

    async def get_private_channel(self, channel_identifier):
        """Получение объекта приватного канала"""
        try:
            if isinstance(channel_identifier, int):
                channel = await self.client.get_entity(channel_identifier)
            elif isinstance(channel_identifier, str):
                channel = await self.client.get_entity(channel_identifier)
            else:
                print("❌ Неверный идентификатор канала")
                return None

            if isinstance(channel, Channel):
                return channel
            else:
                print("❌ Указанный объект не является каналом")
                return None

        except ValueError as e:
            print(f"❌ Канал не найден: {e}")
            print("🔍 Попробуйте найти ID канала через бота @username_to_id_bot")
            return None
        except Exception as e:
            print(f"❌ Ошибка доступа: {e}")
            return None

    async def export_private_messages(self, channel_identifier, days_back=30):
        """Экспорт сообщений из приватного канала"""
        if not self.client:
            await self.initialize()

        channel = await self.get_private_channel(channel_identifier)
        if not channel:
            return None

        try:
            full_channel = await self.client.get_entity(channel_identifier)
            participant = await self.client.get_participants(channel, limit=1)
        except Exception as e:
            print(f"❌ Нет доступа к каналу: {e}")
            print("📝 Убедитесь, что вы администратор/участник канала")
            return None

        since_date = datetime.now() - timedelta(days=days_back)

        messages_data = []

        try:
            async for message in self.client.iter_messages(
                channel,
                offset_date=since_date,
                reverse=True
            ):
                if message:
                    msg_data = {
                        'id': message.id,
                        'date': message.date.isoformat(),
                        'text': message.text or '',
                        'views': getattr(message, 'views', 0)
                    }
                    messages_data.append(msg_data)

                    if len(messages_data) % 20 == 0:
                        print(f"Обработано {len(messages_data)} сообщений...")

        except Exception as e:
            print(f"❌ Ошибка при сборе сообщений: {e}")
            return None

        return messages_data

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()


async def fetch_telegram_data():
    """Получение данных из Telegram"""
    exporter = PrivateChannelExporter(API_ID, API_HASH)

    try:
        await exporter.initialize()
        messages = await exporter.export_private_messages(CHANNEL_ID, CONFIG['telegram']['days_back'])

        if messages:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(CONFIG['input_file']), exist_ok=True)

            # Сохраняем результат
            with open(CONFIG['input_file'], 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            return True
        else:
            print("❌ Не удалось получить сообщения из Telegram")
            return False

    except Exception as e:
        print(f"❌ Ошибка при работе с Telegram: {e}")
        return False
    finally:
        await exporter.disconnect()


def load_and_parse_json(filepath: str) -> List[Dict[str, Any]]:
    """Загрузка и парсинг JSON файла"""

    try:
        with open(filepath, "r", encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        logger.error(f"Файл {filepath} не найден")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise

    return data


def extract_transactions_from_json(messages: List[Dict[str, Any]]) -> pd.DataFrame:
    """Извлечение транзакций из JSON данных"""

    dates, names, amounts = [], [], []

    for message in messages:
        if not message.get('text') or not message['text'].strip():
            continue

        text = message['text'].strip()
        parts = text.split()
        if len(parts) < 2:
            logger.warning(f"Неверный формат сообщения: '{text}'")
            continue

        try:
            amount_str = parts[-1]
            name = ' '.join(parts[:-1])
            amount = int(amount_str)

            date_iso = message['date']
            date_obj = datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
            date_str = date_obj.strftime('%d.%m.%Y')

            dates.append(date_str)
            names.append(name)
            amounts.append(amount)

        except ValueError as e:
            logger.warning(f"Неверный формат суммы в сообщении '{text}': {e}")
            continue
        except Exception as e:
            logger.warning(f"Ошибка обработки сообщения '{text}': {e}")
            continue

    df = pd.DataFrame({
        'Дата': dates,
        'Категория': names,
        'Сумма': amounts
    })

    logger.info(f"Создан DataFrame с {len(df)} транзакциями")
    return df


def validate_data(df: pd.DataFrame) -> bool:
    """Валидация данных"""

    if df.empty:
        raise ValueError("DataFrame пустой - нет транзакций для анализа")

    negative_sums = df[df['Сумма'] < 0]
    if not negative_sums.empty:
        logger.warning(
            f"Найдены отрицательные суммы: {len(negative_sums)} записей")

    invalid_dates = []
    for date_str in df['Дата'].unique():
        if safe_date_parse(date_str) is None:
            invalid_dates.append(date_str)

    if invalid_dates:
        logger.warning(f"Найдены некорректные даты: {invalid_dates}")

    return True


def safe_date_parse(date_str: str) -> datetime:
    """Безопасный парсинг даты"""
    try:
        return datetime.strptime(date_str, '%d.%m.%Y')
    except ValueError:
        logger.warning(f"Ошибка парсинга даты: {date_str}")
        return None


def calculate_daily_spendings(df: pd.DataFrame) -> pd.DataFrame:
    """Агрегация расходов по дням"""

    daily = df.groupby('Дата')['Сумма'].sum().reset_index()
    total_row = pd.DataFrame(
        {'Дата': ['Общая сумма'], 'Сумма': [df['Сумма'].sum()]})
    result = pd.concat([total_row, daily], ignore_index=True)

    return result


def categorize_spendings(df: pd.DataFrame, categories: Dict[str, List[str]]) -> Tuple[pd.DataFrame, Set[str]]:
    """Категоризация расходов"""

    category_mapping = {}
    for category, keywords in categories.items():
        for keyword in keywords:
            category_mapping[keyword] = category

    uncategorized = set(df['Категория']) - set(category_mapping.keys())

    if uncategorized:
        uncategorized_file = CONFIG['output_files']['uncategorized']
        with open(uncategorized_file, "w", encoding='utf-8') as f:
            f.write('\n'.join(sorted(uncategorized)))
        logger.info(
            f"Найдены некategorризированные категории: {len(uncategorized)}. Сохранены в {uncategorized_file}")

    df['Основная_категория'] = df['Категория'].map(
        category_mapping).fillna('Неизвестно')
    categorized = df.groupby('Основная_категория')['Сумма'].sum().reset_index()

    return categorized, uncategorized


def analyze_weekdays(daily_df: pd.DataFrame, holidays: List[str]) -> pd.DataFrame:
    """Анализ расходов по дням недели"""

    daily_data = daily_df[daily_df['Дата'] != 'Общая сумма']

    workdays_sum = 0
    weekends_sum = 0
    workdays_count = 0
    weekends_count = 0

    for _, row in daily_data.iterrows():
        date_str = row['Дата']
        amount = row['Сумма']

        if is_weekend(date_str, holidays):
            weekends_sum += amount
            weekends_count += 1
        else:
            workdays_sum += amount
            workdays_count += 1

    workdays_avg = workdays_sum / workdays_count if workdays_count > 0 else 0
    weekends_avg = weekends_sum / weekends_count if weekends_count > 0 else 0

    result_df = pd.DataFrame({
        'День': ['Будние', 'Выходные', 'Среднее за будни', 'Среднее за выходные'],
        'Сумма': [workdays_sum, weekends_sum, workdays_avg, weekends_avg]
    })

    return result_df


def is_weekend(date_str: str, holidays: List[str]) -> bool:
    """Проверка, является ли день выходным или праздником"""
    date_obj = safe_date_parse(date_str)
    if date_obj is None:
        return False

    return date_obj.weekday() >= 5 or date_str in holidays


def export_results(*dataframes: pd.DataFrame) -> None:
    """Экспорт всех DataFrame в Excel файлы"""

    output_files = [
        CONFIG['output_files']['raw_data'],
        CONFIG['output_files']['daily'],
        CONFIG['output_files']['categorized'],
        CONFIG['output_files']['weekday']
    ]

    for df, filename in zip(dataframes, output_files):
        try:
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_excel(filename, index=False)
        except Exception as e:
            logger.error(f"Ошибка при сохранении {filename}: {e}")
            raise


def generate_report(df: pd.DataFrame, categorized_df: pd.DataFrame, weekday_df: pd.DataFrame) -> None:
    """Генерация итогового отчета"""

    total_sum = df['Сумма'].sum()
    total_average = total_sum / len(df['Дата'].unique())

    top_categories = categorized_df.nlargest(
        3, 'Сумма')[['Основная_категория', 'Сумма']].values

    print(' ')
    print(' ')
    print(' ')
    print('\n' + "="*50)
    print("ИТОГОВЫЙ ОТЧЕТ ПО РАСХОДАМ")
    print("="*50)
    print(f"Расходы в этом месяце: {total_sum:,} руб.".replace(",", " "))
    print(
        f"Средний расход в день: {int(total_average):,} руб.".replace(",", " "))
    print(f"Всего дней с расходами: {len(df['Дата'].unique())}")
    print(f"Всего транзакций: {len(df)}")

    print(f"\nТоп-3 категорий расходов:")
    for i, (category, amount) in enumerate(top_categories, 1):
        print(f"  {i}. {category}: {amount:,} руб.".replace(",", " "))

    workdays_avg = weekday_df[weekday_df['День']
                              == 'Среднее за будни']['Сумма'].values[0]
    weekends_avg = weekday_df[weekday_df['День'] ==
                              'Среднее за выходные']['Сумма'].values[0]

    print(f"\nСравнение расходов:")
    print(
        f"  Средний расход в будни: {int(workdays_avg):,} руб.".replace(",", " "))
    print(
        f"  Средний расход в выходные: {int(weekends_avg):,} руб.".replace(",", " "))

    difference = weekends_avg - workdays_avg
    if difference > 0:
        print(
            f"  В выходные тратите на {int(difference):,} руб. больше".replace(",", " "))
    else:
        print(
            f"  В будни тратите на {abs(int(difference)):,} руб. больше".replace(",", " "))

    print("="*50)
    print(' ')
    print(' ')


def analyze_financial_data():
    """Анализ финансовых данных"""

    try:
        # Загрузка и парсинг JSON данных
        messages = load_and_parse_json(CONFIG['input_file'])
        df = extract_transactions_from_json(messages)

        # Валидация данных
        validate_data(df)

        # Расчет различных анализов
        daily_df = calculate_daily_spendings(df)
        categorized_df, uncategorized = categorize_spendings(
            df, CONFIG['categories'])
        weekday_df = analyze_weekdays(daily_df, CONFIG['holidays'])

        # Экспорт результатов
        export_results(df, daily_df, categorized_df, weekday_df)

        # Генерация отчета
        generate_report(df, categorized_df, weekday_df)

        return True

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при анализе данных: {e}")
        return False


async def main():
    """Основная функция"""

    # Шаг 1: Получение данных из Telegram
    telegram_success = await fetch_telegram_data()
    if not telegram_success:
        print("❌ Не удалось получить данные из Telegram. Завершение работы.")
        return

    # Шаг 2: Анализ финансовых данных
    analysis_success = analyze_financial_data()

    if telegram_success and analysis_success:
        pass
    else:
        print("\n⚠️ Процесс завершен с ошибками")

if __name__ == "__main__":
    # Запуск асинхронной главной функции
    asyncio.run(main())
