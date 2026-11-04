# Contributing to WiiForge

Thanks for helping make homebrew planning easier to inspect and safer to resume. Read [AGENTS.md](AGENTS.md) for the shared human/agent boundaries and [the roadmap](docs/roadmap.md) before broadening scope.

## Work locally

Use Python 3.10+ and the standard library. From the checkout, in a POSIX shell:

```sh
export PYTHONPATH="$PWD/src"
python3 -m wiiforge demo
python3 -m unittest discover -s tests -v
python3 -m compileall -q src
git diff --check
```

No dependency installation or physical media is needed. Do not execute unfamiliar tools or downloaded binaries without per-action approval. Tests must use synthetic data and mocked host APIs.

## Good first contributions

- Reproduce a malformed-input or ambiguous-device failure with a small synthetic test.
- Improve a blocker message without relaxing the safety check.
- Clarify the setup instructions or add a verified authoritative link.
- Propose a sanitized hardware observation format before gathering real reports.

## Before a pull request

Describe the problem, resulting behavior and how you checked it. Keep scope small. Add meaningful regression tests for behavior changes, especially failure paths. Preserve strict profile validation and the read-only default. Update docs when command behavior changes.

Review the exact staged files for private data. Never commit real device IDs, serials, personal paths, raw disk reports, console keys, NAND dumps, games, proprietary IOS/WADs or recovery conversations. A removed secret may remain in Git history: follow [SECURITY.md](SECURITY.md) if anything private is exposed.

Adding a model or OS needs current primary-source review, targeted tests and a precise support statement. Mocked tests alone cannot establish hardware compatibility. Record file preparation, content verification, user confirmation and console testing separately.

Contributions use the repository's MIT license. Do not copy upstream code or artwork without checking its license and preserving required attribution. Keep discussion respectful and focused on reproducible behavior.
