"""elda.yaml validation beyond Pydantic."""

from __future__ import annotations

from pathlib import Path

from elda.config import EldaConfig


class ConfigValidationError(Exception):
    pass


def validate_project_config(cfg: EldaConfig) -> list[str]:
    issues: list[str] = []
    kernel = cfg.kernel_source_path
    if not kernel.is_dir():
        issues.append(f"kernel_source not found: {kernel}")
    elif not (kernel / ".git").is_dir():
        issues.append(f"kernel_source is not a git repo: {kernel}")

    if not cfg.enabled_peripherals():
        issues.append("no enabled peripherals in elda.yaml")

    for p in cfg.enabled_peripherals():
        if p.datasheet and not Path(p.datasheet).is_file():
            issues.append(f"peripheral {p.id}: datasheet not found: {p.datasheet}")

    if cfg.board.dts and not Path(cfg.board.dts).is_file():
        issues.append(f"board.dts not found: {cfg.board.dts}")

    if cfg.deploy.tftp and not Path(cfg.deploy.tftp.directory).parent.exists():
        issues.append(f"tftp parent path missing: {cfg.deploy.tftp.directory}")

    return issues


def require_valid_config(cfg: EldaConfig) -> None:
    issues = validate_project_config(cfg)
    if issues:
        raise ConfigValidationError("\n".join(f"  - {i}" for i in issues))
