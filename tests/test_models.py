"""Tests for all model dataclasses and their business rules."""
from __future__ import annotations

import pytest

from writer.models.plot_output import PlotOutput
from writer.models.title_selection_output import TitleSelectionOutput
from writer.models.story_output import StoryOutput
from writer.models.review_output import ReviewOutput
from writer.models.story_metadata import StoryMetadata
from writer.models.story_front_matter import StoryFrontMatter
from writer.models.story_document import StoryDocument


class TestPlotOutput:
    """Tests for PlotOutput dataclass."""

    def test_instantiation(self, sample_plot_output) -> None:
        p = sample_plot_output
        assert isinstance(p.title_candidates, list)
        assert len(p.title_candidates) == 3
        assert isinstance(p.characters, list)
        assert p.theme == "記憶と喪失"
        assert p.setting == "近未来の東京"
        assert p.ending_type == "open"
        assert p.reading_impression == "切なく温かい"

    def test_title_candidates_is_list_of_strings(self, sample_plot_output) -> None:
        for candidate in sample_plot_output.title_candidates:
            assert isinstance(candidate, str)

    def test_characters_is_list_of_dicts(self, sample_plot_output) -> None:
        for char in sample_plot_output.characters:
            assert isinstance(char, dict)

    def test_empty_title_candidates(self) -> None:
        p = PlotOutput(
            title_candidates=[],
            plot="test",
            characters=[],
            theme="",
            setting="",
            ending_type="",
            reading_impression="",
        )
        assert p.title_candidates == []


class TestTitleSelectionOutput:
    """Tests for TitleSelectionOutput dataclass."""

    def test_instantiation(self, sample_title_selection_output) -> None:
        t = sample_title_selection_output
        assert t.selected_title == "夜明けの約束"
        assert isinstance(t.reason, str)
        assert isinstance(t.scores, dict)

    def test_scores_keys_are_strings(self, sample_title_selection_output) -> None:
        for key in sample_title_selection_output.scores:
            assert isinstance(key, str)

    def test_scores_values_are_ints(self, sample_title_selection_output) -> None:
        for val in sample_title_selection_output.scores.values():
            assert isinstance(val, int)

    def test_selected_title_in_scores(self, sample_title_selection_output) -> None:
        t = sample_title_selection_output
        assert t.selected_title in t.scores


class TestStoryOutput:
    """Tests for StoryOutput dataclass."""

    def test_instantiation(self, sample_story_output) -> None:
        s = sample_story_output
        assert s.title == "夜明けの約束"
        assert isinstance(s.body, str)
        assert s.character_count == 3000
        assert s.reading_time_min == 8
        assert isinstance(s.summary, str)
        assert isinstance(s.tags, list)

    def test_tags_is_list_of_strings(self, sample_story_output) -> None:
        for tag in sample_story_output.tags:
            assert isinstance(tag, str)

    def test_character_count_positive(self, sample_story_output) -> None:
        assert sample_story_output.character_count > 0

    def test_reading_time_min_positive(self, sample_story_output) -> None:
        assert sample_story_output.reading_time_min > 0


class TestReviewOutput:
    """Tests for ReviewOutput dataclass, including business rules."""

    def test_instantiation_passed(self, sample_review_output_passed) -> None:
        r = sample_review_output_passed
        assert r.passed is True
        assert r.adsense_risk is False
        assert r.rewrite_instruction is None

    def test_instantiation_failed(self, sample_review_output_failed) -> None:
        r = sample_review_output_failed
        assert r.passed is False
        assert r.adsense_risk is False
        assert r.rewrite_instruction is not None

    def test_business_rule_adsense_risk_forces_passed_false(self) -> None:
        """CRITICAL: adsense_risk=True must force passed=False even if passed=True."""
        r = ReviewOutput(
            passed=True,
            scores={"quality": 90},
            issues=["AdSense violation"],
            adsense_risk=True,
            rewrite_instruction="Fix it.",
        )
        assert r.passed is False, "adsense_risk=True must force passed=False"

    def test_business_rule_adsense_risk_false_does_not_affect_passed(self) -> None:
        r = ReviewOutput(
            passed=True,
            scores={"quality": 90},
            issues=[],
            adsense_risk=False,
            rewrite_instruction=None,
        )
        assert r.passed is True

    def test_scores_dict_structure(self, sample_review_output_passed) -> None:
        for key, val in sample_review_output_passed.scores.items():
            assert isinstance(key, str)
            assert isinstance(val, int)

    def test_issues_list(self, sample_review_output_failed) -> None:
        assert len(sample_review_output_failed.issues) > 0
        for issue in sample_review_output_failed.issues:
            assert isinstance(issue, str)

    def test_adsense_risk_true_with_passed_false_stays_false(self) -> None:
        r = ReviewOutput(
            passed=False,
            scores={},
            issues=["problem"],
            adsense_risk=True,
            rewrite_instruction="rewrite",
        )
        assert r.passed is False


