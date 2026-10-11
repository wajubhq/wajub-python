"""What gets published is what gets imported.

1.1.0 and 1.1.1 went to PyPI as a wheel holding one file, ``wajub/py.typed``:
``pip install wajub`` succeeded and ``import wajub`` raised ModuleNotFoundError.
The sdist was limited to that marker, and ``python -m build`` builds the wheel
from the sdist. These tests build the same way and look inside.
"""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("hatchling")

from hatchling.builders.sdist import SdistBuilder  # noqa: E402
from hatchling.builders.wheel import WheelBuilder  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def wheel_from_sdist(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    sdist = Path(next(SdistBuilder(str(ROOT)).build(directory=str(out), versions=["standard"])))

    unpacked = tmp_path_factory.mktemp("sdist")
    with tarfile.open(sdist) as archive:
        archive.extractall(unpacked, filter="data")
    (source,) = unpacked.iterdir()

    return Path(next(WheelBuilder(str(source)).build(directory=str(out), versions=["standard"])))


def test_the_wheel_built_from_the_sdist_holds_every_module(wheel_from_sdist: Path) -> None:
    shipped = set(zipfile.ZipFile(wheel_from_sdist).namelist())
    expected = {
        f"wajub/{path.relative_to(ROOT / 'src' / 'wajub').as_posix()}"
        for path in (ROOT / "src" / "wajub").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }

    assert "wajub/__init__.py" in expected
    assert expected - shipped == set()


def test_the_built_version_is_the_one_the_client_announces(wheel_from_sdist: Path) -> None:
    namespace: dict[str, str] = {}
    exec((ROOT / "src" / "wajub" / "version.py").read_text(), namespace)

    assert wheel_from_sdist.name == f"wajub-{namespace['__version__']}-py3-none-any.whl"
