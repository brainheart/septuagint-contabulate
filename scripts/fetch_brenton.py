"""Fetch Brenton's Greek Septuagint (ebible.org grcbrent, public domain).

The zip is not versioned upstream, so it is pinned by SHA-256: the download is
refused if its hash differs from `source_text/provenance.json`, and every file
kept in `source_text/brenton/` is checked against its own hash. Run from the
repository root: `python3 scripts/fetch_brenton.py`.
"""
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "source_text"


def main():
    brenton = json.loads((SOURCE / "provenance.json").read_text())["brenton"]
    # ebible.org refuses urllib's default User-Agent.
    request = urllib.request.Request(brenton["url"], headers={"User-Agent": "septuagint-contabulate/1.0"})
    data = urllib.request.urlopen(request, timeout=60).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != brenton["sha256"]:
        sys.exit(f"grcbrent zip changed upstream: {digest} != pinned {brenton['sha256']}")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name, info in brenton["files"].items():
            blob = zf.read(Path(name).name)
            if hashlib.sha256(blob).hexdigest() != info["sha256"]:
                sys.exit(f"checksum mismatch for {name}")
            (SOURCE / name).parent.mkdir(parents=True, exist_ok=True)
            (SOURCE / name).write_bytes(blob)
            print(f"ok {name}")


if __name__ == "__main__":
    main()
