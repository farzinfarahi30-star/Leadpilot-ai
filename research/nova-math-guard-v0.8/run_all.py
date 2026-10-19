#!/usr/bin/env python3
"""One-command NOVA Math Guard v0.8 validation: no downloads, no paid APIs."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def check_manifest():
    manifest = ROOT / 'SHA256SUMS'
    if not manifest.is_file():
        raise RuntimeError('SHA256SUMS missing')
    expected = {str(p.relative_to(ROOT)) for p in ROOT.rglob('*')
                if p.is_file() and '__pycache__' not in p.parts and p.name != 'SHA256SUMS'
                and p.suffix not in ('.pyc',)}
    actual = {}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        checksum, relative = line.split('  ', 1)
        if relative in actual or relative not in expected:
            raise RuntimeError('unexpected or duplicate checksum: ' + relative)
        actual[relative] = checksum
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
            raise RuntimeError('SHA256 mismatch: ' + relative)
    if set(actual) != expected:
        raise RuntimeError('source integrity manifest incomplete: ' + repr(sorted(expected-set(actual))))
    print(f'PASS: {len(actual)} source-and-certificate integrity checksums')


def run(*argv):
    print('RUN:', ' '.join(argv), flush=True)
    subprocess.run([sys.executable, *argv], cwd=ROOT, check=True, timeout=90)


def main():
    check_manifest()
    run('nova_math_guard.py', 'selftest')
    run('-m', 'unittest', '-q', 'test_math_guard', 'test_certificates', 'test_conditional', 'test_groebner', 'test_radical', 'test_countermodels', 'test_real_sos')
    for cert in sorted((ROOT / 'certificates').glob('*.json')):
        run('independent_verifier.py', str(cert))
    run('research_experiment.py')
    run('research_backchain.py')
    try:
        import sympy  # noqa: F401
    except ImportError:
        print('OPTIONAL: SymPy not installed; skipping independent package comparison')
    else:
        run('differential_real_sos_sympy_optional.py')
        if '--with-differential' in sys.argv:
            run('differential_sympy_optional.py')
            run('differential_radical_sympy_optional.py')
        else:
            print('OPTIONAL: pass --with-differential to run the full 3,300 legacy SymPy comparisons')
    print('ALL CHECKS PASSED: within the supported mathematical fragment')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print('CHECK FAILED:', e, file=sys.stderr)
        sys.exit(1)
