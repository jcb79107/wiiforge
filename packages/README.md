# Package provenance

`usb-loader-gx.yaml` records metadata reviewed on 2026-11-05 from the
[upstream GitHub release API](https://api.github.com/repos/wiidev/usbloadergx/releases/tags/v4.0-r1283).
[Wii Hacks Guide](https://wii.hacks.guide/wii-loaders) links to that upstream project.
The ZIP's size and SHA-256 are supplied by GitHub's release API, not locally invented.
This is a pinned observation, not a promise that the version remains current or a signed publisher attestation.

The repository license API returned 404 and no root license file appeared in the reviewed tag's tree.
Pinned source review found component-specific notices:
- [GUI header](https://github.com/wiidev/usbloadergx/blob/v4.0-r1283/source/GUI/gui.h): permission with origin, modification and notice-preservation conditions.
- [FreeTypeGX](https://github.com/wiidev/usbloadergx/blob/v4.0-r1283/source/FreeTypeGX.cpp): LGPL-3.0-or-later.
- [libpng header](https://github.com/wiidev/usbloadergx/blob/v4.0-r1283/portlibs/include/png.h): identifies the libpng license.

These observations do not establish licensing for the complete release or all bundled components.
`license_review` therefore remains `pending`. No binary has been downloaded, extracted, executed or redistributed here.

If you already have the exact release ZIP in a private host folder:

```sh
PYTHONPATH=src python3 -m wiiforge verify-package \
  --manifest packages/usb-loader-gx.yaml \
  --artifact /your/private/folder/usbloadergx_r1283.zip --model original --check-archive
```

The command reads a regular local file and compares its size/hash. It does not fetch the URL or extract the ZIP.
With `--check-archive`, hash verification runs first, then ZIP metadata checks reject traversal/nonportable names,
case collisions, file/directory conflicts, links/special files, encryption, unsupported compression and excessive
entry counts, sizes or compression ratios. No files are extracted or decompressed. The result reports
`archive.status: metadata-checked`; CRCs, local headers, payload contents and expected app layout are **not verified**.
Without the flag only size/hash are checked.

Input size is limited to 64 MiB before ZIP parsing, including direct use of the metadata checker.
The 4,096-entry check runs **after** Python's `ZipFile` parses the central directory; it is not a
preallocation or hard memory/CPU bound. A dense central directory can still consume substantial memory.
This local, reviewed-pin workflow is not suitable as an untrusted upload service. A future service or
broader archive intake needs isolated resource limits before parsing, not just this entry-count check.
Reserved-name checks include Windows' superscript COM/LPT device names and their extensions, per
[Microsoft's naming rules](https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file).

The [pinned build workflow](https://github.com/wiidev/usbloadergx/blob/v4.0-r1283/.github/workflows/main.yml)
stages `boot.dol`, `icon.png` and `meta.xml` under `apps/usbloader_gx`. This is build-layout evidence, not proof
of the unexamined release ZIP's members. Synthetic tests do not validate that release's archive.

A match returns `content-verified` **and exit 2**, because license review, archive content and hardware validation
still block installation. A mismatch also exits 2 with an error. The manifest itself must be trusted/reviewed;
editing its hash can make arbitrary bytes match. This checker is not a signature verifier or malware scanner.
The model list is WiiForge's limited review scope, not an upstream compatibility claim.

Before staging: review licensing, recheck release metadata, verify archive content/layout and capacity, then test preservation and interrupted copies in temporary directories. Media writes remain separate.
