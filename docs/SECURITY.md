# Security / threat-model notes

- Archives and netlists are untrusted input. Parsers use size/count limits, and ZIP path traversal entries are rejected where inputs are extracted or iterated.
- No fabricated data is used as manufacturing approval; outputs identify the check scope.
- Avoid storing private design files in repository fixtures or public CI artifacts.
- Native KiCad is executed as an external executable on the operator's system. Run it with the operator's own installed trusted version, not downloaded anonymous binaries.
- CPU/memory denial-of-service protection is best-effort, not a hardened sandbox. Do not run untrusted third-party files on a privileged machine.
- Report security issues privately to the repository maintainer rather than placing potentially sensitive samples in a public issue.