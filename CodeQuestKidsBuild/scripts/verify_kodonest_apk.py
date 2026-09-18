#!/usr/bin/env python3
"""Fail-closed validator for the KodoNest Junior Uptodown APK."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_PACKAGE = "com.kodonest.junior"
EXPECTED_VERSION = "1.0.0"
EXPECTED_VERSION_CODE = "1"
EXPECTED_LABEL = "KodoNest Junior"
EXPECTED_FILENAME = "CodeQuest-Kids-1.0.0-UPTODOWN-VERIFIED-V4.apk"


def run(*args: str) -> str:
    proc = subprocess.run(args, text=True, capture_output=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise SystemExit(proc.returncode or 1)
    return proc.stdout


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} APK", file=sys.stderr)
        return 2

    apk = Path(sys.argv[1]).resolve()
    if apk.name != EXPECTED_FILENAME:
        print(f"FAIL: filename must be exactly {EXPECTED_FILENAME}", file=sys.stderr)
        return 1
    if not apk.is_file() or apk.stat().st_size == 0:
        print("FAIL: APK missing or empty", file=sys.stderr)
        return 1

    aapt2 = "/usr/local/lib/android/sdk/build-tools/35.0.0/aapt2"
    apksigner = "/usr/local/lib/android/sdk/build-tools/35.0.0/apksigner"

    badging = run(aapt2, "dump", "badging", str(apk))
    package_re = re.search(
        r"package: name='([^']+)' versionCode='([^']+)' versionName='([^']+)'",
        badging,
    )
    label_re = re.search(r"application-label:'([^']*)'", badging)

    if not package_re:
        print("FAIL: package metadata not found", file=sys.stderr)
        return 1
    package, version_code, version = package_re.groups()
    label = label_re.group(1) if label_re else ""

    checks = {
        "package": package == EXPECTED_PACKAGE,
        "versionCode": version_code == EXPECTED_VERSION_CODE,
        "versionName": version == EXPECTED_VERSION,
        "label": label == EXPECTED_LABEL,
    }
    for key, ok in checks.items():
        if not ok:
            actual = {
                "package": package,
                "versionCode": version_code,
                "versionName": version,
                "label": label,
            }[key]
            expected = {
                "package": EXPECTED_PACKAGE,
                "versionCode": EXPECTED_VERSION_CODE,
                "versionName": EXPECTED_VERSION,
                "label": EXPECTED_LABEL,
            }[key]
            print(f"FAIL: {key}: got {actual!r}, expected {expected!r}", file=sys.stderr)
            return 1

    signer = subprocess.run(
        [apksigner, "verify", "--verbose", str(apk)],
        text=True,
        capture_output=True,
    )
    if signer.returncode != 0:
        print("FAIL: apksigner verification failed", file=sys.stderr)
        sys.stderr.write(signer.stdout)
        sys.stderr.write(signer.stderr)
        return signer.returncode or 1

    digest = hashlib.sha256(apk.read_bytes()).hexdigest()
    print("KODONEST JUNIOR UPTODOWN APK VERIFIED")
    print(f"filename={apk.name}")
    print(f"package={package}")
    print(f"versionName={version}")
    print(f"versionCode={version_code}")
    print(f"label={label}")
    print(f"size={apk.stat().st_size}")
    print(f"sha256={digest}")
    print("signature=valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
