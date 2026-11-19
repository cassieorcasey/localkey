import importlib.util
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "localkey"


def _load_build_web() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_web", ROOT / "scripts" / "build_web.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _forget_localkey() -> None:
    for name in [m for m in sys.modules if m.split(".")[0] == "localkey"]:
        del sys.modules[name]


def test_copies_core_files_unchanged(tmp_path: Path) -> None:
    _load_build_web().build(dest=tmp_path)
    for name in ("entropy.py", "generators.py"):
        assert (tmp_path / "localkey" / name).read_bytes() == (SRC / name).read_bytes()


def test_init_exports_random_password(tmp_path: Path) -> None:
    _load_build_web().build(dest=tmp_path)
    sys.path.insert(0, str(tmp_path))
    try:
        _forget_localkey()
        import localkey

        assert localkey.__file__ is not None
        assert Path(localkey.__file__).parent == tmp_path / "localkey"
        assert localkey.random_password(length=12).value
    finally:
        sys.path.remove(str(tmp_path))
        _forget_localkey()
