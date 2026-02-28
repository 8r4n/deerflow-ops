# Contract tests — <skill-name>
#
# Minimum contract per the skill standard:
#   1. The server starts
#   2. Each tool endpoint can be invoked with a minimal request
#   3. Invalid input produces an expected error
#
# Run:  pytest tests/ -v
#       (or via Makefile: make test)

def test_skill_yaml_exists():
    """skill.yaml manifest must be present."""
    from pathlib import Path

    manifest = Path(__file__).resolve().parent.parent / "skill.yaml"
    assert manifest.exists(), "skill.yaml not found in skill root"


def test_dockerfile_exists():
    """Dockerfile must be present."""
    from pathlib import Path

    dockerfile = Path(__file__).resolve().parent.parent / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile not found in skill root"


def test_readme_exists():
    """README.md must be present."""
    from pathlib import Path

    readme = Path(__file__).resolve().parent.parent / "README.md"
    assert readme.exists(), "README.md not found in skill root"


def test_skill_yaml_has_required_fields():
    """skill.yaml must contain name, version, and tools fields."""
    from pathlib import Path

    try:
        import yaml
    except ImportError:
        # Fall back to basic string checks if PyYAML is not installed
        content = (
            Path(__file__).resolve().parent.parent / "skill.yaml"
        ).read_text()
        assert "name:" in content, "skill.yaml missing 'name' field"
        assert "version:" in content, "skill.yaml missing 'version' field"
        assert "tools:" in content, "skill.yaml missing 'tools' field"
        return

    manifest = Path(__file__).resolve().parent.parent / "skill.yaml"
    with open(manifest) as f:
        data = yaml.safe_load(f)

    assert "name" in data, "skill.yaml missing 'name' field"
    assert "version" in data, "skill.yaml missing 'version' field"
    assert "tools" in data, "skill.yaml missing 'tools' field"
