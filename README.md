# WiiForge

An agent-agnostic, read-only assistant toolkit for planning a Wii homebrew setup centered on USB Loader GX. Python performs deterministic checks; your agent explains the evidence and guides manual checkpoints.

**MVP: inspect → validate a manual plan → resume evidence tracking.** There is no installer executor, downloader, formatter, repair tool or console writer. No packages, keys, NAND data, games or Nintendo IOS/WAD content are included. A validated plan is not permission to modify anything.

## Quick start

Python 3.10+, standard library only. From this checkout:

```sh
export PYTHONPATH="$PWD/src"
python3 -m wiiforge --help
python3 -m unittest discover -s tests -v
```

Live inspection currently targets macOS `diskutil`. Identify the intended whole disk yourself using macOS Disk Utility; never guess a disk number. Save reports in a private directory **outside this repository**. The command executes only `diskutil list -plist` and `diskutil info -plist`; it does not mount, read game files or alter media.

```sh
python3 -m wiiforge inspect --device disk4 > /your/private/folder/inspection.json
python3 -m wiiforge plan --profile profiles/original-wii.yaml \
  --evidence /your/private/folder/evidence.yaml \
  --inspection /your/private/folder/inspection.json
```

The paths above are placeholders. Copy `profiles/evidence.example.yaml` privately and replace unknowns only with actual observations. A console model comes from the console label/physical inspection or a reviewed diagnostic, never from an SD card. Family Edition, mini, vWii, conflicts, unknowns and anything outside the initial original-Wii 4.3U reference block the installation plan. Menu version alone does not prove a model.

Profiles use **JSON syntax, a strict subset of YAML 1.2** to avoid parser dependencies and executable YAML tags. Unknown/missing/duplicate fields fail. Customize display, cable, aspect, output, optional autoboot review and optional GameCube review. Defaults preserve video configuration: CRT/HD, adapters and regional capabilities need explicit review; never apply universal 480p or deflicker overrides. Only USB Loader GX is currently implemented as a loader choice.

The conservative USB media check requires a single FAT32 partition, MBR, 32 KiB clusters, known capacity, external physical whole disk and a persistent identifier. Missing diskutil metadata deliberately blocks planning; this may reject otherwise suitable media. It is a candidate assessment, **not filesystem integrity verification, free-space verification, write authorization or proof of Wii compatibility**. No SD preparation capability exists yet.

## Resume manual checkpoints

Use the same profile, evidence and freshly generated inspection with `resume`. With no state argument, it emits an empty state. Record the next checkpoint using `--checkpoint review --level user-confirmed`; pass previous output through `--state /private/state.json` on later invocations. Recovery/loader/game/autoboot tests require `--level console-tested`. Save each output to a new private filename and replace old state only after exit code 0; never redirect onto an input file.

```sh
python3 -m wiiforge resume --profile profiles/original-wii.yaml \
  --evidence /your/private/folder/evidence.yaml \
  --inspection /your/private/folder/inspection.json \
  --checkpoint review --level user-confirmed
```

State is bound to all inputs and ordered steps. Changed disk identity, capacity, device number, profile or evidence invalidates it. Reinspect after every reconnect; identical metadata cannot prove the same physical medium or unchanged file contents. Inputs/state are local user attestations, not signed proof. The tool never marks anything tested automatically, and never accepts “files exist” as console success. All CLI output is JSON except errors on stderr; blocked/invalid operations exit 2.

## Scope and evidence

| Area | Current status |
| --- | --- |
| Original Wii, 4.3U | Manual planning reference only; no new hardware installation tested |
| Family Edition / Wii mini / vWii | Recognized, installation planning blocked |
| macOS inspection | Implemented with mocked diskutil tests; live hardware validation pending |
| Linux / Windows inspection | Not implemented; fails closed |
| Wii / GameCube gameplay | No compatibility claim; individual console tests required |
| Package staging / SD preparation / copying | Deferred until reviewed origins, pinned hashes and failure tests exist |
| Formatting / filesystem repair | Not implemented; requires separate explicit approval in any future implementation |

See [sanitized evidence](docs/evidence.md) and [safety workflow](AGENTS.md). Historical setup results do not verify this implementation. The authoritative procedural source is [Wii Hacks Guide](https://wii.hacks.guide/), with separate [cIOS guidance](https://wii.hacks.guide/cios) and [USB loader guidance](https://wii.hacks.guide/wii-loaders). Recheck these and primary upstream releases before every real installation; this project does not mirror installation payloads or pin historical versions as current recommendations.

## Contributing

Keep changes small and synthetic tests deterministic. Add a platform/model only after targeted review and recorded tests. Before any future preparation feature, implement pinned package manifests, archive traversal defenses, expected size/hash checks, free-space/FAT32 limits, preservation of existing files, interruption recovery, fresh target validation and explicit approval boundaries. Do not execute unrecognized downloads without separate per-action approval. Do not publish private reports or submit them in issues.

Code is MIT licensed. No affiliation with Nintendo or Wii Hacks Guide. Third-party projects retain their own licenses.
