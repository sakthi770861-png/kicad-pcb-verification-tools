# KiCad & EasyEDA PCB Verification Tools

A read-only, open-source Python CLI for basic CAD-file inspection and for running **real, native KiCad** electrical/design-rule checks when KiCad is installed. Intended for electronics students, hobbyists, and makers. Current release: **v1.0.0rc1 (release candidate, NOT STABLE)**.

> ⚠️ **NOT a manufacturing approval tool.** Structural checks are not ERC/DRC. Geometric evidence, exported netlists, and manufacturing file manifests do **not** replace native ERC, DRC, CAM review, or engineering validation. No circuit simulation, datasheet verification, current-density calculation, thermal simulation, USB-C compliance, BOM purchasing check, or JLCPCB assembly verification is performed.

## Capabilities (v1.0.0rc1)

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
unzip kicad-pcb-verification-tools-v1.0.0rc1.zip
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

The release is tested with standard-library synthetic unit tests and inspected against three privately provided EasyEDA Pro V3 archives. The public repository contains **no private design archives**. CI runs on Python 3.10, 3.12, and 3.13. The package build environment did not run an end-to-end native KiCad test. See [Connectivity limitations](docs/CONNECTIVITY_LIMITATIONS.md) before using any result.

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

## Combined project evidence (v0.5.0)

Run independent checks and save their status in one JSON+Markdown bundle:

```bash
python3 -m pcbverify project-audit --easyeda myproject.epro2 --netlist myproject.enet \
  --fabrication pcb-output.zip --assembly --json evidence.json --markdown evidence.md
```

KiCad users may pass `--kicad-schematic circuit.kicad_sch` and `--kicad-board board.kicad_pcb` if `kicad-cli` is installed. Missing or unavailable checks remain explicit. **An evidence bundle is not a manufacturing sign-off.**

## KiCad native JSON summary (v0.6.0)

When the official `kicad-cli` is installed, native ERC and DRC use `--format json`. Their findings include **ERC sheet violations** and **DRC rule violations, unconnected items, and schematic parity**.

```bash
python3 -m pcbverify kicad-check board.kicad_pcb --json board-drc-evidence.json
python3 -m pcbverify kicad-check circuit.kicad_sch --json schematic-erc-evidence.json
```

Missing/malformed reports cannot be shown as clean. These commands have not yet been run against an installed native KiCad binary in this build environment and are NOT a fabrication sign-off.

## Repeatable evidence regression (v1.0.0rc1)

Generate **synthetic, permission-safe** sample files and a baseline, then run an automated regression comparison:

```bash
python3 examples/make_synthetic_regression.py /tmp/pcbverify-demo
python3 -m pcbverify regression-check /tmp/pcbverify-demo/regression-manifest.json --json /tmp/pcbverify-demo/report.json
```

The tool exits nonzero when an expected report value is absent or changes. A regression PASS is **not** an electrical safety or manufacturing certification. See [regression fixtures](docs/REGRESSION_FIXTURES.md).

## v0.8 KiCad CLI contract validation

Mock subprocess contract tests cover clean, nonzero, missing, malformed, and unexpected-issue native JSON responses. These tests do **not** execute the actual KiCad application. To perform a genuine native check, run `pcbverify kicad-check BOARD.kicad_pcb --json drc.json` with KiCad installed and review the resulting native output. An unreadable or missing report never passes.

## v0.9 Manufacturing header review

`pcbverify manufacturing-audit export.zip --json fab.json` records bounded Gerber/Excellon header hints and flags identical copper files, mixed units, or contradictory X2 layer tags. This is **not** a CAM geometry parser. The absence of reported issues cannot approve a board for manufacture.

## v1.0.0rc1: release evidence gate

Run `python -m pcbverify release-gate --json gate.json` to see missing evidence. Supply `--easyeda`, `--netlist`, `--fabrication`, `--kicad-schematic`, and `--kicad-board` paths to evaluate available checks. The command **intentionally returns a nonzero exit status** even when inputs are complete because native ERC/DRC and human CAM/electrical review cannot amount to automatic board approval.

`python -m pcbverify manufacturing-audit exported.zip --strict --json fab.json` exits nonzero if required file categories or CAM-header review findings exist. A zero exit here means the limited preflight did not find those specific issues — **not that fabrication is ready**.

For a real KiCad 10 run on your own Ubuntu computer:

```bash
bash scripts/run_native_kicad10_check.sh schematic.kicad_sch board.kicad_pcb native-reports
```

See [Validation matrix](docs/VALIDATION_MATRIX.md), [Release checklist](docs/RELEASE_CHECKLIST.md), and [Security notes](docs/SECURITY.md) for outstanding evidence. This candidate must not be presented as a fully validated stable v1.0 software release.