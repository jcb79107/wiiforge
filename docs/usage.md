# Usage

Run commands from the repository root with Python 3.10+:

```sh
export PYTHONPATH="$PWD/src"
python3 -m wiiforge --help
```

Begin with `python3 -m wiiforge start`. It asks what you own and gives a guide route without inspecting hardware or writing files. `demo` is a separate invented-data example, not your setup.

## Begin with your own setup

An assistant can collect answers conversationally and keep this JSON privately outside the checkout:

```json
{
  "model": "unknown",
  "menu": "unknown",
  "computer": "unknown",
  "homebrew": "unknown",
  "sd": "unknown",
  "storage": "unknown",
  "display": "unknown",
  "cable": "unknown",
  "gamecube": "unknown"
}
```

Run `python3 -m wiiforge start --answers /private/intake.json` for readable guidance; add `--json` for profile/evidence drafts. No arguments prints questions. Omitted fields remain unknown. Exit 0 means the intake was processed, not that a setup is ready. Invalid input exits 2.

Values: `model` = original/family/mini/vwii/unknown; `menu` = observed version and letter (such as 4.3E) or unknown; `computer` = windows/macos/linux/unknown; `homebrew`, `sd`, `gamecube` = yes/no/unknown; `storage` = sd/usb-hdd/usb-ssd/usb-flash/unknown. Display and cable use the choices below. No serials, MAC addresses, paths or freeform private notes belong in this file.

The JSON result contains `profile_draft` and `evidence_draft` for your assistant to save separately only after you confirm the observations. `reference_plan_scope` identifies the existing original-Wii 4.3U recipe, not hardware validation or storage suitability. Intake routes can link to official guidance outside that recipe without enabling installation. Follow [the playbook](playbook.md).

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

Profiles use **JSON syntax, a strict YAML 1.2 subset**. Unknown, missing and duplicate fields fail validation. Inputs must be regular UTF-8 JSON files with at most 32 nesting levels. Profiles, evidence and state are limited to 1 MiB; preparation plans have a shared 8 MiB generation/read limit. Non-finite numbers are rejected. Final-component symlinks are rejected on hosts supporting no-follow opens. Current choices:

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

Approval binds the exact package bytes, original-Wii model, file inventory and destination directory identity
(canonical path plus root `st_dev`/`st_ino`). This is filesystem identity, not a persistent physical-media identifier.
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
Opened descendant directories and files must report the same `st_dev` as the destination root; different-device
mounts are rejected. This does not detect same-device bind mounts, every mount topology, or malicious same-account
races. The root itself may be a mountpoint. The tool does not classify storage as internal/removable or bind plans
to a drive serial number. Free-space checks are not reservations.

After any reconnect, unmount/remount or changed hardware, inspect the target again and obtain a newly reviewed
plan and approval, even if the tool would accept the previous path/device/inode values. Those values can be reused;
matching them is not proof of the same physical drive. No reconnect, power-loss or real-media safety claim is made.

## Prepare Nintendont from local files

On a POSIX host, obtain these three files from the exact [pinned upstream commit](https://github.com/FIX94/Nintendont/tree/c683db301c941a64e6fe5cef6ac079bd1a726074), following the upstream README: `loader/loader.dol`, `nintendont/meta.xml`, `nintendont/icon.png`. Keep their basenames together in a private host folder. Do not substitute current `master` files or change hashes to make a mismatch pass. The CLI does not download them.

```sh
python3 -m wiiforge verify-package --manifest packages/nintendont.yaml \
  --artifact /private/nintendont --model original --check-archive
python3 -m wiiforge prepare-plan --manifest packages/nintendont.yaml \
  --artifact /private/nintendont --model original \
  --destination /chosen/existing/directory > /private/nintendont-plan.json
```

Verification exit 2 with `content-verified` is expected: installation/licensing/hardware blockers remain. Inspect the plan. After separate approval for that exact destination and inventory:

```sh
python3 -m wiiforge prepare --manifest packages/nintendont.yaml \
  --artifact /private/nintendont --model original --destination /chosen/existing/directory \
  --plan /private/nintendont-plan.json --approve-plan DIGEST_FROM_REVIEWED_PLAN
```

Only `apps/Nintendont/boot.dol`, `meta.xml` and `icon.png` are prepared. Existing differing files block rather than overwrite; existing matching files are verified and retained. Rerunning the same approved command resumes completed files. All controlled-preparation identity, concurrency and interruption limits above apply. No GameCube games, saves, controller configuration or BIOS files are copied. Test Nintendont directly on the Wii before integrating it with GX; preparation is not a console checkpoint.

## Resume the guided journey across computers

For an original Wii 4.3U with computer, homebrew and storage observations, `journey` provides a manual checklist on Windows, macOS or Linux without pretending to inspect a disk:

```sh
python3 -m wiiforge journey --answers /private/intake.json > /private/progress-1.json
```

Read `guide_route`, `next_checkpoint` and its `required_evidence`. After the user actually completes that step, acknowledge it into a **new** file:

```sh
python3 -m wiiforge journey --answers /private/intake.json \
  --state /private/progress-1.json --checkpoint review --level user-confirmed \
  > /private/progress-2.json
```

Pass the entire previous successful output as `--state`; do not redirect onto an input. Check exit 0 before retaining new progress. The next step appears automatically; skipped steps and changed console/storage/display/goals are rejected. Moving between computers retains progress and the originally selected guide. A homebrew change from no to yes is accepted only with the Homebrew Channel console-tested checkpoint or after that checkpoint; regression to no requires investigation. The saved baseline keeps the original plan binding intact. Use `user-confirmed` for review, storage-review, backup and cIOS; `console-tested` for Homebrew Channel, recovery, loader and game tests. File preparation does not acknowledge any of these.

TV/cable and optional GameCube intent may remain unknown initially; video is preserved and no GameCube checkpoint is added until requested. Changing those later requires a reviewed session, not silently reusing prior display/game tests.

This reuses the ordered checkpoint validator. It is a portable record of user attestations, not an inspection, write permission, signed proof or automatic installer. Keep the file private. Revisit storage after every reconnect; never reuse a preparation approval on that basis. Other models/menus remain guide handoffs, and `start` still helps collect their observations. For ModMii follow its generated instructions; use the checklist only to record outcomes, not to substitute a different recipe.
