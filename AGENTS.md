# Help this person get to a game night

If the user gives you only this repo link, start helping; do not ask them to understand the CLI first.
Read README, docs/playbook.md and docs/buying.md. Explain the goal in one sentence, then ask at most
three related questions at a time: what Wii they have, what computer they use, and whether they already
have homebrew. Follow with menu/region, TV/cable, storage, controllers and Wii/GameCube goals. If they
are shopping, ask country/budget and reuse what they own. Never invent observations to get past a check.

Run `PYTHONPATH=src python3 -m wiiforge start` for the intake questions. Optional private JSON answers
produce a tailored route and profile/evidence drafts with `start --answers PATH --json`. You manage these
files; the beginner should not need to edit JSON. For original-Wii 4.3U with computer/homebrew/storage observations, use `journey`
to save/resume console outcomes privately, with no invented disk inspection. Keep a private progress note with observations,
current step, completed outcomes, exact versions, approval scope and next action. Resume from evidence,
not memory of a generic tutorial. Existing homebrew means inventory first, not reinstall everything.

Use docs/playbook.md to own the entire journey: buying → discovery → computer preparation → console
checkpoints → Wii gameplay → optional GameCube → optional autoboot → useful handoff. Read the live
model-specific guide before each procedure. On Windows, offer current ModMii guidance; don't silently
run or install it. On other hosts, review the appropriate guide route. WiiForge's narrow checked planner
is not the full guide's compatibility list. Never forge macOS inspection data for Windows or SD storage.

Do the authorized computer work, rather than handing the user a wall of terminal commands. Explain
what will change and show the exact target/write plan before media writes. Use the reviewed manifests in packages/ for GX, Nintendont, recovery, HackMii and d2x installer files with the existing verify/prepare flow. For unsupported packages,
say what review/preparation is still manual; never edit the GX pin to bypass package validation.
Use journey output's `computer_preparation` for the current step. Ask about Wii internet access only at cIOS;
`--wii-network online` skips the unnecessary offline acquisition route. Never upload a MAC without
specific approval naming the destination. `check-exploit` is only a local partial check, not personalization validation.
Give one console action and its expected outcome at a time, then wait for what the user actually sees.
Before GameCube file organization, use `check-gamecube` on the user's own raw ISO/GCM files to check
headers, disc order and suggested naming. It neither verifies the whole dump nor authorizes a copy.
Do not mark a checkpoint passed because files were copied. Finish with launch/save/recovery instructions
and a private record of what was actually tested. USB Loader GX is the default; preserve video settings,
review Nintendont when requested, and defer autoboot until recovery and gameplay work.

## Safety and implementation rules

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
