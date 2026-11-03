# Contributing

Issues and pull requests are welcome. Please describe the EasyEDA or KiCad version, the command executed, the expected behavior, and the observed output. Prefer tiny synthetic fixtures and avoid uploading confidential project source.

Before opening a PR, run:

```bash
python3 -m unittest discover -s tests -v
```

For new parsers, add tests for normal input, malformed or missing input, deleted records, and large nested archives. Document any tool limitation clearly; never report native ERC or DRC success unless the official CAD application actually ran successfully.

Be respectful of other participants and do not post secrets, passwords, private email addresses, or third-party copyrighted schematics.