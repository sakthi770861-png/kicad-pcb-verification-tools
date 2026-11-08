# Roadmap and release evidence

This roadmap distinguishes **shipped functionality**, **limited functionality**, and **unverified release requirements**. A successful command or a synthetic fixture is not a manufacturing certification.

## Shipped

- v0.2: Informational EasyEDA Pro pin-to-wire geometry, label extraction, and cautious crossing handling.
- v0.3: Comparison with exported EasyEDA `.enet` electrical netlists.
- v0.4 (limited): Fabrication ZIP inventory and BOM/placement reference comparison; no mechanical clearance certification.
- v0.5: Combined project evidence report that records missing and nonzero checks.
- v0.6: Structured KiCad CLI ERC/DRC JSON issue summaries.
- v0.7: Reproducible synthetic evidence-baseline regression fixtures and tests.
- v0.8 (limited): CLI subprocess contract tests and fail-closed handling; not proof of a native KiCad 10 run.
- v0.9 (limited): Gerber/Excellon header and metadata preflight, not geometry verification.
- v1.0.0rc1: Release candidate with documentation, evidence gate, and installation smoke checks. **Not a stable release.**

## Before a stable release

1. Run and record the full unit-test matrix, including Python 3.10, 3.12, and 3.13.
2. Run the actual supported KiCad CLI against permission-cleared, representative KiCad schematic and PCB fixtures; capture the exact KiCad version, commands, exit codes, and ERC/DRC reports.
3. Test representative EasyEDA `.epro2` and `.enet` files with permission to publish or clearly document private test evidence without disclosing confidential designs.
4. Review and resolve CI failures, packaging/install smoke tests, and any discrepancy between the documented and actual CLI behavior.
5. Record release evidence and known limitations before tagging a stable version.

## Future work

- Rigorous board outline and mechanical clearance checks.
- Parsed Gerber/Excellon geometry and user-defined fabrication constraints.
- Assembly centroid, orientation, BOM/CPL, and supplier-part verification.
- Broader native KiCad issue classification and representative fixture coverage.

## Safety boundary

Structural inspection, netlist comparison, CAM header inspection, and even a completed native ERC/DRC **do not** establish electrical safety, thermal performance, manufacturing readiness, USB-C compliance, or physical validation. Keep private client designs and other sensitive data out of public test fixtures.
