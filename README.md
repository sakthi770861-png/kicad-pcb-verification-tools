# KiCad & EasyEDA PCB Verification Tools

A read-only, open-source Python CLI for basic CAD-file inspection and for running **real, native KiCad** electrical/design-rule checks when KiCad is installed. Intended for electronics students, hobbyists, and makers. Current release: **v0.2.0 (prototype)**.

> ⚠️ **NOT a manufacturing approval tool.** Structural checks are not ERC/DRC. Version 0.2 adds **geometric pin-to-wire evidence only**; this does **not** validate complete electrical nets or replace EasyEDA ERC. No circuit simulation, datasheet verification, current-density calculation, thermal simulation, USB-C compliance, BOM purchasing check, or JLCPCB assembly verification is performed.

## Capabilities (v0.4.0)

- Parses EasyEDA Pro V3 `.epro2` ZIP archives, including ZIP folders containing separate schematic and PCB files.
- Distinguishes embedded symbol/footprint library documents from actual placed PCB/schematic components.
- Counts placed component designators, named PCB nets, via records, pad-net records, and active copper layers.
- Detects duplicated designators; checks reference-designator set parity **when schematic and PCB are submitted together**. An intentional omission may be a false positive.
- Gives informational counts of unassigned pad-net records and board-outline polygon records without falsely claiming ERC/DRC status.
- Extracts symbol PIN numbers and positions from embedded EasyEDA libraries, applies part selection, rotation and mirroring, then compares them with **active** schematic WIRE/LINE geometry.
- Associates pin-to-wire geometry with stored `NET` labels; merges explicit same-name wire groups and endpoint/T joins, without assuming electrical contact at plain X crossings.
- Reports `ON_WIRE`, `DIRECT_PIN_CONTACT`, `UNCONNECTED_CANDIDATE` and `AMBIGUOUS_INTERSECTION` statuses. Missing library symbols remain **unknown**, not a false disconnected-pin error.
- Highlights possible conflicting wire NET labels and excludes orphan line records left over from deleted wires. These are **informational review prompts**, not native ERC results.
- Produces JSON and Markdown reports, including a per-pin table for schematic inputs.
- Delegates to `kicad-cli sch erc` and `kicad-cli pcb drc` for **native** checks on KiCad files. Requires a locally installed `kicad-cli`; does **not** silently mark unrun checks as passed.
- Pure Python standard-library runtime dependencies; works on Linux, Windows, and macOS where Python 3.10+ is installed.

## Quick start on Ubuntu

```bash
unzip kicad-pcb-verification-tools-v0.2.0.zip
cd kicad-pcb-verification-tools
python3 -m unittest discover -s tests -v
python3 -m pcbverify analyze "/path/to/your/EasyEDA-project.zip" --json report.json --markdown report.md
```

Analyze a single EasyEDA Pro V3 file:

```bash
python3 -m pcbverify analyze example.epro2 --markdown report.md
```

Run actual native checks on a KiCad file (requires the official KiCad CLI):

```bash
python3 -m pcbverify kicad-check circuit.kicad_sch --json erc.json
python3 -m pcbverify kicad-check board.kicad_pcb --json drc.json
```

Optional installation from the repository directory:

```bash
python3 -m pip install --user .
pcbverify analyze "/path/to/your/project.zip" --markdown report.md
```

## Interpreting reports

- `STRUCTURAL_INSPECTION_ONLY`: EasyEDA records were inventoried, with coordinate-based pin/wire contact evidence where supported; **no real EasyEDA native ERC or DRC was run**.
- `UNCONNECTED_CANDIDATE`: no recognized conductor or second pin at the symbol endpoint. **This is not a proven open circuit**—intentional NC, implicit electrical connections, missing symbols and other EasyEDA features require manual inspection.
- `AMBIGUOUS_INTERSECTION`: a pin touches multiple wire groups that the limited geometry logic cannot safely merge.
- `UNRESOLVED_SYMBOLS`: missing/mismatched embedded symbol; affected pins are **unknown** and omitted from disconnected candidates.
- `CLI_COMPLETED`: KiCad command exited 0; **read the complete native report**. This is not electrical or manufacturing certification.
- `CLI_NONZERO`: KiCad command reported nonzero status; inspect its stderr/report.
- `NOT_RUN`: KiCad CLI was unavailable or failed to start.
- Informational findings are *not* automatic design defects. Empty pad-net records might be intentional NC pins.

## Repository scope and privacy

The code and synthetic tests are intentionally separate from real personal or commissioned PCB data. **Original uploaded EasyEDA source files, personal photographs, exact hardware builds, and private client data are not distributed in this repository.** Share only project files that you own and have permission to publish.

See [docs/PROJECT_PORTFOLIO.md](docs/PROJECT_PORTFOLIO.md) for a summary of example project areas and [docs/ROADMAP.md](docs/ROADMAP.md) for planned extensions.

## Test and support status

The v0.2 implementation is tested using 20 synthetic standard-library unit tests and inspected offline against three privately provided EasyEDA Pro V3 archives. The public repository contains **no private design archives**. CI runs on Python 3.10, 3.12, and 3.13. The package build environment did not run an end-to-end native KiCad test. See [Connectivity limitations](docs/CONNECTIVITY_LIMITATIONS.md) before using any result.

## Contributing

Bug reports, reproducible test inputs without confidential details, pull requests and documentation improvements are welcome. Please do not post sensitive PCB source files or proprietary datasheets without permission.

## License

MIT for original source code in this repository. Trademarks and third-party hardware designs are not granted by this license.

## Format references

- [Official EasyEDA Pro V3 file format overview](https://prodocs.easyeda.com/en/format/index/) — `DOCHEAD`, append-only records, deletion semantics, layer and geometry conventions.
- [EasyEDA Pro schematic PIN](https://prodocs.easyeda.com/en/format/schematic/pin/) and [COMPONENT](https://prodocs.easyeda.com/en/format/schematic/component/) — pin endpoints and rotation/mirroring transformations.
- [EasyEDA client format notes](https://github.com/easyeda/easyeda-client-cli/blob/main/easyeda-format.md) — `.epro2` ZIP containers and logical-ticket precedence.
- [KiCad CLI documentation](https://docs.kicad.org/10.0/en/cli/cli.html) — native schematic ERC and PCB DRC commands.

## Exported EasyEDA Pro netlist analysis (v0.3.0)

EasyEDA Pro's **official** `.enet` export is a JSON snapshot. Use it to cross-check geometric evidence:

```bash
python3 -m pcbverify netlist my-schematic.enet --json netlist.json
python3 -m pcbverify netlist my-schematic.enet --compare my-schematic.epro2 --json comparison.json
```

A missing connection or named-net mismatch is a review candidate, not proof of an electrical defect. Ensure both exports were saved from the **same design revision**. The tool cannot perform native EasyEDA ERC/DRC or confirm manufacturing safety. See `docs/ENET_EXPORT.md`.

## Manufacturing export preflight (v0.4.0)

Run a **filename/CSV manifest audit** on the exported ZIP before sending it to a board house:

```bash
python3 -m pcbverify manufacturing-audit gerber-drill-bundle.zip --json cam-manifest.json
python3 -m pcbverify manufacturing-audit jlcpcb-export.zip --assembly --json assembly-manifest.json
```

The tool recognizes common KiCad and legacy Gerber naming conventions, identifies missing front/back copper, outline and drill categories, and optionally checks for BOM and placement files and compares their reference sets. **This is not CAM validation, manufacturability approval, or confirmation of BOM/CPL orientation accuracy.** See `docs/MANUFACTURING_LIMITATIONS.md`.