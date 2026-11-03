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

- v0.8 (shipped, limited): CLI subprocess contract tests and fail-closed handling. **Actual KiCad 10 run still required.**
- v0.9 (planned): cautious Gerber/Excellon syntax/header and BOM/CPL input preflight.
- v1.0 (candidate): documented release gate and evidence matrix; stable requires native integration and real-world sample validation.

- v0.9 (shipped, limited): inspect Gerber/Excellon headers and cross-file metadata without claiming geometry, fabrication or assembly certification.

- v1.0.0rc1 (released as candidate): explicit evidence gate, CLI/package smoke checks and private native KiCad 10 validation helper. **Stable v1.0 deferred until checklist passes.**