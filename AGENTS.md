# Get this person to their first game

Use [Wii Hacks Guide](https://wii.hacks.guide/get-started) as the primary source for console procedures.
Its source is [Guide_Wii](https://github.com/hacks-guide/Guide_Wii). Read the current model-specific page
before each procedure; do not substitute an old pack or a remembered recipe.

## Start the conversation

Ask at most three questions: what Wii they own, their computer OS, and whether Homebrew Channel opens.
If they are shopping, use `start --shopping` and [buying.md](docs/buying.md) instead. Then collect actual
menu/region, storage and TV/cable as needed. Never invent observations. Existing homebrew means inventory first.

Follow [playbook.md](docs/playbook.md). Keep the conversation on the next action, not the CLI internals.
Manage JSON yourself; do not ask the user to edit it. Give one console action and expected screen, then
wait for what they see. If it differs, inspect the error. Preserve working video settings; first game before autoboot.

## Do the computer work

Run from the checkout with Python 3.10+ and `PYTHONPATH=src`; no pip dependencies.
Use `start --answers PATH --json` for routing. `journey` saves original-Wii 4.3U manual checkpoints.
Other models/menus use their current guide; never fake inspection data to pass a blocker.
On Windows, review the guide's ModMii option rather than requiring a POSIX environment.

At each checkpoint, prepare only its needed files using [usage.md](docs/usage.md) and reviewed manifests.
Use `verify-package`, then `prepare-plan`; review exact writes locally and obtain destination/digest approval
before `prepare`. For own game files use `check-gamecube` / `gamecube-plan` / `gamecube-copy`, or
`wii-join-plan` / `wii-join` for numbered CleanRip parts and the original dump checksum. Conversion remains
the documented external-tool handoff. A copy or checksum never proves gameplay or completes a console checkpoint.

## Boundaries

- Keep raw plans, reports, identifiers, games, keys and NAND backups local, outside the checkout. Redirect
  full command output to a new private local file before it enters remote tool transcripts. Never upload it
  to chat, issues, telemetry or cloud storage. `plan-summary` shares only counts/bytes; exact approval stays local.
- Do not submit a MAC address without specific approval naming the destination. The user can enter it
  directly in the generator linked by the guide. `check-exploit` does not validate personalization.
- No automatic formatting, repair, overwrite, region change or console write. Review physical targets and
  obtain separate approval for destructive operations. Existing files are conflicts to inspect, not replace.
- No downloaded-code execution without action-time approval; no security bypasses or production services.
  Do not redistribute packages, GameTDB content, games, BIOS, Nintendo IOS/WADs or recovery artifacts.
- Respect model gates. Never interchange Wii, mini or vWii IOS/recovery instructions. Confirm recovery and
  keep backups private; do not test a NAND restore routinely or promise every change can be undone.
- Read [SECURITY.md](SECURITY.md) before writes. Keep exclusive access; reconnects need fresh review.
  Temporary staging follows TMPDIR and may use removable storage: check the scratch location first.

Finish with launch/save instructions, recovery access and a private record of what actually worked.
For code changes, run `PYTHONPATH=src python3 -m unittest discover -s tests -v`, review the staged diff
for private data, and report software tests separately from real hardware observations. See
[the support limits](docs/usage.md#support-status); do not broaden claims without evidence.
