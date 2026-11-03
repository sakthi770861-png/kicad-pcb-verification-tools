"""Use the official KiCad CLI when installed; never emulate native ERC/DRC."""
from __future__ import annotations
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def native_check(path: Path | str) -> dict[str, Any]:
    path = Path(path).resolve()
    if path.suffix not in {".kicad_sch", ".kicad_pcb"}:
        raise ValueError("Expected .kicad_sch or .kicad_pcb")
    if not path.is_file():
        raise FileNotFoundError(path)
    exe = shutil.which("kicad-cli")
    if not exe:
        return {"input": path.name, "status": "NOT_RUN", "reason": "kicad-cli is not installed or not on PATH"}
    subcommand = ["sch", "erc"] if path.suffix == ".kicad_sch" else ["pcb", "drc"]
    with tempfile.TemporaryDirectory() as folder:
        output = Path(folder) / "native-report.txt"
        args = [exe, *subcommand, "--severity-all", "--exit-code-violations", "--output", str(output), str(path)]
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as err:
            return {"input": path.name, "status": "NOT_RUN", "reason": str(err)}
        report = output.read_text(encoding="utf-8", errors="replace") if output.exists() else ""
    # Exit code 0 alone does not certify manufacturing safety.
    return {"input": path.name, "status": "CLI_COMPLETED" if result.returncode == 0 else "CLI_NONZERO",
            "exit_code": result.returncode, "command": "kicad-cli " + " ".join(subcommand),
            "report": report, "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:],
            "note": "Review native report. Passing ERC/DRC does not establish functional or manufacturing safety."}