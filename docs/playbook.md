# From a Wii to a game night

Give your assistant this repo. It should do the computer work it can verify, explain what it is changing, and give you one console task at a time. You should not have to learn JSON to begin.

**Starting setup:** USB Loader GX, existing video settings preserved, Wii games first, Nintendont if you want GameCube, optional autoboot last. This is adjustable. No theme pack, region change or giant bundle is needed to get a first game working.

## 1. Find out what you have

The assistant runs `python3 -m wiiforge start` after setting `PYTHONPATH=src`. Ask the user, a few questions at a time:

- Console label/model; full menu version including region letter; whether Homebrew Channel already opens. Do not infer model from an SD card, serial prefix or case color.
- Computer OS, SD card/reader, game storage, TV inputs/cable, controllers, Wii-only or also GameCube.
- If shopping: country, budget and existing equipment. Use [the buying guide](buying.md), not a fixed shopping cart.

Keep observations and progress in a private folder outside the repo. For the supported original-Wii 4.3U path, use [journey](usage.md#resume-the-guided-journey-across-computers) to persist and resume ordered manual checkpoints. Do not collect serial numbers, MAC addresses, keys or backups into chat. If an exploit needs a MAC address, have the user enter it directly in the reviewed tool. Unknown is a valid answer.

The optional `start --answers /private/intake.json --json` command turns observations into a route, questions, and profile/evidence drafts. [Input format](usage.md#begin-with-your-own-setup). It never certifies a drive or console. Different hardware can have an official guide even when WiiForge's stricter planner does not support it.

## 2. Choose one current setup route

Read [Get Started](https://wii.hacks.guide/get-started) live before proceeding. An already-modded console needs an inventory first; do not start by reinstalling everything.

| Situation | Route to review | WiiForge boundary |
| --- | --- | --- |
| Original Wii / Windows | [ModMii](https://wii.hacks.guide/modmii), then its generated guide | Agent may help with its inputs; installation/execution of external software needs specific approval. Do not mix its recipe with an old pack. |
| Original Wii / SD card | [Wilbrand](https://wii.hacks.guide/wilbrand) for supported menu versions | Verify real version/region and card requirements. Generated exploits are not supported by WiiForge's GX package preparer. |
| Family Edition | Model-specific selection in Get Started | Guide handoff; no WiiForge installation/preparation recipe. Recovery and GameCube hardware differ. |
| Wii mini | [BlueBomb](https://wii.hacks.guide/bluebomb) | Dedicated guide only; never apply original-Wii packages. |
| Wii U / vWii | vWii selection in Get Started | Dedicated Wii U/vWii workflow; original-Wii IOS and recovery instructions do not transfer. |

WiiForge's checked `plan`/`resume` currently covers only original Wii 4.3U with its conservative macOS USB inspection. Do not fake that input for a PAL Wii, Windows PC or SD-only setup. The assistant can explain the official guide outside this scope; that is guide assistance, not tested WiiForge automation.

## 3. Prepare files on the computer

The assistant owns the inventory, source checks, file layout and verification. The user owns target selection and approval.

1. Identify the exact storage and preserve existing files. Review capacity, filesystem and backup needs. Never auto-format, repair, repartition or overwrite. Do not use a folder as proof of physical-drive identity.
2. Obtain needed tools only from links in the selected current guide or primary upstream. Record source and version privately. Do not execute unfamiliar downloads without approval or disable antivirus to make them run.
3. For the reviewed local GX ZIP, use [verify-package and controlled preparation](usage.md#controlled-file-preparation): preflight → show exact writes → approve digest → prepare → read-back verification. This supports POSIX hosts, not Windows destinations. Package licensing stays unresolved; no redistribution or website hosting of bundled GameTDB data.
4. Nintendont has a [local-file preparation path](usage.md#prepare-nintendont-from-local-files) using the same engine. The [Priiloader installer and menu launcher](usage.md#prepare-priiloader-recovery-files) also have reviewed local-ZIP preparation. Other apps/exploits still need guide-specific preparation. **Do not change the GX manifest to pretend they are reviewed.** Review their archive, source, layout and destination separately before any explicitly authorized copy. Never silently replace `apps`, `private`, saves or loader configuration.
5. Show the resulting layout and safe-eject instructions. Reinspect and approve a new plan after reconnect. The agent should identify what it completed and what still needs manual work.

Windows users should be offered the current ModMii workflow rather than asked to install a POSIX environment just to run WiiForge. The `start` command itself runs with Python 3.10+; CI includes a Windows intake/smoke job, separate from POSIX preparation tests.

### Personalized exploit handoff (Wilbrand)

If the selected guide calls for Wilbrand, keep this handoff short:

1. Ask the user to read the actual menu/region and console MAC privately. Open the generator linked by the live [Wilbrand guide](https://wii.hacks.guide/wilbrand); the user enters the MAC directly, selects the observed menu/region and includes HackMii. Do not put their MAC or generated payload into this repo or chat.
2. Keep the generated ZIP in a private host folder. The agent can list it and review the intended `private` folder and `boot.elf` layout, but **WiiForge does not validate that this personalized payload matches the console**. A file hash or plausible filename does not establish that match. Do not relabel it as a GX/recovery manifest.
3. Before a guide-specific copy, inventory the selected SD card and show exactly what would be added. An existing `private` folder or `boot.elf` is a conflict to inspect, not permission to replace it. This copy is a separately reviewed agent task, outside WiiForge's package preparer; no automatic extraction or overwrite is authorized by downloading the ZIP.
4. After authorized preparation, tell the user to safely eject, insert SD in the Wii's own slot and follow the guide's Message Board step. Ask what screen appears. If the expected letter is absent, check the console date and adjacent days as the guide describes; don't generate a different region or update the menu to guess a fix.

For ModMii users, use its generated instructions instead; do not mix exploit outputs. HackMii/BootMii and NAND-dumper preparation still require their own reviewed files and procedure. No console MAC is required to use WiiForge's other commands.

## 4. Walk through the console, one checkpoint at a time

For the original-Wii manual route, use the following sequence. For ModMii, follow its generated guide instead and use these outcomes as checks, not a competing recipe. Before each console change explain the action, expected screen and stop condition; wait for the user's observed result. If the screen differs, stop and inspect the error rather than guessing.

| Stage | Agent handles | User confirms before moving on |
| --- | --- | --- |
| Homebrew | Open the selected exploit and [HBC/BootMii guide](https://wii.hacks.guide/hbc); prepare reviewed files | Homebrew Channel actually opens; record BootMii options offered, never assume boot2 eligibility |
| Backup | Follow [NAND backup](https://wii.hacks.guide/nand-backup); help privately verify/copy the resulting files | Backup completed and verification result recorded; copies and unique keys are kept private, outside the repo |
| Recovery | Follow [Priiloader](https://wii.hacks.guide/priiloader) for the exact model | Recovery menu can actually be entered; user knows how to reach it again |
| Wii loading | Review the correct model tab in [cIOS](https://wii.hacks.guide/cios); never reuse another model's IOS | Installer results match the selected current guide; no unresolved errors |
| GX | Prepare the reviewed package; follow [USB Loader GX](https://wii.hacks.guide/wii-loaders) | Loader opens from Homebrew Channel and sees the intended storage |
| First game | Help organize a lawful personal dump using [dumping](https://wii.hacks.guide/dump-games) and [backup management](https://wii.hacks.guide/backups) | Actual gameplay, controls, audio/video and save/reload work; loader launch alone is not success |

BootMii as boot2 is only offered on eligible hardware. BootMii as IOS plus Priiloader is not a guarantee against every brick. Backing up is not the same as proving restoration works; Family Edition and mini have additional restore constraints. Do not test a NAND restore as a routine checkpoint. No backups or keys belong in issues, chat uploads or public commits.

## 5. Add GameCube, then convenience

Use [Nintendont upstream](https://github.com/FIX94/Nintendont) for app files and controller options; the assistant can verify and prepare the three [pinned local files](usage.md#prepare-nintendont-from-local-files). Test Nintendont directly before integrating it into GX. A simple disc layout is `games/Your Game/game.iso`; for two-disc titles put `disc2.iso` beside it. These are destination examples, not files supplied by WiiForge. Keep Wii backups in the loader's documented `wbfs` layout; changing an extension is not conversion. The current [backup-management guide](https://wii.hacks.guide/backups) uses TinyWiiBackupManager for conversion/organization. Review its exact release and proposed operations before approving execution; do not automatically normalize existing paths or bypass operating-system security warnings.

Confirm controller mapping, memory-card choice, a real save/reload and return behavior. Preserve video defaults at first. Use only games you can lawfully dump/use; ownership is not an instruction to download someone else's copy. No ROM sites, keys or copyrighted bundles are provided.

Once recovery and both desired game types work, offer the separately reviewed forwarder/autoboot path. Record the previous setting and how to re-enter recovery before changing boot behavior. Keep a working Homebrew Channel launch path. Defer themes, forced video patches and broad “optimization packs.”

## 6. Finish with something the user can use

Give a short private handoff: how to start GX, launch each game type, save, safely remove storage, find recovery, and where backups live. Record exact versions and unresolved issues. A useful finish is a tested game session, not a green JSON report.

If GX cannot find USB storage, check the guide's USB-port-0 diagram, filesystem and power before changing IOS. If only one game fails, keep global settings unchanged and investigate that game's dump and documented requirements. If video disappears after a change, return to the recorded known-working settings through the previously tested recovery path; do not promise a universal rollback.

**Evidence:** this walkthrough was source-reviewed on 2026-11-06. WiiForge's tests exercise software with synthetic data; no end-to-end hardware run has been completed. Community discussions are useful failure reports, not replacement install recipes: older [USB-focused advice](https://www.reddit.com/r/WiiHacks/comments/hargyu/usb_loader_gx_for_dummies_you_cant_screw_this_up/) predates current SD support. Prefer the live guide when they differ.
