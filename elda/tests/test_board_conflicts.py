"""Board conflict policy tests."""

from elda.config import EldaConfig
from elda.executor.board_conflicts import check_board_conflicts


def test_hard_cs_conflict():
    cfg = EldaConfig(
        project={"name": "t", "output_dir": "o", "api_url": "http://x"},
        target={
            "soc": "x", "arch": "arm", "kernel_version": "1",
            "kernel_source": "/k", "cross_compile": "arm-",
        },
        peripherals=[
            {
                "id": "a", "name": "s1", "enabled": True, "bus": "spi",
                "board": {"spi": {"bus_id": 1, "cs_gpio": "CS0", "mode": 0, "max_frequency": 1}},
            },
            {
                "id": "b", "name": "s2", "enabled": True, "bus": "spi",
                "board": {"spi": {"bus_id": 1, "cs_gpio": "CS0", "mode": 0, "max_frequency": 1}},
            },
        ],
    )
    report = check_board_conflicts(cfg)
    assert report.has_hard_errors


def test_soft_irq_warning_only():
    cfg = EldaConfig(
        project={"name": "t", "output_dir": "o", "api_url": "http://x"},
        target={
            "soc": "x", "arch": "arm", "kernel_version": "1",
            "kernel_source": "/k", "cross_compile": "arm-",
        },
        peripherals=[
            {
                "id": "a", "name": "s1", "enabled": True, "bus": "spi",
                "board": {
                    "spi": {"bus_id": 1, "cs_gpio": "CS0", "mode": 0, "max_frequency": 1},
                    "gpios": {"irq": "GPIO1"},
                },
            },
            {
                "id": "b", "name": "s2", "enabled": True, "bus": "spi",
                "board": {
                    "spi": {"bus_id": 1, "cs_gpio": "CS1", "mode": 0, "max_frequency": 1},
                    "gpios": {"irq": "GPIO1"},
                },
            },
        ],
    )
    report = check_board_conflicts(cfg)
    assert not report.has_hard_errors
    assert any(c.severity == "warning" for c in report.conflicts)
