# Working on WiiForge

Use deterministic Python commands for inspection/planning. Read README and docs/evidence.md first.
Never infer console model, region, cIOS, BootMii eligibility or TV capability from storage contents.
Unknown, conflicting or ambiguous evidence blocks model-sensitive planning. Recognize original,
Family Edition, mini and vWii separately. Do not reuse original-Wii payloads across them.

The current CLI never writes media, downloads packages, executes downloaded code, formats, repairs,
or performs console operations. Preserve that boundary. Proposed future destructive operations need
separate explicit approval naming the physical target and data loss, plus fresh device validation.
Do not treat a plan, checkpoint, historical success or GitHub publication approval as write permission.
Never run unrecognized tools/scripts/binaries without per-action approval. No production services.

Keep recovery reports, personal logs, device identifiers, console keys, NAND dumps, games and Nintendo
IOS/WADs out of source, fixtures, issues and releases. Use only synthetic tests and sanitized findings.
No automatic game-ID changes, no broad cleanup, no repair of a failing source, no game/key distribution.
Consult current https://wii.hacks.guide/ and primary upstream releases for each added procedure.
Historical versions are evidence, not package pins. Record hashes, origin and model constraints before
adding any staging capability. Do not call locally computed hashes upstream authenticity.

Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`. Review the exact Git index before push.
Report prepared, content-verified, user-confirmed and console-tested evidence separately. Synthetic
unit tests do not establish hardware support. Reconnects and changed inputs invalidate old plans.
