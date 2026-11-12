import pytest

from localkey.cli import main


def test_random_prints_password_only_on_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["--show-entropy", "random", "-l", "20"]) == 0
    out, err = capsys.readouterr()
    assert len(out.strip()) == 20
    assert "bit" in err and "bit" not in out


def test_below_threshold_is_rejected(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["random", "-l", "8"]) == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert "ambang" in err


def test_strict_raises_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    # 10 karakter ~65 bit: lolos default 60, gagal --strict 80
    assert main(["random", "-l", "10"]) == 0
    assert main(["--strict", "random", "-l", "10"]) == 1


def test_invalid_length_returns_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["random", "-l", "0"]) == 2
