"""Driver module path resolution."""

import json

from elda.config import EldaConfig
from elda.driver_paths import (
    driver_module_paths_from_config,
    resolve_driver_module_paths,
    resolve_peripheral_module_path,
)


def test_resolve_from_framework():
    from elda.config import PeripheralConfig

    p = PeripheralConfig(id="a", name="s", bus="spi", driver_framework="iio")
    assert resolve_peripheral_module_path(p) == "drivers/iio"


def test_resolve_explicit_path():
    from elda.config import PeripheralConfig

    p = PeripheralConfig(
        id="a", name="s", bus="spi", driver_framework="iio", driver_module_path="drivers/iio/imu"
    )
    assert resolve_peripheral_module_path(p) == "drivers/iio/imu"


def test_manifest_overrides_config(tmp_path):
    cfg = EldaConfig(
        project={"name": "t", "output_dir": "o", "api_url": "http://x"},
        target={
            "soc": "x", "arch": "arm", "kernel_version": "1",
            "kernel_source": "/k", "cross_compile": "arm-",
        },
        peripherals=[
            {"id": "a", "name": "s", "enabled": True, "bus": "spi", "driver_framework": "iio"},
        ],
    )
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "driver_manifest.json").write_text(
        json.dumps({"module_paths": ["drivers/iio/custom"]}), encoding="utf-8"
    )
    assert resolve_driver_module_paths(cfg, tmp_path) == ["drivers/iio/custom"]


def test_config_paths_without_manifest(tmp_path):
    cfg = EldaConfig(
        project={"name": "t", "output_dir": "o", "api_url": "http://x"},
        target={
            "soc": "x", "arch": "arm", "kernel_version": "1",
            "kernel_source": "/k", "cross_compile": "arm-",
        },
        peripherals=[
            {
                "id": "a", "name": "s", "enabled": True, "bus": "spi",
                "driver_framework": "hwmon", "driver_module_path": "drivers/hwmon",
            },
        ],
    )
    assert driver_module_paths_from_config(cfg) == ["drivers/hwmon"]
