"""Basic tests for ELDA config and board conflicts."""

from pathlib import Path

from elda.config import EldaConfig
from elda.executor.board_conflicts import check_board_conflicts


def test_elda_config_roundtrip(tmp_path: Path) -> None:
    cfg = EldaConfig(
        project={"name": "test", "output_dir": "output", "api_url": "http://localhost:8000"},
        target={
            "soc": "imx6ull",
            "arch": "arm",
            "kernel_version": "4.1.15",
            "kernel_source": "/tmp/linux",
            "cross_compile": "arm-linux-gnueabihf-",
        },
        peripherals=[
            {
                "id": "imu0",
                "name": "my_sensor",
                "enabled": True,
                "bus": "spi",
                "board": {
                    "spi": {"bus_id": 3, "cs_gpio": "GPIO1_IO20", "mode": 0, "max_frequency": 10000000},
                    "gpios": {"irq": "GPIO1_IO19"},
                },
            }
        ],
    )
    path = tmp_path / "elda.yaml"
    cfg.save(path)
    loaded = EldaConfig.load(path)
    assert loaded.project.name == "test"
    assert len(loaded.enabled_peripherals()) == 1


def test_board_cs_conflict() -> None:
    cfg = EldaConfig(
        project={"name": "t", "output_dir": "o", "api_url": "http://x"},
        target={
            "soc": "x",
            "arch": "arm",
            "kernel_version": "1",
            "kernel_source": "/k",
            "cross_compile": "arm-",
        },
        peripherals=[
            {
                "id": "a",
                "name": "s1",
                "enabled": True,
                "bus": "spi",
                "board": {"spi": {"bus_id": 1, "cs_gpio": "CS0", "mode": 0, "max_frequency": 1}},
            },
            {
                "id": "b",
                "name": "s2",
                "enabled": True,
                "bus": "spi",
                "board": {"spi": {"bus_id": 1, "cs_gpio": "CS0", "mode": 0, "max_frequency": 2}},
            },
        ],
    )
    report = check_board_conflicts(cfg)
    assert any(c.severity == "error" for c in report.conflicts)
