# Usage

Run commands from the repository root with Python 3.10+:

```sh
export PYTHONPATH="$PWD/src"
python3 -m wiiforge --help
```

Use `python3 -m wiiforge demo` first. It uses invented data; it is not a hardware test.

## Collect evidence

Copy [evidence.example.yaml](../profiles/evidence.example.yaml) to a private folder outside the checkout. Replace unknown values only with actual observations:

| Field | Accepted values |
| --- | --- |
| `model` | `original`, `family`, `mini`, `vwii`, `unknown` |
| `model_source`, `region_source` | `user-observation`, `diagnostic`, `unknown` |
| `region` | `U`, `E`, `J`, `K`, `unknown` |
| `menu` | A menu string such as `4.3U`, or `unknown` |

Keep `schema` at `1`. Model evidence comes from the console label/physical inspection or a reviewed diagnostic, never an SD card. The planner currently accepts only confirmed original-Wii 4.3U evidence. A menu string does not establish a model.

## Inspect storage on macOS

Identify the intended whole disk in Disk Utility yourself. Replace `diskN` below with that exact identifier. Replace the private paths with existing directories you own; these are placeholders, not runnable defaults.

```sh
python3 -m wiiforge inspect --device diskN > /your/private/folder/inspection.json
```

The command only runs `diskutil list -plist` and `diskutil info -plist`. It does not mount, inspect game contents or write media. Missing metadata, internal/virtual targets and ambiguous layouts are rejected. Reports omit raw labels, UUIDs, serials and mount paths but contain a device number and fingerprint: keep them private.

Exit `2` means blocked or invalid. Do not edit an inspection report to remove blockers. Inspection compares two disk and partition snapshots and rejects changed identity or geometry. Reinspect after every reconnect. No filesystem integrity, free-space, SD preparation or gameplay check is performed.

## Choose a profile and plan

Start with [original-wii.yaml](../profiles/original-wii.yaml); customize a private copy if needed.

```sh
python3 -m wiiforge plan --profile profiles/original-wii.yaml \
  --evidence /your/private/folder/evidence.yaml \
  --inspection /your/private/folder/inspection.json
```

Profiles use **JSON syntax, a strict YAML 1.2 subset**. Unknown, missing and duplicate fields fail validation. Inputs must be regular UTF-8 JSON files no larger than 1 MiB with at most 32 nesting levels. Non-finite numbers are rejected. Final-component symlinks are rejected on hosts supporting no-follow opens. Current choices:

| Field | Values / default behavior |
| --- | --- |
| `loader` | `usb-loader-gx` only |
| `display` | `crt`, `hd`, `unknown` |
| `cable` | `composite`, `rgb`, `component`, `adapter`, `unknown` |
| `output` | `preserve`, `480i`, `576i`, `480p` |
| `aspect` | `preserve`, `4:3`, `16:9` |
| `autoboot`, `gamecube` | `off` or `review`; defaults are `review` and `off` respectively |

`480p` requires explicit HD/component selections; adapters require separate review. `576i` requires region `E`, whose installation path is currently blocked. These validation rules are not a tested display compatibility matrix. Preserve unknown video settings; do not force deflicker or output modes universally.

An accepted result is `manual-review-only` with `execution_supported: false`. Follow the linked current [Wii Hacks Guide](https://wii.hacks.guide/) procedures and obtain separate approval for any changes. Historical package versions are not current install pins.

## Resume checkpoints

Run `resume` with the same three input arguments. With no state or checkpoint it emits empty state. To acknowledge the first step **after actually reviewing it**:

```sh
python3 -m wiiforge resume --profile profiles/original-wii.yaml \
  --evidence /your/private/folder/evidence.yaml \
  --inspection /your/private/folder/inspection.json \
  --checkpoint review --level user-confirmed
```

Save successful JSON output privately. On later calls add `--state /your/private/folder/state.json` and acknowledge only the next step. Use `user-confirmed` for `review`, `backup` and `cios`; use `console-tested` for `recovery`, `loader`, `wii-test`, `gamecube-test` and `autoboot-test`. Optional steps appear only when enabled in the profile.

Write output to a **new** private filename and replace prior state only after exit `0`. Never redirect onto an input file: shell redirection truncates it before Python runs.

Changed profile, evidence, disk identity, device number or capacity invalidates old state. Identical metadata cannot prove the same physical medium or unchanged content. Supply `--checkpoint` and `--level` together; failed acknowledgments leave the previous state unchanged. Plans generated before a fingerprint change must be regenerated. All checkpoints are local user attestations, not signed proof. Loader launch does not prove gameplay.

## Rehearse file preparation without media

```sh
python3 -m wiiforge rehearse
```

This command uses two built-in text fixtures, validates their ZIP metadata, writes them exclusively inside
a newly created private OS temporary directory, checks byte counts/CRC and read-back hashes, then removes
the directory. Output lists synthetic paths, sizes and hashes. It accepts no artifact or destination argument,
performs no network access, and never calls the installation planner or changes its blockers.

On an ordinary exception or keyboard interrupt, partial temporary work is removed. A new invocation starts
fresh; this is not persistent copy/resume support. Forced process termination or host failure can leave the
OS temporary directory behind. No general cleanup command is provided. Use a host whose OS temporary
directory is on local scratch storage. No package licensing, archive compatibility or hardware support is implied.
