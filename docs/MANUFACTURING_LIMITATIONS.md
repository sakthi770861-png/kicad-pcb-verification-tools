# Manufacturing-export manifest audit

This command reads a ZIP *without extracting its contents* and recognizes common Gerber, Excellon and assembly CSV filenames. It is intended to reduce accidental omissions, **not approve manufacturing**.

## What a positive manifest means

- The archive contains files with recognizable names for `front_copper`, `back_copper`, `outline`, and `drill`.
- If `--assembly` is selected, recognizable BOM and placement CSVs exist.
- Optional CSV parsing can compare visible reference designator sets, with grouped BOM entries such as `R1,R2`.

## What it does not mean

- No Gerber or drill geometric data is parsed or validated.
- No board stackup, copper thickness, drill registration, routing, cutout, mouse-bite, V-score, or solder-mask clearance is checked.
- No manufacturer MPN, supplier stock, correct origin, pick-and-place rotations, DNP status, pad/paste design, or pin-1 polarity is checked.
- No real electrical operation or current/thermal rating is verified.
- Other naming conventions can trigger false missing-file messages. Multiple boards in one ZIP can falsely satisfy the manifest.

Use the factory CAM preview and CAD-native DRC, verify the BOM/CPL together, and seek qualified engineering review for hazardous/high-current designs. Do not order production solely on this output.