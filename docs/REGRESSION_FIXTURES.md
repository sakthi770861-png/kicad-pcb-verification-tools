# Reproducible regression fixtures (Version 0.7)

The public examples are **entirely synthetic**. No user photographs, client
boards, layout data, custom footprints or proprietary source projects are
included. The fabricated Gerber placeholders intentionally contain **invalid
CAM data**: this is a filename-manifest regression, *not* CAM verification.

Create the three synthetic inputs and a JSON baseline:

```bash
python3 examples/make_synthetic_regression.py /tmp/pcbverify-demo
python3 -m pcbverify regression-check /tmp/pcbverify-demo/regression-manifest.json --json /tmp/pcbverify-demo/report.json
```

The command returns exit code `0` only when every selected evidence assertion
matches its baseline. A changed, absent or malformed input returns a nonzero
status. It compares structured output values with [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901)
paths, for example `/summary/pcb_boards`. The supported manifest schema is:

```json
{
  "schema_version": 1,
  "cases": [{
    "name": "netlist-counts",
    "kind": "enet",
    "input": "synthetic.enet",
    "expected": {"/component_count": 1, "/pin_count": 2}
  }]
}
```

Kinds are `enet`, `easyeda`, and `manufacturing` (the latter can set
`"assembly": true`). Every file must live *inside* the manifest directory;
symlinks, absolute paths and `../` may not escape that directory. Up to 50
cases and 60 assertions per case are accepted. Regression reports show only
input names, expected/observed values, and pass/fail status.

**Important:** A green regression result means *the software still reports the
expected values*. It is not proof that a source PCB is electrically correct,
or that its Gerbers are valid or ready to manufacture.

## Private design regression

You can keep a separate private manifest with a known-safe baseline and the
original EasyEDA archives in a private directory. Do **not** upload client
files, their netlists or their derived sensitive results to a public repo
without permission. Public CI uses synthetic fixtures only.