from __future__ import annotations
from tools.verify import paragraphs as pg
from tools.verify.convert import common
from .conftest import GOLD_SLUG, RAW_TEXT, SLUG


def test_blank_line_blocks_are_numbered_from_one():
    blocks = pg.split_blocks(RAW_TEXT, "codex_raw")
    assert [b.para_id for b in blocks] == [f"codex_raw#{i:04d}" for i in range(1, 7)]
    assert blocks[0].text == "Title of a Demo Paper\nSome Author"
    assert blocks[-1].word_count == 2


def test_form_feed_is_a_line_break():
    blocks = pg.split_blocks("a b c\fd e f\n\ng h", "v")
    assert [b.text for b in blocks] == ["a b c\nd e f", "g h"]


def test_frame_keeps_blocks_of_min_words():
    blocks = pg.split_blocks(RAW_TEXT, "codex_raw")
    assert [b.seq for b in pg.frame(blocks, 20)] == [2, 3, 4, 5]


def test_merge_blocks_to_target_words():
    blocks = pg.split_blocks("one two\n\nthree four five\n\nsix\n\nseven eight nine ten", "v")
    merged = pg.merge_blocks(blocks, target=4)
    assert [m.word_count for m in merged] == [5, 5]
    assert merged[0].para_id == "v~m0001"


def test_resolve_survives_line_break_hyphen_and_case():
    blocks = pg.split_blocks("Alpha beta gamma\n\nThe infer-\nence system is fast and it is\nsimple.", "v")
    assert pg.resolve("the inference system is fast and it is simple", blocks) == [2]


def test_resolve_across_two_blocks_and_ellipsis():
    blocks = pg.split_blocks(RAW_TEXT, "codex_raw")
    quote = ("Requests span a wide range of token lengths. … every model family we study in the trace. "
             "Prefix reuse is common")
    assert pg.resolve(quote, blocks) == [3, 4]
    assert pg.resolve("words that are nowhere in the paper at all", blocks) == []
    assert pg.resolve("Short", blocks) == []  # probe below minimum length never resolves


def test_variant_paths_report_unavailable(source_root):
    paths = common.variant_paths(source_root, SLUG)
    assert set(paths) == {"codex_raw", "codex_layout", "claude_body", "claude_column"}
    assert paths["claude_column"] is None
    assert paths["codex_raw"].exists()


def test_gold_paper_raw_blocks(real_root):
    text = common.variant_paths(real_root, GOLD_SLUG)["codex_raw"].read_text(errors="replace")
    blocks = pg.split_blocks(text, "codex_raw")
    assert len(pg.frame(blocks, 20)) == 70


def test_resolve_quote_interrupted_by_figure_labels():
    text = ("Intro words that do not matter here at all today.\n\n"
            "Figure 14a shows that per-user inter-arrival time remains\n"
            "Req #0 Decode 10^2\n"
            "on the order of seconds for most users, while the tail stretches to hours.")
    blocks = pg.split_blocks(text, "v")
    quote = ("Figure 14a shows that per-user inter-arrival time remains on the order of seconds"
             " for most users, while the tail stretches to hours.")
    assert pg.resolve(quote, blocks) == [2]


def test_shingles_need_eight_words():
    blocks = pg.split_blocks("alpha beta gamma delta epsilon zeta eta\n\nother", "v")
    assert pg.resolve("zzzz alpha beta gamma delta epsilon zeta eta", blocks) == []


def test_single_shared_shingle_is_not_enough():
    blocks = pg.split_blocks("filler text here\n\none two three four five six seven eight nine", "v")
    quote = "zz one two three four five six seven eight qq and more words after it"
    assert pg.resolve(quote, blocks) == []
    assert pg.resolve("one two three four five six seven eight nine", blocks) == [2]


def test_primary_block_prefers_contiguous_match():
    text = ("one two three four five six seven eight nine ten appear in a caption here\n\n"
            "The body sentence says one two three four five six seven eight nine ten exactly.")
    blocks = pg.split_blocks(text, "v")
    quote = "The body sentence says one two three four five six seven eight nine ten exactly."
    assert pg.resolve(quote, blocks) == [1, 2]
    assert pg.primary(quote, blocks) == 2


def test_repeated_sentence_resolves_to_every_occurrence():
    sentence = "Most requests share a long system prompt with an earlier request."
    blocks = pg.split_blocks(f"{sentence}\n\nfiller words\n\n{sentence}", "v")
    assert pg.resolve(sentence, blocks) == [1, 3]
    assert pg.primary(sentence, blocks) == 1
