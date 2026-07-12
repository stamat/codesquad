"""`squad init` scaffolding + .env merge (append missing keys, never clobber values)."""

from typer.testing import CliRunner

from codesquad.cli import app, merge_env
from codesquad.config import load_config

runner = CliRunner()

TEMPLATE_ENV = "OPENAI_API_KEY=\nGEMINI_API_KEY=\nANTHROPIC_API_KEY=\n"


def test_merge_env_adds_missing_preserves_existing():
    merged, added = merge_env("OPENAI_API_KEY=sk-secret\n", TEMPLATE_ENV)
    assert added == ["GEMINI_API_KEY", "ANTHROPIC_API_KEY"]
    assert "OPENAI_API_KEY=sk-secret" in merged        # existing value untouched
    assert merged.count("OPENAI_API_KEY") == 1          # not duplicated
    assert "GEMINI_API_KEY=" in merged


def test_merge_env_noop_when_all_present():
    existing = "OPENAI_API_KEY=x\nGEMINI_API_KEY=y\nANTHROPIC_API_KEY=z\n"
    merged, added = merge_env(existing, TEMPLATE_ENV)
    assert added == [] and merged == existing


def test_init_scaffolds_loadable_project(tmp_path):
    res = runner.invoke(app, ["init", str(tmp_path)])
    assert res.exit_code == 0, res.output
    assert (tmp_path / "codesquad.yaml").exists()
    assert (tmp_path / ".env").exists()
    assert list((tmp_path / "prompts").glob("*.md"))
    load_config(tmp_path / "codesquad.yaml")            # scaffold loads clean (prompts resolve)


def test_init_does_not_clobber_config_without_force(tmp_path):
    (tmp_path / "codesquad.yaml").write_text("roles: {}\n")
    runner.invoke(app, ["init", str(tmp_path)])
    assert (tmp_path / "codesquad.yaml").read_text() == "roles: {}\n"


def test_init_force_overwrites(tmp_path):
    (tmp_path / "codesquad.yaml").write_text("roles: {}\n")
    runner.invoke(app, ["init", str(tmp_path), "--force"])
    assert (tmp_path / "codesquad.yaml").read_text() != "roles: {}\n"


def test_init_appends_missing_env_keys(tmp_path):
    (tmp_path / ".env").write_text("OPENAI_API_KEY=keep\n")
    runner.invoke(app, ["init", str(tmp_path)])
    txt = (tmp_path / ".env").read_text()
    assert "OPENAI_API_KEY=keep" in txt and "GEMINI_API_KEY=" in txt
