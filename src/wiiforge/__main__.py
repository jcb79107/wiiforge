import argparse
import hashlib
import io
import json
import math
import os
import stat
import platform
import plistlib
import re
import subprocess
import sys
import zipfile

from .onboarding import start, render
from .nintendont import nintendont_bytes
from .hackmii import hackmii_snapshot
from .exploit import check_exploit
from .archive import check_zip
from .rehearsal import rehearse, _stage_zip
from .prepare import PREPARATION_PLAN_LIMIT, plan_preparation, execute_preparation

GUIDE = 'https://wii.hacks.guide/'
RECOVERY_RELEASES = {
    'priiloader': ('DacoTaco/priiloader', '0.10.0', 'Priiloader_v0_10.zip', 'local-sha256-official-release'),
    'loadpriiloader': ('DacoTaco/priiloader', '0.10.0', 'LoadPriiloader.zip', 'local-sha256-official-release'),
    'nanddumper-ios': ('Naim2000/nanddumper_ios', '1.1', 'nanddumper_ios.zip', 'github-release-api'),
    'd2x-cios-installer': ('wiidev/d2x-cios', 'd2x-v11-beta3', 'd2x-v11-beta3.zip', 'local-sha256-official-release'),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path, max_bytes=1048576):
    # JSON is a strict YAML 1.2 subset. No YAML tags, constructors or dependencies.
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, 'Duplicate key: ' + key)
            out[key] = value
        return out
    # Reject devices/FIFOs and final-component symlinks before reading bytes.
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'Input must be a regular file')
        raw = stream.read(max_bytes + 1)
    require(len(raw) <= max_bytes, f'Input exceeds {max_bytes} bytes')
    def constant(value):
        raise ValueError('Non-finite JSON numbers are not supported')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique, parse_constant=constant)
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            require(depth <= 32, 'JSON nesting exceeds 32 levels')
            if isinstance(item, float):
                require(math.isfinite(item), 'Non-finite JSON numbers are not supported')
            elif isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
        return value
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Input must be bounded UTF-8 JSON without excessive nesting') from exc


def keys(obj, expected):
    require(isinstance(obj, dict) and set(obj) == set(expected.split()), 'Unexpected or missing fields')


def profile(p):
    keys(p, 'schema model region display cable output aspect loader autoboot gamecube')
    require(type(p['schema']) is int and p['schema'] == 1, 'Unsupported profile schema')
    choices = {'model': ['original', 'family', 'mini', 'vwii', 'unknown'],
               'region': ['U', 'E', 'J', 'K', 'unknown'],
               'display': ['crt', 'hd', 'unknown'],
               'cable': ['composite', 'rgb', 'component', 'adapter', 'unknown'],
               'output': ['preserve', '480i', '576i', '480p'],
               'aspect': ['preserve', '4:3', '16:9'],
               'loader': ['usb-loader-gx'],
               'autoboot': ['off', 'review'], 'gamecube': ['off', 'review']}
    for key, options in choices.items():
        require(p[key] in options, 'Invalid profile ' + key)
    require(p['output'] != '480p' or (p['display'] == 'hd' and p['cable'] == 'component'),
            '480p requires explicit compatible display/cable evidence; adapters need separate review')
    require(p['output'] != '576i' or p['region'] == 'E', '576i requires PAL region')
    return p


def evidence(e):
    keys(e, 'schema model model_source region region_source menu')
    require(type(e['schema']) is int and e['schema'] == 1, 'Unsupported evidence schema')
    require(e['model'] in ['original', 'family', 'mini', 'vwii', 'unknown'], 'Invalid model evidence')
    require(e['region'] in ['U', 'E', 'J', 'K', 'unknown'], 'Invalid region evidence')
    for key in ['model_source', 'region_source']:
        require(e[key] in ['unknown', 'user-observation', 'diagnostic'], 'Invalid evidence source')
    require(isinstance(e['menu'], str) and re.fullmatch(r'(unknown|[1-4]\.[0-3][UEJK])', e['menu']), 'Invalid menu')
    return e


def diskutil(*args):
    r = subprocess.run(['/usr/sbin/diskutil', *args], check=True, capture_output=True, timeout=20)
    return plistlib.loads(r.stdout)


