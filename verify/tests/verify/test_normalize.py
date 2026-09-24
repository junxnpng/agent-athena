from __future__ import annotations
import pytest

from tools.verify import normalize as nz

RULES = ("hyphen", "ligature", "quotes", "whitespace", "sentence_case", "line_join_space")


def test_config_has_the_six_rules_and_two_profiles():
    cfg = nz.load()
    assert tuple(cfg.rules) == RULES
    assert cfg.strict == RULES
    assert cfg.loose_citation


def _only(rule, text):
    return nz.apply(text, [rule]).text


def test_whitespace_folds_runs():
    assert _only("whitespace", "a  \n\t\f b c") == "a b c"


def test_hyphen_unifies_dashes_and_joins_line_breaks():
    assert _only("hyphen", "10–20 — x−y") == "10-20 - x-y"
    assert _only("hyphen", "soft­hyphen") == "softhyphen"
    assert _only("hyphen", "the infer-\n  ence system") == "the inference system"
    assert _only("hyphen", "load-balance only") == "load-balance only"


def test_quotes_become_straight():
    assert _only("quotes", "“word” it’s `x′") == "\"word\" it's 'x'"


def test_ligatures_are_spelled_out():
    assert _only("ligature", "ﬁnd the ﬂow ﬃx") == "find the flow ffix"


def test_sentence_case_lowers_sentence_initial_letters_only():
    assert _only("sentence_case", "Inputs stay. Figure 11 shows DeepSeek") == \
        "inputs stay. figure 11 shows DeepSeek"


def test_line_join_space_ignores_spaces():
    assert _only("line_join_space", "inference system") == _only("line_join_space", "inferencesystem")


def test_offsets_point_back_to_the_original():
    text = "The ﬁrst infer-\nence  system"
    norm = nz.apply(text, list(RULES))
    assert norm.text == "thefirstinferencesystem"
    at = norm.text.index("inference")
    start, end = norm.span(at, at + len("inference"))
    assert text[start:end] == "infer-\nence"
    at = norm.text.index("fi")
    assert norm.span(at, at + 2) == (4, 5)  # both letters come from the one ligature


def test_loose_is_the_old_alphanumeric_canon():
    assert nz.loose("Preble [47] is FAST-ish, [3, 5] really.").text == "prebleisfastishreally"


def test_strict_keeps_case_and_punctuation_that_loose_drops():
    strict = nz.strict("so DeepSeek-V3.2, then")
    assert strict.text == "soDeepSeek-V3.2,then"
    assert nz.loose("so DeepSeek-V3.2, then").text == "sodeepseekv32then"


def test_piece_start_may_differ_in_case():
    hay = nz.strict("most requests share a prompt. Inputs stay stable")
    assert nz.find(hay, nz.strict_needle("Most requests share")) == (0, len("mostrequestsshare"))
    assert nz.find(hay, nz.strict_needle("inputs stay")) is not None
    assert nz.find(hay, nz.strict_needle("REQUESTS share")) is None


def test_unknown_rule_is_refused():
    with pytest.raises(nz.NormalizationError, match="unknown rule"):
        nz.apply("x", ["nfkc"])


def test_case_allowance_applies_to_the_first_letter_not_the_first_character():
    hay = nz.strict("algorithms: FIFO, LRU, ARC [14], S3FIFO [27], GDSF")
    assert nz.find(hay, nz.strict_needle(", S3FIFO")) is not None


def test_gapped_profile_parameters():
    g = nz.load().gapped
    assert (g.min_run, g.max_runs, g.max_gap_chars) == (20, 3, 1000)
