"""Gold set G: sentence split by the rules of config/gold_split.json, notes kept apart."""
from __future__ import annotations
import re

import pytest

from tools.verify import cli, ledger
from tools.verify.convert import gold
from .conftest import GOLD_SLUG, SLUG

RULES = gold.load_rules()


def _doc(line: str) -> str:
    return f"# G\n\n- 출처: 테스트\n\n## 원문(그대로)\n\n### {line}\n"


def _texts(parsed, kind):
    return [i.text for i in parsed.items if i.kind == kind]


def test_emphasis_separates_heading_review_and_body():
    p = gold.parse(_doc("Demo Paper**한줄평: 좋은 논문. 다만 짧음****First sentence here."), RULES)
    assert p.heading == "Demo Paper"
    assert _texts(p, "user_note") == ["한줄평: 좋은 논문. 다만 짧음"]
    assert _texts(p, "sentence") == ["First sentence here."]


def test_sentence_glued_to_the_review_survives():
    """`****` is a marker, so the first sentence is split, not repaired; `.R` is a repair."""
    p = gold.parse(_doc("T**한줄평: x****User behavior induces locality [11].Realistic traces matter."),
                   RULES)
    first, second = [i for i in p.items if i.kind == "sentence"]
    assert first.text == "User behavior induces locality [11]."
    assert (first.boundary_repaired, second.boundary_repaired) == (0, 1)
    assert second.text == "Realistic traces matter."


def test_spaced_boundary_is_not_repaired():
    p = gold.parse(_doc("T**한줄평: x**** Alpha one. Beta two."), RULES)
    assert [(i.text, i.boundary_repaired) for i in p.items if i.kind == "sentence"] \
        == [("Alpha one.", 0), ("Beta two.", 0)]


def test_periods_before_digits_and_abbreviations_do_not_split():
    p = gold.parse(_doc("T**한줄평: x**** It takes 2.7 s over 10 GB/s, e.g. The case. Next one."), RULES)
    assert _texts(p, "sentence") == ["It takes 2.7 s over 10 GB/s, e.g. The case.", "Next one."]


def test_note_ends_at_a_glued_period():
    p = gold.parse(_doc("T**한줄평: x****Figure 2c confirms fewer outputs-> so prefill matters here."
                        "MiniMax-M2.5 has longer inputs."), RULES)
    assert _texts(p, "sentence") == ["Figure 2c confirms fewer outputs", "MiniMax-M2.5 has longer inputs."]
    assert _texts(p, "user_note")[1:] == ["so prefill matters here."]


def test_note_ends_at_camel_glue_and_at_a_sentence_opener():
    p = gold.parse(_doc("T**한줄평: x****A first. -> Thus, models may be prefill-heavy due to long "
                        "promptsOutput length drives duration.B then.->  This matters for "
                        "cache-reuse opportunities While these users may be agents."), RULES)
    assert _texts(p, "user_note")[1:] == [
        "Thus, models may be prefill-heavy due to long prompts",
        "This matters for cache-reuse opportunities"]
    assert _texts(p, "sentence") == ["A first.", "Output length drives duration.", "B then.",
                                     "While these users may be agents."]
    repaired = {i.text: i.boundary_repaired for i in p.items if i.kind == "sentence"}
    assert repaired["Output length drives duration."] == 1
    assert repaired["While these users may be agents."] == 0


def test_no_split_names_are_not_camel_glue():
    p = gold.parse(_doc("T**한줄평: x****A first.-> about the DeepSeekR1 and MiniMaxM2.5 usage.Next one."),
                   RULES)
    assert _texts(p, "user_note")[1:] == ["about the DeepSeekR1 and MiniMaxM2.5 usage."]
    assert _texts(p, "sentence") == ["A first.", "Next one."]


def test_last_sentence_needs_no_period():
    p = gold.parse(_doc("T**한줄평: x****One. Two without a period"), RULES)
    assert _texts(p, "sentence") == ["One.", "Two without a period"]


def test_document_without_the_section_is_refused():
    with pytest.raises(gold.GoldError, match="no pasted line"):
        gold.parse("# nothing here\n", RULES)


