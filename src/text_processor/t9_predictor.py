# src/text_processor/t9_predictor.py
import os
import json
import re
from collections import defaultdict
from typing import List, Dict, Set
import pickle

from src.utils.logger import get_logger


class T9Predictor:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.word_frequency: Dict[str, int] = defaultdict(int)
        self.word_prefixes: Dict[str, Set[str]] = defaultdict(set)

        self.dictionary_path = os.path.join(config.dictionaries_dir, "t9_dictionary.json")

        # Создаем папку если её нет
        os.makedirs(config.dictionaries_dir, exist_ok=True)

        self.load_dictionary()

    def load_dictionary(self):
        """Загрузка словаря из файла"""
        try:
            if os.path.exists(self.dictionary_path):
                with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.word_frequency = defaultdict(int, data.get('frequencies', {}))
                    self.logger.info(f"Загружено {len(self.word_frequency)} слов из словаря")
            else:
                self.logger.info("Словарь не найден, создаем новый...")
                self._create_default_dictionary()

            self._update_prefix_index()

        except Exception as e:
            self.logger.error(f"Ошибка загрузки словаря: {e}")
            self._create_default_dictionary()

    def _create_default_dictionary(self):
        """Создание расширенного словаря по умолчанию"""
        # Базовые слова
        default_words = [
            # Местоимения
            "я", "ты", "он", "она", "оно", "мы", "вы", "они",
            "меня", "тебя", "его", "её", "нас", "вас", "их",
            "мне", "тебе", "ему", "ей", "нам", "вам", "им",
            "мой", "твой", "его", "её", "наш", "ваш", "их",

            # Глаголы
            "быть", "стать", "иметь", "делать", "сказать", "пойти",
            "идти", "ехать", "лететь", "бежать", "плыть", "сидеть",
            "стоять", "лежать", "работать", "учиться", "читать", "писать",
            "говорить", "слышать", "видеть", "смотреть", "слушать",
            "думать", "понимать", "знать", "помнить", "любить",

            # Прилагательные
            "хороший", "плохой", "большой", "маленький", "новый", "старый",
            "красивый", "умный", "добрый", "злой", "веселый", "грустный",
            "теплый", "холодный", "светлый", "темный", "быстрый", "медленный",

            # Существительные
            "работа", "дом", "машина", "город", "улица", "время",
            "день", "ночь", "утро", "вечер", "год", "месяц", "неделя",
            "человек", "друг", "семья", "ребенок", "родитель", "учитель",
            "компьютер", "телефон", "программа", "интернет", "сайт",

            # Наречия и служебные слова
            "сегодня", "завтра", "вчера", "сейчас", "потом", "всегда",
            "никогда", "иногда", "часто", "редко", "быстро", "медленно",
            "хорошо", "плохо", "красиво", "громко", "тихо",

            # Вопросительные слова
            "кто", "что", "где", "когда", "почему", "зачем", "как",
            "какой", "которая", "который", "которое", "которые",

            # Союзы и предлоги
            "и", "а", "но", "да", "или", "либо", "то", "чтобы",
            "потому", "также", "зато", "однако", "в", "на", "с", "к",
            "у", "за", "под", "над", "о", "об", "при", "без", "до",

            # Вводные слова
            "здравствуйте", "спасибо", "пожалуйста", "извините", "до свидания",
            "привет", "пока", "да", "нет", "может", "нужно", "можно", "нельзя",
            "конечно", "возможно", "наверное", "вероятно", "кажется",
        ]

        # Добавляем слова с частотой
        for i, word in enumerate(default_words):
            self.word_frequency[word] = 100 - i  # Более частые слова имеют больший вес

        # Сохраняем словарь
        self.save_dictionary()
        self.logger.info(f"Создан словарь из {len(self.word_frequency)} слов")

    def _update_prefix_index(self):
        """Обновление префиксного индекса"""
        self.word_prefixes.clear()

        for word in self.word_frequency.keys():
            for i in range(1, len(word) + 1):
                prefix = word[:i]
                self.word_prefixes[prefix].add(word)

        self.logger.info(f"Индекс префиксов обновлен")

    def save_dictionary(self):
        """Сохранение словаря в файл"""
        try:
            # Создаем папку если её нет
            os.makedirs(os.path.dirname(self.dictionary_path), exist_ok=True)

            data = {
                'frequencies': dict(self.word_frequency)
            }
            with open(self.dictionary_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Словарь сохранен: {self.dictionary_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения словаря: {e}")
            return False

    def predict(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """Предсказание слов по префиксу.

        Точное совпадение (сам префикс как слово) исключается из выдачи —
        предсказание должно предлагать продолжения слова, а не повторять
        уже набранное.
        """
        if not prefix or len(prefix) < 1:
            return []

        prefix_lower = prefix.lower()

        # Поиск слов с данным префиксом
        if prefix_lower in self.word_prefixes:
            candidates = {w for w in self.word_prefixes[prefix_lower] if w != prefix_lower}

            # Сортировка по частоте использования, затем по алфавиту.
            sorted_candidates = sorted(
                candidates,
                key=lambda w: (-self.word_frequency.get(w, 0), w)
            )

            # Возвращаем уникальные результаты
            return sorted_candidates[:max_suggestions]
        else:
            return []

    def add_word(self, word: str):
        """Добавление нового слова в словарь"""
        word_lower = word.lower()
        self.word_frequency[word_lower] += 1

        # Обновляем префиксный индекс
        for i in range(1, len(word_lower) + 1):
            prefix = word_lower[:i]
            self.word_prefixes[prefix].add(word_lower)

        self.save_dictionary()

    def update_frequency(self, word: str):
        """Обновление частоты использования слова (инкремент +1)."""
        word_lower = word.lower().strip()
        if not word_lower:
            return
        if word_lower in self.word_frequency:
            self.word_frequency[word_lower] += 1
        else:
            self.word_frequency[word_lower] = 1
            # Инкрементальное обновление индекса вместо полной перестройки
            for i in range(1, len(word_lower) + 1):
                self.word_prefixes[word_lower[:i]].add(word_lower)

        self.save_dictionary()

    # ---------- Динамическое обучение ----------

    _WORD_SPLIT_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
    _LEARN_MIN_LEN = 2       # однобуквенные не учим (шум от опечаток)
    _LEARN_MAX_LEN = 30

    def learn_from_text(self, text: str):
        """Динамическое обучение словаря по набранному тексту.

        Каждое слово из текста увеличивает частоту на 1. Вызывается
        пакетно (см. TextEditor/T9Predictor.should_learn), чтобы не писать
        на диск при каждом нажатии клавиши.
        """
        if not text:
            return
        words = self._WORD_SPLIT_RE.findall(text.lower())
        changed = False
        for w in words:
            if not (self._LEARN_MIN_LEN <= len(w) <= self._LEARN_MAX_LEN):
                continue
            self.word_frequency[w] += 1
            for i in range(1, len(w) + 1):
                self.word_prefixes[w[:i]].add(w)
            changed = True
        if changed:
            self.save_dictionary()

    def learn_word(self, word: str):
        """Обучение на одном слове (используется при выборе подсказки T9)."""
        w = (word or "").lower().strip()
        if self._LEARN_MIN_LEN <= len(w) <= self._LEARN_MAX_LEN:
            self.update_frequency(w)

    def get_word_frequency(self, word: str) -> int:
        return self.word_frequency.get(word.lower(), 0)