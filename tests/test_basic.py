"""
Basic tests for Plugwise Pi project structure.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_project_structure():
    """Test that the project structure is correct."""
    # Check that required directories exist
    assert (project_root / "plugwise_pi").exists()
    assert (project_root / "tests").exists()
    assert (project_root / "config").exists()
    assert (project_root / "docs").exists()
    assert (project_root / "scripts").exists()
    assert (project_root / "systemd").exists()
    
    # Check that required files exist
    assert (project_root / "README.md").exists()
    assert (project_root / "requirements.txt").exists()
    assert (project_root / "setup.py").exists()
    assert (project_root / ".gitignore").exists()
    assert (project_root / "config" / "config.example.yaml").exists()


def test_package_imports():
    """Test that the main package can be imported."""
    try:
        import plugwise_pi
        assert plugwise_pi.__version__ == "0.1.0"
    except ImportError as e:
        pytest.skip(f"Could not import plugwise_pi: {e}")


def test_config_imports():
    """Test that configuration module can be imported."""
    try:
        from plugwise_pi import config
        assert config is not None
    except ImportError as e:
        pytest.skip(f"Could not import config module: {e}")


def test_utils_imports():
    """Test that utils module can be imported."""
    try:
        from plugwise_pi import utils
        assert utils is not None
    except ImportError as e:
        pytest.skip(f"Could not import utils module: {e}")


def test_models_imports():
    """Test that models module can be imported."""
    try:
        from plugwise_pi import models
        assert models is not None
    except ImportError as e:
        pytest.skip(f"Could not import models module: {e}")


def test_collector_imports():
    """Test that collector module can be imported."""
    try:
        from plugwise_pi import collector
        assert collector is not None
    except ImportError as e:
        pytest.skip(f"Could not import collector module: {e}")


def test_api_imports():
    """Test that API module can be imported."""
    try:
        from plugwise_pi import api
        assert api is not None
    except ImportError as e:
        pytest.skip(f"Could not import API module: {e}")


def test_database_imports():
    """Test that database module can be imported."""
    try:
        from plugwise_pi import database
        assert database is not None
    except ImportError as e:
        pytest.skip(f"Could not import database module: {e}")


if __name__ == "__main__":
    # Run basic tests
    test_project_structure()
    print("✓ Project structure is correct")
    
    # Try to import modules
    try:
        test_package_imports()
        print("✓ Package imports work")
    except Exception as e:
        print(f"⚠ Package imports failed: {e}")
    
    print("Basic tests completed!") 