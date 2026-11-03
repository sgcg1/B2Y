"""Lossless gzip/base64 transport chunks; never modify original evidence."""
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def split_files(sources, output, part_bytes=65536, prefix="result-parts"):
    assert 1024 <= part_bytes <= 65536
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / (prefix + "-manifest.json")
    assert not manifest_path.exists(), "Output exists; choose a new prefix"
    entries = []
    pending = []
    for original_name, source in sources:
        assert Path(original_name).name == original_name
        raw = source.read_bytes()
        compressed = gzip.compress(raw, mtime=0)
        encoded = base64.b64encode(compressed)
        parts = []
        for i, start in enumerate(range(0, len(encoded), part_bytes), 1):
            name = f"{prefix}-{original_name}-part-{i:04d}.txt"
            assert not (output / name).exists(), name
            chunk = encoded[start:start + part_bytes]
            parts.append({"name": name, "bytes": len(chunk), "sha256": sha(chunk)})
            pending.append((output / name, chunk))
        entries.append({"original_name": original_name, "source_path": str(source),
                        "original_bytes": len(raw), "original_sha256": sha(raw),
                        "gzip_bytes": len(compressed), "gzip_sha256": sha(compressed), "parts": parts})
    manifest = {"version": 1, "encoding": "gzip+base64", "part_max_bytes": part_bytes, "files": entries}
    for path, chunk in pending:
        with path.open("xb") as handle:
            handle.write(chunk)
    with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
    return manifest_path


def restore(manifest_path, output):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["version"] == 1 and manifest["encoding"] == "gzip+base64"
    pending = []
    for entry in manifest["files"]:
        name = entry["original_name"]
        assert Path(name).name == name and not Path(name).is_absolute()
        assert not (output / name).exists(), "Refuse to overwrite existing evidence"
        chunks = []
        for part in entry["parts"]:
            assert Path(part["name"]).name == part["name"]
            raw = (manifest_path.parent / part["name"]).read_bytes()
            assert len(raw) == part["bytes"] and sha(raw) == part["sha256"], part["name"]
            chunks.append(raw)
        compressed = base64.b64decode(b"".join(chunks), validate=True)
        assert len(compressed) == entry["gzip_bytes"] and sha(compressed) == entry["gzip_sha256"]
        raw = gzip.decompress(compressed)
        assert len(raw) == entry["original_bytes"] and sha(raw) == entry["original_sha256"]
        pending.append((output / name, raw))
    output.mkdir(parents=True, exist_ok=True)
    for path, raw in pending:
        with path.open("xb") as handle:
            handle.write(raw)
    return [p for p, _ in pending]


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split")
    split.add_argument("--run", default="topk-formal-decode-r2-20261103-101431-41662")
    split.add_argument("--root", type=Path, default=Path("/home/y00937463"))
    split.add_argument("--part-kib", type=int, default=64)
    merge = commands.add_parser("restore")
    merge.add_argument("manifest", type=Path)
    merge.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "restore":
        for path in restore(args.manifest, args.output):
            print("RESTORED", path)
        return
    assert Path(args.run).name == args.run and args.run.startswith("topk-formal-decode-r")
    assert 1 <= args.part_kib <= 64
    output = args.root / "B2Y/AAA_Results"
    sources = []
    for repeat in [1, 2]:
        name = f"{args.run}-repeat-{repeat}.txt"
        source = output / name
        if not source.is_file():
            source = args.root / args.run / f"repeat-{repeat}" / "formal-return.txt"
        assert source.is_file(), f"Missing original result: {name}; check the existing private run directory before any rerun"
        sources.append((name, source))
    prefix = "parts-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = split_files(sources, output, args.part_kib * 1024, prefix)
    info = json.loads(manifest.read_text())
    print("MANIFEST", manifest)
    for entry in info["files"]:
        print("SOURCE", entry["source_path"], "BYTES", entry["original_bytes"], "PARTS", len(entry["parts"]))
        for part in entry["parts"]:
            print("UPLOAD", output / part["name"], "BYTES", part["bytes"])
    print("Upload the manifest and every listed part. Original files were not changed.")


if __name__ == "__main__":
    main()
