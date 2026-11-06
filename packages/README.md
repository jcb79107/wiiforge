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

The hash-verified ZIP’s `wiitdb.xml` header identifies GameTDB and describes Wii-related project use,
but requires permission for website use. This component notice does not resolve the complete package’s
license. WiiForge does not bundle this database, publish its records or provide a web viewer. Package
commands operate on user-supplied local files and report paths, sizes and hashes rather than database
contents. Keep prepared files private; do not use this workflow to redistribute the package or place
the database in a website’s served directory. The destination checker cannot determine whether another
application serves a directory. Local preparation is not a legal clearance or redistribution approval.

CRC/size checks establish readable archive members, not trustworthy executable behavior, license clearance
or console compatibility. No physical media or console was accessed. Installation remains blocked.

## Experimental disposable staging

Add `--experimental-stage` to `verify-package` to rehearse preparation of a local, pinned package.
This is opt-in host-only scratch work: it accepts no destination, does not select drives or console storage, and never runs any staged program.
It follows the host OS temporary-directory configuration; it does not classify that backing device.
Use a host with its OS temporary directory on local scratch storage, never a removable-media mount.
The manifest remains a trusted reviewed input, not proof of publisher authenticity.

The verifier captures a bounded snapshot while hashing the open regular file, checks its size/hash and
metadata stability, then passes those same immutable bytes to staging. ZIP metadata validation runs before
creating the private temporary directory. A free-space preflight reserves declared contents plus 1 MiB;
this is not a reservation against concurrent disk usage, so I/O failures still abort and clean up.
Files are created exclusively, streamed with size/CRC checks and verified again using bounded read-back
hashes. All staged files are deleted before a success result is returned. Ordinary exceptions and keyboard
interrupts also clean up; forced termination can leave scratch files behind. Persistent resume is not implemented.

`staging.status` becomes `experimental-stage-verified`, while the top-level result still has blockers and
exit code 2. Licensing, installation safety and real hardware behavior remain unapproved. The package's
metadata-only `archive` field is null in this mode; staging performs its own required ZIP check on the snapshot.

On 2026-11-05, the pinned release completed this temporary rehearsal with 27 files verified and removed.
No package bytes were committed, published or executed. This does not establish that its executable is safe
or that redistribution obligations have been satisfied.

For explicitly approved, persistent file preparation, see [controlled preparation](../docs/usage.md#controlled-file-preparation).
It uses the same package pin and original-Wii restriction, preserves installation blockers, and refuses overwrites.
Only isolated synthetic destination fixtures have been tested for that path; the real ZIP was tested only in disposable staging.

## Nintendont local files — 2026-11-06

`nintendont.yaml` pins the [official tree at c683db3](https://github.com/FIX94/Nintendont/tree/c683db301c941a64e6fe5cef6ac079bd1a726074).
The [upstream instructions at that commit](https://github.com/FIX94/Nintendont/blob/c683db301c941a64e6fe5cef6ac079bd1a726074/README.md)
map `loader/loader.dol` to `apps/Nintendont/boot.dol`, with `nintendont/meta.xml` and `nintendont/icon.png` beside it.
The three files total 1,649,855 bytes. Their Git blob IDs were obtained from GitHub's tree API; fetched bytes matched those IDs before local SHA-256 calculation. These are **locally calculated pins**, not publisher signatures or independently supplied upstream SHA-256 digests.

The CLI accepts an existing private folder containing `loader.dol`, `meta.xml` and `icon.png`.
It checks sizes, SHA-256, Git blob identities and metadata stability, then builds a deterministic ZIP only in memory
for the existing preparation engine. Fixed names prevent manifest-selected output paths; extra files are ignored.
Nothing is fetched, executed or bundled by the CLI. The default verification path writes nothing.
This path currently requires POSIX and explicitly confirmed original-Wii selection, regardless of upstream's wider support.

The source tree contains component-specific COPYING/LICENSE files; that is not a complete distribution review.
`license_review` stays pending. No game, BIOS, save, key or upstream binary is included in this repo.
Read-only verification of the actual pinned files passed; destination preparation and resume were tested with synthetic files only.
See [Nintendont preparation](../docs/usage.md#prepare-nintendont-from-local-files) for commands.
