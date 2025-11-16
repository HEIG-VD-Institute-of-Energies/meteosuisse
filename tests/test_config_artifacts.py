from pathlib import Path
from meteosuisse.config import APIConfig


def test_artifacts_dirs_created(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = APIConfig()
    # Ensure each artifacts subdir is created and returned
    assert cfg.artifacts_dir.exists()
    assert cfg.artifacts_logs_dir.exists()
    assert cfg.artifacts_figures_dir.exists()
    assert cfg.artifacts_reports_dir.exists()
    assert cfg.artifacts_outputs_dir.exists()


