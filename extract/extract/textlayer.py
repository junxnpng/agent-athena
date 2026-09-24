"""Local Poppler text extraction, with source hashes and byte comparisons."""
from __future__ import annotations

import difflib
import hashlib
import os
from pathlib import Path
import signal
import subprocess
from typing import Optional


def _run(command: list[str], timeout: float = 60) -> str:
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding="utf-8", errors="replace", start_new_session=True)
    except OSError as exc:
        raise RuntimeError(f"pdftotext 실행 실패: {exc}") from exc
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise RuntimeError("pdftotext 시간 제한 초과") from exc
    if process.returncode:
        raise RuntimeError(f"pdftotext 종료 {process.returncode}: {stderr.strip()}")
    return stderr.strip() if command[-1] == "-v" else stdout


def compare_text(text: str, reference: str) -> dict:
    actual, expected = text.encode("utf-8"), reference.encode("utf-8")
    first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), None)
    if first is None and len(actual) != len(expected):
        first = min(len(actual), len(expected))
    changes = difflib.SequenceMatcher(None, text.splitlines(keepends=True),
                                     reference.splitlines(keepends=True), autojunk=False)
    lines = sum(max(b - a, d - c) for tag, a, b, c, d in changes.get_opcodes() if tag != "equal")
    return {"equal": actual == expected, "diff_lines": lines, "first_diff": first}


def extract_raw(pdf_path: Path, codex_raw: Optional[str] = None) -> tuple[str, dict]:
    path = Path(pdf_path).resolve(strict=True)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    version = _run(["pdftotext", "-v"])
    text = _run(["pdftotext", "-q", str(path), "-"])
    if hashlib.sha256(path.read_bytes()).hexdigest() != before:
        raise RuntimeError("추출 도중 PDF가 변경되었습니다")
    if not text.strip():
        raise RuntimeError("PDF 텍스트 층이 비어 있습니다; OCR은 지원하지 않습니다")
    meta = {"pdf_sha256": before, "extract_raw_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "poppler_version": version,
            "comparison": compare_text(text, codex_raw) if codex_raw is not None else None}
    return text, meta
