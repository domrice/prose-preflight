"""Guards the silent failure: default.yaml not shipping in the wheel, so uvx
installs fine and dies on first run."""

import subprocess

import yaml

from prose_preflight.run_all import DEFAULT_CONFIG


def test_bundled_config_resolves_and_parses():
    assert isinstance(yaml.safe_load(DEFAULT_CONFIG.read_text()), dict)


def test_console_script_is_wired():
    assert subprocess.run(["prose-preflight", "--help"], check=False).returncode == 0