def normalize(info, parts):
    require(isinstance(info, dict) and isinstance(parts, list) and all(isinstance(p, dict) for p in parts),
            'Invalid disk metadata')
    # Never expose labels, serials, UUIDs or mount paths in reports.
    identity = {k: info.get(k) for k in ['DeviceIdentifier', 'DiskUUID', 'MediaUUID', 'TotalSize', 'Internal', 'Whole']}
    partitions = [{k: p.get(k) for k in ['DeviceIdentifier', 'PartitionType', 'FilesystemType', 'TotalSize', 'VolumeAllocationBlockSize', 'DiskUUID', 'VolumeUUID']} for p in parts]
    blockers = []
    if info.get('Internal') is not False:
        blockers.append('internal-or-unknown-device')
    if info.get('Whole') is not True:
        blockers.append('not-a-whole-physical-disk')
    if info.get('VirtualOrPhysical') != 'Physical':
        blockers.append('virtual-or-unknown-device')
    if type(info.get('TotalSize')) is not int or info['TotalSize'] <= 0:
        blockers.append('unknown-capacity')
    if not any(isinstance(info.get(k), str) and info[k].strip() for k in ['DiskUUID', 'MediaUUID']):
        blockers.append('no-stable-identity')
    if info.get('Content') != 'FDisk_partition_scheme':
        blockers.append('mbr-not-confirmed')
    if len(partitions) != 1:
        blockers.append('ambiguous-partition-layout')
    elif partitions[0]['FilesystemType'] != 'msdos' or partitions[0]['PartitionType'] != 'DOS_FAT_32':
        blockers.append('fat32-not-confirmed')
    if len(partitions) == 1 and partitions[0]['VolumeAllocationBlockSize'] != 32768:
        blockers.append('32k-clusters-not-confirmed')
    if len(partitions) == 1:
        part = partitions[0]
        if (type(part['TotalSize']) is not int or part['TotalSize'] <= 0
                or type(info.get('TotalSize')) is not int or part['TotalSize'] > info['TotalSize']):
            blockers.append('invalid-partition-capacity')
    return {'schema': 1, 'kind': 'macos-diskutil', 'device': info.get('DeviceIdentifier'),
            'fingerprint': digest({'identity': identity, 'partitions': partitions}),
            'capacity': info.get('TotalSize'), 'blockers': blockers,
            'write_authorized': False}


def inspect(device):
    require(platform.system() == 'Darwin', 'Live inspection currently requires macOS; no other OS is hardware-tested')
    require(re.fullmatch(r'disk[0-9]+', device), 'Select an exact whole-disk identifier, e.g. disk4')
    def snapshot():
        listing = diskutil('list', '-plist')
        require(isinstance(listing, dict), 'Invalid disk listing')
        rows = listing.get('AllDisksAndPartitions')
        require(isinstance(rows, list) and all(isinstance(d, dict) for d in rows), 'Invalid disk listing')
        matches = [d for d in rows if d.get('DeviceIdentifier') == device]
        require(len(matches) == 1, 'Device missing or ambiguous')
        partitions = matches[0].get('Partitions')
        require(isinstance(partitions, list) and all(isinstance(p, dict) for p in partitions),
                'Missing or invalid partition listing')
        ids = [p.get('DeviceIdentifier') for p in partitions]
        require(all(isinstance(i, str) and re.fullmatch(re.escape(device) + r's[0-9]+', i) for i in ids),
                'Partition does not belong to selected disk')
        require(len(ids) == len(set(ids)), 'Duplicate partition identifiers')
        info = diskutil('info', '-plist', device)
        require(isinstance(info, dict) and info.get('DeviceIdentifier') == device,
                'Whole-disk identity mismatch')
        parts = []
        for identifier in ids:
            part = diskutil('info', '-plist', identifier)
            require(isinstance(part, dict) and part.get('DeviceIdentifier') == identifier,
                    'Partition identity mismatch')
            parts.append(part)
        return normalize(info, parts)
    before, after = snapshot(), snapshot()
    require(before == after, 'Device or partitions changed during inspection; reconnect and reinspect')
    return after


