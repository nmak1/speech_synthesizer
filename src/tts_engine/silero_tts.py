# src/tts_engine/silero_tts.py - полная версия с исправлениями
import torch
import numpy as np
import sounddevice as sd
import soundfile as sf
import os
import re
from typing import Optional, List
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from src.utils.logger import get_logger


class SileroTTS:
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sample_rate = config.sample_rate

        self.model = None
        self.current_voice = None
        self.available_voices = config.available_voices

        # Добавляем предварительную обработку текста
        self._init_text_processor()

        self.logger.info(f"Используется устройство: {self.device}")

        self._load_model()

    def _init_text_processor(self):
        """Инициализация обработки текста"""
        # Словарь для замены сокращений
        self.abbreviations = {
            'т.е.': 'то есть',
            'т.д.': 'так далее',
            'т.п.': 'тому подобное',
            'и т.д.': 'и так далее',
            'и т.п.': 'и тому подобное',
            'т.к.': 'так как',
            'т.н.': 'так называемый',
            'г.': 'год',
            'гг.': 'годы',
            'стр.': 'страница',
            'рис.': 'рисунок',
            'ул.': 'улица',
            'д.': 'дом',
            'кв.': 'квартира',
        }

        # Словарь для числительных (расширенный)
        self.numbers = {
            '0': 'ноль', '1': 'один', '2': 'два', '3': 'три', '4': 'четыре',
            '5': 'пять', '6': 'шесть', '7': 'семь', '8': 'восемь', '9': 'девять',
            '10': 'десять', '11': 'одиннадцать', '12': 'двенадцать', '13': 'тринадцать',
            '14': 'четырнадцать', '15': 'пятнадцать', '16': 'шестнадцать',
            '17': 'семнадцать', '18': 'восемнадцать', '19': 'девятнадцать',
            '20': 'двадцать', '30': 'тридцать', '40': 'сорок', '50': 'пятьдесят',
            '60': 'шестьдесят', '70': 'семьдесят', '80': 'восемьдесят', '90': 'девяносто',
            '100': 'сто', '200': 'двести', '300': 'триста', '400': 'четыреста',
            '500': 'пятьсот', '600': 'шестьсот', '700': 'семьсот', '800': 'восемьсот',
            '900': 'девятьсот', '1000': 'тысяча'
        }

        # Словарь для автокоррекции частых ошибок
        self.autocorrect = {
            'зравстуй': 'здравствуй',
            'зравствуй': 'здравствуй',
            'приветсвовать': 'приветствовать',
            'приветсвуй': 'приветствуй',
            'здраствуй': 'здравствуй',
            'здрасьте': 'здравствуйте',
            'пажалуйста': 'пожалуйста',
            'спасибо': 'спасибо',
            'извените': 'извините',
        }

    def _autocorrect_text(self, text: str) -> str:
        """Автокоррекция частых орфографических ошибок"""
        text_lower = text.lower()
        for wrong, correct in self.autocorrect.items():
            if wrong in text_lower:
                text = text.replace(wrong, correct)
                text = text.replace(wrong.capitalize(), correct.capitalize())
        return text

    def _number_to_words(self, num_str: str) -> str:
        """Преобразование числа в слова"""
        try:
            num = int(num_str)

            # Для чисел до 1000
            if num == 0:
                return "ноль"
            elif 1 <= num <= 20:
                return self.numbers[num_str]
            elif 21 <= num <= 99:
                tens = (num // 10) * 10
                units = num % 10
                result = self.numbers[str(tens)]
                if units > 0:
                    result += " " + self.numbers[str(units)]
                return result
            elif 100 <= num <= 999:
                hundreds = (num // 100) * 100
                remainder = num % 100
                result = self.numbers[str(hundreds)]
                if remainder > 0:
                    result += " " + self._number_to_words(str(remainder))
                return result
            else:
                return num_str
        except:
            return num_str

    def _ensure_punctuation(self, text: str) -> str:
        """Добавляет точку в конце текста, если её нет"""
        text = text.strip()
        if text and text[-1] not in '.!?…':
            text += '.'
        return text

    def _preprocess_text(self, text: str) -> str:
        """Предварительная обработка текста для улучшения произношения"""
        original_text = text

        # Автокоррекция орфографических ошибок
        text = self._autocorrect_text(text)

        # Добавляем пунктуацию в конце
        text = self._ensure_punctuation(text)

        # Заменяем сокращения
        for abbr, full in self.abbreviations.items():
            text = text.replace(abbr, full)

        # Обрабатываем числа
        def replace_number(match):
            num_str = match.group()
            # Проверяем, не является ли число частью слова
            return self._number_to_words(num_str)

        text = re.sub(r'\b\d+\b', replace_number, text)

        # Нормализуем пробелы
        text = re.sub(r'\s+', ' ', text)

        # Убираем лишние пробелы
        text = ' '.join(text.split())

        if text != original_text:
            self.logger.debug(f"Предобработка: '{original_text[:50]}...' -> '{text[:50]}...'")
        return text

    def _load_model(self):
        """Загрузка модели Silero TTS"""
        try:
            self.logger.info("Загрузка модели Silero TTS...")

            # Используем torch.hub для загрузки модели
            try:
                self.logger.info("Загрузка через torch.hub...")
                self.model, _ = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language='ru',
                    speaker='v3_1_ru'
                )
                self.model.to(self.device)
                self.logger.info("Модель загружена через torch.hub")

            except Exception as e:
                self.logger.warning(f"Ошибка загрузки через hub: {e}")

                # Альтернативный способ - из локального файла
                model_path = os.path.join(self.config.models_dir, "v3_1_ru.pt")
                if os.path.exists(model_path):
                    self.logger.info("Загрузка из локального файла...")
                    self.model = torch.package.PackageImporter(model_path).load_pickle("tts_models", "model")
                    self.model.to(self.device)
                    self.logger.info("Модель загружена из файла")
                else:
                    raise Exception("Модель не найдена")

            self.logger.info(f"Модель Silero TTS успешно загружена")

        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {e}")
            raise

    def set_voice(self, voice_name: str):
        """Установка голоса для синтеза"""
        if voice_name not in self.available_voices:
            self.logger.warning(f"Голос {voice_name} не найден, используется aidar")
            voice_name = "aidar"

        self.current_voice = voice_name
        self.logger.info(f"Установлен голос: {voice_name}")

    def synthesize(self, text: str, speed: float = 1.0) -> Optional[np.ndarray]:
        """Синтез речи из текста с улучшенным качеством"""
        if not self.model:
            self.logger.error("Модель не загружена")
            return None

        if not self.current_voice:
            self.set_voice(self.available_voices[0])

        try:
            text = text.strip()
            if not text:
                return None

            # Предварительная обработка текста
            processed_text = self._preprocess_text(text)
            self.logger.info(f"Синтез текста: '{processed_text[:100]}...' голосом: {self.current_voice}")

            # Разбиваем на предложения
            sentences = self._split_sentences(processed_text)

            if not sentences:
                self.logger.error("Не удалось разбить текст на предложения")
                return None

            audio_parts = []

            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                # Убеждаемся, что предложение не пустое и имеет разумную длину
                if len(sentence) < 1:
                    continue

                # Удаляем лишние знаки препинания в начале
                sentence = sentence.lstrip('.!?… ')

                self.logger.debug(f"Синтез предложения {i + 1}/{len(sentences)}: {sentence}")

                try:
                    # Синтез одного предложения
                    audio = self.model.apply_tts(
                        text=sentence,
                        speaker=self.current_voice,
                        sample_rate=self.sample_rate
                    )

                    # Конвертируем в numpy
                    if torch.is_tensor(audio):
                        audio = audio.cpu().numpy()

                    if len(audio) > 0:
                        # Пост-обработка аудио
                        audio = self._postprocess_audio(audio)
                        audio_parts.append(audio)

                        # Добавляем паузу между предложениями
                        if i < len(sentences) - 1:
                            pause_duration = self.config.default_pause_duration
                        else:
                            # Для последнего предложения добавляем небольшую паузу в конце
                            pause_duration = 0.3

                        pause_samples = int(self.sample_rate * pause_duration)
                        pause = np.zeros(pause_samples)
                        audio_parts.append(pause)

                except Exception as e:
                    self.logger.error(f"Ошибка синтеза предложения '{sentence}': {e}")
                    continue

            if not audio_parts:
                self.logger.error("Нет аудио для объединения")
                return None

            # Объединяем все части
            full_audio = np.concatenate(audio_parts)

            # Нормализуем финальное аудио
            max_val = np.max(np.abs(full_audio))
            if max_val > 1.0:
                full_audio = full_audio / max_val
                self.logger.info(f"Аудио нормализовано (max={max_val:.2f})")

            # Применяем изменение скорости
            if speed != 1.0:
                full_audio = self._change_speed(full_audio, speed)

            self.logger.info(f"Аудио синтезировано, длина: {len(full_audio)} samples")
            return full_audio

        except Exception as e:
            self.logger.error(f"Ошибка синтеза речи: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _postprocess_audio(self, audio: np.ndarray) -> np.ndarray:
        """Пост-обработка аудио для улучшения качества"""
        if len(audio) == 0:
            return audio

        # Плавное начало
        fade_in_duration = int(0.01 * self.sample_rate)
        if fade_in_duration < len(audio):
            fade_in = np.linspace(0, 1, fade_in_duration)
            audio[:fade_in_duration] *= fade_in

        # Плавное окончание
        fade_out_duration = int(0.05 * self.sample_rate)
        if fade_out_duration < len(audio):
            fade_out = np.linspace(1, 0, fade_out_duration)
            audio[-fade_out_duration:] *= fade_out

        return audio

    def play(self, audio: np.ndarray):
        """Воспроизведение аудио"""
        try:
            if audio is None or len(audio) == 0:
                self.logger.error("Нет аудио для воспроизведения")
                return

            self.logger.info(f"Воспроизведение аудио, длина: {len(audio)} samples, частота: {self.sample_rate} Hz")

            sd.play(audio, self.sample_rate)
            sd.wait()

            self.logger.info("Воспроизведение завершено")

        except Exception as e:
            self.logger.error(f"Ошибка воспроизведения: {e}")

    def save_to_file(self, audio: np.ndarray, filepath: str) -> bool:
        """Сохранение аудио в файл"""
        try:
            if audio is None or len(audio) == 0:
                self.logger.error("Нет аудио для сохранения")
                return False

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            sf.write(filepath, audio, self.sample_rate)
            self.logger.info(f"Аудио сохранено в: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Ошибка сохранения файла: {e}")
            return False

    def _split_sentences(self, text: str) -> List[str]:
        """Разбивка текста на предложения"""
        # Разбиваем по знакам препинания
        sentences = re.split(r'([.!?…])', text)

        # Объединяем предложения с их знаками препинания
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = (sentences[i] + sentences[i + 1]).strip()
                if sentence:
                    result.append(sentence)

        # Если остался текст без знака препинания
        if not result and text.strip():
            result = [text.strip() + '.']

        # Фильтруем пустые и слишком короткие предложения
        result = [s for s in result if len(s) > 1]

        return result

    def _change_speed(self, audio: np.ndarray, speed: float) -> np.ndarray:
        """Изменение скорости воспроизведения"""
        try:
            old_length = len(audio)
            new_length = int(old_length / speed)

            indices = np.linspace(0, old_length - 1, new_length)
            indices = indices.astype(np.int32)
            indices = indices[indices < old_length]

            return audio[indices]

        except Exception as e:
            self.logger.error(f"Ошибка изменения скорости: {e}")
            return audio