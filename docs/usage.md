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
directory is on appropriate scratch storage; the tool does not verify its backing device and TMPDIR can point to removable media. No package licensing, archive compatibility or hardware support is implied.

## When a command stops

| Result | Next step |
| --- | --- |
| Unknown/conflicting console model or region | Check the console label/menu or a reviewed diagnostic; do not infer it from storage. |
| Internal/ambiguous disk or missing geometry | Stop. Recheck the selected whole disk; retain the blocker if metadata is unavailable. Do not format to make the check pass. |
| Inputs changed during resume | Generate a fresh plan and reverify its checkpoints; do not copy old completion records across. |
| Package verified but exit code 2 | Integrity matched, but the listed installation blockers remain. This is expected, including after experimental staging. |
| Interrupted experimental staging | Ordinary failures clean up; rerun from the verified source. There is no persistent staging resume or console rollback. |

If a bug remains, use a synthetic reproducer in an issue. Never attach raw disk reports or recovery artifacts.

## Controlled file preparation

`prepare-plan` and `prepare` support a caller-selected **existing, dedicated directory** on POSIX hosts.
They are tested only against isolated temporary fixtures, not SD/USB hardware. No formatting, package execution,
console write or overwrite operation exists. The model must be explicitly `original`; other paths remain blocked.
Package licensing and console-installation blockers remain in every result. Preparing files does not clear them.

Use an already downloaded pinned ZIP and a trusted reviewed manifest. Choose the destination yourself;
WiiForge does not automatically choose a disk or certify its suitability. Paths below are placeholders.
Keep the plan outside the destination and repository: it includes private path/device metadata.

```sh
python3 -m wiiforge prepare-plan --manifest packages/usb-loader-gx.yaml \
  --artifact /private/usbloadergx_r1283.zip --model original \
  --destination /chosen/existing/directory > /private/preparation-plan.json
```

Inspect the JSON: every file has a path, byte size, SHA-256 and `create` or `keep` action; directories are
listed too. `required_bytes` is the payload size to create, with an additional 1 MiB free-space safety check.
A missing or conflicting target, unsupported model, invalid archive or insufficient space stops the operation.
Preflight reads and hashes all package members; it writes nothing. Do not approve a plan you have not reviewed.

After explicit approval for that destination and those writes, copy its `digest` into the command:

```sh
python3 -m wiiforge prepare --manifest packages/usb-loader-gx.yaml \
  --artifact /private/usbloadergx_r1283.zip --model original \
  --destination /chosen/existing/directory --plan /private/preparation-plan.json \
  --approve-plan DIGEST_FROM_REVIEWED_PLAN
```

Approval binds the exact package bytes, original-Wii model, file inventory and destination directory identity.
The tool rechecks these and all existing target files before writes. Missing files are created exclusively;
unrelated files remain untouched. Files are flushed and read-back verified. Exit 0 means preparation completed,
not installation approval: inspect `installation_supported: false` and `installation_blockers`.

Run the same approved command to resume: already complete files are rehashed and skipped. Normal errors or
keyboard interruption remove only the newly created in-progress file; completed files and created directories
remain. Forced termination, disconnect or power loss can leave a partial file. A conflicting partial file is
**never overwritten or automatically deleted on resume**: separately review and authorize cleanup, then retry.
No completion ledger is trusted in place of content verification. This is not an atomic multi-file transaction
or a guarantee of durability through power failure.

Do not modify, rename, reconnect or concurrently access the destination during preparation. Directory descriptors
and no-follow opens constrain paths, but cannot secure a destination against another process with your privileges.
Free-space checks are not reservations. Reconnection or changed identity requires a newly reviewed plan.
