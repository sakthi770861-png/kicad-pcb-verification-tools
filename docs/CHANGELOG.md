# Changelog

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