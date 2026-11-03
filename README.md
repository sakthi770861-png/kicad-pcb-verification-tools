# KiCad & EasyEDA PCB Verification Tools

A read-only, open-source Python CLI for basic CAD-file inspection and for running **real, native KiCad** electrical/design-rule checks when KiCad is installed. Intended for electronics students, hobbyists, and makers. First release: **v0.1.0 (prototype)**.

> ⚠️ **NOT a manufacturing approval tool.** Structural checks are not ERC/DRC. No circuit simulation, datasheet verification, net connectivity analysis, current-density calculation, thermal simulation, USB-C compliance, BOM purchasing check, or JLCPCB assembly verification is performed on EasyEDA files.

## Capabilities (v0.1.0)

- Parses EasyEDA Pro V3 `.epro2` ZIP archives, including ZIP folders containing separate schematic and PCB files.
- Distinguishes embedded symbol/footprint library documents from actual placed PCB/schematic components.
- Counts placed component designators, named PCB nets, via records, pad-net records, and active copper layers.
- Detects duplicated designators; checks reference-designator set parity **when schematic and PCB are submitted together**. An intentional omission may be a false positive.
- Gives informational counts of unassigned pad-net records and board-outline polygon records without falsely claiming ERC/DRC status.
- Produces JSON and Markdown reports.
- Delegates to `kicad-cli sch erc` and `kicad-cli pcb drc` for **native** checks on KiCad files. Requires a locally installed `kicad-cli`; does **not** silently mark unrun checks as passed.
- Pure Python standard-library runtime dependencies; works on Linux, Windows, and macOS where Python 3.10+ is installed.

## Quick start on Ubuntu

```bash
unzip kicad-pcb-verification-tools-v0.1.0.zip
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

- `STRUCTURAL_INSPECTION_ONLY`: EasyEDA records were inventoried; **no real EasyEDA native ERC or DRC was run**.
- `CLI_COMPLETED`: KiCad command exited 0; **read the complete native report**. This is not electrical or manufacturing certification.
- `CLI_NONZERO`: KiCad command reported nonzero status; inspect its stderr/report.
- `NOT_RUN`: KiCad CLI was unavailable or failed to start.
- Informational findings are *not* automatic design defects. Empty pad-net records might be intentional NC pins.

## Repository scope and privacy

The code and synthetic tests are intentionally separate from real personal or commissioned PCB data. **Original uploaded EasyEDA source files, personal photographs, exact hardware builds, and private client data are not distributed in this repository.** Share only project files that you own and have permission to publish.

See [docs/PROJECT_PORTFOLIO.md](docs/PROJECT_PORTFOLIO.md) for a summary of example project areas and [docs/ROADMAP.md](docs/ROADMAP.md) for planned extensions.

## Test and support status

Tested with Python 3.13 using synthetic fixtures and inspected against three user-provided EasyEDA Pro V3 archives. This release does not yet include a public fixture corpus or end-to-end KiCad test (KiCad CLI was unavailable in the package build environment).

## Contributing

Bug reports, reproducible test inputs without confidential details, pull requests and documentation improvements are welcome. Please do not post sensitive PCB source files or proprietary datasheets without permission.

## License

MIT for original source code in this repository. Trademarks and third-party hardware designs are not granted by this license.

## Format references

- [Official EasyEDA Pro V3 file format overview](https://prodocs.easyeda.com/en/format/index/) — `DOCHEAD`, append-only records, deletion semantics, layer and geometry conventions.
- [EasyEDA client format notes](https://github.com/easyeda/easyeda-client-cli/blob/main/easyeda-format.md) — `.epro2` ZIP containers and logical-ticket precedence.
- [KiCad CLI documentation](https://docs.kicad.org/10.0/en/cli/cli.html) — native schematic ERC and PCB DRC commands.