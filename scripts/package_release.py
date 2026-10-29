"""Package the component and documentation for manual installation."""

import hashlib
import json
import os
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
component = root / "custom_components/path_rail"
manifest = json.loads((component / "manifest.json").read_text())
version = manifest["version"]
if tag := os.environ.get("RELEASE_TAG"):
    assert tag == f"v{version}", "Release tag must match manifest version"
assert manifest["requirements"] == ["panynj-ridepath-client==0.2.0"]
assert not (component / "_vendor").exists()
output = root / "dist"
output.mkdir(exist_ok=True)
archive = output / f"path_rail-{version}.zip"
files = [
    path
    for path in component.rglob("*")
    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
]
files += list(root.glob("*.md")) + [root / "LICENSE", root / "hacs.json"]
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
    for path in sorted(files):
        if path.suffix == ".py":
            compile(path.read_bytes(), str(path), "exec")
        bundle.write(path, path.relative_to(root).as_posix())
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(output / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n")
print(f"Created {archive.name}, SHA256 {digest}")
