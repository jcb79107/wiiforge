# GameCube through Nintendont

Nintendont is the GameCube part of the normal setup. On Wii hardware this is not a PC-style emulator.
Follow [Nintendont upstream](https://github.com/FIX94/Nintendont) and keep working Wii games unchanged.

1. Use the reviewed `packages/nintendont.yaml` with the [file preparation commands](usage.md).
   Review the exact plan and destination before copying. The app needs `boot.dol`, `meta.xml` and `icon.png`
   in its app directory; do not replace an existing installation or saves without separate review.
2. Use your own lawful game file. `check-gamecube`, `gamecube-plan` and `gamecube-copy` can check and
   prepare raw ISO/GCM files with approval. Layout: `games/ID6/game.iso`, with `disc2.iso` for disc two.
   A header check is not an integrity or compatibility guarantee.
3. Launch Nintendont from Homebrew Channel. Choose the correct storage and test one game with the
   actual controller. Select the appropriate memory-card mode; preserve existing card files.
   Play, save, quit and reload before moving on.
4. In USB Loader GX, select Nintendont as the GameCube loader. Confirm **Nintendont Loader Path**
   points to the app directory and **Main GameCube Path** / **SD GameCube Path** matches your storage.
   Launch that same game and verify the same save loads. Match memory-card settings to the direct test.

Use `journey`'s `gamecube-test` checkpoint only after that console test succeeds. Preparing files alone
never completes it. Family Edition, mini and vWii lack native GameCube controller/memory-card ports
and cannot read GameCube discs; check upstream controller and storage support for the actual model.
WiiReady's own file preparation remains original-Wii/macOS/Linux only.

GX setting names: [upstream paths](https://github.com/wiidev/usbloadergx/blob/enhanced/source/settings/menus/CustomPathsSM.cpp)
and [GameCube settings](https://github.com/wiidev/usbloadergx/blob/enhanced/source/settings/menus/GCGameLoadSM.cpp).