class TestStoryMetadata:
    """Tests for StoryMetadata dataclass."""

    def test_instantiation(self, sample_story_metadata) -> None:
        m = sample_story_metadata
        assert m.date == "2026-03-01"
        assert m.slug == "yoake-no-yakusoku"
        assert m.title == "夜明けの約束"
        assert isinstance(m.tags, list)
        assert m.character_count == 3000
        assert m.reading_time_min == 8
        assert m.review_score == 85

    def test_tags_is_list(self, sample_story_metadata) -> None:
        assert isinstance(sample_story_metadata.tags, list)


class TestStoryFrontMatter:
    """Tests for StoryFrontMatter dataclass."""

    def test_instantiation(self, sample_story_front_matter) -> None:
        fm = sample_story_front_matter
        assert fm.title == "夜明けの約束"
        assert fm.date == "2026-03-09"
        assert fm.slug == "yoake-no-yakusoku"
        assert fm.ai_generated is True
        assert fm.review_score == 85
        assert fm.status == "published"

    def test_ai_generated_is_bool(self, sample_story_front_matter) -> None:
        assert isinstance(sample_story_front_matter.ai_generated, bool)

    def test_tags_is_list(self, sample_story_front_matter) -> None:
        assert isinstance(sample_story_front_matter.tags, list)


class TestStoryDocument:
    """Tests for StoryDocument dataclass and its methods."""

    def test_instantiation(self, sample_story_document) -> None:
        doc = sample_story_document
        assert isinstance(doc.front_matter, StoryFrontMatter)
        assert isinstance(doc.body, str)

    def test_from_outputs_returns_story_document(
        self,
        sample_plot_output,
        sample_story_output,
        sample_review_output_passed,
    ) -> None:
        result = StoryDocument.from_outputs(
            plot=sample_plot_output,
            story=sample_story_output,
            review=sample_review_output_passed,
            slug="test-slug",
            date="2026-03-09",
        )
        assert isinstance(result, StoryDocument)

    def test_from_outputs_is_classmethod(self) -> None:
        assert isinstance(StoryDocument.__dict__["from_outputs"], classmethod)

    def test_to_index_entry_returns_story_metadata_inline(
        self, sample_story_document
    ) -> None:
        from writer.models.story_metadata import StoryMetadata
        result = sample_story_document.to_index_entry()
        assert isinstance(result, StoryMetadata)
        assert result.slug == sample_story_document.front_matter.slug

    def test_from_outputs_returns_story_document(
        self,
        sample_plot_output,
        sample_story_output,
        sample_review_output_passed,
    ) -> None:
        """Once implemented, from_outputs must return StoryDocument."""
        try:
            result = StoryDocument.from_outputs(
                plot=sample_plot_output,
                story=sample_story_output,
                review=sample_review_output_passed,
                slug="test-slug",
                date="2026-03-09",
            )
            assert isinstance(result, StoryDocument)
            assert isinstance(result.front_matter, StoryFrontMatter)
        except NotImplementedError:
            pytest.xfail("StoryDocument.from_outputs not yet implemented")

    def test_to_index_entry_returns_story_metadata(
        self, sample_story_document
    ) -> None:
        """Once implemented, to_index_entry must return StoryMetadata."""
        from writer.models.story_metadata import StoryMetadata
        try:
            result = sample_story_document.to_index_entry()
            assert isinstance(result, StoryMetadata)
            assert result.slug == sample_story_document.front_matter.slug
            assert result.title == sample_story_document.front_matter.title
        except NotImplementedError:
            pytest.xfail("StoryDocument.to_index_entry not yet implemented")
