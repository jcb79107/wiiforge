<p align="center">
  <img src="docs/assets/wiiready.png" alt="WiiReady" width="100%">
</p>

# Your Wii, ready for game night

Give this repo to your AI coding agent. It helps you buy what you need, prepare files on your computer,
and follow **[Wii Hacks Guide](https://wii.hacks.guide/get-started)** on your console.
USB Loader GX for Wii games. Nintendont for GameCube. Your own lawful games, your setup.

## Get started

Paste this into your agent:

> Help me set up my Wii using https://github.com/jcb79107/wiiready. Read AGENTS.md. Ask what I own, help with the computer work, and walk me through Wii Hacks Guide one step at a time. Use USB Loader GX and Nintendont for Wii and GameCube. Ask before changing my storage or console, and keep my private files local.

No console yet? Tell it your budget and what you want to play. Already modded? Tell it what works.
You handle the Wii remote; your agent handles the supported computer work and explains the rest.

**[What to buy](docs/buying.md)** · **[Extra systems](docs/extras.md)** · **[Picture setup](docs/video.md)** · **[Setup flow](docs/playbook.md)** · **[Commands](docs/usage.md)**

## What it handles

- Hardware questions and the right guide route.
- Checking and preparing local homebrew files, with approval and no overwrites.
- Resuming setup checkpoints, organizing raw GameCube files and joining CleanRip parts.

Console steps stay manual. Wii format conversion uses a guided external tool.
File preparation currently needs macOS/Linux and original-Wii selection; other models follow their
own guide. See [support details](docs/usage.md#support-status) and [safety](SECURITY.md).

## Run it yourself

With Python 3.10+ and Git:

```sh
git clone https://github.com/jcb79107/wiiready.git
cd wiiready
PYTHONPATH=src python3 -m wiiready start
```

Add `--shopping` if you do not own a Wii. No pip dependencies.
[Windows and command setup](docs/usage.md#run-the-tools) · [Contributing](CONTRIBUTING.md)

Modding instructions: [Wii Hacks Guide](https://wii.hacks.guide/) / [Guide_Wii](https://github.com/hacks-guide/Guide_Wii).
WiiReady is independent of those projects and Nintendo. [MIT license](LICENSE); upstream tools retain their own licenses.
