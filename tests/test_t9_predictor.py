# tests/test_t9_predictor.py
"""Юнит-тесты T9Predictor: предсказание, частоты, динамическое обучение."""
import json

import pytest


@pytest.fixture()
def predictor(tmp_config):
    from src.text_processor.t9_predictor import T9Predictor

    return T9Predictor(tmp_config)


class TestBasicPrediction:
    def test_default_dictionary_created(self, predictor, tmp_config):
        assert len(predictor.word_frequency) > 0
        # файл словаря создан в tmp-директории (пути унифицированы через Config)
        import os
        assert os.path.exists(predictor.dictionary_path)

    def test_predict_by_prefix(self, predictor):
        suggestions = predictor.predict("прив")
        assert "привет" in suggestions

    def test_predict_case_insensitive(self, predictor):
        assert predictor.predict("ПриВ") == predictor.predict("прив")

    def test_predict_unknown_prefix(self, predictor):
        assert predictor.predict("zzzzqqq") == []

    def test_predict_empty(self, predictor):
        assert predictor.predict("") == []

    def test_max_suggestions(self, predictor):
        assert len(predictor.predict("а", max_suggestions=3)) <= 3

    def test_frequency_ordering(self, predictor):
        # более частотное слово должно быть выше
        predictor.update_frequency("привет")
        top = predictor.predict("при", max_suggestions=1)
        assert top and top[0] == "привет"


class TestDynamicLearning:
    def test_learn_new_word(self, predictor):
        predictor.learn_from_text("голубоглагол сегодня")
        assert predictor.get_word_frequency("голубоглагол") == 1
        assert "голубоглагол" in predictor.predict("голуб")

    def test_learning_increases_frequency(self, predictor):
        before = predictor.get_word_frequency("дом")
        predictor.learn_from_text("дом дом дом")
        after = predictor.get_word_frequency("дом")
        assert after == before + 3

    def test_learn_ignores_short_words(self, predictor):
        predictor.learn_from_text("a б я")
        # однобуквенные латиницы/кириллицы не должны добавляться
        assert predictor.get_word_frequency("a") == 0

    def test_learn_persistence(self, tmp_config):
        """Словарь переживает перезапуск: сохранён на диск и перечитан."""
        from src.text_processor.t9_predictor import T9Predictor

        p1 = T9Predictor(tmp_config)
        p1.learn_from_text("космобиолог")
        del p1

        p2 = T9Predictor(tmp_config)
        assert "космобиолог" in p2.predict("космо")

    def test_learn_handles_punctuation(self, predictor):
        predictor.learn_from_text("привет, мир! привет...")
        assert predictor.get_word_frequency("мир") == 1
        # знаки препинания не стали отдельными «словами»
        assert "" not in predictor.word_frequency

    def test_update_frequency_incremental_index(self, predictor):
        predictor.update_frequency("словокот")
        assert "словокот" in predictor.predict("слов")
        assert predictor.get_word_frequency("словокот") == 1
