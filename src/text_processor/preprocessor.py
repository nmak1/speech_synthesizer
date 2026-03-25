# src/text_processor/preprocessor.py
"""
Модуль для предобработки текста перед синтезом
"""
import re
import unicodedata
from typing import List, Tuple
import pyphen

from src.utils.logger import get_logger


class TextPreprocessor:
    """Класс для предобработки текста"""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        # Инициализация pyphen для расстановки переносов
        self.dic = pyphen.Pyphen(lang='ru_RU')

        # Регулярные выражения для обработки
        self.number_pattern = re.compile(r'\d+')
        self.email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.abbreviation_pattern = re.compile(r'\b[А-Я]{2,5}\b')

    def preprocess(self, text: str) -> str:
        """Основная функция предобработки текста"""
        # Нормализация текста
        text = self.normalize_text(text)

        # Обработка специальных символов
        text = self.process_special_symbols(text)

        # Обработка чисел
        text = self.process_numbers(text)

        # Обработка сокращений
        text = self.process_abbreviations(text)

        # Расстановка ударений (опционально)
        text = self.process_stress(text)

        return text

    def normalize_text(self, text: str) -> str:
        """Нормализация текста"""
        # Приведение к нижнему регистру для обработки
        # Но сохраняем заглавные буквы для имен собственных

        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)

        # Нормализация кавычек
        text = text.replace('«', '"').replace('»', '"')
        text = text.replace('“', '"').replace('”', '"')

        return text.strip()

    def process_special_symbols(self, text: str) -> str:
        """Обработка специальных символов"""
        # Замена символов на слова
        replacements = {
            '№': 'номер',
            '%': 'процентов',
            '&': 'и',
            '+': 'плюс',
            '=': 'равно',
            '@': 'собака',
            '#': 'номер',
            '*': 'звездочка',
            '/': 'слэш',
            '\\': 'обратный слэш',
            '~': 'тильда',
            '^': 'степень',
            '°': 'градусов',
            '±': 'плюс-минус',
            '∞': 'бесконечность',
            '€': 'евро',
            '$': 'доллар',
            '£': 'фунт',
            '¥': 'иена',
        }

        for symbol, word in replacements.items():
            text = text.replace(symbol, f' {word} ')

        return text

    def process_numbers(self, text: str) -> str:
        """Обработка чисел"""

        def replace_number(match):
            num = match.group()
            # Простое преобразование чисел в слова
            # В реальном проекте здесь нужна более сложная логика
            return self.number_to_words(num)

        return self.number_pattern.sub(replace_number, text)

    def number_to_words(self, num_str: str) -> str:
        """Преобразование числа в слова"""
        # Упрощенная версия
        num = int(num_str)

        if 1 <= num <= 4:
            words = ['один', 'два', 'три', 'четыре']
            return words[num - 1]
        elif 5 <= num <= 20:
            words = ['пять', 'шесть', 'семь', 'восемь', 'девять', 'десять',
                     'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
                     'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать',
                     'девятнадцать', 'двадцать']
            return words[num - 5]
        else:
            return num_str

    def process_abbreviations(self, text: str) -> str:
        """Обработка сокращений"""
        abbreviations = {
            'т.е.': 'то есть',
            'т.д.': 'так далее',
            'т.п.': 'тому подобное',
            'и.т.д.': 'и так далее',
            'и.т.п.': 'и тому подобное',
            'т.к.': 'так как',
            'т.н.': 'так называемый',
            'пр.': 'прочее',
            'см.': 'смотри',
            'г.': 'год',
            'гг.': 'годы',
            'стр.': 'страница',
            'рис.': 'рисунок',
            'табл.': 'таблица',
            'ул.': 'улица',
            'пл.': 'площадь',
            'пр-т': 'проспект',
            'пер.': 'переулок',
            'д.': 'дом',
            'кв.': 'квартира',
            'оф.': 'офис',
        }

        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)

        return text

    def process_stress(self, text: str) -> str:
        """Расстановка ударений"""
        # Здесь можно использовать словарь с ударениями
        # Для упрощения возвращаем текст без изменений
        return text

    def split_into_sentences(self, text: str) -> List[str]:
        """Разбивка текста на предложения"""
        # Разбиваем по знакам препинания
        sentences = re.split(r'[.!?…]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def process_pauses(self, text: str) -> List[Tuple[str, float]]:
        """Обработка пауз в тексте"""
        sentences = self.split_into_sentences(text)
        result = []

        for i, sentence in enumerate(sentences):
            result.append((sentence, self.config.default_pause_duration))

        return result