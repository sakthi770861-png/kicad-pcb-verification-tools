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

**Not included:** native EasyEDA ERC/DRC, official exported `.enet` netlist verification, real-world current/thermal testing, or manufacturing sign-off.

## v0.1.0 — 2026-11-03

- Initial EasyEDA Pro V3 project inventory, simple component parity, and native KiCad CLI check wrappers.
- Published initial synthetic test suite and GitHub Actions CI.