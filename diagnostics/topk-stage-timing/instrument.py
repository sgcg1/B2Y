"""Decode-only diagnostic clone and strict post-schedule stage boundaries."""

import ast
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "topk-timer-probe"))
from postproc import VF, closing, entry, masked, statements

SOURCE_SHA256 = "987da9f9d314f8744bef05a628e60a14b88e63db320374f36a3b6411ce5eb2e3"
TAG = re.compile(r"// TILEOPS_TOPK_STAGE1 mode=([012])")
GROUPS = [
    ("initialize", 0, 1),
    ("round_reset", 2, 2),
    ("histogram", 3, 3),
    ("scan", 4, 7),
    ("compact", 8, 8),
    ("state_update_with_trace", 9, 9),
    ("final_tie_and_finish", 10, 13),
]
SLOTS = (
    [{"stage": "initialize", "round": None}]
    + [{"stage": name, "round": r} for r in range(5) for name, _, _ in GROUPS[1:6]]
    + [{"stage": "final_tie_and_finish", "round": None}]
)
PRELUDE = """// TILEOPS_TOPK_STAGE1 mode={mode}
#include "kernel_operator.h"
__aicore__ inline int32_t tileops_stage_keep_ticks(__gm__ int64_t* ticks) {{ return 0; }}
"""


def clone_source(raw):
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256, "Unsupported production kernel SHA"
    tree = ast.parse(raw.decode("utf-8"))
    outer = next(n for n in tree.body if isinstance(n, ast.FunctionDef))
    outer.args.args.append(ast.arg(arg="DIAG_MODE", annotation=ast.Name(id="int", ctx=ast.Load())))
    outer.args.defaults.append(ast.Constant(0))
    main = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    additions = ast.parse(
        "def f(ticks: T.Tensor((128,), T.int64), phase_tags: T.Tensor((14,), T.int32), state_trace: T.Tensor((5, 7), T.int32)): pass"
    ).body[0]
    main.args.args.extend(additions.args.args)

    class SelectGrouped(ast.NodeTransformer):
        def visit_If(self, node):
            if isinstance(node.test, ast.Name) and node.test.id == "PARALLEL_SCAN":
                return node.body
            return self.generic_visit(node)

    SelectGrouped().visit(main)
    regions = sorted(
        (
            n
            for n in ast.walk(main)
            if isinstance(n, ast.With)
            and ast.unparse(n.items[0].context_expr).startswith("T.SimtVF(")
        ),
        key=lambda n: n.lineno,
    )
    assert len(regions) == 14, "Unexpected source VF structure"
    for index, region in enumerate(regions):
        region.body.extend(
            ast.parse(
                f"for diagnostic_lane in T.Parallel(H):\n"
                f"    if diagnostic_lane == 0:\n        phase_tags[{index}] = {101 + index}\n"
            ).body
        )
    update_if = regions[9].body[0].body[0]
    assert isinstance(update_if, ast.If) and ast.unparse(update_if.test) == "thread == 0"
    # The same producer lane snapshots its own updates; no new cross-lane UB dependency.
    update_if.body.extend(
        ast.parse(
            "for diagnostic_field in T.serial(7):\n"
            "    state_trace[round, diagnostic_field] = state[diagnostic_field]\n"
        ).body
    )
    kernel = next(
        n
        for n in ast.walk(main)
        if isinstance(n, ast.With) and ast.unparse(n.items[0].context_expr).startswith("T.Kernel(")
    )
    # Use the same no-op ABI retention that passed probe2; remove it after scheduling.
    expression = ast.JoinedStr(
        values=[
            ast.Constant(PRELUDE.split("{mode}")[0]),
            ast.FormattedValue(value=ast.Name(id="DIAG_MODE", ctx=ast.Load()), conversion=-1),
            ast.Constant(PRELUDE.split("{mode}")[1].replace("{{", "{").replace("}}", "}")),
        ]
    )
    kernel.items[0].context_expr.keywords.append(ast.keyword(arg="prelude", value=expression))
    anchor = ast.parse(
        'T.call_extern("int32", "tileops_stage_keep_ticks", T.address_of(ticks[0]))'
    ).body[0]
    kernel.body.append(anchor)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"


def helpers(mode):
    store = (
        "int64_t stamp = AscendC::GetSystemCycle();\n  tl::write_gm_bypass_dcache(p, stamp);"
        if mode == 2
        else ""
    )
    return (
        "\n#include <tl_templates/ascend/dcache_bypass.h>\n"
        + f"""
__aicore__ inline void tileops_stage_stamp(__gm__ int64_t* p) {{
  AscendC::PipeBarrier<PIPE_ALL>();
  {store}
}}
"""
    )


