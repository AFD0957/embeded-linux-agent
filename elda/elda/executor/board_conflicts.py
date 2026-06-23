"""Board-level bus/GPIO conflict detection with hard/soft policy."""

from __future__ import annotations

from pydantic import BaseModel, Field

from elda.config import EldaConfig, PeripheralConfig


class ConflictItem(BaseModel):
    severity: str  # error | warning
    peripheral_ids: list[str]
    resource: str
    message: str
    resolution: str | None = None
    auto_resolved: bool = False


class ConflictReport(BaseModel):
    conflicts: list[ConflictItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    resolutions_applied: list[str] = Field(default_factory=list)

    @property
    def has_hard_errors(self) -> bool:
        return any(c.severity == "error" for c in self.conflicts)

    def to_markdown(self) -> str:
        lines = ["# Board Conflict Log", ""]
        if not self.conflicts and not self.warnings:
            lines.append("No conflicts detected.")
            return "\n".join(lines)
        for c in self.conflicts:
            tag = "ERROR" if c.severity == "error" else "WARNING"
            lines.append(f"## [{tag}] {c.resource}")
            lines.append(f"- Peripherals: {', '.join(c.peripheral_ids)}")
            lines.append(f"- {c.message}")
            if c.resolution:
                lines.append(f"- Resolution: {c.resolution}")
            lines.append("")
        for w in self.warnings:
            lines.append(f"- ⚠ {w}")
        return "\n".join(lines)


def check_board_conflicts(cfg: EldaConfig) -> ConflictReport:
    report = ConflictReport()
    enabled = cfg.enabled_peripherals()

    cs_map: dict[str, list[str]] = {}
    irq_map: dict[str, list[str]] = {}
    i2c_addr_map: dict[str, list[str]] = {}

    for p in enabled:
        _collect_spi_cs(p, cs_map)
        _collect_irq(p, irq_map)
        _collect_i2c_addr(p, i2c_addr_map)

    # HARD: duplicate CS on SPI
    for gpio, ids in cs_map.items():
        if len(ids) > 1:
            report.conflicts.append(
                ConflictItem(
                    severity="error",
                    peripheral_ids=ids,
                    resource=f"SPI CS {gpio}",
                    message="Multiple devices share the same chip-select GPIO. Fix elda.yaml.",
                    resolution="Assign unique CS GPIO per device or disable unused peripherals.",
                )
            )

    # SOFT: shared IRQ (warn only)
    for gpio, ids in irq_map.items():
        if len(ids) > 1:
            report.conflicts.append(
                ConflictItem(
                    severity="warning",
                    peripheral_ids=ids,
                    resource=f"IRQ GPIO {gpio}",
                    message="Multiple devices share interrupt GPIO — verify hardware.",
                    resolution="Continue if intentional shared IRQ line.",
                )
            )

    # HARD: duplicate I2C address
    for key, ids in i2c_addr_map.items():
        if len(ids) > 1:
            report.conflicts.append(
                ConflictItem(
                    severity="error",
                    peripheral_ids=ids,
                    resource=f"I2C {key}",
                    message="Duplicate I2C bus/address — fix elda.yaml.",
                    resolution="Use unique address or separate bus.",
                )
            )

    spi_buses: dict[int, list[PeripheralConfig]] = {}
    for p in enabled:
        if p.bus == "spi" and p.board.spi:
            spi_buses.setdefault(p.board.spi.bus_id, []).append(p)

    for bus_id, devices in spi_buses.items():
        freqs = {d.board.spi.max_frequency for d in devices if d.board.spi}
        if len(freqs) > 1:
            report.warnings.append(
                f"SPI bus {bus_id}: devices request different max_frequency {freqs}."
            )

    return report


def _collect_spi_cs(p: PeripheralConfig, cs_map: dict[str, list[str]]) -> None:
    if p.bus == "spi" and p.board.spi:
        cs_map.setdefault(p.board.spi.cs_gpio, []).append(p.id)


def _collect_irq(p: PeripheralConfig, irq_map: dict[str, list[str]]) -> None:
    if p.board.gpios and p.board.gpios.irq:
        irq_map.setdefault(p.board.gpios.irq, []).append(p.id)


def _collect_i2c_addr(p: PeripheralConfig, i2c_addr_map: dict[str, list[str]]) -> None:
    if p.bus == "i2c" and p.board.i2c:
        key = f"bus{p.board.i2c.bus_id}@{p.board.i2c.address}"
        i2c_addr_map.setdefault(key, []).append(p.id)