def manual_steps(p):
    steps = [
        ('review', 'Review current model-specific guide and inspect media after every reconnect', GUIDE),
        ('backup', 'Manually establish Homebrew Channel and model-appropriate recovery; verify private NAND backup', GUIDE),
        ('recovery', 'Manually verify Priiloader recovery before optional autoboot', GUIDE + 'priiloader'),
        ('cios', 'Review current original-Wii cIOS instructions; separately approve console changes', GUIDE + 'cios'),
        ('loader', 'Review upstream USB Loader GX package/version/hash before any staging; manually test loader launch', GUIDE + 'wii-loaders'),
        ('wii-test', 'Manually test a lawfully dumped Wii game; loader launch alone is insufficient', GUIDE + 'wii-loaders')]
    if p['gamecube'] == 'review':
        steps.append(('gamecube-test', 'Prepare reviewed Nintendont files; test direct launch, gameplay and save/reload before GX integration', 'https://github.com/FIX94/Nintendont'))
    if p['autoboot'] == 'review':
        steps.append(('autoboot-test', 'Separately review Wii forwarder/autoboot and retest Priiloader recovery', GUIDE + 'priiloader'))
    return steps


def plan(p, e, d):
    profile(p)
    evidence(e)
    keys(d, 'schema kind device fingerprint capacity blockers write_authorized')
    require(type(d['schema']) is int and d['schema'] == 1 and d['kind'] == 'macos-diskutil', 'Invalid inspection')
    require(isinstance(d['fingerprint'], str) and re.fullmatch('[0-9a-f]{64}', d['fingerprint']), 'Invalid fingerprint')
    require(isinstance(d['device'], str) and re.fullmatch('disk[0-9]+', d['device']), 'Invalid device')
    require(type(d['capacity']) is int and d['capacity'] > 0, 'Invalid capacity')
    require(d['write_authorized'] is False, 'Inspection cannot authorize writes')
    require(isinstance(d['blockers'], list) and all(isinstance(x, str) for x in d['blockers']), 'Invalid blockers')
    blocked = list(d['blockers'])
    if p['model'] != 'original' or e['model'] != p['model'] or e['model_source'] == 'unknown':
        blocked.append('original-Wii-model-not-confirmed; family/mini/vWii recipes are not implemented')
    if p['region'] != e['region'] or e['region_source'] == 'unknown' or p['region'] == 'unknown':
        blocked.append('region-not-confirmed')
    if e['menu'] == 'unknown' or e['menu'][-1:] != e['region']:
        blocked.append('menu-or-region-conflict')
    if e['menu'] != '4.3U':
        blocked.append('outside-initial-4.3U-reference-scope')
    steps = manual_steps(p)
    body = {'schema': 1, 'inputs': digest([p, e, d]), 'blockers': blocked,
            'status': 'blocked' if blocked else 'manual-review-only',
            'steps': [] if blocked else [{'id': i, 'instruction': t, 'source': u} for i, t, u in steps],
            'execution_supported': False}
    return dict(body, digest=digest(body))


def checkpoint_level(checkpoint):
    return 'console-tested' if checkpoint in ['homebrew', 'recovery', 'loader', 'wii-test', 'gamecube-test', 'autoboot-test'] else 'user-confirmed'


def resume(current, state=None, checkpoint=None, level=None):
    keys(current, 'schema inputs blockers status steps execution_supported digest')
    body = {key: value for key, value in current.items() if key != 'digest'}
    require(current['digest'] == digest(body), 'Plan content changed; regenerate the plan')
    require(current['execution_supported'] is False and current['status'] == 'manual-review-only'
            and current['schema'] == 1, 'Invalid manual plan')
    require(not current['blockers'], 'Blocked plans cannot record completion')
    require((checkpoint is None) == (level is None), 'Provide --checkpoint and --level together')
    expected = {'schema': 1, 'plan_digest': current['digest'], 'completed': []}
    state = expected if state is None else state
    keys(state, 'schema plan_digest completed')
    require(type(state['schema']) is int and state['schema'] == 1, 'Invalid state schema')
    require(state['plan_digest'] == current['digest'], 'Inputs changed; start new state and reverify checkpoints')
    require(isinstance(state['completed'], list), 'Invalid completion list')
    ids = [s['id'] for s in current['steps']]
    for index, item in enumerate(state['completed']):
        keys(item, 'id evidence')
        require(index < len(ids) and item['id'] == ids[index], 'Invalid checkpoint order')
        require(item['evidence'] == checkpoint_level(item['id']), 'Insufficient checkpoint evidence')
    if checkpoint:
        n = len(state['completed'])
        require(n < len(ids) and checkpoint == ids[n], 'Only the next checkpoint can be acknowledged')
        updated = dict(state, completed=[*state['completed'], {'id': checkpoint, 'evidence': level}])
        return resume(current, updated)
    return state


