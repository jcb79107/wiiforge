# Working on WiiForge

Use deterministic Python commands for inspection/planning. Read README and docs/evidence.md first.
Never infer console model, region, cIOS, BootMii eligibility or TV capability from storage contents.
Unknown, conflicting or ambiguous evidence blocks model-sensitive planning. Recognize original,
Family Edition, mini and vWii separately. Do not reuse original-Wii payloads across them.

Inspection, planning, `prepare-plan` and default package verification are read-only.
`prepare` writes only files/directories listed by a reviewed preparation plan, after explicit digest approval.
It refuses overwrites and verifies completed files when resumed. Never run it against actual user media
without authorization for that specific destination and exact plan; our tests use temporary fixtures only. `rehearse` and opt-in
`verify-package --experimental-stage` write files inside newly created private OS temporary directories.
The backing device is not classified: TMPDIR (or the host equivalent) can point to removable media.
Before running either write-capable command, confirm the host temporary directory is appropriate scratch
storage. Do not describe these commands as media-write-free. The temporary rehearsal/staging commands accept no destination; controlled `prepare` does.
The CLI does not download packages, execute downloaded code, format, repair or perform console operations.
Preserve those boundaries. Proposed future destructive operations need
separate explicit approval naming the physical target and data loss, plus fresh device validation.
Do not treat a plan, checkpoint, historical success or GitHub publication approval as write permission.
Never run unrecognized tools/scripts/binaries without per-action approval. No production services.

Keep recovery reports, personal logs, device identifiers, console keys, NAND dumps, games and Nintendo
IOS/WADs out of source, fixtures, issues and releases. Use only synthetic tests and sanitized findings.
Keep package preparation limited to user-supplied local files. Do not publish bundled GameTDB records,
serve prepared database files on a website, or redistribute upstream packages; complete licensing remains unresolved.
No automatic game-ID changes, no broad cleanup, no repair of a failing source, no game/key distribution.
Consult current https://wii.hacks.guide/ and primary upstream releases for each added procedure.
Historical versions are evidence, not package pins. Record hashes, origin and model constraints before
adding any staging capability. Do not call locally computed hashes upstream authenticity.

Run `PYTHONPATH=src python3 -m unittest discover -s tests -v`. Review the exact Git index before push.
Report prepared, content-verified, user-confirmed and console-tested evidence separately. Synthetic
unit tests do not establish hardware support. Reconnects and changed inputs invalidate old plans.
