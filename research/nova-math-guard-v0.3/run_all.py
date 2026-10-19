#!/usr/bin/env python3
"""One-command NOVA Math Guard v0.3 validation: no downloads, no paid APIs."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check_manifest():
    manifest = ROOT / 'SHA256SUMS'
    if not manifest.is_file():
        raise RuntimeError('SHA256SUMS missing')
    for line in manifest.read_text(encoding='utf-8').splitlines():
        checksum, relative = line.split('  ', 1)
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise RuntimeError('SHA256 mismatch: ' + relative)
    print('PASS: source integrity checksums')


def run(*argv):
    print('RUN:', ' '.join(argv), flush=True)
    subprocess.run([sys.executable, *argv], cwd=ROOT, check=True, timeout=90)


def main():
    check_manifest()
    run('nova_math_guard.py', 'selftest')
    run('-m', 'unittest', '-q', 'test_math_guard', 'test_certificates')
    for cert in sorted((ROOT / 'certificates').glob('*.json')):
        run('independent_verifier.py', str(cert))
    run('research_experiment.py')
    try:
        import sympy  # noqa: F401
    except ImportError:
        print('OPTIONAL: SymPy not installed; skipping independent package comparison')
    else:
        run('differential_sympy_optional.py')
    print('ALL CHECKS PASSED: within the supported mathematical fragment')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print('CHECK FAILED:', e, file=sys.stderr)
        sys.exit(1)