def checkpoint_preparation(checkpoint, wii_network):
    packages = {'homebrew': ['hackmii'], 'backup': ['nanddumper-ios'],
                'recovery': ['priiloader', 'loadpriiloader'], 'cios': ['d2x-cios-installer'],
                'loader': ['usb-loader-gx'], 'gamecube-test': ['nintendont']}
    result = {'manifests': ['packages/' + name + '.yaml' for name in packages.get(checkpoint, [])],
              'instruction': 'Use only needed packages: verify local files, review the exact destination plan, then obtain approval before preparation. No console checkpoint is completed by copying files.'}
    if checkpoint == 'homebrew':
        result['instruction'] = 'If HBC already opens, verify it instead of reinstalling. Otherwise follow the selected exploit route. Check a private Wilbrand ZIP with check-exploit, treating the result as partial only. Standalone HackMii is unnecessary when the reviewed exploit already bundles it.'
    elif checkpoint == 'cios':
        result['source'] = GUIDE + 'cios'
        if wii_network == 'online':
            result['instruction'] = 'The guide permits skipping offline IOS acquisition when the Wii can connect. Prepare the d2x installer; review the original-Wii console instructions before any install. Do not download a WAD pack.'
        elif wii_network == 'offline':
            result['instruction'] = 'Review NUSGet from the live guide for your host; require specific approval before running downloaded software. Acquire only the original-Wii IOS versions listed here into private storage, following the guide. No download, copy or console write is automated by this output.'
            result['tool_source'] = 'https://github.com/NinjaCheetah/NUSGet/releases/latest'
            result['base_ios'] = [{'ios': ios, 'version': version, 'filename': f'IOS{ios}-64-v{version}.wad'}
                                  for ios, version in [(38, 4123), (56, 5661), (57, 5918), (58, 6175)]]
        else:
            result['instruction'] = 'Ask one question now: can this Wii connect to the internet? Rerun journey with --wii-network online or offline. This selects guidance only; no download or install is authorized.'
    return result


