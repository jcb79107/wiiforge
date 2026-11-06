# Usage

## Run the tools

Use Python 3.10+ from the repository root. No pip dependencies or virtual environment needed.

macOS/Linux:

```sh
export PYTHONPATH="$PWD/src"
python3 -m wiiforge start
```

Windows PowerShell:

```powershell
$env:PYTHONPATH="$PWD/src"
py -3 -m wiiforge start
```

Add `--shopping` if you do not own a console, or `--help` for commands. If Python/Git is missing,
your agent can still use the guide while you review tool installation separately. Check `python3 --version`
or `py -3 --version`. For `No module named wiiforge`, return to the checkout and set `PYTHONPATH` again
in the same terminal. Repeat that line after opening a new terminal.

Begin with `python3 -m wiiforge start`. It asks what you own and gives a guide route without inspecting hardware or writing files. `demo` is a separate invented-data example, not your setup.

**Keep raw plans/reports local.** They can contain paths, device identities, game IDs and hashes.
An agent should redirect full output to a **new private local file outside this checkout**, check the exit code,
and avoid sending that output through chat, remote-agent/tool transcripts, telemetry or cloud storage.
Do not overwrite an existing report or redirect onto an input file. The examples below use placeholder paths.
For a package or GameCube preparation plan, share only aggregate totals using:

```sh
python3 -m wiiforge plan-summary --plan /private/saved-plan.json
```

This checks saved-plan consistency and reports counts/bytes without paths, IDs or hashes. It does not
recheck the source/destination or authorize writes. Open the full plan locally to review exact paths and
digest before approving; keep that digest local for the copy command.

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

Pass the entire previous successful output as `--state`; do not redirect onto an input. Check exit 0 before retaining new progress. The next step appears automatically; skipped steps and changed console/storage are rejected. Moving between computers retains progress and the originally selected guide. A homebrew change from no to yes is accepted only with the Homebrew Channel console-tested checkpoint or after that checkpoint; regression to no requires investigation. The saved baseline keeps the original plan binding intact. Use `user-confirmed` for review, storage-review, backup and cIOS; `console-tested` for Homebrew Channel, recovery, loader and game tests. File preparation does not acknowledge any of these.

TV/cable and optional GameCube intent may remain unknown initially. Identifying the same previously unknown TV/cable preserves progress; replacing a known display/cable requires review. Video settings remain preserved. Adding GameCube appends its console test without repeating completed Wii steps or skipping pending steps. Removing that goal is rejected. These are local attestations about the same console, not automatic hardware detection.

This reuses the ordered checkpoint validator. It is a portable record of user attestations, not an inspection, write permission, signed proof or automatic installer. Keep the file private. Revisit storage after every reconnect; never reuse a preparation approval on that basis. Other models/menus remain guide handoffs, and `start` still helps collect their observations. For ModMii follow its generated instructions; use the checklist only to record outcomes, not to substitute a different recipe.

## Prepare Priiloader recovery files

