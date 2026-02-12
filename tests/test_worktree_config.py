"""Tests for worktree path template expansion."""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_config():
    """Fixture to mock CONFIG dictionary."""
    return {}


class TestWorktreePathTemplate:
    """Test worktree path template expansion."""

    def test_expand_template_with_repo_name(self):
        """Test ${repo_name} variable expansion."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "/tmp/worktrees/${repo_name}",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        assert result == Path("/tmp/worktrees/my-repo")

    def test_expand_template_with_branch_name(self):
        """Test ${branch_name} variable expansion."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "/tmp/worktrees/${branch_name}",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        assert result == Path("/tmp/worktrees/test-feature")

    def test_expand_template_with_feature_name(self):
        """Test ${feature_name} alias expansion."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "/tmp/worktrees/${feature_name}",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        assert result == Path("/tmp/worktrees/test-feature")

    def test_expand_template_with_home(self):
        """Test $HOME variable expansion."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "$HOME/worktrees/test",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        assert result == Path.home() / "worktrees" / "test"

    def test_expand_template_with_tilde(self):
        """Test ~ expansion."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "~/worktrees/test",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        assert result == Path.home() / "worktrees" / "test"

    def test_expand_template_combined(self):
        """Test combined template with multiple variables."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "$HOME/code/worktrees/${repo_name}/${branch_name}",
            repo_name="my-repo",
            feature_name="test-feature",
        )
        expected = Path.home() / "code" / "worktrees" / "my-repo" / "test-feature"
        assert result == expected

    def test_expand_template_with_spaces_in_names(self):
        """Test handling of spaces in repo/branch names."""
        from claudechic.features.worktree.git import _expand_worktree_path

        result = _expand_worktree_path(
            "/tmp/${repo_name}/${branch_name}",
            repo_name="my repo",
            feature_name="test feature",
        )
        assert result == Path("/tmp/my repo/test feature")


class TestStartWorktreeWithConfig:
    """Test start_worktree() with path_template config."""

    @patch("claudechic.features.worktree.git.subprocess.run")
    @patch("claudechic.features.worktree.git.get_repo_name")
    @patch("claudechic.features.worktree.git.get_main_worktree")
    def test_uses_custom_template_when_configured(
        self, mock_get_main, mock_get_repo, mock_run, tmp_path
    ):
        """Test that custom path template is used when configured."""
        from claudechic.features.worktree.git import start_worktree

        mock_get_repo.return_value = "test-repo"
        mock_get_main.return_value = (Path("/original/test-repo"), "main")

        # Use tmp_path for testing
        template = f"{tmp_path}/worktrees/${{repo_name}}/${{branch_name}}"

        with patch("claudechic.config.CONFIG", {"worktree": {"path_template": template}}):
            success, message, path = start_worktree("test-feature")

        expected_path = tmp_path / "worktrees" / "test-repo" / "test-feature"
        assert success
        assert path == expected_path
        assert "Created worktree at" in message
        mock_run.assert_called_once()

    @patch("claudechic.features.worktree.git.subprocess.run")
    @patch("claudechic.features.worktree.git.get_repo_name")
    @patch("claudechic.features.worktree.git.get_main_worktree")
    def test_uses_sibling_behavior_when_template_is_null(
        self, mock_get_main, mock_get_repo, mock_run
    ):
        """Test that sibling behavior is preserved when path_template is null."""
        from claudechic.features.worktree.git import start_worktree

        mock_get_repo.return_value = "test-repo"
        main_worktree_path = Path("/original/test-repo")
        mock_get_main.return_value = (main_worktree_path, "main")

        with patch("claudechic.config.CONFIG", {"worktree": {"path_template": None}}):
            success, message, path = start_worktree("test-feature")

        expected_path = Path("/original/test-repo-test-feature")
        if not success:
            print(f"Failed: {message}")
        assert success, f"Expected success but got failure: {message}"
        assert path == expected_path
        mock_run.assert_called_once()

    @patch("claudechic.features.worktree.git.subprocess.run")
    @patch("claudechic.features.worktree.git.get_repo_name")
    @patch("claudechic.features.worktree.git.get_main_worktree")
    def test_uses_sibling_behavior_when_config_missing(
        self, mock_get_main, mock_get_repo, mock_run
    ):
        """Test that sibling behavior is preserved when worktree config is missing."""
        from claudechic.features.worktree.git import start_worktree

        mock_get_repo.return_value = "test-repo"
        main_worktree_path = Path("/original/test-repo")
        mock_get_main.return_value = (main_worktree_path, "main")

        with patch("claudechic.config.CONFIG", {}):
            success, message, path = start_worktree("test-feature")

        expected_path = Path("/original/test-repo-test-feature")
        assert success
        assert path == expected_path
        mock_run.assert_called_once()

    @patch("claudechic.features.worktree.git.subprocess.run")
    @patch("claudechic.features.worktree.git.get_repo_name")
    @patch("claudechic.features.worktree.git.get_main_worktree")
    def test_creates_parent_directories_for_custom_path(
        self, mock_get_main, mock_get_repo, mock_run, tmp_path
    ):
        """Test that parent directories are created for custom paths."""
        from claudechic.features.worktree.git import start_worktree

        mock_get_repo.return_value = "test-repo"
        mock_get_main.return_value = (Path("/original/test-repo"), "main")

        # Use a nested path that doesn't exist
        template = f"{tmp_path}/deep/nested/path/${{repo_name}}/${{branch_name}}"

        with patch("claudechic.config.CONFIG", {"worktree": {"path_template": template}}):
            success, message, path = start_worktree("test-feature")

        expected_path = tmp_path / "deep" / "nested" / "path" / "test-repo" / "test-feature"
        assert success
        assert path == expected_path
        # Verify parent directories were created
        assert expected_path.parent.exists()
