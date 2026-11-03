# Working with EasyEDA Pro exported `.enet` netlists

1. Open the schematic in EasyEDA Pro and select **File → Export → Export Netlist**.
2. Choose the EasyEDA Pro (`.enet`) format and export the netlist.
3. Run `python -m pcbverify netlist exported.enet --json netlist-report.json`.
4. Optionally compare with a separately exported `.epro2` archive representing the **same saved revision**:
   `python -m pcbverify netlist exported.enet --compare project.epro2 --json compare.json`

The `.enet` file is a JSON snapshot containing `components` with `props` and `pinInfoMap`; each pin has an exported `net` string. An empty value indicates an unconnected pin in the exported snapshot. The tool currently does not automatically prove the files share the same revision or detect a hidden graphical connection in all cases.

Differences between exported net names and geometric labels should be reviewed in the editor. They may indicate a stale export, intentional NC, hierarchy, unsupported geometry, or true unintended wiring. No production/safety certification is implied.

Source specification: https://github.com/easyeda/easyeda-netlist-format/blob/main/easyeda-pro-netlist-format-en.md