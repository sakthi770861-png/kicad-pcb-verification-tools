# Stable v1.0 release checklist — NOT COMPLETE

The `1.0.0rc1` tag in package metadata denotes an **unstable release candidate**. Do not advertise it as a stable production verification tool.

- [x] Installable Python package with tested CLI entrypoint.
- [x] Automated Python-version matrix and synthetic regression on GitHub Actions.
- [x] Fail-closed native CLI JSON error classification and synthetic subprocess contract tests.
- [x] Safe archive bounds and bounded CAM header preflight.
- [x] Release evidence gate with explicit blockers and non-approval semantics.
- [ ] Run native KiCad **10** on a publicly shareable representative schematic and PCB, retaining version and ERC/DRC JSON outputs.
- [ ] Test at least one real exported EasyEDA Pro `.enet` from the same revision as its `.epro2` schematic.
- [ ] Independent engineering review of CAM tool limitations and documented out-of-scope features.
- [ ] Permission review for any candidate public example designs, including contributors and third-party symbols.
- [ ] Final changelog and semantic-version review before marking a release stable.

## License and privacy

MIT covers only original software source code. Do not publish private client board layouts, firmware, credentials, personal photos, or third-party libraries without permission.