# --- the real gold file (in this repository) -------------------------------

@pytest.fixture(scope="module")
def real():
    return gold.parse(gold.source_path(GOLD_SLUG).read_text(encoding="utf-8"), RULES)


def test_real_gold_has_six_notes(real):
    notes = _texts(real, "user_note")
    assert len(notes) == 6
    assert notes[0].startswith("한줄평:")
    assert real.heading == "A Year in LLM Serving (Harvard)"


def test_real_gold_first_sentence_survives_the_join(real):
    first = _texts(real, "sentence")[0]
    assert first.startswith("User behavior induces temporal locality")
    assert first.endswith("[11, 29, 35, 37].")


def test_real_gold_sentences_carry_no_note_text(real):
    sentences = _texts(real, "sentence")
    for s in sentences:
        assert "->" not in s and "한줄평" not in s and "**" not in s
        assert not re.search(r"[가-힣]", s), s
    for note in _texts(real, "user_note"):
        body = note.split(":", 1)[-1].strip()[:30]
        assert not any(body in s for s in sentences), note


def test_real_gold_items_are_the_whole_line(real):
    """Every character of the pasted line ends in the heading, a note, a sentence or a separator."""
    line = gold.pasted_line(gold.source_path(GOLD_SLUG).read_text(encoding="utf-8"), RULES)
    rest = line
    for piece in [real.heading] + [i.text for i in real.items]:
        rest = rest.replace(piece, "", 1)
    assert re.fullmatch(r"[\s*\->]*", rest), rest[:200]


# --- registration --------------------------------------------------------

def _file(tmp_path, line):
    path = tmp_path / "g.md"
    path.write_text(_doc(line))
    return path


LINE = ("Demo**한줄평: 짧은 평****We analyze a one-year production trace from CompanyX.Requests span a "
        "wide range of token lengths. -> 메모 하나.Figure 2 shows that input lengths are long")


def test_register_records_the_split_count(tmp_path, ledger_path):
    conn = ledger.init(ledger_path)
    res = gold.register(conn, SLUG, _file(tmp_path, LINE))
    assert (res.sentences, res.notes, res.inserted) == (3, 2, 5)
    kinds = dict(conn.execute("select kind, count(*) from gold group by kind").fetchall())
    assert kinds == {"sentence": 3, "user_note": 2}
    meta = gold.registration(conn, SLUG)
    assert meta["gold_split_count"] == 3 and meta["user_notes"] == 2
    assert meta["rules_version"] == RULES.version
    assert conn.execute("select count(*) from gold where source='hand' and disputable=1").fetchone()[0] == 5
    texts = [t for (t,) in conn.execute("select text from gold where kind='sentence' order by seq")]
    assert texts[1] == "Requests span a wide range of token lengths."


def test_register_is_idempotent_and_refuses_a_changed_file(tmp_path, ledger_path):
    conn = ledger.init(ledger_path)
    gold.register(conn, SLUG, _file(tmp_path, LINE))
    again = gold.register(conn, SLUG, _file(tmp_path, LINE))
    assert again.inserted == 0
    with pytest.raises(gold.GoldError, match="through an audit"):
        gold.register(conn, SLUG, _file(tmp_path, LINE.replace("long", "short")))


def test_gold_sentences_read_back_in_order(tmp_path, ledger_path):
    conn = ledger.init(ledger_path)
    gold.register(conn, SLUG, _file(tmp_path, LINE))
    rows = gold.sentences(conn, SLUG)
    assert [r["seq"] for r in rows] == [1, 2, 3]
    assert rows[0]["gold_id"] == f"{SLUG}:s001"
    with pytest.raises(gold.GoldError, match="convert gold"):
        gold.sentences(conn, "other__paper")


def test_cli_convert_gold(tmp_path, ledger_path, capsys):
    path = _file(tmp_path, LINE)
    assert cli.main(["convert", "gold", "--paper", SLUG, "--file", str(path),
                     "--ledger", str(ledger_path)]) == 0
    out = capsys.readouterr().out
    assert "gold_split_count: 3" in out and "user_notes: 2" in out
    assert "boundary_repaired: 2" in out