def journey(answers, saved=None, checkpoint=None, level=None, wii_network='unknown'):
    require(wii_network in ('online', 'offline', 'unknown'), 'Invalid Wii network observation')
    intake = start(answers)
    require(intake['reference_plan_scope'] and all(intake['observations'][key] != 'unknown'
            for key in ['computer', 'homebrew', 'sd', 'storage']),
            'Guided sessions need original Wii 4.3U, computer, homebrew and storage observations; use start to collect them')
    p = intake['profile_draft']
    steps = manual_steps(p)
    steps[1:1] = [
        ('storage-review', 'Review actual storage, backups and the selected current guide. No writes authorized.', GUIDE + 'get-started'),
        ('homebrew', 'Verify Homebrew Channel opens after the selected guide, or confirm the existing installation.', GUIDE + 'hbc')]
    baseline = intake['observations']
    previous = baseline
    state = None
    if saved is not None:
        require(isinstance(saved, dict) and saved.get('kind') == 'guided-session', 'Expected a saved guided-session result')
        previous = start(saved.get('observations'))['observations']
        baseline = start(saved.get('baseline_answers', previous))['observations']
        protected = set(baseline) - {'computer', 'homebrew'}
        require(all(intake['observations'][key] == baseline[key] == previous[key] for key in protected),
                'Console, storage, display or goals changed; review a new session')
        state = saved.get('state')
        require(isinstance(state, dict), 'Missing guided-session state')
    body = {'schema': 1, 'inputs': digest(baseline), 'blockers': [],
            'status': 'manual-review-only', 'execution_supported': False,
            'steps': [{'id': i, 'instruction': instruction, 'source': url} for i, instruction, url in steps]}
    current = dict(body, digest=digest(body))
    state = resume(current, state)
    if previous['homebrew'] != intake['observations']['homebrew']:
        require(previous['homebrew'] == 'no' and intake['observations']['homebrew'] == 'yes',
                'Homebrew status regressed or is unknown; investigate before continuing')
        require(any(item['id'] == 'homebrew' for item in state['completed']) or
                (checkpoint == 'homebrew' and level == 'console-tested'),
                'Confirm the Homebrew Channel checkpoint before recording installation progress')
    state = resume(current, state, checkpoint, level)
    pending = current['steps'][len(state['completed']):]
    return {'kind': 'guided-session', 'observations': intake['observations'], 'baseline_answers': baseline, 'state': state,
            'guide_route': start(baseline)['route'],
            'next_checkpoint': dict(pending[0], required_evidence=checkpoint_level(pending[0]['id']),
                                    computer_preparation=checkpoint_preparation(pending[0]['id'], wii_network)) if pending else None,
            'status': 'manual-checkpoints-complete' if not pending else 'awaiting-user',
            'write_authorized': False, 'inspection_performed': False, 'installation_supported': False,
            'notice': 'User attestations only. File preparation does not complete a console checkpoint; computer changes preserve the selected guide; console/storage/display/goal changes require review.'}


def demo():
    """Exercise real validation using invented data, without device access."""
    p = {'schema': 1, 'model': 'original', 'region': 'U', 'display': 'unknown',
         'cable': 'unknown', 'output': 'preserve', 'aspect': 'preserve',
         'loader': 'usb-loader-gx', 'autoboot': 'review', 'gamecube': 'off'}
    e = {'schema': 1, 'model': 'original', 'model_source': 'user-observation',
         'region': 'U', 'region_source': 'user-observation', 'menu': '4.3U'}
    d = normalize({'DeviceIdentifier': 'disk99', 'DiskUUID': 'synthetic-demo-only',
                   'TotalSize': 2000000000, 'Internal': False, 'Whole': True,
                   'VirtualOrPhysical': 'Physical', 'Content': 'FDisk_partition_scheme'},
                  [{'DeviceIdentifier': 'disk99s1', 'PartitionType': 'DOS_FAT_32',
                    'FilesystemType': 'msdos', 'TotalSize': 1999000000,
                    'VolumeAllocationBlockSize': 32768}])
    current = plan(p, e, d)
    blocked = plan(p, dict(e, model='unknown', model_source='unknown'), d)
    return {'demo': True, 'notice': 'Synthetic data only. No hardware was inspected or tested.',
            'manual_plan': current, 'unknown_model_plan': blocked,
            'initial_state': resume(current)}


