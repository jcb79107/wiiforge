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
`license_review` therefore remains `pending`. The pinned ZIP was downloaded to a temporary host directory for the read-only review below; no payload was extracted, executed, committed or redistributed.

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
stages `boot.dol`, `icon.png` and `meta.xml` under `apps/usbloader_gx`. The read-only release inspection below confirms that layout for this exact ZIP. Synthetic tests alone do not validate a release archive.

A match returns `content-verified` **and exit 2**, because license review, archive content and hardware validation
still block installation. A mismatch also exits 2 with an error. The manifest itself must be trusted/reviewed;
editing its hash can make arbitrary bytes match. This checker is not a signature verifier or malware scanner.
The model list is WiiForge's limited review scope, not an upstream compatibility claim.

Before staging: review licensing, recheck release metadata, verify archive content/layout and capacity, then test preservation and interrupted copies in temporary directories. Media writes remain separate.

## Exact-release inspection — 2026-11-05

The official pinned ZIP was retrieved into a temporary host directory. Its 11,160,243-byte size and
SHA-256 matched the manifest before any ZIP parsing. The existing validator passed without relaxing checks.
It reports 30 entries and 37,811,633 declared uncompressed bytes. All 27 file members were then streamed
in bounded chunks through Python's ZIP reader with matching lengths and successful CRC checks; nothing
was extracted to disk or executed. This one-off review is separate from the CLI's metadata-only check.

The member list contains three directories, `boot.dol` (4,483,840 bytes), `icon.png`, `meta.xml`,
23 language files and `wiitdb.xml`, all under `apps/usbloader_gx`. The ZIP carries no Unix file-type
bits; the validator accepts this normal ZIP representation. `meta.xml` identifies version `4.0 r1283`.
No member name identifies a LICENSE, COPYING, NOTICE or README file, and `meta.xml` has no license terms.
That is not proof that binaries contain no notices or that distribution rights are absent: complete
component and distribution-obligation review is still outstanding.

CRC/size checks establish readable archive members, not trustworthy executable behavior, license clearance
or console compatibility. No physical media or console was accessed. Installation remains blocked.
