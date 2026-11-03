# Roadmap (proposals, not shipped features)

- v0.2 (shipped): **geometric** EasyEDA Pro pin-to-wire evidence, net-label extraction, cautious crossing handling, and synthetic tests. This is not authoritative schematic net connectivity or ERC.
- v0.3 (shipped): import and compare the official EasyEDA-exported `.enet` electrical netlist so actual pin/net assignments can be verified without relying on geometry alone.
- v0.4 (planned): actual board-edge reconstruction and footprint/body-to-outline mechanical clearance checks.
- v0.5 (planned): structured KiCad CLI JSON report import and issue classification.
- v0.6 (planned): export artifact checks for manufacturing (Gerbers, Excellon, centroid and BOM with user-supplied fab rules).
- v0.7 (planned): automated regression tests for approved, permission-cleared hardware example projects.

**All validation must remain clearly separated from certification or physical testing.**