# Safety and private reporting

WiiForge provides read-only inspection/planning and opt-in temporary file preparation experiments. Its test suite does not certify console safety or hardware compatibility. Do not use a generated plan as approval to write to storage or a console.

## Reporting a problem

For a normal bug, open an issue with a **synthetic reproducer**, command, exit code and expected behavior. Remove account names, local paths, device IDs, serials, labels and any console-specific data. Do not upload raw reports, screenshots containing identifiers, recovery conversations, keys, NAND dumps, games or IOS/WADs.

For a vulnerability, use GitHub's private vulnerability reporting option if it is available on the repository's Security tab. If unavailable, open only a minimal issue requesting a private contact route; omit exploit details and private data. No response-time guarantee is made.

If private material is accidentally published, stop sharing it and notify the repository owner through an available private route. Deleting a file in a new commit does not remove it from history. Rotate exposed credentials where applicable; coordinate history cleanup separately.

## Boundaries

`rehearse` and `verify-package --experimental-stage` write into private OS temporary directories and
normally remove them on completion or failure. The tool does not verify the backing device of TMPDIR
(or its host equivalent); it could be removable storage. Confirm appropriate scratch storage before
running either command. Forced termination or cleanup failure can leave files behind. Neither command
accepts a destination argument. Default package verification and inspection remain read-only.

`prepare` is a separate write-capable command with an explicit destination and saved plan approval.
It never overwrites an existing file: matching content is verified and skipped; mismatches block preparation.
Run it only after reviewing every planned path and authorizing that destination. Keep exclusive access to
the destination while it runs; directory descriptors and no-follow opens do not protect against an adversary
with the same account or physical device removal. Plan identity is the canonical root path plus filesystem device/inode, not persistent physical-media identity.
Different-device descendants are rejected, but same-device bind mounts and same-account races are not excluded.
Reconnections require renewed inspection and approval even if those values match. No physical-media compatibility
testing has been completed.

The CLI has no package execution, formatting, filesystem-repair or console-write path. Future changes that introduce these capabilities require a separate safety review and explicit target-specific approval. Unsupported or uncertain model paths must stay blocked.
