#!/usr/bin/env python3
"""Package the complete skill from an explicit public-file allowlist."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ROOT_FILES = (
    "SKILL.md", "README.md", "README.zh-CN.md", "LICENSE",
    "THIRD_PARTY_NOTICES.md", ".light-ui-ux.example.json", ".gitignore", ".gitattributes",
)
PUBLIC_TREES = {
    "references": {".md"},
    "scripts": {".py"},
    "docs": {".md", ".svg", ".webp", ".jpg", ".png"},
    "licenses": {".txt", ".md", ""},
}


def public_files(root=ROOT):
    files = [root / name for name in ROOT_FILES]
    files.append(root / "assets/light-arsenal.db")
    for folder, suffixes in PUBLIC_TREES.items():
        files.extend(
            path for path in sorted((root / folder).rglob("*"))
            if path.is_file() and path.suffix.lower() in suffixes
            and "__pycache__" not in path.parts
        )
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Invalid public file: {path.relative_to(root)}")
    template = json.loads((root / ".light-ui-ux.example.json").read_text(encoding="utf-8"))
    if template != {
        "api_url": "https://your-api.example/v1/images/generations",
        "api_key": "",
        "model": "YOUR_IMAGE_MODEL_ID",
        "provider": "openai-compatible",
    }:
        raise ValueError("The public configuration template must contain only the documented placeholders.")
    return sorted(set(files))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="Release version, for example 1.0.0")
    parser.add_argument("--out-dir", default=".light-ui/releases", help="Output directory")
    args = parser.parse_args()
    version = args.version.removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        parser.error("Use a semantic version such as 1.0.0")
    files = public_files()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive = out / f"light-ui-ux-v{version}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            name = "light-ui-ux/" + path.relative_to(ROOT).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n", encoding="utf-8", newline="\n")
    print(f"Packaged {len(files)} public files: {archive.name} ({archive.stat().st_size / 1048576:.1f} MiB)")
    print("Private configuration, raw resources, website files and local evidence are excluded.")


if __name__ == "__main__":
    main()
