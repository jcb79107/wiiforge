# What to buy (and what to keep)

No console yet? Your assistant can run `python3 -m wiiforge start --shopping` from the configured checkout (add `--json` for structured output). This asks three shopping questions without requesting a console label/menu or creating installation evidence.

First tell your assistant your country, budget, TV inputs, what you already own, and whether you want GameCube discs/controllers. Ask it to check current listings and returns before recommending an exact product. No model of card, enclosure or HDMI adapter has been hardware-certified by WiiForge. Avoid paying for a seller's preloaded game library.

## A practical starting basket

| Item | Starting choice | Check before paying |
| --- | --- | --- |
| Console | Original Wii **RVL-001**, working disc drive, matching power supply | Ask for a photo of the model label with serial hidden, GameCube ports and a disc running. Do not buy by case color alone. |
| Wii controls | Wii Remote, Nunchuk, sensor bar and batteries | Confirm pointer, buttons and battery compartment condition. Game-specific accessories are separate. |
| SD + reader | Reputable SD card from an authorized seller; reader matching your computer | For a typical 4.x setup, 32 GB is a modest apps/recovery starting point; use larger storage if games will live here. Pre-4.0 stock menus require 2 GB or less at the exploit stage. |
| Game storage | Existing good SD card or USB HDD first | Current GX supports SD. For a bigger collection, a 500 GB–1 TB HDD is a reasonable starting budget, not a requirement. Size from your own library. Avoid USB flash sticks as the default. |
| TV connection | Keep a working cable while setting up | Check actual sockets and accepted resolutions before buying component cables, an HDMI adapter or a scaler. |
| GameCube controls | Original controller if using RVL-001 ports; otherwise a specifically supported Nintendont controller | Check the exact controller/adapter against upstream; do not assume any USB gamepad works. |

The original Wii recommendation favors a straightforward disc-dumping and controller path. Stock Family Edition, mini and vWii cannot dump GameCube discs; this does **not** mean every model is incapable of playing backups through homebrew. See the [disc-dumping guide](https://wii.hacks.guide/dump-games) and [Nintendont upstream](https://github.com/FIX94/Nintendont). WiiForge's own Family/mini/vWii installation paths remain blocked.

## Storage tradeoffs

SD keeps the setup tidy; USB HDD provides room without buying a high-capacity card. HDDs need suitable power: a 3.5-inch enclosure needs its own supply. SSDs are an option if already owned, but don't buy one expecting a major Wii USB speed improvement. The enclosure/controller matters as well as the drive. Keep a return option.

Use FAT32 for the shared Wii/GameCube starting setup. A card sold as exFAT needs separate formatting review and data backup; never format just because an assistant selected a drive. FAT32's file-size limit means large Wii backups need proper splitting, not renaming. An old WBFS **partition** is different from `.wbfs` game files. See the current [storage FAQ](https://wii.hacks.guide/faq#storage-device-faq) and [loader layout](https://wii.hacks.guide/wii-loaders).

## CRT or modern TV?

For a CRT, retain its known-working signal and aspect ratio. For a modern TV, check whether it accepts the console's existing signal directly; an adapter or scaler is a separate purchase decision. Ask for the TV model and adapter model, not just “HDMI.” Do not force progressive output, widescreen patches or deflicker changes globally. Test one game and change one setting at a time. These are conservative setup choices, not a display compatibility matrix.

A memory card is a choice, not an automatic purchase: Nintendont supports memory-card emulation. Confirm saves work and back them up before choosing physical cards or enabling unusual peripherals. See [upstream features and limitations](https://github.com/FIX94/Nintendont).
