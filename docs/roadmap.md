# Roadmap

A small evidence-driven roadmap, not a compatibility promise or dated release schedule.

## Now — make the read-only path reliable

Implemented: strict profiles, conservative macOS metadata inspection, original-Wii 4.3U manual planning, ordered resume checks, a hardware-free demo and synthetic safety tests.

**Next acceptance gate:** an opt-in macOS inspection session with no writes to media. Verify the actual diskutil field names and behavior for suitable FAT32/MBR media, internal disks, missing identity and reconnects. Keep raw observations private; add only redacted, synthetic-equivalent fixtures. Document false rejections rather than silently weakening checks. Test the supported Python/host matrix before claiming it.

## In progress — reviewed package manifests

An initial USB Loader GX metadata pin and offline byte checker are available in [packages](../packages/README.md). License approval, archive validation and staging remain blocked.

Review current official guidance and primary upstream releases. Record per-artifact origin, version, license, model constraints, expected size and hash. Distinguish upstream authenticity from a locally computed checksum. Do not execute downloads, bundle proprietary console content or reuse historical metadata as a current pin.

**Acceptance gate:** a reviewable manifest and synthetic rejection tests for wrong model, missing origin, stale pins and hash/size mismatch. Downloads/execution are not implied by this milestone.

## In progress — non-destructive staging

A synthetic-only `rehearse` command now exercises bounded copies, read-back verification and cleanup in a private temporary host directory. It cannot accept release packages or a destination. Separately, `verify-package --experimental-stage` can verify a pinned snapshot in disposable host storage, with exclusive writes, bounded read-back and capacity checks. Persistent staging/resume and licensing approval are still outstanding.

Start in a temporary host directory. Reject archive traversal and symlinks, check capacity and FAT32 file-size limits, preserve unrelated files and stop on I/O errors. Track partial work with source identity and expected content, not file presence.

**Acceptance gate:** interruption/resume, preexisting files, insufficient space and corrupt-input tests. Any later write to real media requires fresh target validation and separate approval. Formatting and repair remain outside the default workflow.

## Later — earn broader support

Add each original-Wii region/menu, Family Edition, Wii mini and vWii path separately after current authoritative review and targeted validation. Add CRT/HD and gameplay evidence as individual observations. Never convert one successful loader launch into a general compatibility claim.

No release date is promised. See [the support table](../README.md#support-status) for what works today.
