# Roadmap

A small evidence-driven roadmap, not a compatibility promise or dated release schedule.

## Implemented — planning and controlled preparation

Implemented: a beginner intake with guide routing and profile drafts, a buying-to-gameplay playbook, strict profiles, conservative macOS metadata inspection, original-Wii 4.3U manual planning, ordered resume checks, a hardware-free demo, offline package verification, bounded archive validation, disposable staging and explicitly approved no-overwrite file preparation. Synthetic tests cover interruption/resume, conflicts, capacity failures and unsafe archives.

**Next acceptance gate:** an opt-in macOS inspection session with no writes to media. Verify the actual diskutil field names and behavior for suitable FAT32/MBR media, internal disks, missing identity and reconnects. Keep raw observations private; add only redacted, synthetic-equivalent fixtures. Document false rejections rather than silently weakening checks. Test the supported Python/host matrix before claiming it.

## Remaining — package license review

An initial USB Loader GX metadata pin and offline byte checker are available in [packages](../packages/README.md). Archive validation and host-side staging are implemented. License approval, redistribution and console installation remain blocked.

Review current official guidance and primary upstream releases. Record per-artifact origin, version, license, model constraints, expected size and hash. Distinguish upstream authenticity from a locally computed checksum. Do not execute downloads, bundle proprietary console content or reuse historical metadata as a current pin.

**Acceptance gate:** establish applicable license terms and notice requirements for the complete pinned artifact from primary evidence. The current manifest and synthetic rejection tests verify origin constraints, model and hash/size checks; those checks do not establish licensing. Downloads/execution are not implied by this milestone.

## Remaining — real-media preparation validation

A synthetic-only `rehearse` command now exercises bounded copies, read-back verification and cleanup in a private temporary host directory. It cannot accept release packages or a destination. Separately, `verify-package --experimental-stage` can verify a pinned snapshot in disposable host storage, with exclusive writes, bounded read-back and capacity checks. Controlled `prepare-plan` / `prepare` now support explicitly approved destinations with no overwrites and content-verified resume. Only temporary fixtures have been tested; physical-media validation and licensing approval remain outstanding.

Start in a temporary host directory. Reject archive traversal and symlinks, check capacity and FAT32 file-size limits, preserve unrelated files and stop on I/O errors. Track partial work with source identity and expected content, not file presence.

**Acceptance gate:** separately authorized preparation on disposable media, followed by independent content verification and observations of actual filesystem behavior. Synthetic interruption/resume, preexisting-file, insufficient-space and corrupt-input tests already pass; they do not establish power-loss or reconnect safety. Any write to real media requires fresh target validation and separate approval. Formatting and repair remain outside the workflow.

## Later — earn broader support

Add each original-Wii region/menu, Family Edition, Wii mini and vWii path separately after current authoritative review and targeted validation. Add CRT/HD and gameplay evidence as individual observations. Never convert one successful loader launch into a general compatibility claim.

No release date is promised. See [the support table](../README.md#support-status) for what works today.
