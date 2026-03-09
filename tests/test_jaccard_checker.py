"""Tests for writer.utils.jaccard_checker.JaccardChecker.

JaccardChecker is fully implemented (pure math), so these tests should PASS
immediately and serve as regression tests.
"""
from __future__ import annotations

import pytest

from writer.models.story_metadata import StoryMetadata
from writer.utils.jaccard_checker import JaccardChecker


@pytest.fixture
def checker() -> JaccardChecker:
    return JaccardChecker(threshold=0.8)


@pytest.fixture
def checker_low_threshold() -> JaccardChecker:
    return JaccardChecker(threshold=0.3)


class TestCharNgrams:
    """Tests for JaccardChecker.char_ngrams()."""

    def test_bigrams_simple(self, checker) -> None:
        result = checker.char_ngrams("abc", 2)
        assert result == {"ab", "bc"}

    def test_trigrams_simple(self, checker) -> None:
        result = checker.char_ngrams("abcd", 3)
        assert result == {"abc", "bcd"}

    def test_text_shorter_than_n_returns_empty_set(self, checker) -> None:
        assert checker.char_ngrams("ab", 3) == set()
        assert checker.char_ngrams("", 2) == set()

    def test_exact_length_returns_one_element(self, checker) -> None:
        result = checker.char_ngrams("abc", 3)
        assert result == {"abc"}

    def test_returns_set_no_duplicates(self, checker) -> None:
        result = checker.char_ngrams("aaa", 2)
        assert result == {"aa"}

    def test_unicode_text(self, checker) -> None:
        result = checker.char_ngrams("夜明け", 2)
        assert "夜明" in result
        assert "明け" in result

    def test_single_char_text_n1(self, checker) -> None:
        result = checker.char_ngrams("a", 1)
        assert result == {"a"}

    def test_long_text_bigrams_count(self, checker) -> None:
        text = "abcde"
        result = checker.char_ngrams(text, 2)
        assert len(result) == 4  # ab, bc, cd, de


class TestJaccard:
    """Tests for JaccardChecker.jaccard()."""

    def test_identical_sets(self, checker) -> None:
        a = {"ab", "bc", "cd"}
        assert checker.jaccard(a, a) == 1.0

    def test_disjoint_sets(self, checker) -> None:
        a = {"ab", "bc"}
        b = {"xy", "yz"}
        assert checker.jaccard(a, b) == 0.0

    def test_both_empty_returns_zero(self, checker) -> None:
        assert checker.jaccard(set(), set()) == 0.0

    def test_one_empty_returns_zero(self, checker) -> None:
        assert checker.jaccard({"ab"}, set()) == 0.0
        assert checker.jaccard(set(), {"ab"}) == 0.0

    def test_partial_overlap(self, checker) -> None:
        a = {"ab", "bc", "cd"}
        b = {"bc", "cd", "de"}
        # intersection = {bc, cd} = 2, union = {ab, bc, cd, de} = 4
        assert checker.jaccard(a, b) == pytest.approx(2 / 4)

    def test_result_between_zero_and_one(self, checker) -> None:
        a = {"ab", "bc"}
        b = {"bc", "cd"}
        result = checker.jaccard(a, b)
        assert 0.0 <= result <= 1.0

    def test_symmetry(self, checker) -> None:
        a = {"ab", "bc", "cd"}
        b = {"cd", "de"}
        assert checker.jaccard(a, b) == checker.jaccard(b, a)


class TestCompare:
    """Tests for JaccardChecker.compare()."""

    def _make_story(self, title: str, summary: str) -> StoryMetadata:
        return StoryMetadata(
            date="2026-01-01",
            slug="test-slug",
            title=title,
            summary=summary,
            tags=[],
            character_count=2000,
            reading_time_min=5,
            review_score=80,
        )

    def test_empty_recent_list(self, checker) -> None:
        result = checker.compare("テストタイトル", "テストのあらすじ", [])
        assert result["max_title_similarity"] == 0.0
        assert result["max_summary_similarity"] == 0.0
        assert result["is_duplicate"] is False

    def test_returns_required_keys(self, checker) -> None:
        result = checker.compare("タイトル", "あらすじ", [])
        assert "max_title_similarity" in result
        assert "max_summary_similarity" in result
        assert "is_duplicate" in result

    def test_identical_title_detected_as_duplicate(self, checker_low_threshold) -> None:
        story = self._make_story("夜明けの約束", "全く別のあらすじ")
        result = checker_low_threshold.compare("夜明けの約束", "新しいあらすじの内容", [story])
        assert result["max_title_similarity"] == pytest.approx(1.0)
        assert result["is_duplicate"] is True

    def test_identical_summary_detected_as_duplicate(
        self, checker_low_threshold
    ) -> None:
        story = self._make_story("別のタイトル", "これはサンプルのあらすじです")
        result = checker_low_threshold.compare(
            "新しいタイトル", "これはサンプルのあらすじです", [story]
        )
        assert result["max_summary_similarity"] == pytest.approx(1.0)
        assert result["is_duplicate"] is True

    def test_completely_different_not_duplicate(self, checker) -> None:
        story = self._make_story("AAAAAAAAAA", "BBBBBBBBBB")
        result = checker.compare("XXXXXXXXXX", "YYYYYYYYYY", [story])
        assert result["is_duplicate"] is False

    def test_multiple_stories_returns_max(self, checker) -> None:
        stories = [
            self._make_story("関係ないタイトル一", "関係ないあらすじ一"),
            self._make_story("夜明けの約束", "全く別のあらすじ"),
            self._make_story("関係ないタイトル三", "関係ないあらすじ三"),
        ]
        result = checker.compare("夜明けの約束", "新しいあらすじ", stories)
        # The second story has identical title so max_title_similarity should be 1.0
        assert result["max_title_similarity"] == pytest.approx(1.0)

    def test_is_duplicate_true_when_title_sim_meets_threshold(self) -> None:
        checker = JaccardChecker(threshold=0.5)
        story = self._make_story("夜明けの約束", "別のあらすじ")
        result = checker.compare("夜明けの約束", "全然違うあらすじ内容テスト", [story])
        assert result["is_duplicate"] is True

    def test_is_duplicate_false_when_below_threshold(self) -> None:
        checker = JaccardChecker(threshold=0.99)
        story = self._make_story("ABC", "DEF")
        result = checker.compare("ABX", "DEY", [story])
        # Partial overlap but probably below 0.99 threshold
        assert result["is_duplicate"] is False

    def test_similarity_values_between_zero_and_one(
        self, checker, recent_stories
    ) -> None:
        result = checker.compare("テストタイトル", "テストあらすじ内容", recent_stories)
        assert 0.0 <= result["max_title_similarity"] <= 1.0
        assert 0.0 <= result["max_summary_similarity"] <= 1.0

    def test_threshold_attribute_stored(self) -> None:
        checker = JaccardChecker(threshold=0.75)
        assert checker.threshold == 0.75
