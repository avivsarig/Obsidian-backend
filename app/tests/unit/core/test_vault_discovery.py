import tempfile
from pathlib import Path

import pytest


class TestVaultDiscoveryAlgorithm:
    """Test the vault discovery algorithm used in Settings._discover_vault_path()."""

    def _create_algorithm_function(self):
        """Extract the vault discovery algorithm for isolated testing."""

        def vault_discovery_algorithm(start_path: Path) -> Path:
            """Isolated implementation of the vault discovery algorithm."""
            current = start_path
            while current != current.parent:
                if (current / "pyproject.toml").exists() or (current / ".git").exists():
                    vault_path = current.parent / "vault"
                    if vault_path.exists():
                        return vault_path
                    break
                current = current.parent
            raise ValueError("Vault not found. Set VAULT_PATH environment variable.")

        return vault_discovery_algorithm

    def test_finds_vault_with_pyproject_toml(self):
        """Test algorithm finds vault when pyproject.toml exists."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create project structure
            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            # Add pyproject.toml marker
            (project_root / "pyproject.toml").write_text("[tool.poetry]")

            # Add vault directory
            vault_path = temp_path / "vault"
            vault_path.mkdir()

            result = vault_discovery_algorithm(config_dir)
            assert result == vault_path

    def test_finds_vault_with_git_directory(self):
        """Test algorithm finds vault when .git directory exists."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            # Add .git marker instead of pyproject.toml
            (project_root / ".git").mkdir()

            vault_path = temp_path / "vault"
            vault_path.mkdir()

            result = vault_discovery_algorithm(config_dir)
            assert result == vault_path

    def test_handles_both_markers(self):
        """Test algorithm when both pyproject.toml and .git exist."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            # Add both markers
            (project_root / "pyproject.toml").write_text("[tool.poetry]")
            (project_root / ".git").mkdir()

            vault_path = temp_path / "vault"
            vault_path.mkdir()

            result = vault_discovery_algorithm(config_dir)
            assert result == vault_path

    def test_marker_exists_but_no_vault(self):
        """Test algorithm when project marker exists but vault doesn't."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            # Add marker but no vault
            (project_root / "pyproject.toml").write_text("[tool.poetry]")

            with pytest.raises(ValueError, match="Vault not found"):
                vault_discovery_algorithm(config_dir)

    def test_no_project_markers(self):
        """Test algorithm when no project markers are found."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create structure without any markers
            config_dir = temp_path / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            with pytest.raises(ValueError, match="Vault not found"):
                vault_discovery_algorithm(config_dir)

    def test_multiple_directory_levels(self):
        """Test algorithm traverses multiple directory levels."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create deeply nested structure
            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core" / "submodule" / "deep"
            config_dir.mkdir(parents=True)

            (project_root / "pyproject.toml").write_text("[tool.poetry]")

            vault_path = temp_path / "vault"
            vault_path.mkdir()

            result = vault_discovery_algorithm(config_dir)
            assert result == vault_path

    def test_break_behavior_when_marker_found(self):
        """Test that algorithm breaks when marker found but vault doesn't exist."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create structure where marker exists but no vault at expected location
            project_root = temp_path / "project"
            project_root.mkdir()
            config_dir = project_root / "app" / "src" / "core"
            config_dir.mkdir(parents=True)

            # Marker in project but no vault at project.parent/vault
            (project_root / "pyproject.toml").write_text("[tool.poetry]")

            # Create vault at different location that shouldn't be found
            other_dir = temp_path / "other"
            other_dir.mkdir()
            (other_dir / "vault").mkdir()

            # Algorithm should break at project level and not find other vault
            with pytest.raises(ValueError, match="Vault not found"):
                vault_discovery_algorithm(config_dir)

    def test_loop_termination_at_root(self):
        """Test that algorithm terminates when reaching filesystem root."""
        vault_discovery_algorithm = self._create_algorithm_function()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Very shallow structure
            config_dir = temp_path / "config"
            config_dir.mkdir()

            with pytest.raises(ValueError, match="Vault not found"):
                vault_discovery_algorithm(config_dir)


class TestVaultDiscoveryEdgeCases:
    """Test edge cases for vault discovery algorithm."""

    def test_marker_at_start_location(self):
        """Test when project marker is in the starting directory itself."""
        vault_discovery_algorithm = (
            TestVaultDiscoveryAlgorithm()._create_algorithm_function()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Put marker directly in the config directory
            config_dir = temp_path / "config"
            config_dir.mkdir()
            (config_dir / "pyproject.toml").write_text("[tool.poetry]")

            # Vault should be one level up
            vault_path = temp_path / "vault"
            vault_path.mkdir()

            result = vault_discovery_algorithm(config_dir)
            assert result == vault_path

    def test_realistic_project_structure(self):
        """Test with complex realistic directory structure."""
        vault_discovery_algorithm = (
            TestVaultDiscoveryAlgorithm()._create_algorithm_function()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Simulate realistic Python project
            project_root = temp_path / "obsidian-backend"
            project_root.mkdir()

            # Create typical directories
            (project_root / "app").mkdir()
            (project_root / "app" / "src").mkdir()
            (project_root / "app" / "src" / "core").mkdir()
            (project_root / "app" / "src" / "domain").mkdir()
            (project_root / "app" / "tests").mkdir()

            config_location = project_root / "app" / "src" / "core"

            # Add project marker
            (project_root / "pyproject.toml").write_text(
                """
[tool.poetry]
name = "obsidian-backend"
version = "0.1.0"
"""
            )

            # Add vault with Obsidian structure
            vault_path = temp_path / "vault"
            vault_path.mkdir()
            (vault_path / "Tasks").mkdir()
            (vault_path / "Tasks" / "Completed").mkdir()
            (vault_path / "Knowledge Archive").mkdir()

            result = vault_discovery_algorithm(config_location)

            assert result == vault_path
            assert (result / "Tasks").exists()
            assert (result / "Tasks" / "Completed").exists()
            assert (result / "Knowledge Archive").exists()
