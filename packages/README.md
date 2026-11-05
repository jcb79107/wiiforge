# Package provenance

`usb-loader-gx.yaml` records metadata reviewed on 2026-11-05 from the
[upstream GitHub release API](https://api.github.com/repos/wiidev/usbloadergx/releases/tags/v4.0-r1283).
[Wii Hacks Guide](https://wii.hacks.guide/wii-loaders) links to that upstream project.
The ZIP's size and SHA-256 are supplied by GitHub's release API, not locally invented.
This is a pinned observation, not a promise that the version remains current or a signed publisher attestation.

The repository license API returned 404 and no root license file appeared in the reviewed tag's tree.
That does not prove the project is unlicensed: source headers and bundled components still need review.
`license_review` therefore remains `pending`. No binary has been downloaded, extracted, executed or redistributed here.

If you already have the exact release ZIP in a private host folder:

```sh
PYTHONPATH=src python3 -m wiiforge verify-package \
  --manifest packages/usb-loader-gx.yaml \
  --artifact /your/private/folder/usbloadergx_r1283.zip --model original
```

The command reads a regular local file and compares its size/hash. It does not fetch the URL or extract the ZIP.
A match returns `content-verified` **and exit 2**, because license review, archive safety and hardware validation
still block installation. A mismatch also exits 2 with an error. The manifest itself must be trusted/reviewed;
editing its hash can make arbitrary bytes match. This checker is not a signature verifier or malware scanner.
The model list is WiiForge's limited review scope, not an upstream compatibility claim.

Before staging: review licensing, recheck release metadata, implement archive traversal/symlink and capacity
checks, then test preservation and interrupted copies in temporary directories. Media writes remain separate.
