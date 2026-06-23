"""Command result helpers."""

from elda.executor.runner import CommandResult


def test_command_result_success():
    r = CommandResult(0, "ok\n", "")
    assert r.success
    assert "ok" in r.log
    d = r.as_dict()
    assert d["success"] is True
    assert d["returncode"] == 0


def test_command_result_failure():
    r = CommandResult(2, "", "error\n")
    assert not r.success
    assert r.as_dict()["success"] is False
