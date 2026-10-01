"""Tests for auto_fix script."""

from pathlib import Path
from unittest import mock

import pytest

from scripts.auto_fix import main, run_ruff_fixes, run_shellcheck_fixes


@pytest.fixture
def sh_files(tmp_path: Path) -> Path:
    """Create a temporary directory tree with shell files and a .venv to skip."""
    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy" / "start.sh").write_text("#!/bin/bash\necho hello\n")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "helper.sh").write_text("#!/bin/bash\necho world\n")
    venv = tmp_path / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "activate").write_text("#!/bin/bash\n")
    return tmp_path


class TestRunRuffFixes:
    """Tests for run_ruff_fixes."""

    def test_runs_import_sort_then_format(self, tmp_path: Path) -> None:
        """Verify both ruff import sort and ruff format commands are invoked."""
        with mock.patch("scripts.auto_fix.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0)
            run_ruff_fixes(tmp_path)
        calls = mock_run.call_args_list
        assert any(
            "--select" in str(c) and "I" in str(c) and "'.'" in str(c) for c in calls
        )
        assert any("format" in str(c) and "'.'" in str(c) for c in calls)

    def test_returns_zero_when_all_pass(self, tmp_path: Path) -> None:
        """Verify zero is returned when all ruff commands succeed."""
        with mock.patch("scripts.auto_fix.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0)
            assert run_ruff_fixes(tmp_path) == 0

    def test_returns_worst_exit_code(self, tmp_path: Path) -> None:
        """Verify the highest exit code across ruff commands is returned."""
        results = [mock.Mock(returncode=0), mock.Mock(returncode=1)]
        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=results):
            assert run_ruff_fixes(tmp_path) == 1

    def test_import_sort_runs_before_format(self, tmp_path: Path) -> None:
        """Verify ruff import sort must precede ruff format."""
        call_order = []

        def capture(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Record the command and return a success mock."""
            call_order.append(cmd)
            return mock.Mock(returncode=0)

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=capture):
            run_ruff_fixes(tmp_path)

        sort_idx = next(i for i, c in enumerate(call_order) if "--select" in c)
        fmt_idx = next(i for i, c in enumerate(call_order) if "format" in c)
        assert sort_idx < fmt_idx


class TestRunShellcheckFixes:
    """Tests for run_shellcheck_fixes."""

    def test_skips_venv_directory(self, sh_files: Path) -> None:
        """Verify .venv shell scripts are not passed to shellcheck."""
        seen: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Record commands and return a no-diff success mock."""
            seen.append(cmd)
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            run_shellcheck_fixes(root=sh_files)

        shellcheck_targets = [
            cmd[cmd.index(next(a for a in cmd if a.endswith(".sh")))]
            for cmd in seen
            if "shellcheck" in cmd
        ]
        assert not any(".venv" in t for t in shellcheck_targets)

    def test_applies_diff_when_shellcheck_suggests_fixes(self, sh_files: Path) -> None:
        """Verify git apply is called when shellcheck produces a diff."""
        diff_output = "--- a/deploy/start.sh\n+++ b/deploy/start.sh\n@@ ...\n"
        apply_calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Return a diff for shellcheck calls and record git apply calls."""
            if "shellcheck" in cmd:
                return mock.Mock(returncode=1, stdout=diff_output)
            if "apply" in cmd:
                apply_calls.append(cmd)
                return mock.Mock(returncode=0, stdout="")
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            run_shellcheck_fixes(root=sh_files)

        assert len(apply_calls) > 0

    def test_skips_git_apply_when_no_diff(self, sh_files: Path) -> None:
        """Verify git apply is not called when shellcheck finds nothing to fix."""
        apply_calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Return empty stdout for shellcheck and record any git apply calls."""
            if "shellcheck" in cmd:
                return mock.Mock(returncode=0, stdout="")
            if "apply" in cmd:
                apply_calls.append(cmd)
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            run_shellcheck_fixes(root=sh_files)

        assert apply_calls == []

    def test_shellcheck_uses_root_relative_path_and_cwd(self, sh_files: Path) -> None:
        """Verify shellcheck receives root-relative paths and runs with cwd=root."""
        seen: list[tuple[list[str], Path | None]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Record shellcheck invocations including cwd."""
            if "shellcheck" in cmd:
                seen.append((cmd, kwargs.get("cwd")))
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            run_shellcheck_fixes(root=sh_files)

        assert seen, "shellcheck was never called"
        for cmd, cwd in seen:
            target = cmd[-1]
            assert not target.startswith("/"), f"expected relative path, got {target!r}"
            assert cwd == sh_files

    def test_git_apply_uses_p1_and_cwd(self, sh_files: Path) -> None:
        """Verify git apply uses -p1 to strip shellcheck's a/b/ prefixes."""
        diff_output = (
            "--- a/deploy/start.sh\n+++ b/deploy/start.sh\n"
            "@@ -1 +1 @@\n-echo hello\n+echo hello\n"
        )
        apply_invocations: list[tuple[list[str], Path | None]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Return a diff for shellcheck and capture git apply invocations."""
            if "shellcheck" in cmd:
                return mock.Mock(returncode=1, stdout=diff_output)
            if "apply" in cmd:
                apply_invocations.append((cmd, kwargs.get("cwd")))
                return mock.Mock(returncode=0, stdout="")
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            run_shellcheck_fixes(root=sh_files)

        assert apply_invocations, "git apply was never called"
        for cmd, cwd in apply_invocations:
            assert "-p1" in cmd
            assert cwd == sh_files

    def test_reports_and_fails_on_unfixable_shellcheck_issues(
        self, sh_files: Path
    ) -> None:
        """Verify unfixable shellcheck issues cause nonzero exit and a plain verify run.

        The final plain shellcheck always runs against all files after the diff loop.
        """
        calls: list[list[str]] = []

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Return exit 1 with no diff for shellcheck -f diff; record all calls."""
            calls.append(cmd)
            if "shellcheck" in cmd and "-f" in cmd:
                return mock.Mock(returncode=1, stdout="")
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            result = run_shellcheck_fixes(root=sh_files)

        assert result == 1
        # plain shellcheck (without -f diff) is always run at the end for all files
        assert any("shellcheck" in c and "-f" not in c for c in calls)

    def test_returns_zero_when_all_pass(self, sh_files: Path) -> None:
        """Verify zero is returned when shellcheck reports no issues."""
        with mock.patch("scripts.auto_fix.subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(returncode=0, stdout="")
            assert run_shellcheck_fixes(root=sh_files) == 0

    def test_returns_nonzero_on_shellcheck_error(self, sh_files: Path) -> None:
        """Verify exit code >1 from shellcheck (not a lint warning) propagates."""

        def fake_run(cmd: list[str], **kwargs: object) -> mock.Mock:
            """Return exit code 2 for shellcheck to simulate a tool error."""
            if "shellcheck" in cmd:
                return mock.Mock(returncode=2, stdout="")
            return mock.Mock(returncode=0, stdout="")

        with mock.patch("scripts.auto_fix.subprocess.run", side_effect=fake_run):
            result = run_shellcheck_fixes(root=sh_files)

        assert result != 0


class TestMain:
    """Tests for main entry point."""

    def test_returns_zero_when_all_fixers_pass(self) -> None:
        """Verify zero is returned when all fixers succeed."""
        with (
            mock.patch("scripts.auto_fix.run_ruff_fixes", return_value=0),
            mock.patch("scripts.auto_fix.run_shellcheck_fixes", return_value=0),
        ):
            assert main() == 0

    def test_returns_nonzero_when_any_fixer_fails(self) -> None:
        """Verify nonzero is returned when any fixer fails."""
        with (
            mock.patch("scripts.auto_fix.run_ruff_fixes", return_value=0),
            mock.patch("scripts.auto_fix.run_shellcheck_fixes", return_value=1),
        ):
            assert main() != 0

    def test_runs_all_fixers_even_if_one_fails(self) -> None:
        """Verify shellcheck fixer runs even when ruff fixer fails."""
        shellcheck_called: list[bool] = []
        with (
            mock.patch("scripts.auto_fix.run_ruff_fixes", return_value=1),
            mock.patch(
                "scripts.auto_fix.run_shellcheck_fixes",
                side_effect=lambda *args, **kw: shellcheck_called.append(True) or 0,
            ),
        ):
            main()
        assert shellcheck_called