def verify_package(manifest, artifact, model, check_archive=False, experimental_stage=False):
    """Check a reviewed pin; optionally stage a verified snapshot in disposable host storage."""
    if isinstance(manifest, dict) and manifest.get('package') == 'nintendont':
        data = nintendont_bytes(manifest, artifact, model)
        return {'package': 'nintendont', 'commit': manifest['commit'], 'status': 'content-verified',
                'sha256': hashlib.sha256(data).hexdigest(),
                'archive': check_zip(io.BytesIO(data)) if check_archive else None,
                'staging': _stage_zip(data, synthetic=False) if experimental_stage else None,
                'blockers': ['license-review-pending', 'console-installation-not-implemented', 'hardware-untested'],
                'execution_supported': False}
    keys(manifest, 'schema package version asset url size sha256 digest_source models license_review')
    require(type(manifest['schema']) is int and manifest['schema'] == 1, 'Invalid package schema')
    require(isinstance(manifest['package'], str) and (manifest['package'] in ('usb-loader-gx', 'hackmii') or manifest['package'] in RECOVERY_RELEASES), 'Unreviewed package')
    if manifest['package'] == 'usb-loader-gx':
        require(isinstance(manifest['version'], str) and re.fullmatch(r'v[0-9]+\.[0-9]+-r[0-9]+', manifest['version']),
                'Package requires an exact release version')
        require(isinstance(manifest['asset'], str) and re.fullmatch(r'usbloadergx_r[0-9]+\.zip', manifest['asset']),
                'Invalid package asset')
        repository, digest_source = 'wiidev/usbloadergx', 'github-release-api'
    elif manifest['package'] == 'hackmii':
        require(manifest['version'] == '1.2' and manifest['asset'] == 'hackmii_installer_v1.2.zip', 'Unreviewed HackMii release')
        repository, digest_source = None, 'local-sha256-official-release'
    else:
        repository, version, asset, digest_source = RECOVERY_RELEASES[manifest['package']]
        require(manifest['version'] == version and manifest['asset'] == asset, 'Unreviewed recovery release or asset')
    expected = ('https://bootmii.org/hackmii_installer_v1.2.zip' if repository is None else
                'https://github.com/' + repository + '/releases/download/' + manifest['version'] + '/' + manifest['asset'])
    require(manifest['url'] == expected, 'Package origin does not match reviewed upstream')
    require(manifest['digest_source'] == digest_source, 'Unreviewed digest source')
    require(isinstance(manifest['sha256'], str) and re.fullmatch('[0-9a-f]{64}', manifest['sha256']),
            'Missing or invalid SHA-256 pin')
    require(type(manifest['size']) is int and 0 < manifest['size'] <= 64 * 1024 * 1024,
            'Package size must be pinned and at most 64 MiB')
    require(manifest['models'] == ['original'] and model == 'original', 'Package model path is not reviewed')
    require(manifest['license_review'] == 'pending', 'License approval is not implemented')
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(artifact, flags)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), 'Package must be a regular file')
        require(before.st_size == manifest['size'], 'Package size mismatch')
        remaining, checksum = manifest['size'], hashlib.sha256()
        snapshot = bytearray() if experimental_stage else None
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            require(chunk, 'Package was truncated during verification')
            checksum.update(chunk)
            if snapshot is not None:
                snapshot.extend(chunk)
            remaining -= len(chunk)
        require(not stream.read(1), 'Package grew during verification')
        require(checksum.hexdigest() == manifest['sha256'], 'Package SHA-256 mismatch')
        archive_result = None
        if check_archive and not experimental_stage:
            stream.seek(0)
            archive_result = check_zip(stream)
        after = os.fstat(stream.fileno())
        require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                (after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Package changed during verification')
    if experimental_stage and manifest['package'] == 'hackmii':
        snapshot = hackmii_snapshot(bytes(snapshot))
    staging = _stage_zip(bytes(snapshot), synthetic=False) if experimental_stage else None
    return {'staging': staging, 'archive': archive_result, 'package': manifest['package'], 'version': manifest['version'],
            'status': 'content-verified', 'sha256': checksum.hexdigest(),
            'blockers': ['license-review-pending', 'archive-content-unverified' if check_archive else 'archive-safety-unverified', 'hardware-untested'],
            'execution_supported': False}


def package_bytes(manifest, artifact, model):
    if isinstance(manifest, dict) and manifest.get('package') == 'nintendont':
        return nintendont_bytes(manifest, artifact, model)
    verify_package(manifest, artifact, model)
    fd = os.open(artifact, os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(fd, 'rb') as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), 'Package must be a regular file')
        data = source.read(manifest['size'] + 1)
    require(len(data) == manifest['size'] and hashlib.sha256(data).hexdigest() == manifest['sha256'],
            'Package changed after verification')
    return hackmii_snapshot(data) if manifest['package'] == 'hackmii' else data


