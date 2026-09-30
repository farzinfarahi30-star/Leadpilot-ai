from pathlib import Path
import hashlib
import stat
import zipfile

SOURCE = Path("agent")
OUTPUT = Path("submission.zip")
REQUIRED = {"agent.yaml", "eval_config.yaml", "prompts/system.md"}

paths = list(SOURCE.rglob("*"))
if any(p.is_symlink() for p in paths):
    raise SystemExit("Symlinks are not allowed in the submission package.")

files = {p.relative_to(SOURCE).as_posix(): p for p in paths if p.is_file()}
missing = REQUIRED - set(files)
if missing:
    raise SystemExit(f"Missing required files: {sorted(missing)}")

total = sum(p.stat().st_size for p in files.values())
if total >= 3 * 1024**3:
    raise SystemExit("Unpacked submission must remain below 3 GiB.")

with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for name in sorted(files):
        info = zipfile.ZipInfo(name, date_time=(2026, 9, 30, 0, 0, 0))
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(info, files[name].read_bytes())

with zipfile.ZipFile(OUTPUT) as zf:
    bad = zf.testzip()
    names = set(zf.namelist())
    if bad:
        raise SystemExit(f"Archive CRC failure: {bad}")
    if "agent.yaml" not in names:
        raise SystemExit("agent.yaml must be at the archive root.")

print(f"Built {OUTPUT}")
print(f"Files: {', '.join(sorted(names))}")
print(f"SHA256: {hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}")
