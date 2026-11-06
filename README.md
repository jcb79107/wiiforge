<p align="center">
  <img src="docs/assets/wiiforge.svg" alt="WiiForge" width="100%">
</p>

# Your Wii, ready for game night

Give WiiForge to your AI coding assistant. It helps you choose hardware, figure out your setup, prepare files on your computer, and work through the Wii steps with you—one checkpoint at a time.

**USB Loader GX is the starting point.** Play your lawful Wii backups, add GameCube through Nintendont if you want it, and consider autoboot once the basics work. Keep what already works; customize the rest.

## Start here

**Experimental: tested with synthetic files, not a real Wii or drive.** The checked setup path is original
Wii 4.3U; other models/menus need their separate guide and remain blocked in WiiForge’s installation planner.
Your assistant should explain each proposed change and ask before media or console changes. Console
changes are not all reversible; recovery preparation comes before gameplay.

1. Open your AI coding assistant on the computer you will use for setup.
2. Paste the prompt below. Start with what you own; if you are shopping, say so.
3. Let the assistant handle the supported computer steps and guide you through one Wii screen at a time.

Copy this prompt:

> Help me set up my Wii using https://github.com/jcb79107/wiiforge. Read AGENTS.md and follow the playbook. Ask what I own first, help me buy only what I need, do the computer work you can verify, and walk me through the console steps. Keep my files private and ask before changing my media or console.

You don't need to know Python or write configuration files to start the conversation. Your assistant needs repository access, a way to read current guides, and permission to run local commands. It cannot press buttons on your Wii or verify a game works without your observations.

**[The walkthrough](docs/playbook.md)** · **[What to buy](docs/buying.md)** · **[Command reference](docs/usage.md)**

## What the journey looks like

| Stage | Your assistant | You |
| --- | --- | --- |
| Choose gear | Compare suitable console/storage/TV/controller options | Say what you own, your budget and what you want to play |
| Discover | Record model, menu, existing mods and missing information | Read the label/menu and identify cables |
| Prepare | Review sources, inspect supported storage, show exact writes and verify prepared files | Choose the destination and approve that plan |
| Set up | Explain the current model-specific guide, one task at a time | Operate the Wii; report the actual screen/result |
| Play | Help with your own dumps, loader settings and troubleshooting | Test gameplay, controls, audio/video and save/reload |
| Finish | Record versions, backups, recovery access and daily-use instructions | Keep a private copy; enjoy the setup |

The first milestone is a working game, not a theme pack. Defaults preserve video settings; GameCube and autoboot are separate choices. Hardware suggestions are tradeoffs, not promises that every adapter or drive works.

## Try the tools

With Git and Python 3.10+ already installed, on macOS/Linux:

```sh
git clone https://github.com/jcb79107/wiiforge.git
cd wiiforge
export PYTHONPATH="$PWD/src"
python3 -m wiiforge start
```

No Wii yet? Run `python3 -m wiiforge start --shopping` for budget, existing gear and game goals instead of console questions.

`start` prints beginner questions and a next step. It makes no changes. Your assistant can supply private observations with `--answers PATH` and request draft profiles with `--json`. Unknowns stay unknown.

On Windows, with Git and Python 3.10+ installed, use PowerShell:

```powershell
git clone https://github.com/jcb79107/wiiforge.git
cd wiiforge
$env:PYTHONPATH="$PWD/src"
py -3 -m wiiforge start
```

Add `--shopping` if you do not own the console yet. These commands run directly from the checkout: no
`pip install`, virtual environment or third-party Python packages are needed. If Git/Python is missing,
the assistant can still use the playbook and buying guide immediately; review any tool installation
separately. Check `python3 --version` (or `py -3 --version`) before running; Python must be 3.10 or newer.
If Python reports `No module named wiiforge`, return to the repository folder and repeat the `PYTHONPATH`
line in that same terminal. This variable must be set again in a new terminal.

CI includes Windows intake, private ZIP and smoke checks; the destination-writing tool requires POSIX. The official guide's **ModMii** route is the Windows preparation option to review with your assistant.

For a hardware-free demonstration or developer check:

```sh
python3 -m wiiforge demo
python3 -m unittest discover -s tests -v
```

## What works today