After reviewing the current [original-Wii Priiloader procedure](https://wii.hacks.guide/priiloader), obtain the two ZIPs from the [author's pinned release](https://github.com/DacoTaco/priiloader/releases/tag/0.10.0). Keep them in a private host folder. Use the existing verification and controlled-preparation commands with these pairs:

| `--manifest` | `--artifact` |
| --- | --- |
| `packages/priiloader.yaml` | Your local `Priiloader_v0_10.zip` |
| `packages/loadpriiloader.yaml` | Your local `LoadPriiloader.zip` |

For each pair: run `verify-package --model original --check-archive`, then `prepare-plan --model original --destination YOUR_TARGET`, review its output, and run `prepare` with the saved plan and explicit digest approval. Use a separate saved plan for each package. Neither command installs Priiloader on the console, alters its settings or records recovery as tested. The installer ZIP includes a root `LICENSE`; preserve it and stop if it conflicts with an existing file.

After preparation and safe eject, the agent opens the guide, explains that the installer changes the console's internal storage, obtains approval for that console action, and waits for the user's result. Recovery is complete only after the user can actually enter Priiloader; record `recovery --level console-tested` in the journey then. The Load Priiloader app launches an existing installation; it is not the installer. Do not install a forwarder or enable autoboot at this stage.

## Prepare Homebrew Channel, backup and cIOS tools

Use the same `verify-package` → `prepare-plan` → explicit digest-approved `prepare` sequence, with a separate plan per package:

| Manifest | User-supplied artifact | When needed |
| --- | --- | --- |
| `packages/hackmii.yaml` | `hackmii_installer_v1.2.zip` from the [publisher](https://bootmii.org/download/) | Standalone HackMii preparation when the chosen guide calls for it; skip if your reviewed exploit already includes it |
| `packages/nanddumper-ios.yaml` | `nanddumper_ios.zip` from [release 1.1](https://github.com/Naim2000/nanddumper_ios/releases/tag/1.1) | Before the NAND-backup checkpoint |
| `packages/d2x-cios-installer.yaml` | `d2x-v11-beta3.zip` from [the original-Wii release](https://github.com/wiidev/d2x-cios/releases/tag/d2x-v11-beta3) | After backup/recovery review and before the cIOS checkpoint |

Pass `--model original`, the exact private artifact path, and the specifically approved destination. Example preflight:

```sh
python3 -m wiiforge prepare-plan --manifest packages/nanddumper-ios.yaml \
  --artifact /private/nanddumper_ios.zip --model original \
  --destination /chosen/existing/directory > /private/nand-tool-plan.json
```

HackMii preparation places `boot.elf` at the destination root and retains notices under `wiiforge-notices/hackmii`. It excludes `bootmini.elf` and PC tools. A different existing `boot.elf` blocks preparation; do not overwrite an exploit or app to force a match. This does not create Wilbrand's personalized `private` directory. Download directly from the publisher, never a WiiForge mirror or repacked bundle.

On the console, follow the selected guide and confirm actual results. For NAND backup, verify the dumper's checksums locally and keep the backup, keys and verification files in two private locations under your control; do not send them to the agent's hosted chat or commit them. A matching copy is not proof that restoration will succeed.

For cIOS, review the **Wii/Family Edition tab for this original Wii** in the live guide. The pinned package is the installer, not installed cIOS. Online installation and offline base-IOS acquisition remain console/guide-specific work; WiiForge does not fetch Nintendo IOS WADs or keys. Explain the exact proposed console changes and get approval before the user runs the installer. If the expected d2x version is absent or the screen differs, stop. Do not substitute vWii/mini files, guess a slot or automatically repeat writes after an error.

## Partially check a private Wilbrand ZIP

After the user obtains their personalized archive using the current official guide:

```sh
python3 -m wiiforge check-exploit --artifact /private/generated.zip --model original --menu 4.3U
```

This command reads only a regular local ZIP (maximum 16 MiB), applies the existing bounded archive checks,
streams members for size/CRC verification and requires root `boot.elf` to match the installer inside the
publisher's pinned HackMii 1.2 archive. Other files must be under `private/`, with a nonempty payload.
It writes/extracts nothing, submits no network requests, accepts no MAC, and reports no private member names or payload hashes.

A successful partial check returns **exit 2**, `status: partial-check-only` and `personalization_verified: false`.
It does not prove payload origin, correct menu/region/MAC, exploit validity or safety on a Wii. Even arbitrary bytes
inside a well-formed `private/` tree can pass these limited checks. Do not interpret this as approval to install,
copy or run them. Confirm the user's official generation flow, then separately review the exact destination copy.
Unexpected extra files or another installer build are rejected rather than silently accepted. Only synthetic
personalized archives have been tested; no real console payload was generated or exercised.

## Choose the cIOS acquisition route when needed

`journey` now includes `next_checkpoint.computer_preparation`, listing relevant local manifests and the next
computer task. These are suggestions for the current step, not a command to prepare every package at once.
At cIOS, rerun the same session with `--wii-network online` or `--wii-network offline` according to the Wii's
actual internet availability. The observation is saved; later resumes retain it unless overridden. Use `--wii-network unknown` to clear it. This does not query the network, invalidate progress, download files or authorize execution.

The [current original-Wii guide](https://wii.hacks.guide/cios) permits online users to skip offline IOS acquisition.
Offline output lists only its four base-IOS versions and expected filenames and links [NUSGet upstream](https://github.com/NinjaCheetah/NUSGet/releases/latest).
Review the correct host build and publisher/signature information, then obtain specific approval before running it.
Do not disable security controls or treat a guide's antivirus reassurance as an authorization to bypass them.
Use the guide's original-Wii choices, keep acquired files private, and review any copying/renaming separately.
WiiForge does not validate WAD contents or acquire/distribute Nintendo files. Never substitute the vWii versions.

## Check a local GameCube dump before first launch

```sh
python3 -m wiiforge check-gamecube --disc1 /private/own-dump.iso
# For a two-disc game, add: --disc2 /private/own-disc-two.iso
```

This read-only check reads 1,120 header bytes from each selected regular ISO/GCM file.
It catches unsupported headers, reversed discs and mismatched game IDs, then suggests
`games/<your-game-folder>/game.iso` and, when supplied, `disc2.iso` beside it.
It reports whether the selected paths already match that layout; alternate layouts may work too.
It never scans a library, copies, renames, converts or downloads games. Reports omit source paths,
titles and game IDs. Keep your files and reports private.

Exit 0 means the limited header check completed; it does **not** verify the complete dump,
lawful provenance, disc contents, required disc count or playability. Smaller files may be trimmed
or incomplete; their headers cannot distinguish those cases. NKit, RVZ, CISO, WBFS, extracted games,
multi-game compilations and oversized images are outside this check; do not rename them to bypass it.
Keep the original dump/checksum record and use the [backup-management guide](https://wii.hacks.guide/backups)
for conversion/organization. Any copy or conversion needs separate review and approval.

Layout follows [Nintendont's instructions](https://github.com/FIX94/Nintendont#quick-installation).
Header fields were checked against its [pinned format detection](https://github.com/FIX94/Nintendont/blob/c683db301c941a64e6fe5cef6ac079bd1a726074/loader/source/global.c#L407)
and Dolphin's [disc metadata reader](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/DiscIO/VolumeDisc.cpp).
No upstream code or game data was copied. Test controls and a real save/reload in Nintendont before GX integration.

## Copy your own raw GameCube files

On POSIX, with explicitly identified original-Wii hardware and an existing dedicated destination folder:

```sh
python3 -m wiiforge gamecube-plan --disc1 /private/own-disc.iso --model original --destination /chosen/folder
```

Add `--disc2 /private/own-disc-two.iso` for a two-disc game. The command reads and hashes each **entire**
file, checks the limited header/disc order, inventories destination conflicts and checks free space.
It makes no writes. Save its JSON output privately outside the destination, using a new file.
The plan contains source paths/identity/hashes and exact writes to `games/<six-character-game-ID>/game.iso`
and optionally `disc2.iso`. Review those paths and obtain explicit approval for that destination and digest.

```sh
python3 -m wiiforge gamecube-copy --disc1 /private/own-disc.iso --model original --destination /chosen/folder --plan /private/game-plan.json --approve-plan EXACT_APPROVED_DIGEST
```

Repeat the same `--disc2` option if planned. No files are moved, deleted or overwritten. Identical destination
content is checked and retained; conflicts stop the operation. The copier rechecks sources/target, streams
bounded chunks, flushes and reads back written files. Run the same approved command to resume after an
ordinary interruption; completed content is verified before skipping it. Changed inputs require a new plan.
After a reconnect, review/approve anew even if filesystem IDs match. Power loss can leave a conflicting
partial file; cleanup needs separate review/approval. Keep exclusive access while planning/copying.

The full-file SHA-256 verifies copy equality, **not** correctness/completeness of the original dump,
lawful provenance, disc compatibility or gameplay. No trusted dump database is queried. Only synthetic
files have tested this path; no physical-media validation. Windows copy, compressed/converted images,
multi-game images and Wii backup copying/conversion are not implemented. Existing games with another
folder name are not discovered or deduplicated; inspect your destination before approving a plan.

The [current Wii layout](https://wii.hacks.guide/wii-loaders#game-folder-structure) is a `wbfs` game folder
containing a `.wbfs` file and, when split, `.wbf1`; FAT32 requires splitting files over its limit.
Use the [guide's backup-manager workflow](https://wii.hacks.guide/backups) with separate tool/action approval
for that task. Renaming an ISO to WBFS is not conversion. GameCube layout follows
[Nintendont](https://github.com/FIX94/Nintendont#quick-installation); changing a raw GCM's destination name
to `game.iso` does not change its bytes.

## Prepare CleanRip for your own discs

If you already have a lawful verified dump, skip this. Otherwise obtain your own copy of the
[pinned Wii release](https://github.com/emukidid/cleanrip/releases/tag/2.4), then use the same approved preparation flow:

```sh
python3 -m wiiforge verify-package --manifest packages/cleanrip.yaml --artifact /private/CleanRip-v2.4.zip --model original --check-archive
python3 -m wiiforge prepare-plan --manifest packages/cleanrip.yaml --artifact /private/CleanRip-v2.4.zip --model original --destination /chosen/folder
```

Successful byte verification still exits 2 for licensing/hardware blockers. Review the exact plan and use
[controlled preparation](#controlled-file-preparation) only after destination/digest approval. This copies
the app, never a game. On the console, follow the [dumping guide](https://wii.hacks.guide/dump-games):
check free space, select the correct storage and enable checksum verification. Dumping writes storage;
obtain separate approval and keep all resulting games/checksum records private. Joining split Wii dumps uses the separately approved flow below;
converting formats remains a separately reviewed task; never rename extensions as conversion.


## Get a Wii dump ready for its first launch

Use the [current backup guide](https://wii.hacks.guide/backups) and
[TinyWiiBackupManager upstream releases](https://github.com/mq1/TinyWiiBackupManager/releases).
This is an agent-guided external-tool handoff, not a WiiForge copy command:

1. Keep the original dump and checksum record unchanged. For CleanRip PART files, join only the explicitly
   reviewed, numbered parts of one game into a new file on host storage that supports large files.
   Check the joined checksum against the dump record before conversion; do not use a broad wildcard or overwrite an existing ISO.
2. Select the official build for the computer's OS/architecture and check its release digest when supplied.
   Obtain specific approval before executing it. Stop on security warnings; do not disable protections.
3. Start with one game and a new empty host staging folder, with enough space for both source and output.
   Review the selected destination immediately before importing: the application can remember a previous folder.
   Use the reviewed settings below, including forced splitting for FAT32 even when host staging uses another
   filesystem. Do not normalize an existing library, delete originals or accept replacements.
4. Inspect the resulting `wbfs/<game folder>/` files, including all split parts, and use the tool's integrity check.
   An integrity result does not establish lawful provenance or console compatibility. Review the final media
   destination and conflicts separately before approving transfer; WiiForge does not yet copy Wii backups.
5. Safely eject after the approved transfer, launch the one game in USB Loader GX and test play/save before
   acknowledging the journey's Wii-game checkpoint. Report an error rather than changing cIOS or video settings at random.

For **v6.1.11**, check these controls in the application's settings before adding a game:

| Setting | Choice for this first-game staging workflow |
| --- | --- |
| Wii output format | WBFS |
| Split output | Always 4GB-32KB |
| Remove update partition on WBFS/CISO | No |
| Delete sources when adding games | No |

These labels are checked against the [upstream settings source](https://github.com/mq1/TinyWiiBackupManager/blob/v6.1.11/src/config/ui/settings.rs).
Recheck them for another version. Do not assume a prior installation has default settings. The
[stored configuration](https://github.com/mq1/TinyWiiBackupManager/blob/v6.1.11/src/config/mod.rs) includes the
previous destination and deletion preference. Ask the user to confirm the visible selected folder when the
agent cannot inspect the app. Import the selected ISO into the empty staging folder; a generic Convert action
is not interchangeable with this import path's splitting and folder layout.

A successful conversion does not mean its WBFS bytes should hash identically to the source ISO. Preserve
source checksum records, check the tool's verification result, and keep any partial/failed output separate.
Do not retry into a failed staging folder or delete its contents automatically; use a newly approved empty
folder. Before a media transfer, inventory every generated part and existing destination conflict locally.

The [v6.1.11 import source](https://github.com/mq1/TinyWiiBackupManager/blob/v6.1.11/src/games/import.rs)
supports configurable Wii output and splitting; its
[conversion code](https://github.com/mq1/TinyWiiBackupManager/blob/v6.1.11/src/games/convert.rs) can replace output files.
Do not assume it has WiiForge's no-overwrite guarantees. This route was source-reviewed, not executed or
hardware-tested here. No converter binary or game content is included in this repository.

Automation assessment: this reviewed release starts a graphical application; no documented headless
conversion interface was established. [Wiimm's official COPY documentation](https://wit.wiimm.de/wit/cmd-copy.html)
describes a CLI with preview, splitting and no overwrite by default, but WiiForge has not validated a host
binary or its failure behavior. Neither tool is installed, launched or wrapped automatically. A future adapter
needs an approved exact binary, isolated conversion/failure tests and verified output inventory before
claiming controlled conversion. The current handoff remains the supported route.


### Join CleanRip parts without overwriting

On POSIX, choose an existing dedicated **host staging folder** with enough space and a filesystem
supporting the full ISO size (not FAT32). WiiForge does not classify its backing device or filesystem.
Read the original private dump record's SHA-1; never calculate a new expected checksum just to pass a failed check.
The [guide](https://wii.hacks.guide/backups#joining-part-files-from-a-wii-disc-on-a-fat32-device) requires the
joined checksum to match. [CleanRip source](https://github.com/emukidid/cleanrip/blob/master/source/main.c)
records SHA-1 when checksum calculation is enabled and numbers parts from zero.

```sh
python3 -m wiiforge wii-join-plan --model original \
  --part /private/own-game.part0.iso --part /private/own-game.part1.iso \
  --dump-sha1 SHA1_FROM_ORIGINAL_DUMP_RECORD --destination /chosen/host-staging
```

List every part explicitly in order; no wildcard expansion. Save the plan directly to a new private local
file, then review it locally and obtain approval for its exact destination/digest. `plan-summary` provides
redacted totals. Repeat all source options when running `wii-join`, adding `--plan /private/join-plan.json`
and `--approve-plan EXACT_APPROVED_DIGEST`. Raw plans contain private paths, identities and hashes.

The planner reads all selected parts in bounded chunks and requires the supplied SHA-1 to match before
any output write. The executor rechecks the plan, creates only `joined.iso`, verifies SHA-256/readback and
preserves every source. Existing different output blocks; identical completed output is retained on resume.
Ordinary interrupted writes remove only the newly created partial file; power loss may leave a conflict
requiring separately approved cleanup. There is no byte-offset resume. Keep exclusive access throughout.
The same device-identity, concurrency and reconnect limits as controlled preparation apply.

This accepts 2–16 consecutive same-basename parts, totaling at most 9 GiB. It does **not** parse an image,
check full-disc size, validate the supplied record's authenticity, establish lawful provenance, convert to
WBFS or prove gameplay. Even invented bytes can match an invented checksum. Tests use only such synthetic
fixtures. Windows joining remains blocked; use the reviewed guide handoff there. After joining, continue
with the one-game conversion workflow above, with separate execution/transfer approval.


## Support status

Guide assistance and tool support are different. Follow [Wii Hacks Guide](https://wii.hacks.guide/get-started)
for the console's current route; never invent observations to pass a WiiForge check.

| Tool | Current scope |
| --- | --- |
| `start`, shopping and routing | Windows, macOS, Linux; all listed console models recognized |
| `journey` manual checkpoints | Original Wii 4.3U; portable between computers |
| Package preparation / game copying / joining | POSIX hosts; original-Wii selection; user-supplied local files |
| Disk inspection and checked `plan` | macOS USB reference path: original Wii 4.3U, external physical disk with known identity/capacity, one MBR/FAT32 partition, 32 KiB clusters |
| Other menus/regions, Family, mini, vWii | Guide assistance only; installation planning/preparation blocked |
| Wii format conversion | External-tool handoff; execution needs separate approval |
| Formatting, repair, console operations | Not implemented |

Tests use synthetic fixtures, including interruption and conflict cases. WiiForge has no completed
end-to-end console or physical-media validation; there is no certified storage, controller or display matrix.
Inspection does not check filesystem integrity. Partial game-header checks and matching copy hashes do not
establish dump authenticity or gameplay. Temporary storage follows the host configuration; see
[SECURITY.md](../SECURITY.md) for device identity, concurrency, reconnect and power-loss limits.

Package verification/preparation does not clear upstream licensing. No games, keys, backups, IOS/WADs or
upstream binaries are distributed. GameTDB contents must not be republished or served on a website.
WiiForge's MIT license covers its own code; the linked guide and tools retain their own notices and licenses.
