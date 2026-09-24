from __future__ import annotations
import pytest

from tools.verify import cli, ledger, waivers
from .conftest import GOLD_SLUG, SLUG

HEADER = "slug\tqid\tfrag_sha1_12\t사유\t확인 방법\n"
ROWS = [
    f"{SLUG}\tDM-A1.q1\taaaaaaaaaaaa\t이탤릭 `without`이 밀림 + 같은 문구가 두 곳에 있어 greedy\t쪽 이미지 확인\n",
    f"other__paper\tOT-B1.q2\tbbbbbbbbbbbb\t앞 조각과의 간격이 MAX_GAP 초과\t추출 텍스트 인접 줄에서 밀린 토큰 확인\n",
    f"other__paper\tOT-B1.q3\tcccccccccccc\t\"1차 검토에서 쪽 이미지로 확인함: 식별자 x_y가 \"\"x_-\"\" / \"\"y\"\"로 갈려\"\t쪽 이미지 확인\n",
]


def _tsv(tmp_path, rows=ROWS):
    path = tmp_path / "waivers.tsv"
    path.write_text(HEADER + "".join(rows))
    return path


def test_reason_takes_the_earliest_mechanism():
    cfg = waivers.load_codes()
    assert waivers.map_reason("이탤릭 `without`이 밀림 + 같은 문구가 §5에도 나와 greedy", cfg) == "italic_reorder"
    assert waivers.map_reason("같은 문구가 두 곳에 있어 greedy가 다른 쪽을 잡음", cfg) == "gap_exceeded"
    assert waivers.map_reason("arXiv 스탬프가 `LLM`을 별도 줄로 분리", cfg) == "stamp_intrusion"
    assert waivers.map_reason("본문이 왼쪽 단 끝에서 오른쪽 단 머리로, 그림 2의 라벨이 끼어듦", cfg) \
        == "column_interleave"
    assert waivers.map_reason("1차 검토에서 쪽 이미지로 확인함: 식별자가 갈려", cfg) == "visual_check"


def test_unmapped_reason_is_refused():
    with pytest.raises(waivers.WaiverError, match="no reason code"):
        waivers.map_reason("아무 설명 없음", waivers.load_codes())


def test_codes_are_at_most_six():
    assert len(waivers.load_codes().codes) == 6


def test_import_counts_and_is_idempotent(ledger_path, tmp_path):
    conn = ledger.init(ledger_path)
    path = _tsv(tmp_path)
    assert waivers.import_tsv(conn, path) == {"read": 3, "inserted": 3}
    assert waivers.import_tsv(conn, path) == {"read": 3, "inserted": 0}
    rows = conn.execute("select row_ref, reason_code, verification_method from waivers"
                        " order by waiver_id").fetchall()
    assert rows == [("DM-A1.q1", "italic_reorder", "쪽 이미지 확인"),
                    ("OT-B1.q2", "gap_exceeded", "추출 텍스트 인접 줄에서 밀린 토큰 확인"),
                    ("OT-B1.q3", "visual_check", "쪽 이미지 확인")]


def test_import_refuses_a_changed_reason(ledger_path, tmp_path):
    conn = ledger.init(ledger_path)
    waivers.import_tsv(conn, _tsv(tmp_path))
    changed = [ROWS[0].replace("이탤릭", "arXiv 스탬프")] + ROWS[1:]
    with pytest.raises(waivers.WaiverError, match="already imported"):
        waivers.import_tsv(conn, _tsv(tmp_path, changed))


def test_empty_reason_is_refused(ledger_path, tmp_path):
    rows = [f"{SLUG}\tDM-A1.q1\taaaaaaaaaaaa\t\t쪽 이미지 확인\n"]
    with pytest.raises(waivers.WaiverError, match="without a reason"):
        waivers.import_tsv(ledger.init(ledger_path), _tsv(tmp_path, rows))


def test_rates_are_per_paper_rows_and_overall(sealed, source_root, tmp_path):
    waivers.import_tsv(sealed, _tsv(tmp_path))
    r = waivers.rates(sealed, source_root)
    assert r["papers"] == {SLUG: (1, 4)}  # one waived of the paper's four Claude rows
    assert r["overall_rows"] == (3, 5)    # waived quotes / every Claude quote in the record file
    assert r["overall_records"] == (2, 5)  # distinct waived records / Claude records


def test_cli_convert_waivers(sealed, ledger_path, source_root, tmp_path, capsys):
    sealed.close()
    path = _tsv(tmp_path)
    assert cli.main(["convert", "waivers", "--file", str(path), "--ledger", str(ledger_path),
                     "--source-root", str(source_root)]) == 0
    out = capsys.readouterr().out
    assert "waivers: 3 (inserted 3), reason codes: 3" in out
    assert f"waiver_rate {SLUG}: 1/4 rows" in out
    assert "overall: 3/5 rows (2/5 records)" in out


def test_cli_convert_needs_paper_for_records(capsys, source_root):
    assert cli.main(["convert", "claude", "--source-root", str(source_root)]) == 1
    assert "--paper" in capsys.readouterr().err


def test_real_waivers(real_root, ledger_path, capsys):
    from tools.verify.convert import claude
    conn = ledger.init(ledger_path)
    ledger.import_converted(conn, claude.convert(real_root, GOLD_SLUG).payload(), real_root)
    counts = waivers.import_tsv(conn, waivers.default_path(real_root))
    assert counts == {"read": 48, "inserted": 48}
    n, codes = conn.execute("select count(*), count(distinct reason_code) from waivers").fetchone()
    assert n == 48 and codes <= 6
    r = waivers.rates(conn, real_root)
    assert r["papers"][GOLD_SLUG] == (0, 44)
    assert r["overall_rows"] == (48, 1489)
    assert r["overall_records"] == (46, 804)