def main():
    parser = argparse.ArgumentParser(prog='wiiforge', description='Wii homebrew inspection, planning and explicitly approved file preparation.')
    sub = parser.add_subparsers(dest='command', required=True)
    welcome = sub.add_parser('start', help='Get beginner questions and a tailored guide route; no writes')
    welcome.add_argument('--answers', help='Private JSON intake file; omitted fields stay unknown')
    welcome.add_argument('--json', action='store_true', help='Include draft profile/evidence for your assistant')
    session = sub.add_parser('journey', help='Resume a portable manual checklist for a confirmed original Wii 4.3U')
    session.add_argument('--answers', required=True)
    session.add_argument('--state', help='Previous successful journey JSON output, saved privately')
    session.add_argument('--checkpoint')
    session.add_argument('--wii-network', choices=['online', 'offline', 'unknown'], default='unknown', help='Wii internet availability for cIOS guidance; no network requests')
    session.add_argument('--level', choices=['user-confirmed', 'console-tested'])
    exploit = sub.add_parser('check-exploit', help='Partially inspect a private Wilbrand ZIP; never verify personalization or authorize writes')
    for arg in ['artifact', 'model', 'menu']:
        exploit.add_argument('--' + arg, required=True)
    sub.add_parser('rehearse', help='Copy synthetic fixtures into a temporary host directory, verify, then remove')
    sub.add_parser('demo', help='Try synthetic plans; no media or network access')
    sub.add_parser('inspect', help='Read macOS whole-disk metadata').add_argument('--device', required=True)
    package_parser = sub.add_parser('verify-package', help='Verify package bytes read-only by default; optional temporary staging; never execute')
    package_parser.add_argument('--experimental-stage', action='store_true',
                                help='Write hash-verified files to OS temporary storage, verify, then delete; backing device is not verified; installation stays blocked')
    package_parser.add_argument('--check-archive', action='store_true', help='Check ZIP metadata after hash verification; never extract')
    for arg in ['manifest', 'artifact', 'model']:
        package_parser.add_argument('--' + arg, required=True)
    for name in ['prepare-plan', 'prepare']:
        preparation = sub.add_parser(name, help='Review exact destination writes' if name == 'prepare-plan' else 'Apply an explicitly approved no-overwrite file plan')
        for arg in ['manifest', 'artifact', 'model', 'destination']:
            preparation.add_argument('--' + arg, required=True)
        if name == 'prepare':
            preparation.add_argument('--plan', required=True)
            preparation.add_argument('--approve-plan', required=True)
    for name in ['plan', 'resume']:
        p = sub.add_parser(name, help={'plan': 'Validate evidence and produce manual checkpoints',
                                      'resume': 'Validate or acknowledge ordered checkpoints'}[name])
        for arg in ['profile', 'evidence', 'inspection']:
            p.add_argument('--' + arg, required=True)
        if name == 'resume':
            p.add_argument('--state')
            p.add_argument('--checkpoint')
            p.add_argument('--level', choices=['user-confirmed', 'console-tested'])
    args = parser.parse_args()
    try:
        if args.command == 'start':
            result = start(read(args.answers) if args.answers else None)
            print(json.dumps(result, indent=2, sort_keys=True) if args.json else render(result))
            return 0
        elif args.command == 'check-exploit':
            result = check_exploit(args.artifact, args.model, args.menu)
        elif args.command == 'journey':
            result = journey(read(args.answers), read(args.state) if args.state else None, args.checkpoint, args.level, args.wii_network)
        elif args.command == 'demo':
            result = demo()
        elif args.command == 'rehearse':
            result = rehearse()
        elif args.command == 'verify-package':
            result = verify_package(read(args.manifest), args.artifact, args.model, args.check_archive, args.experimental_stage)
        elif args.command in ('prepare-plan', 'prepare'):
            data = package_bytes(read(args.manifest), args.artifact, args.model)
            if args.command == 'prepare-plan':
                result = plan_preparation(data, args.destination, args.model)
            else:
                result = execute_preparation(data, args.destination, args.model, read(args.plan, PREPARATION_PLAN_LIMIT), args.approve_plan)
        elif args.command == 'inspect':
            result = inspect(args.device)
        else:
            result = plan(read(args.profile), read(args.evidence), read(args.inspection))
            if args.command == 'resume':
                result = resume(result, read(args.state) if args.state else None, args.checkpoint, args.level)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result.get('blockers') else 0
    except (ValueError, OSError, zipfile.BadZipFile, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        print('WiiForge: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
