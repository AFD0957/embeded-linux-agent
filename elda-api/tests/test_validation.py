"""Schema validation tests."""

import pytest

pytest.importorskip("jsonschema")
from jsonschema import ValidationError

from app.validation.schemas import (
    extract_kernel_paths_from_diff,
    infer_module_paths_from_patches,
    validate_fix_patch,
    validate_patch_envelope,
)


def test_validate_patch_envelope_ok():
    data = {
        "version": "1",
        "patches": [
            {
                "id": "p1",
                "unified_diff": "--- a/drivers/iio/foo.c\n+++ b/drivers/iio/foo.c\n@@ -1 +1 @@\n",
                "rationale": "init",
            }
        ],
    }
    patches = validate_patch_envelope(data)
    assert len(patches) == 1
    assert patches[0]["id"] == "p1"


def test_validate_patch_envelope_rejects_empty_diff():
    with pytest.raises(ValidationError):
        validate_patch_envelope({"version": "1", "patches": [{"id": "x", "unified_diff": ""}]})


def test_validate_fix_patch():
    p = validate_fix_patch({"id": "f1", "unified_diff": "--- a/x.c\n+++ b/x.c\n@@\n", "rationale": "fix"})
    assert p["id"] == "f1"


def test_infer_module_paths():
    patches = [
        {
            "id": "p1",
            "unified_diff": "--- a/drivers/iio/sensor.c\n+++ b/drivers/iio/sensor.c\n@@\n",
        }
    ]
    assert infer_module_paths_from_patches(patches) == ["drivers/iio"]


def test_extract_paths():
    diff = "--- a/drivers/spi/spi-x.c\n+++ b/drivers/spi/spi-x.c\n"
    assert extract_kernel_paths_from_diff(diff) == ["drivers/spi/spi-x.c"]
