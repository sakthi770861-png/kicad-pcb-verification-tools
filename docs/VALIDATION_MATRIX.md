# Evidence matrix — Version 1.0.0 release candidate

This project is a read-only **preflight** and evidence-gathering utility. No result in the application indicates that a circuit is safe, a product will function, or a board is ready to order.

| Verification | v1.0.0rc1 evidence | Release conclusion |
| --- | --- | --- |
| Python source syntax | CI tests on Python 3.10, 3.12 and 3.13 | Automated compatibility tested |
| Synthetic EasyEDA V3 archive | Unit fixtures + regression baseline | Synthetic fixture coverage only |
| EasyEDA Pro exported `.enet` | JSON parser synthetic data | **REAL EXPORT PENDING** |
| User-provided EasyEDA archives | Previous internal inventory on 3 archives; private | Not published as fixtures |
| Actual KiCad 10 schematic ERC | Fake CLI contract tests; no KiCad 10 in runtime | **REAL NATIVE CHECK PENDING** |
| Actual KiCad 10 board DRC | Fake CLI contract tests; no KiCad 10 in runtime | **REAL NATIVE CHECK PENDING** |
| Fabrication Gerber/Excellon | Names and bounded headers only | **FULL CAM GEOMETRY NOT SUPPORTED** |
| BOM/CPL | CSV headers and reference-set parity only | Supplier, centroid orientation, and placement not approved |
| Physical electrical tests | None | **OUTSIDE SOFTWARE SCOPE** |
| JLCPCB manufacturing order approval | None | **OUTSIDE SOFTWARE SCOPE** |

`pcbverify release-gate` reports missing/insufficient inputs and exits nonzero. Even if all evidence is present, it reports `ENGINEERING_REVIEW_REQUIRED` and still exits nonzero: engineering sign-off cannot be automated by this project.

To generate real KiCad 10 evidence, run `scripts/run_native_kicad10_check.sh schematic.kicad_sch board.kicad_pcb results/` on a machine with KiCad 10. Keep proprietary design files out of public GitHub repositories.