# SPDX-FileCopyrightText: 2026 Keresztes Zsolt <https://kereszteszsolt.hu>
# SPDX-License-Identifier: Apache-2.0

import hashlib
import ipaddress
import json
import os
import socket
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path('/mnt/c/P/ghpub/www-temp/cite-nook-ai')
OUTPUT = ROOT / 'docs/releases/release-0.8-llm-judge-evaluation/results/2026-10-17/native-llama3.1-8b-run1'
INPUT = ROOT / 'docs/releases/release-0.7-rag-safety-checks/results/2026-10-16/native/results.json'
assert not OUTPUT.exists(), 'Refusing to overwrite an existing output directory.'
os.chdir(ROOT / 'apps/api')
sys.path.insert(0, str(ROOT / 'apps/api'))
os.environ.update({
    'DEEPEVAL_TELEMETRY_OPT_OUT': '1',
    'DEEPEVAL_UPDATE_WARNING_OPT_IN': '0',
    'DEEPEVAL_DISABLE_DOTENV': '1',
    'PYTHONUNBUFFERED': '1',
})

roots = (
    'apps/api/evaluation/fixtures',
    'docs/releases/release-0.6-rag-evaluation-and-ci',
    'docs/releases/release-0.7-rag-safety-checks',
)
names = subprocess.check_output(['git', 'ls-files', '-z', '--', *roots], cwd=ROOT).decode().split('\0')

def fingerprint():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in names if name}

before = fingerprint()
input_sha = hashlib.sha256(INPUT.read_bytes()).hexdigest()
started = datetime.now(UTC).isoformat()
start_clock = time.monotonic()
network = {'allowedConnections': 0, 'blockedAttempts': []}
original_resolve = socket.getaddrinfo
original_connect = socket.socket.connect
original_connect_ex = socket.socket.connect_ex

def check_host(host, port):
    if isinstance(host, bytes):
        host = host.decode('ascii')
    try:
        allowed = ipaddress.ip_address(host).is_loopback and int(port) == 11434
    except (ValueError, TypeError):
        allowed = host == 'localhost' and str(port) == '11434'
    if not allowed:
        network['blockedAttempts'].append({'host': str(host), 'port': str(port)})
        raise PermissionError('This judge process may contact loopback Ollama port 11434 only.')

def resolve(host, port, *args, **kwargs):
    check_host(host, port)
    return original_resolve(host, port, *args, **kwargs)

def connect(sock, address):
    check_host(address[0], address[1])
    network['allowedConnections'] += 1
    return original_connect(sock, address)

def connect_ex(sock, address):
    check_host(address[0], address[1])
    network['allowedConnections'] += 1
    return original_connect_ex(sock, address)

socket.getaddrinfo = resolve
socket.socket.connect = connect
socket.socket.connect_ex = connect_ex

from evaluation import judge

original_factory = judge.create_judge
calls = []
case_ids = {row['question']: row['id'] for row in json.loads(INPUT.read_text())['cases']}

def factory(config):
    adapter = original_factory(config)
    original_measure = adapter.measure
    def measure(name, question, answer, snippets):
        entry = {'caseId': case_ids[question], 'metric': name,
                 'startedAt': datetime.now(UTC).isoformat()}
        calls.append(entry)
        print(f"[{len(calls)}] {entry['caseId']} / {name}: started", flush=True)
        try:
            result = original_measure(name, question, answer, snippets)
            entry.update(status='returned', score=result.get('score'))
            print(f"[{len(calls)}] {entry['caseId']} / {name}: returned score {result.get('score')}", flush=True)
            return result
        except Exception as error:
            entry.update(status='error', error=f'{type(error).__name__}: {error}')
            print(f"[{len(calls)}] {entry['caseId']} / {name}: {entry['error']}", flush=True)
            raise
        finally:
            entry['finishedAt'] = datetime.now(UTC).isoformat()
    adapter.measure = measure
    return adapter

judge.create_judge = factory
args = [
    '--input', str(INPUT), '--output-dir', str(OUTPUT),
    '--model', 'llama3.1:8b',
    '--model-version', '46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e',
    '--base-url', 'http://127.0.0.1:11434',
    '--temperature', '0', '--threshold', '0.5', '--request-timeout', '120',
    '--synthetic-data',
]
exit_code = 2
try:
    exit_code = judge.main(args)
finally:
    after = fingerprint()
    unchanged = before == after and hashlib.sha256(INPUT.read_bytes()).hexdigest() == input_sha
    manifest = {
        'startedAt': started, 'finishedAt': datetime.now(UTC).isoformat(),
        'elapsedSeconds': round(time.monotonic() - start_clock, 3),
        'command': [sys.executable, '-m', 'evaluation.judge', *args],
        'networkPolicy': 'Loopback Ollama port 11434 only; DNS for all other hosts blocked.',
        'network': network, 'inputSha256': input_sha,
        'historicFilesUnchanged': unchanged, 'historicFileCount': len(before),
        'historicSha256Before': before, 'historicSha256After': after,
        'metricCalls': calls, 'exitCode': exit_code,
    }
    if OUTPUT.is_dir():
        (OUTPUT / 'run-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Historical files unchanged: {unchanged}; checked {len(before)} files.', flush=True)
    assert unchanged, 'A source fixture or historic evidence file changed during the judge run.'
raise SystemExit(exit_code)
