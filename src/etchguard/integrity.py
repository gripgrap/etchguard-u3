"""SHA256 content manifest; original team's recipe-key hash is a distinct ID."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path


class IntegrityError(ValueError):
    pass


def _digest(path: Path) -> str:
    hasher=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def manifest_for(directory: str | Path) -> dict:
    root=Path(directory).resolve()
    if not root.is_dir():
        raise IntegrityError(f"not a directory: {root}")
    files=[]
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise IntegrityError(f"symlinks not allowed in artifact root: {p}")
        if p.is_file() and p != (root / "manifest.sha256.json"):
            files.append({"path":p.relative_to(root).as_posix(), "size":p.stat().st_size,"sha256":_digest(p)})
    if not files:
        raise IntegrityError("no data files found")
    canonical=json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"version":1, "hash_algorithm":"sha256", "files":files,
            "content_fingerprint":hashlib.sha256(canonical).hexdigest()}


def freeze(directory: str | Path) -> dict:
    doc=manifest_for(directory)
    path=Path(directory)/"manifest.sha256.json"
    if path.exists():
        raise IntegrityError("manifest already exists: refusing overwrite")
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return doc


def verify(directory: str | Path) -> dict:
    path=Path(directory)/"manifest.sha256.json"
    if not path.is_file():
        raise IntegrityError("manifest missing; freeze first")
    try:
        expected=json.loads(path.read_text(encoding="utf-8"))
    except (ValueError,UnicodeDecodeError) as e:
        raise IntegrityError("invalid manifest") from e
    if expected.get("version") != 1 or expected.get("hash_algorithm") != "sha256":
        raise IntegrityError("unsupported manifest format")
    actual=manifest_for(directory)
    if expected != actual:
        raise IntegrityError("data content, filename or file set changed")
    return actual
