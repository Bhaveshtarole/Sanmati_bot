"""
Unit tests for the hot-lead detection service.
"""

import pytest

from app.services.lead_detector import detect_hot_lead


class TestDetectHotLead:
    """Tests for detect_hot_lead()."""

    # ── Positive cases (should return True) ──────────────────────────

    @pytest.mark.parametrize("message", [
        "What are the fees for CSE?",
        "I want to know about admission process",
        "Tell me about placements",
        "How many seats are available?",
        "How do I apply?",
        "Is hostel available?",
        "Do you offer any scholarship?",
        "What is the cutoff for CSE?",
        "What is the last date to apply?",
        "Tell me about the merit list",
        "When does counselling start?",
    ])
    def test_positive_keywords(self, message):
        assert detect_hot_lead(message) is True

    # ── Case insensitivity ───────────────────────────────────────────

    @pytest.mark.parametrize("message", [
        "FEES for engineering?",
        "ADMISSION details please",
        "Placement record?",
        "FEE structure",
    ])
    def test_case_insensitive(self, message):
        assert detect_hot_lead(message) is True

    # ── Negative cases (should return False) ─────────────────────────

    @pytest.mark.parametrize("message", [
        "Hello",
        "Good morning",
        "What courses do you offer?",
        "Tell me about the campus",
        "Where is the college located?",
        "Thank you",
        "1",
        "2",
        "3",
    ])
    def test_negative_keywords(self, message):
        assert detect_hot_lead(message) is False

    # ── Edge cases ───────────────────────────────────────────────────

    def test_empty_string(self):
        assert detect_hot_lead("") is False

    def test_none_input(self):
        assert detect_hot_lead(None) is False

    def test_keyword_in_longer_sentence(self):
        assert detect_hot_lead("I heard the placement record is good, can you share details?") is True

    def test_multiple_keywords(self):
        assert detect_hot_lead("Tell me about fees and admission process for hostel students") is True

    def test_partial_word_no_match(self):
        """'fee' should match but 'feeling' should not."""
        assert detect_hot_lead("I am feeling happy") is False

    def test_fee_singular_matches(self):
        assert detect_hot_lead("What is the fee?") is True

    def test_cut_off_variants(self):
        assert detect_hot_lead("What is the cut-off?") is True
        assert detect_hot_lead("What is the cut off?") is True
        assert detect_hot_lead("What is the cutoff?") is True
