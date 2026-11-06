# Safety and private reporting

WiiReady provides read-only inspection/planning, temporary preparation experiments and explicitly approved file copying. Its test suite does not certify console safety or hardware compatibility. Do not use a generated plan as approval to write to storage or a console.

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

`prepare`, `batch-prepare`, `gamecube-copy` and `wii-join` are write-capable commands with an explicit destination and saved plan approval.
They never overwrite an existing file: matching content is verified and skipped; mismatches block preparation.
Run it only after reviewing every planned path and authorizing that destination. Keep exclusive access to
the destination while it runs; directory descriptors and no-follow opens do not protect against an adversary
with the same account or physical device removal. Plan identity is the canonical root path plus filesystem device/inode, not persistent physical-media identity.
Different-device descendants are rejected, but same-device bind mounts and same-account races are not excluded.
Reconnections require renewed inspection and approval even if those values match. No physical-media compatibility
testing has been completed.

Game-copy plans contain private source paths, game IDs and full-file hashes. Keep raw plans/reports local;
do not publish or transmit them through chats, remote-agent/tool transcripts, telemetry or cloud storage.
`plan-summary` emits aggregate preparation counts/bytes without those fields. It does not inspect current
sources/destinations or replace the user's local review of the exact plan before approval.
Source files are read-only and size-bounded; keep exclusive access to both sources and destination.
Copy hashes prove byte equality to the supplied files, not a complete/correct dump, lawful provenance or gameplay.
On POSIX, handled failures remove only a newly created partial file. Windows leaves newly created partial files for explicit review. Power loss or forced termination can leave a partial
file that blocks resume; inspect it and obtain separate approval before any cleanup. Nothing is auto-repaired.

The CLI has no package execution, formatting, filesystem-repair or console-write path. Future changes that introduce these capabilities require a separate safety review and explicit target-specific approval. Unsupported or uncertain model paths must stay blocked.

Windows writes use native handles denying write/delete sharing, reject reparse points in source/destination
ancestors, and create files only with CREATE_NEW. Existing sources are held read-only while accessed.
Root identity uses volume serial/file index and path; it is not persistent physical-media identity.
Volume inspection does not prove USB bus type or Wii layout. No elevation, raw disk writes or formatting is used.
API reference: [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).
