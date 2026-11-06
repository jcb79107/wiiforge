# More systems, only if you want them

Choose extra systems before the file copy to avoid another card swap, or skip entirely.
Get Wii and GameCube working first on the console, then test one extra app at a time.
The [Wii emulator guide](https://wiki.hacks.guide/wiki/Wii:Emulators) is the starting point;
use each project's current Wii instructions for setup.

```sh
PYTHONPATH=src python3 -m wiiready extras
PYTHONPATH=src python3 -m wiiready extras --system nes --system gba --model original
PYTHONPATH=src python3 -m wiiready extras --skip
```

The selector provides upstream links and a checklist for only your choices. It changes no core progress.
NES, SNES and Game Boy/GBA have [batch file preparation](#one-computer-side-pass); other choices stay guided.

Start with FCE Ultra GX (NES), Snes9x GX (SNES), Genesis Plus GX (Sega), or VBA GX (Game Boy/GBA; mGBA is an alternative).
N64 and PlayStation need per-game research; DS is a limited, often slow option. Arcade requires an
exact emulator/ROM-set match. Sega CD requires the correct lawful region BIOS; Genesis Plus GX does
not support 32X. PSP games are [not a Wii path](https://dev.ppsspp.org/docs/development/porting/);
a PS1 game stored as PBP does not become a PSP game.

The agent should check the selected app's release source, license, storage layout and controller support,
then show an exact file plan and obtain approval before any copy. No ROM bundles, BIOS downloads or
forwarder WADs. Owning a game does not automatically authorize downloading someone else's copy.
Mini needs app-specific USB support; vWii uses Wii apps, not native Wii U builds.
Launch through Homebrew Channel, test controls and save/reload, then decide whether to add another system.

## One computer-side pass

For **original Wii on macOS/Linux**, the agent can prepare FCE Ultra GX 4.0.4, Snes9x GX 5.0.5,
and VBA GX 3.0.5 together with selected existing WiiReady packages, including GX and Nintendont.
GB and GBA use one VBA GX package, not two copies. Other models remain guide-only.

Fetch just the chosen manifest URLs to private host staging. These pins select official **Wii ZIPs**,
not GameCube/Wii U builds or channel installers. WiiReady checks size/hash and the three app files plus
empty game/save folders. No games, BIOS or save files are included. Downloads are not executed.

Example with two already downloaded archives and an existing, separately identified destination:

```sh
PYTHONPATH=src python3 -m wiiready batch-plan \
  --package packages/fceugx.yaml /private/downloads/FCEUltraGX-4.0.4-Wii.zip \
  --package packages/snes9xgx.yaml /private/downloads/Snes9xGX-5.0.5-Wii.zip \
  --model original --destination /chosen/destination > /private/batch-plan.json
```

Review every file and the destination locally. After explicit approval, repeat the same arguments with
`batch-prepare --plan /private/batch-plan.json --approve-plan APPROVED_DIGEST` instead of `batch-plan`.
Keep the raw plan local. The command rechecks every package and destination before copying.
It never formats or overwrites; conflicting app versions stop the whole preflight. Existing saves stay put.
Identical completed files allow a retry with the same plan. This is not an atomic transaction: a failure
can leave completed new files, and power-loss partial files require manual review. Do not unplug during copying.

The upstream apps support SD/USB, but WiiReady has not tested this flow on hardware. File preparation
is not console installation or a gameplay test. Eject safely, launch each selected app from Homebrew Channel,
then verify controls and save/reload. Licensing review remains pending; WiiReady distributes no app binaries.
Sources: [FCE Ultra GX](https://github.com/dborth/fceugx/releases/tag/4.0.4),
[Snes9x GX](https://github.com/dborth/snes9xgx/releases/tag/5.0.5),
[VBA GX](https://github.com/dborth/vbagx/releases/tag/3.0.5).
