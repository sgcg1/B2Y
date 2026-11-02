"""Strict post-schedule instrumentation of this probe's generated C++ only."""

import hashlib
import re

TAG = re.compile(r"// TILEOPS_TIMER_PROBE2 mode=(\d+) repeats=(\d+)")
NONCODE = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)


def masked(code):
    return NONCODE.sub(lambda m: "".join("\n" if c == "\n" else " " for c in m[0]), code)


def closing(code, start, left, right):
    depth = 0
    for i in range(start, len(code)):
        depth += code[i] == left
        depth -= code[i] == right
        if depth == 0:
            return i
    raise AssertionError("Unclosed generated source region")


def entry(code):
    clean = masked(code)
    matches = list(
        re.finditer(r"(?m)^[ \t]*extern\s+__global__\s+__vector__\s+void\s+main_kernel\s*\(", clean)
    )
    assert len(matches) == 1, "Expected one Vector main_kernel entry"
    start = matches[0].start()
    assert clean[:start].count("{") == clean[:start].count("}"), "Expected a global-scope entry"
    brace = clean.index("{", matches[0].end())
    assert re.search(r"\bticks\b", clean[start:brace]), "Missing clock-buffer argument"
    end = closing(clean, brace, "{", "}")
    return start, brace, end


def statements(body, pattern):
    clean = masked(body)
    result = []
    for match in re.finditer(pattern, clean):
        paren = clean.index("(", match.start(), match.end())
        end = closing(clean, paren, "(", ")") + 1
        while end < len(clean) and clean[end].isspace():
            end += 1
        assert end < len(clean) and clean[end] == ";", "Expected a standalone call statement"
        line_start = clean.rfind("\n", 0, match.start()) + 1
        assert not clean[line_start : match.start()].strip(), (
            "Call is not on its own statement line"
        )
        result.append((line_start, match.start(), end + 1))
    return result


VF = r"\basc_vf_call\s*<[^<>]+>\s*\("


def validate(code, mode, repeats):
    _, brace, end = entry(code)
    body = code[brace + 1 : end]
    assert "tileops_probe2_keep_ticks" not in masked(body), "ABI anchor was not removed"
    vfs = statements(body, VF)
    begins = statements(body, r"\btileops_probe2_begin\s*\(")
    ends = statements(body, r"\btileops_probe2_end\s*\(")
    if mode == 0:
        assert not begins and not ends, "Plain entry contains instrumentation"
        return
    assert len(begins) == len(ends) == 1, "Expected exactly one begin/end in entry body"
    if repeats:
        assert len(vfs) == 3, "Expected load, work and output VF call sites"
        assert vfs[0][2] <= begins[0][1] < vfs[1][1] < ends[0][1] < vfs[2][1], (
            "Injected begin/end do not enclose only the work VF region"
        )
    else:
        assert vfs and vfs[-1][2] <= begins[0][1] < ends[0][1], "Empty stamps must follow output"


def helpers(mode):
    begin = end = ""
    if mode == 2:
        begin = "int64_t stamp = AscendC::GetSystemCycle();\n    tl::write_gm_bypass_dcache(ticks + 0, stamp);"
        end = "int64_t stamp = AscendC::GetSystemCycle();\n    tl::write_gm_bypass_dcache(ticks + 1, stamp);"
    return f"""
#include <tl_templates/ascend/dcache_bypass.h>
__aicore__ inline void tileops_probe2_begin(__gm__ int64_t* ticks) {{
    AscendC::PipeBarrier<PIPE_ALL>();
    {begin}
}}
__aicore__ inline void tileops_probe2_end(__gm__ int64_t* ticks) {{
    AscendC::PipeBarrier<PIPE_ALL>();
    {end}
}}
"""


def transform(code):
    tags = TAG.findall(code)
    assert len(tags) == 1, "Refuse an unmarked or multiply marked kernel"
    mode, repeats = map(int, tags[0])
    assert mode in (0, 1, 2) and repeats in (0, 1, 16, 64)
    start, brace, end = entry(code)
    body = code[brace + 1 : end]
    anchors = statements(body, r"\btileops_probe2_keep_ticks\s*\(")
    assert len(anchors) == 1, "Expected one removable clock-buffer ABI anchor"
    a, _, b = anchors[0]
    body = body[:a] + body[b:]
    vfs = statements(body, VF)
    assert vfs, "No VF calls in generated entry"
    if repeats:
        assert len(vfs) == 3, "Unsupported VF layout; do not guess insertion points"
        assert re.search(r"\bx\b", body[vfs[0][1] : vfs[0][2]])
        assert re.search(r"\by\b", body[vfs[-1][1] : vfs[-1][2]])
        begin_at, end_at = vfs[0][2], vfs[-1][0]
        placement = "between-load-and-output"
    else:
        begin_at = end_at = vfs[-1][2]
        placement = "empty-after-output"
    if mode:
        begin = "\n  tileops_probe2_begin(ticks);"
        finish = "\n  tileops_probe2_end(ticks);\n"
        if begin_at == end_at:
            body = body[:begin_at] + begin + finish + body[begin_at:]
        else:
            body = body[:end_at] + finish + body[end_at:]
            body = body[:begin_at] + begin + body[begin_at:]
    injected = helpers(mode) if mode else ""
    patched = code[:start] + injected + code[start : brace + 1] + body + code[end:]
    validate(patched, mode, repeats)
    return patched, {"mode": mode, "repeats": repeats, "placement": placement}


def install(root):
    try:
        from tilelang.ascend.callback import register_ascend_postproc_callback
    except ImportError as exc:
        raise RuntimeError(
            "This TileLang build lacks the mainline Ascend postproc callback; stop and report, do not upgrade blindly"
        ) from exc
    captures = {}

    def callback(code, target):
        code = str(code)
        assert target.kind.name == "ascend", "Unexpected target in probe-only callback"
        tags = TAG.findall(code)
        assert len(tags) == 1, "Refuse postprocessing an unrelated kernel"
        mode, repeats = map(int, tags[0])
        name = f"r{repeats}-" + ["plain", "fenced", "timed"][mode]
        (root / (name + "-original.cpp")).write_text(code, encoding="utf-8")
        patched, info = transform(code)
        assert name not in captures, "Repeated callback; inspect rather than reuse ambiguous output"
        (root / (name + "-postproc.cpp")).write_text(patched, encoding="utf-8")
        captures[name] = {
            **info,
            "target": str(target),
            "original_source_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "postproc_source_sha256": hashlib.sha256(patched.encode()).hexdigest(),
            "entry_boundary_check_passed": True,
        }
        return patched

    # This registry is process-local. The runner uses a fresh dedicated Python process.
    register_ascend_postproc_callback(callback, override=True)
    return captures
