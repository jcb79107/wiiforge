# Evidence and defaults

Two supplied blueprint copies were byte-identical, as were two recovery copies. They were reviewed privately; original artifacts, identifiers, paths and inventories are excluded from this repository.

## Recovered observations (historical, not current hardware validation)

- A user reported System Menu 4.3U, functioning Homebrew Channel, completed NAND verification and an opening USB Loader GX.
- Original Wii identification was a historical interpretation; exact model code was not recorded. Every new run requires explicit model evidence.
- Priiloader installation/recovery steps were acknowledged together. Forwarder completion and installed-file autoboot success were reported.
- The recovered cIOS arrangement was d2x-v11-beta3, revision 65535: 248/38, 249/56, 250/57, 251/58. This is evidence, not an automatic install specification.
- SD FAT32 and USB MBR/FAT32/32 KiB geometry were historical inspection reports, not checks of currently attached hardware.
- A private backup was checksum-checked in the recovery process; that does not establish restore viability. WiiReady neither imports nor distributes it.

The user also reports completing manual setup on two different Wiis. This is process experience, not evidence that WiiReady ran on either console; model-specific and display compatibility remain unverified.

## Provisional settings

Display type, cable, adapter, aspect and output mode were not established. Update-blocking and deflicker settings were part of combined acknowledgments, not an independently verified settings dump. Return To, memory-card emulation and controller preferences were suggestions. Optional themes, online services, emulators and save tools were aspirations. GameCube files were staged, but Wii/GameCube gameplay tests were not confirmed.

Accordingly the default chooses USB Loader GX and offers optional autoboot review, preserving video settings and leaving GameCube review off. Historical success is never prefilled into new evidence or checkpoints. Package versions in old staging metadata are not verified executable versions and are not fresh-install pins.

## Current source review

Reviewed 2026-11-04:
- https://wii.hacks.guide/ — choose the console-specific path and establish recovery evidence.
- https://wii.hacks.guide/cios — explicit model separation; do not mix Wii, mini and vWii IOS/System Menu payloads.
- https://wii.hacks.guide/wii-loaders — USB Loader GX prerequisites, upstream links and storage considerations.

The MVP links to these procedures rather than reproducing a fixed console-write recipe. The pinned USB Loader GX package has since passed host-side integrity checks and disposable experimental staging; see [package evidence](../packages/README.md). No package has been executed or tested on a console by WiiReady. Licensing and installation remain blocked.

## Gamer journey review — 2026-11-06

Current Get Started links Windows users to ModMii, SD-card Wii users to Wilbrand, and mini users to BlueBomb. The loader guide now supports SD for Wii games; USB-only historical advice is not a universal requirement. The new intake routes to those guides without expanding the checked installation recipe. HBC/BootMii, NAND backup, Priiloader, cIOS and disc-dumping pages were reviewed for sequencing; Nintendont upstream supplies the GameCube layout/controller reference. See [the playbook](playbook.md) for linked sources and handoffs. No software test here establishes physical-media, console or display compatibility.
