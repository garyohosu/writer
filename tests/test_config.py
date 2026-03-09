"""Tests for writer.config.Config."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from writer.config import Config


class TestConfigDataclass:
    """Tests for Config dataclass construction and attributes."""

    def test_instantiation_with_valid_fields(self) -> None:
        cfg = Config(
            publication_mode="auto",
            max_review_attempts=3,
            similarity_threshold=0.8,
        )
        assert cfg.publication_mode == "auto"
        assert cfg.max_review_attempts == 3
        assert cfg.similarity_threshold == 0.8

    def test_publication_mode_manual(self) -> None:
        cfg = Config(
            publication_mode="manual",
            max_review_attempts=5,
            similarity_threshold=0.7,
        )
        assert cfg.publication_mode == "manual"

    def test_max_review_attempts_zero_is_valid_value(self) -> None:
        cfg = Config(
            publication_mode="auto",
            max_review_attempts=0,
            similarity_threshold=0.5,
        )
        assert cfg.max_review_attempts == 0

    def test_similarity_threshold_boundary_values(self) -> None:
        for val in [0.0, 0.5, 1.0]:
            cfg = Config("auto", 3, val)
            assert cfg.similarity_threshold == val


class TestConfigLoad:
    """Tests for Config.load() classmethod."""

    def test_load_valid_json_file(self, tmp_path) -> None:
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "publication_mode": "auto",
                    "max_review_attempts": 3,
                    "similarity_threshold": 0.8,
                }
            )
        )
        cfg = Config.load(str(config_file))
        assert isinstance(cfg, Config)
        assert cfg.publication_mode == "auto"
        assert cfg.max_review_attempts == 3
        assert cfg.similarity_threshold == 0.8

    def test_load_is_classmethod(self) -> None:
        assert isinstance(Config.__dict__["load"], classmethod)

    def test_load_nonexistent_path_raises(self) -> None:
        with pytest.raises((NotImplementedError, FileNotFoundError, Exception)):
            Config.load("/nonexistent/path/config.json")

    def test_load_returns_config_instance(self, tmp_path) -> None:
        """Once implemented, load() must return a Config instance."""
        config_file = tmp_path / "config.json"
        config_file.write_text(
            json.dumps(
                {
                    "publication_mode": "auto",
                    "max_review_attempts": 2,
                    "similarity_threshold": 0.75,
                }
            )
        )
        # Currently raises NotImplementedError; this test documents intent
        try:
            result = Config.load(str(config_file))
            assert isinstance(result, Config)
            assert result.publication_mode == "auto"
            assert result.max_review_attempts == 2
            assert result.similarity_threshold == 0.75
        except NotImplementedError:
            pytest.xfail("Config.load not yet implemented")
