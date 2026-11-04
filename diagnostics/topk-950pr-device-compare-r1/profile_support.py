"""Raw-device parser support, ported from frozen target harness; no event fallback."""
import hashlib
import json
import struct
from pathlib import Path
from kernel_task_profile import parse_profile

def _resolve_kernel_names(prof_path: Path) -> dict[int, str]:
    """Map each raw record's sequence number to its kernel name.

    Same hash_dic/task_track parsing ``tilelang/tilelang/profiler/msprof.py::bench_with_msprof``
    already does to exclude its own flush kernel by name; ported here because
    ``_parse_ffts_profile`` otherwise has no way to tell the flush kernel's or a ``reset()``
    callback's device records apart from the timed op's (Findings 1 and 2).
    """
    hash_to_name: dict[int, str] = {}
    for path in prof_path.rglob("*hash_dic.slice_*"):
        if path.name.endswith(".done"):
            continue
        text = path.read_bytes().decode("utf-8", errors="replace")
        for line in text.strip().split("\n"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                try:
                    h = int(parts[0])
                    if h >= 2**63:
                        h -= 2**64
                    hash_to_name[h] = parts[1]
                except ValueError:
                    pass

    seq_to_name: dict[int, str] = {}
    for path in prof_path.rglob("*task_track.slice_*"):
        if path.name.endswith(".done"):
            continue
        data = path.read_bytes()
        for offset in range(0, len(data) - (len(data) % 64), 64):
            values = struct.unpack_from("<8q", data, offset)
            seq = (values[3] >> 32) & 0xFFFF
            name_hash = values[5]
            if name_hash != 0:
                seq_to_name[seq] = hash_to_name.get(name_hash, f"<unknown {name_hash}>")
    return seq_to_name

def names_for(path):
    return _resolve_kernel_names(path)

def decode(path):
    path = Path(path)
    names = names_for(path)
    ffts = set()
    for f in path.rglob("ffts_profile*.slice_*"):
        if f.name.endswith(".done"):
            continue
        data = f.read_bytes()
        assert len(data) % 128 == 0
        for v in struct.iter_unpack("<16q", data):
            if v[1] and v[15] >= v[14]:
                ffts.add((v[0] >> 32) & 65535)
    tasks = []
    for f in path.rglob("stars_soc.data.*.slice_*"):
        if f.name.endswith(".done"):
            continue
        info = json.loads((f.parent.parent / "info.json.0").read_text())
        assert str(info["platform_version"]) == "15", "decoder limited to verified V6 platform"
        mhz = float(info["DeviceInfo"][0]["hwts_frequency"])
        assert mhz > 0
        data = f.read_bytes()
        assert len(data) % 32 == 0
        pending = {}
        for v in struct.iter_unpack("<4HQHH3L", data):
            assert v[1] == 0x6BD3
            func = v[0] & 63
            if func not in (0, 1):
                continue
            seq = v[2] + (v[3] << 16)
            kind = v[0] >> 10
            key = (seq, kind)
            if func == 0:
                assert key not in pending
                pending[key] = v[4]
            else:
                assert key in pending, ("unmatched end", key)
                start = pending.pop(key)
                assert v[4] >= start
                tasks.append(
                    dict(
                        seq=seq,
                        type=kind,
                        name=names.get(seq),
                        duration_us=(v[4] - start) / mhz,
                        start_ticks=start,
                        end_ticks=v[4],
                        ffts_counted=seq in ffts,
                    )
                )
        assert not pending, ("unmatched start", pending)
    covered = ffts | {t["seq"] for t in tasks if t["type"] in (4, 5)}
    # GE re-emits persistent model registration (unaging type 109) in every
    # profiling session, even when that model is not executed. It is metadata,
    # not evidence of an execution whose device duration went missing.
    registered, launched = set(), set()
    for f in path.rglob("*task_track.slice_*"):
        if f.name.endswith((".done", ".complete")):
            continue
        data = f.read_bytes()
        assert len(data) % 64 == 0, "Truncated task track"
        for v in struct.iter_unpack("<8q", data):
            if not v[5]:
                continue
            seq = (v[3] >> 32) & 65535
            if f.name.startswith("unaging.") and v[4] == 109:
                registered.add(seq)
            else:
                launched.add(seq)
    observed = ffts | {t["seq"] for t in tasks}
    inactive = registered - launched - observed
    missing = {seq: name for seq, name in names.items() if seq not in covered and seq not in inactive}
    assert not missing, ("uncovered tracked kernels", missing)
    additions = [t for t in tasks if t["name"] and not t["ffts_counted"]]
    assert all(t["type"] in (4, 5) for t in additions), additions
    return dict(
        tasks=tasks,
        ffts_sequences=sorted(ffts),
        inactive_registered_tasks={str(seq): names[seq] for seq in sorted(inactive)},
        added_aicpu=additions,
        added_us=sum(t["duration_us"] for t in additions),
    )

def complete_digest(root):
    root = Path(root)
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.name.endswith((".done", ".complete")):
            h.update(str(p.relative_to(root)).encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

def read_profile(path, expected_kernels):
    names = names_for(path)
    assert names and all(n and not n.startswith("<unknown ") for n in names.values()), "Unresolved tracked kernel name"
    extra = decode(path)
    result = parse_profile(path, 1, seq_to_name=names)
    assert result["profile_kernel_count"] == expected_kernels, ("Unexpected FFTS task count", result)
    assert all(task["name"] for task in result["profile_kernel_tasks"]), "Unresolved kernel name"
    assert not any("_tilelang_profiler_cache_flush" in task["name"] for task in result["profile_kernel_tasks"]), "Flush leaked into timed window"
    additions = extra["added_aicpu"]
    result["latency_ms"] += extra["added_us"] / 1000
    result["added_aicpu_us"] = extra["added_us"]
    result["added_aicpu_tasks"] = additions
    result["coverage"] = extra
    result["complete_sha256"] = complete_digest(path)
    result["profile_path"] = str(path)
    return result
