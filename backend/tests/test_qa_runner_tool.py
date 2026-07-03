from app.tools.qa_runner_tool import QATestRunnerTool


def test_parses_all_passing(tmp_path):
    (tmp_path / "test_sample.py").write_text(
        "def test_one():\n    assert True\n\ndef test_two():\n    assert 1 + 1 == 2\n"
    )
    tool = QATestRunnerTool()
    result = tool.run("run_pytest", cwd=str(tmp_path))
    assert result.success
    assert result.data == {"passed": 2, "failed": 0, "errors": 0}


def test_parses_a_failure(tmp_path):
    (tmp_path / "test_sample.py").write_text(
        "def test_pass():\n    assert True\n\ndef test_fail():\n    assert 1 == 2\n"
    )
    tool = QATestRunnerTool()
    result = tool.run("run_pytest", cwd=str(tmp_path))
    assert not result.success
    assert result.data["passed"] == 1
    assert result.data["failed"] == 1


def test_no_tests_collected_is_treated_as_a_pass(tmp_path):
    tool = QATestRunnerTool()
    result = tool.run("run_pytest", cwd=str(tmp_path))
    assert result.success
    assert result.data == {"passed": 0, "failed": 0, "errors": 0}


def test_unknown_action_fails(tmp_path):
    tool = QATestRunnerTool()
    result = tool.run("not_run_pytest", cwd=str(tmp_path))
    assert not result.success