WiiForge includes a tested intake/router, read-only macOS metadata inspection, resumable manual checkpoints, local homebrew package verification, archive checks, and **explicitly approved no-overwrite file preparation**. It can resume completed files by checking their contents. [Commands and limits](docs/usage.md).

For your own GameCube dumps, [`check-gamecube`](docs/usage.md#check-a-local-gamecube-dump-before-first-launch) checks raw ISO/GCM headers, disc order and suggested naming before first launch. It does not copy games or verify the entire dump.
On POSIX, [`gamecube-plan` / `gamecube-copy`](docs/usage.md#copy-your-own-raw-gamecube-files) add exact-plan approval, no-overwrite copying and full-file read-back verification. Original files stay untouched; no games are supplied.

For split CleanRip dumps, `wii-join-plan` / `wii-join` can join explicitly selected parts after checksum matching and exact-plan approval on POSIX. WBFS conversion and Wii backup transfer still use the [guided external-tool handoff](docs/usage.md#get-a-wii-dump-ready-for-its-first-launch).

It is **not a one-click exploit installer**. The guided journey uses current [Wii Hacks Guide](https://wii.hacks.guide/get-started) procedures; the CLI's checked recipe and package support are narrower. Personalized exploit generation and base-IOS acquisition still need guide-specific work. A local `check-exploit` checks ZIP structure and the bundled installer, without claiming personalization validity. GX, Nintendont, Priiloader, HackMii, NAND-dumper, d2x installer and CleanRip files have local preparation paths; console actions remain manual. `journey` resumes original-Wii 4.3U checkpoints across computers without claiming disk inspection. The agent must explain these handoffs instead of pretending automation exists.

Current GX supports Wii games on SD as well as USB; a USB drive is not mandatory. The existing storage planner is conservative and USB-oriented, so SD-only users follow the guide without a fabricated inspection report. No end-to-end WiiForge hardware run has been completed.

## Support status

| Area | Implemented today | Validation / limit |
| --- | --- | --- |
| Original Wii, 4.3U | Manual planning reference | Historical setup evidence; this tool has no live installation validation |
| Other original-Wii menus/regions | Input recognized | Installation planning blocked |
| Family Edition | Model recognized | Installation planning blocked; no recipe |
| Wii mini | Model recognized | Installation planning blocked; no recipe |
| Wii U vWii | Model recognized | Installation planning blocked; no recipe |
| macOS storage inspection | Read-only `diskutil` adapter | Mocked tests only; real-device validation pending |
| Linux / Windows inspection | Not implemented | Linux runs synthetic tests; Windows has intake, private ZIP and smoke checks only |
| CRT / HD / regional video | Explicit profile fields; preserve by default | No tested display compatibility matrix |
| Wii / GameCube gameplay | Manual checkpoints | No gameplay compatibility claims |
| Package staging | Opt-in disposable host staging | Experimental; licensing/installation blocked; no destination accepted |
| Controlled file preparation | Explicit destination, reviewed plan and digest approval; no overwrites | Tested with isolated fixtures only; real-media validation pending |
| Formatting / console installation | Not implemented | Separate approval and model-specific validation required |

Storage checks conservatively require an external physical whole disk, persistent identifier, known capacity and a single MBR/FAT32 partition with 32 KiB clusters. Missing metadata blocks planning even if a drive might otherwise work. This is **not a filesystem integrity check or a guarantee of compatibility**.

## Boundaries that protect your setup

No automatic formatting, overwrites, console writes, region changes or downloaded-code execution. Media writes require a reviewed exact plan and specific approval. No games, BIOS, keys, NAND backups or upstream binaries are bundled. Local package preparation is not license clearance; redistribution and GameTDB web publication remain outside scope.

Keep backups, identifiers and reports outside the checkout. Temporary staging follows the host's temporary-directory configuration; WiiForge does not certify its backing device. Reconnects require fresh review. See [SECURITY.md](SECURITY.md) for concurrency and power-loss limits.

## Help improve it

See [CONTRIBUTING.md](CONTRIBUTING.md), [remaining work](docs/roadmap.md) and [evidence behind the defaults](docs/evidence.md). Synthetic tests are not hardware compatibility claims. Report reproducible issues without private recovery files.

WiiForge is independent of Nintendo, Wii Hacks Guide and USB Loader GX. [MIT license](LICENSE) covers WiiForge; upstream projects retain their own licenses.
