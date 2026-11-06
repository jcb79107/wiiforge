"""Conservative ZIP metadata checks; no extraction or decompression."""
import re
import stat
import unicodedata
import zipfile


def check_zip(stream):
    def require(ok, message):
        if not ok:
            raise ValueError(message)

    stream.seek(0, 2)
    require(stream.tell() <= 64 * 1024 * 1024, 'ZIP input exceeds 64 MiB limit')
    stream.seek(0)
    try:
        with zipfile.ZipFile(stream) as archive:
            entries = archive.infolist()
            require(0 < len(entries) <= 4096, 'ZIP entry count outside review limits')
            paths, spellings, total = {}, {}, 0
            for entry in entries:
                name = entry.orig_filename
                require(name == entry.filename and len(name) <= 240, 'Ambiguous ZIP name')
                require(not any(ord(c) < 32 or ord(c) == 127 for c in name), 'Control character in ZIP name')
                require(not any(c in name for c in '\\:<>"|?*'), 'Nonportable ZIP path')
                require(unicodedata.normalize('NFC', name) == name, 'Noncanonical ZIP name')
                parts = (name[:-1] if name.endswith('/') else name).split('/')
                require(all(p and p not in ('.', '..') and not p.endswith((' ', '.')) for p in parts),
                        'Unsafe ZIP path')
                require(all(not re.fullmatch(r'(CON|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³])',
                                             p.split('.')[0], re.I) for p in parts), 'Reserved ZIP path')
                for i in range(1, len(parts) + 1):
                    prefix = '/'.join(parts[:i])
                    folded = prefix.casefold()
                    require(spellings.setdefault(folded, prefix) == prefix,
                            'Case-colliding ZIP path component')
                canonical = '/'.join(parts).casefold()
                require(canonical not in paths, 'Duplicate or case-colliding ZIP path')
                is_dir = entry.is_dir()
                mode = stat.S_IFMT(entry.external_attr >> 16)
                require(mode in (0, stat.S_IFDIR if is_dir else stat.S_IFREG), 'ZIP link or special file')
                require(not entry.external_attr & 0x400, 'ZIP reparse attribute')
                require(not entry.flag_bits & 1, 'Encrypted ZIP is unsupported')
                require(entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                        'Unsupported ZIP compression')
                require(0 <= entry.file_size <= 64 * 1024 * 1024, 'ZIP member exceeds size limit')
                require(not is_dir or entry.file_size == 0, 'ZIP directory contains data')
                require(entry.file_size <= max(1, entry.compress_size) * 200, 'ZIP compression ratio exceeds limit')
                total += entry.file_size
                require(total <= 128 * 1024 * 1024, 'ZIP expanded size exceeds limit')
                paths[canonical] = is_dir
            for path in paths:
                parts = path.split('/')
                for i in range(1, len(parts)):
                    require(paths.get('/'.join(parts[:i]), True), 'ZIP file conflicts with parent directory')
            return {'status': 'metadata-checked', 'entries': len(entries), 'declared_bytes': total,
                    'content_verified': False}
    except (zipfile.BadZipFile, NotImplementedError) as exc:
        raise ValueError('Invalid or unsupported ZIP archive') from exc
