# Roadmap (proposals, not shipped features)

- v0.2 (shipped): **geometric** EasyEDA Pro pin-to-wire evidence, net-label extraction, cautious crossing handling, and synthetic tests. This is not authoritative schematic net connectivity or ERC.
- v0.3 (shipped): import and compare the official EasyEDA-exported `.enet` electrical netlist so actual pin/net assignments can be verified without relying on geometry alone.
- v0.4 (shipped, limited): fabrication ZIP category audit and BOM/placement CSV reference comparison. Actual board-edge reconstruction and mechanical clearance checks are NOT shipped.
- v0.5 (planned): structured KiCad CLI JSON report import and issue classification.
- v0.6 (planned): detailed drill/CAM geometry checks using appropriate format parsers, user-provided fab rules, and assembly centroid semantics.
- v0.7 (planned): automated regression tests for approved, permission-cleared hardware example projects.

**All validation must remain clearly separated from certification or physical testing.**