def transform(code):
    tags = TAG.findall(code)
    assert len(tags) == 1, "Refuse an unrelated or multiply marked kernel"
    mode = int(tags[0])
    original_code = code
    # Each source VF carries a unique diagnostic GM store. Identify then remove it.
    definitions = list(
        re.finditer(
            r"__simt_vf__\s+__launch_bounds__\(128\)\s+inline\s+void\s+(main_kernel_simt_vf_\d+)\s*\(",
            masked(code),
        )
    )
    assert len(definitions) == 14, "Unsupported VF fusion/layout; inspect captured source"
    ids = {}
    edits = []
    for definition in definitions:
        brace = masked(code).index("{", definition.end())
        end = closing(masked(code), brace, "{", "}")
        matches = list(re.finditer(r"\bphase_tags\[(\d+)\]\s*=\s*(\d+)\s*;", code[brace + 1 : end]))
        assert len(matches) == 1, "VF marker missing or fused; do not guess stage semantics"
        marker = matches[0]
        index, value = map(int, marker.groups())
        assert 0 <= index < 14 and value == 101 + index and index not in ids.values()
        ids[definition[1]] = index
        edits.append((brace + 1 + marker.start(), brace + 1 + marker.end(), ""))
    for a, b, text in reversed(edits):
        code = code[:a] + text + code[b:]
    start, brace, end = entry(code)
    body = code[brace + 1 : end]
    anchors = statements(body, r"\btileops_stage_keep_ticks\s*\(")
    assert len(anchors) == 1, "Expected one removable ticks anchor"
    a, _, b = anchors[0]
    body = body[:a] + body[b:]
    calls = statements(body, VF)
    symbols = [re.search(r"asc_vf_call\s*<([^<>]+)>", body[a:b])[1] for _, a, b in calls]
    assert [ids[s] for s in symbols] == list(range(14)), "Unexpected generated VF call order"
    clean = masked(body)
    assert len(re.findall(r"\bfor\s*\(", clean)) == 1, (
        "Unexpected entry loop; refuse unbounded sample writes"
    )
    assert not re.search(r"\b(if|while|do)\b", clean), "Unexpected entry control flow"
    loops = list(
        re.finditer(r"for\s*\(int32_t\s+round\s*=\s*0;\s*round\s*<\s*5;\s*\+\+round\)\s*\{", clean)
    )
    assert len(loops) == 1, "Expected one five-round Decode loop"
    loop_begin = loops[0].end() - 1
    loop_end = closing(clean, loop_begin, "{", "}")
    assert calls[1][2] < loop_begin < calls[2][1] < calls[9][2] < loop_end < calls[10][1]
    assert not re.search(r"\bphase_tags\[", masked(code)), "Marker write was not removed"
    if mode:
        insertions = []
        for _, first, last in GROUPS:
            insertions.append((calls[first][0], "  tileops_stage_stamp(ticks + 2 * stage_slot);\n"))
            insertions.append(
                (
                    calls[last][2],
                    "\n  tileops_stage_stamp(ticks + 2 * stage_slot + 1);\n  ++stage_slot;\n",
                )
            )
        for at, text in sorted(insertions, reverse=True):
            body = body[:at] + text + body[at:]
        # Outer envelope includes observer work between individual intervals.
        init = statements(body, r"\basc_init\s*\(")
        assert len(init) == 1
        at = init[0][2]
        body = (
            body[:at]
            + "\n  int32_t stage_slot = 0;\n  tileops_stage_stamp(ticks + 126);\n"
            + body[at:]
        )
        body += "\n  tileops_stage_stamp(ticks + 127);\n"
    patched = (
        code[:start] + (helpers(mode) if mode else "") + code[start : brace + 1] + body + code[end:]
    )
    assert len(statements(patched[entry(patched)[1] + 1 : entry(patched)[2]], VF)) == 14
    return patched, {
        "mode": mode,
        "vf_stage_ids": ids,
        "groups": GROUPS,
        "expected_dynamic_intervals": len(SLOTS),
        "original_source_sha256": hashlib.sha256(original_code.encode()).hexdigest(),
        "postproc_source_sha256": hashlib.sha256(patched.encode()).hexdigest(),
        "marker_writes_removed": True,
    }
