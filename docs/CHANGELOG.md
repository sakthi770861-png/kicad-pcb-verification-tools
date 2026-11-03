# Changelog

## v0.7.0 — 2026-11-04

- Added reproducible `regression-check` CLI: compare baseline JSON Pointer values across EasyEDA Pro ZIP, exported `.enet` and manufacturing export-manifest reports.
- Added generator for fully fictional, permission-safe sample archives and baseline; no private project sources are included.
- Failing or missing input results cannot masquerade as a passing regression; CLI exits nonzero on differences.
- Restricts baseline inputs to the manifest directory (including symlink resolution) and caps manifest size and number of cases/assertions.
- Added synthetic behavioral, security and integration tests; release is still not manufacturing approval.

**Limit:** Synthetic manufacturing Gerber placeholders are intentionally invalid CAM files; this feature checks report stability only. KiCad-native real runs and externally approved hardware fixture validation remain outstanding.



## v0.2.0 — 2026-11-03

- Added EasyEDA Pro V3 schematic pin-to-wire geometric evidence using embedded symbol pins.
- Added component rotation, mirror, and placed pin-number override handling.
- Added named wire NET labels, matching-name merging, and endpoint/T wire grouping.
- Marked ambiguous X intersections without silently joining them.
- Added per-pin JSON output and Markdown pin/net evidence tables.
- Added explicit conservative statuses for unsupported symbols and unconnected candidates.
- Ignored historical orphan wire-line geometry when the parent wire was deleted.
- Added 10 synthetic geometry/net tests, bringing standard-library unit tests to 20.
- Updated documentation of limitations and compatibility.
- CI compatibility fix: avoid Python 3.12-only f-string expression syntax in Markdown rendering; add Python 3.10 grammar regression check.

**Not included:** native EasyEDA ERC/DRC, official exported `.enet` netlist verification, real-world current/thermal testing, or manufacturing sign-off.

## v0.1.0 — 2026-11-03

- Initial EasyEDA Pro V3 project inventory, simple component parity, and native KiCad CLI check wrappers.
- Published initial synthetic test suite and GitHub Actions CI.

## v0.3.0 — 2026-11-03

- Added read-only parser for official EasyEDA Pro exported `.enet` JSON netlists (version 2.0.0 schema).
- Added safe input limits, pin and component net inventories, and handling for malformed and duplicate identifiers.
- Added optional cross-check against geometric `.epro2` data from the same intended revision.
- Reports conflicting named nets, geometry-missed connections, and snapshot mismatches as **review findings only**.
- Added synthetic tests for exported-netlist parsing and comparisons.

**Not included:** native EasyEDA ERC/DRC, electrical simulation, or proof that separately exported files represent the same revision. No real user `.enet` was supplied for end-to-end validation.

## v0.4.0 — 2026-11-03

- Added `manufacturing-audit` read-only ZIP manifest command.
- Detects common Gerber layer categories, board-edge files, and Excellon drill files by filename only.
- Optional `--assembly` presence checks for BOM and placement CSVs.
- Best-effort CSV header parsing and BOM/CPL reference-designator comparison with advisory mismatches.
- Includes tests for missing categories, legacy suffixes, invalid/path-traversal ZIPs, and reference mismatches.

**Not included:** Gerber/Excellon geometry parsing, electrical clearance/thermal verification, full placement orientation checks, or factory approval.

## v0.5.0 — 2026-11-03

- Added `project-audit` CLI command combining provided EasyEDA geometry, exported `.enet`, fabrication ZIP and native KiCad CLI checks.
- Captures unavailable and missing verification stages, and provides short Markdown summary plus complete structured JSON.
- Maintains explicit evidence-only status; no implied manufacturing or electrical sign-off.
- Added synthetic integration and mock-native test coverage.

**Not included:** end-to-end physical validation, factory review or comprehensive CAM parsing.

## v0.6.0 — 2026-11-03

- Updated official KiCad CLI integration to request machine-readable JSON ERC/DRC reports.
- Summarizes every ERC sheet's violation array.
- Summarizes PCB DRC violation, unconnected-item and schematic-parity arrays, including severity counts.
- Missing/malformed native report is not accepted as successful verification, even on a process exit code of 0.
- Added six new synthetic/mocked native integration tests.

**Limit:** No actual KiCad executable is present in the build environment; a real KiCad 10 integration run remains outstanding.

## v0.8.0 — 2026-11-04

- Added subprocess-based **fake KiCad CLI contract tests** for schematic and board JSON reporting; clearly not native KiCad execution.
- Fixed fail-closed behavior when a native report is malformed, oversized, absent, or contains findings despite a zero exit code.
- Added explicit `validation_passed` evidence flag, limited to clean parseable native CLI output.
- **Known blocker:** KiCad 10 executable and user-authorized representative netlist exports have not been supplied to this runtime. No claim of actual KiCad 10 end-to-end testing.