# More systems, only if you want them

Get Wii and GameCube working first. Then name one system and one game, or skip this entirely.
The [Wii emulator guide](https://wiki.hacks.guide/wiki/Wii:Emulators) is the starting point;
use each project's current Wii instructions for setup.

```sh
PYTHONPATH=src python3 -m wiiready extras
PYTHONPATH=src python3 -m wiiready extras --system nes --system gba --model original
PYTHONPATH=src python3 -m wiiready extras --skip
```

The selector provides upstream links and a checklist for only your choices. It does not download or
prepare emulator packages, change your core session, or establish hardware compatibility.

Start with FCE Ultra GX (NES), Snes9x GX (SNES), Genesis Plus GX (Sega), or mGBA (Game Boy/GBA).
N64 and PlayStation need per-game research; DS is a limited, often slow option. Arcade requires an
exact emulator/ROM-set match. Sega CD requires the correct lawful region BIOS; Genesis Plus GX does
not support 32X. PSP games are [not a Wii path](https://dev.ppsspp.org/docs/development/porting/);
a PS1 game stored as PBP does not become a PSP game.

The agent should check the selected app's release source, license, storage layout and controller support,
then show an exact file plan and obtain approval before any copy. No ROM bundles, BIOS downloads or
forwarder WADs. Owning a game does not automatically authorize downloading someone else's copy.
Mini needs app-specific USB support; vWii uses Wii apps, not native Wii U builds.
Launch through Homebrew Channel, test controls and save/reload, then decide whether to add another system.
