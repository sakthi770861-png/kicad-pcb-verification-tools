# EasyEDA Pro schematic pin-to-wire inspection — v0.2

**Scope:** This is read-only **geometric evidence**, not an EasyEDA electrical netlist, ERC, short-circuit checker, or manufacturing approval. Physical behavior and current/voltage ratings remain unverified.

## How it works

1. Loads active `.epru` records from `.epro2` ZIP design files, preserving the winning ticket and ignoring deleted components/wires.
2. Looks up a placed schematic component's `Symbol` attribute in the embedded `SYMBOL` document. Reads its active `PIN` coordinates and `Pin Number`/`Pin Name` attributes (including placed pin-number overrides).
3. Applies **rotation → horizontal mirror (if set) → translation**, following the [official COMPONENT spec](https://prodocs.easyeda.com/en/format/schematic/component/). Pin coordinates refer to the electrical endpoints per the [official PIN spec](https://prodocs.easyeda.com/en/format/schematic/pin/).
4. Tests pin endpoints against active `WIRE` geometry stored in grouped `LINE` records. Uses line endpoints/T joins and matching nonempty `NET` properties as evidence of shared nets. Does **not** assume an interior X crossing is joined without evidence.
5. Emits the per-pin `position`, `pin_number`, `pin_name`, `connection_status`, `net_id`, and the explicit `net_name` when unambiguous.

## Status interpretations

| Status | Meaning | What to do |
| --- | --- | --- |
| `ON_WIRE` | Placed pin endpoint lies on one resolved wire group. | Confirm circuit intent and pin functions in EasyEDA. |
| `DIRECT_PIN_CONTACT` | At least two placed pins meet at one point with no stored wire. | Confirm editor treats that as connected. |
| `UNCONNECTED_CANDIDATE` | No active wire or second pin is found at the endpoint. | Check whether NC is intentional, then inspect in EasyEDA. |
| `AMBIGUOUS_INTERSECTION` | Pin touches multiple wire groups without a demonstrated join. | Inspect junction marker, nets, and actual native netlist. |
| Component in `unresolved_components` | Missing symbol or no matching part ID. | Export with complete library; its pins are **unknown**. |

Names in `net_name` originate only from stored WIRE `NET` attributes. A null net name may represent a perfectly valid **unnamed** wire; it is not an electrical failure. `net_id` is an **internal report identifier**, not an EasyEDA net ID.

## Important limitations

- This is **not** the editor's electrical interpretation. Complex crossings, bus connections, hierarchy, global net flags, implicit power connections, hidden pins, no-connect markers, short symbols, net ties, unusual symbols, and unsupported library/part variants may not be modeled correctly.
- The tool excludes leftover `LINE` records when their owning `WIRE` no longer exists. That avoids false positive connections from deleted wires, but may miss legitimate unsupported geometry.
- Net labels are case-sensitive, and multiple distinct labels on joined geometry generate a warning for **manual review**, not a definitive short verdict.
- A symbol missing from its `.epro2` archive must never be reported as an unconnected pin. Inconsistent coordinate data also cannot establish connectivity.
- This version does not compare computed schematic nets with PCB pad nets. **The next planned milestone is comparing against EasyEDA's authoritative exported `.enet` netlist**, and then native ERC/DRC remains necessary.
- Geometric findings must never be used as proof that a lithium charging, high-current motor, USB-C, or safety circuit is safe to energize.

## Privacy and testing

All public tests use **handwritten synthetic** symbol/line records. Privately uploaded EasyEDA projects are used only for local regression runs and private reports. Do not commit design files without permission.