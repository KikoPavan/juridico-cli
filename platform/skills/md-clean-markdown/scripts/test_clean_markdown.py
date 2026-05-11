"""Tests for clean_markdown.py — focused on _fix_trailing_whitespace regression."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from clean_markdown import CleanStats, _fix_trailing_whitespace, clean_lines


# ---------------------------------------------------------------------------
# _fix_trailing_whitespace unit tests
# ---------------------------------------------------------------------------

def test_spaces_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("foo   \n", stats)
    assert result == "foo\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_tab_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("bar\t\n", stats)
    assert result == "bar\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_mixed_space_tab_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("baz \t \n", stats)
    assert result == "baz\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_forced_break_two_spaces_preserved():
    stats = CleanStats()
    result = _fix_trailing_whitespace("line  \n", stats)
    assert result == "line  \n", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_single_space_before_newline_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("word \n", stats)
    assert result == "word\n", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_line_without_newline_trailing_spaces_removed():
    stats = CleanStats()
    result = _fix_trailing_whitespace("end   ", stats)
    assert result == "end", repr(result)
    assert stats.trailing_ws_fixed == 1


def test_forced_break_no_newline_preserved():
    stats = CleanStats()
    result = _fix_trailing_whitespace("line  ", stats)
    assert result == "line  ", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_clean_line_unchanged():
    stats = CleanStats()
    result = _fix_trailing_whitespace("clean line\n", stats)
    assert result == "clean line\n", repr(result)
    assert stats.trailing_ws_fixed == 0


def test_empty_line_unchanged():
    stats = CleanStats()
    result = _fix_trailing_whitespace("\n", stats)
    assert result == "\n", repr(result)
    assert stats.trailing_ws_fixed == 0


# ---------------------------------------------------------------------------
# Pipeline integration: markers pass through untouched
# ---------------------------------------------------------------------------

def test_page_marker_primary_preserved():
    lines = ["[[Pág. 3]]\n", "text with space   \n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    assert result[0] == "[[Pág. 3]]\n", repr(result[0])
    assert result[1] == "text with space\n", repr(result[1])


def test_page_marker_legacy_preserved():
    lines = ["<!-- page 5 -->\n", "trailing tab\t\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=True, stats=stats, verbose=False)
    assert result[0] == "<!-- page 5 -->\n", repr(result[0])
    assert result[1] == "trailing tab\n", repr(result[1])


def test_page_marker_not_preserved_when_disabled():
    lines = ["[[Pág. 1]]\n"]
    stats = CleanStats()
    result = clean_lines(lines, max_blank=2, preserve_markers=False, stats=stats, verbose=False)
    # Marker treated as normal text — trailing whitespace fix still applies
    assert result[0] == "[[Pág. 1]]\n", repr(result[0])


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
