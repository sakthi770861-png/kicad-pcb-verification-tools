# Roadmap (proposals, not shipped features)

- v0.2 (shipped): **geometric** EasyEDA Pro pin-to-wire evidence, net-label extraction, cautious crossing handling, and synthetic tests. This is not authoritative schematic net connectivity or ERC.
- v0.3 (shipped): import and compare the official EasyEDA-exported `.enet` electrical netlist so actual pin/net assignments can be verified without relying on geometry alone.
- v0.4 (shipped, limited): fabrication ZIP category audit and BOM/placement CSV reference comparison. Actual board-edge reconstruction and mechanical clearance checks are NOT shipped.
- v0.6 (shipped): structured KiCad CLI JSON severity/issue summaries, excluding native command integration testing without KiCad executable.
- v0.6 (planned): detailed drill/CAM geometry checks using appropriate format parsers, user-provided fab rules, and assembly centroid semantics.
- v0.7 (shipped): automated evidence-baseline regression command with generated, permission-safe **synthetic** EasyEDA/netlist/fabrication examples; real approved public hardware reference designs remain future work.
- v0.8 (planned): test and review actual exported `.enet` and KiCad 10 native ERC/DRC on permission-cleared representative designs; no stable release without real toolchain evidence.

**All validation must remain clearly separated from certification or physical testing.**

- v0.5 (shipped): combined project evidence report, with explicit missing and nonzero checks.
- Future work: rigorous outline/mechanical clearance, parsed Gerber/Excellon geometry, BOM/CPL orientation and supplier-part verification, native KiCad issue classification, real representative permitted fixtures, field validation and release review before any v1.0 stable claim.

- v0.6 (shipped): KiCad CLI JSON ERC/DRC issue summary, including PCB unconnected and parity categories.