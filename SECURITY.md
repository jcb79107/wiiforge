# Safety and private reporting

WiiForge is an early read-only planning tool. Its test suite does not certify console safety or hardware compatibility. Do not use a generated plan as approval to write to storage or a console.

## Reporting a problem

For a normal bug, open an issue with a **synthetic reproducer**, command, exit code and expected behavior. Remove account names, local paths, device IDs, serials, labels and any console-specific data. Do not upload raw reports, screenshots containing identifiers, recovery conversations, keys, NAND dumps, games or IOS/WADs.

For a vulnerability, use GitHub's private vulnerability reporting option if it is available on the repository's Security tab. If unavailable, open only a minimal issue requesting a private contact route; omit exploit details and private data. No response-time guarantee is made.

If private material is accidentally published, stop sharing it and notify the repository owner through an available private route. Deleting a file in a new commit does not remove it from history. Rotate exposed credentials where applicable; coordinate history cleanup separately.

## Boundaries

The CLI has no media-write, package execution, formatting, filesystem-repair or console-write path. Future changes that introduce these capabilities require a separate safety review and explicit target-specific approval. Unsupported or uncertain model paths must stay blocked.
