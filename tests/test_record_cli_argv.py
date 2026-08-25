"""The recorder is the evidence, so it gets checked before it is trusted."""

import contextlib
import importlib.util
import shutil
import subprocess
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "record_cli_argv",
    Path(__file__).resolve().parent.parent.parent / "tools" / "record_cli_argv.py")
_REC = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_REC)


@contextlib.contextmanager
def _installed_stubs():
    """Install the recorder's stubs and guarantee every one is undone.

    ``_install_stubs()`` patches four different things (subprocess.run/Popen,
    shutil.rmtree/copy2, Path.write_text/write_bytes). A test that only reloads
    the module it cares about leaves the rest patched on the class/module object
    for the remainder of the process -- ``importlib.reload`` cannot undo a
    ``Path.write_text`` patch at all, since every other module's already-bound
    reference to :class:`Path` keeps pointing at the same (patched) class. So
    everything is captured and put back here, in one place, regardless of which
    single stub the calling test means to exercise.
    """
    real_run = subprocess.run
    real_popen = subprocess.Popen
    real_rmtree = shutil.rmtree
    real_copy2 = shutil.copy2
    real_write_text = Path.write_text
    real_write_bytes = Path.write_bytes

    _REC._RECORDS.clear()
    _REC._install_stubs()
    try:
        yield _REC._RECORDS
    finally:
        subprocess.run = real_run
        subprocess.Popen = real_popen
        shutil.rmtree = real_rmtree
        shutil.copy2 = real_copy2
        Path.write_text = real_write_text
        Path.write_bytes = real_write_bytes


def test_a_list_command_is_recorded_and_not_run():
    with _installed_stubs() as records:
        result = subprocess.run(["definitely-not-a-real-binary", "--flag"], cwd=".")
        assert result.returncode == 0
        assert records == [
            {"kind": "run", "argv": ["definitely-not-a-real-binary", "--flag"],
             "cwd": "."}]


def test_rmtree_is_recorded_and_deletes_nothing(tmp_path):
    victim = tmp_path / "build"
    victim.mkdir()
    with _installed_stubs() as records:
        shutil.rmtree(victim)
        assert victim.is_dir(), "the stub must not delete anything"
        assert records[0]["kind"] == "rmtree"


def test_copy2_is_recorded_and_copies_nothing(tmp_path):
    # A stand-in for the package-consumer DLL deploy (sushiblas/sushiai's
    # _deploy_consumer_dlls): a real write into a sibling checkout that goes
    # through shutil.copy2 rather than subprocess, so it needs its own stub.
    src = tmp_path / "source.dll"
    src.write_bytes(b"binary-payload")
    dst = tmp_path / "dest.dll"
    with _installed_stubs() as records:
        shutil.copy2(src, dst)
        assert not dst.exists(), "the stub must not copy anything"
        assert records[0]["kind"] == "copy"


def test_write_text_is_recorded_and_writes_nothing(tmp_path):
    # A stand-in for SushiRuntime's configure-stamp write (build() writing
    # STAMP_NAME via Path.write_text): also real disk I/O outside subprocess
    # and shutil.rmtree, so it too needs its own stub.
    target = tmp_path / "stamp.txt"
    with _installed_stubs() as records:
        target.write_text("hello")
        assert not target.exists(), "the stub must not write anything"
        assert records[0]["kind"] == "write"


def test_write_bytes_is_recorded_and_writes_nothing(tmp_path):
    target = tmp_path / "stamp.bin"
    with _installed_stubs() as records:
        target.write_bytes(b"hello")
        assert not target.exists(), "the stub must not write anything"
        assert records[0]["kind"] == "write"
