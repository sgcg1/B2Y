"""CPU checks of clone semantics, strict mapping and returned stage statistics."""

import ast
import copy
import hashlib
import unittest
from pathlib import Path

from instrument import GROUPS, SLOTS, SOURCE_SHA256, clone_source, entry, transform
from run import summarize


def generated(mode=2):
    definitions = []
    for i in range(14):
        definitions.append(f"""__simt_vf__ __launch_bounds__(128) inline void main_kernel_simt_vf_{i}(int32_t* phase_tags) {{
  if (threadIdx.x == 0) {{ phase_tags[{i}] = {101 + i}; }}
  work_{i}();
}}
""")

    def call(i):
        return f"  asc_vf_call<main_kernel_simt_vf_{i}>(cce::dim3(128), phase_tags);\n"

    return (
        f"// TILEOPS_TOPK_STAGE1 mode={mode}\n"
        + "\n".join(definitions)
        + 'extern "C" __global__ __vector__ void main_kernel(int64_t* ticks, int32_t* phase_tags) {\n'
        + "  asc_init();\n"
        + call(0)
        + call(1)
        + "  for (int32_t round = 0; round < 5; ++round) {\n"
        + "".join(call(i) for i in range(2, 10))
        + "  }\n"
        + "".join(call(i) for i in range(10, 14))
        + "  tileops_stage_keep_ticks(ticks);\n}\n"
    )


class StageTest(unittest.TestCase):
    def test_transform_has_semantic_mapping_and_removes_runtime_tags(self):
        for mode in (0, 1, 2):
            patched, info = transform(generated(mode))
            self.assertEqual(len(info["vf_stage_ids"]), 14)
            self.assertEqual(info["expected_dynamic_intervals"], 27)
            _, brace, end = entry(patched)
            body = patched[brace + 1 : end]
            self.assertNotIn("phase_tags[", patched)
            self.assertNotIn("tileops_stage_keep_ticks", body)
            self.assertEqual(body.count("tileops_stage_stamp("), 16 if mode else 0)
            self.assertEqual(patched.count("GetSystemCycle"), 1 if mode == 2 else 0)
            self.assertEqual(body.count("asc_vf_call"), 14)
            if mode:
                self.assertLess(body.index("ticks + 126"), body.index("asc_vf_call"))
                self.assertGreater(body.index("ticks + 127"), body.rindex("asc_vf_call"))
                for _, first, last in GROUPS:
                    a = body.index(f"asc_vf_call<main_kernel_simt_vf_{first}>")
                    b = body.index(f"asc_vf_call<main_kernel_simt_vf_{last}>")
                    self.assertLess(body.rfind("tileops_stage_stamp", 0, a), a)
                    self.assertGreater(body.index("tileops_stage_stamp", b), b)

    def test_marker_fusion_or_changed_id_is_rejected(self):
        for bad in (
            generated().replace("phase_tags[3] = 104;", ""),
            generated().replace("phase_tags[3] = 104;", "phase_tags[3] = 105;"),
            generated().replace(
                "phase_tags[3] = 104;", "phase_tags[3] = 104; phase_tags[4] = 105;"
            ),
        ):
            with self.assertRaises(AssertionError):
                transform(bad)

    def test_call_reordering_and_unknown_rounds_are_rejected(self):
        for bad in (
            generated().replace(
                "asc_vf_call<main_kernel_simt_vf_4>", "asc_vf_call<main_kernel_simt_vf_5>"
            ),
            generated().replace("round < 5", "round < 4"),
        ):
            with self.assertRaises(AssertionError):
                transform(bad)

    def test_wrong_source_hash_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Unsupported production"):
            clone_source(b"def f(): pass\n")

    def test_extra_entry_loop_is_rejected_before_counter_buffer_can_overrun(self):
        bad = generated().replace("  asc_init();", "  asc_init();\n  for (int i=0; i<2; ++i) {}")
        with self.assertRaisesRegex(AssertionError, "Unexpected entry loop"):
            transform(bad)

    def test_clone_preserves_work_after_diagnostic_additions_are_removed(self):
        # In B2Y pass TOPK_SOURCE via the CLI test environment only when the repo exists.
        import os

        path = Path(
            os.environ.get("TOPK_SOURCE", "src/tileops/_kernels/attention/topk_select_ascend.py")
        )
        if not path.is_file():
            self.skipTest("Production source path unavailable; set TOPK_SOURCE")
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_SHA256)
        clone = ast.parse(clone_source(raw))
        original = ast.parse(raw)
        trace_loop = next(
            n
            for n in ast.walk(clone)
            if isinstance(n, ast.For)
            and isinstance(n.target, ast.Name)
            and n.target.id == "diagnostic_field"
        )
        self.assertEqual(ast.unparse(trace_loop.iter), "T.serial(7)")
        self.assertTrue(
            any(
                isinstance(n, ast.If)
                and ast.unparse(n.test) == "thread == 0"
                and trace_loop in n.body
                for n in ast.walk(clone)
            )
        )

        class Strip(ast.NodeTransformer):
            def visit_If(self, node):
                if isinstance(node.test, ast.Name) and node.test.id == "PARALLEL_SCAN":
                    return [self.visit(n) for n in node.body]
                return self.generic_visit(node)

            def visit_For(self, node):
                if isinstance(node.target, ast.Name) and node.target.id.startswith("diagnostic_"):
                    return None
                return self.generic_visit(node)

            def visit_Expr(self, node):
                if "tileops_stage_keep_ticks" in ast.unparse(node):
                    return None
                return node

        outer = next(n for n in clone.body if isinstance(n, ast.FunctionDef))
        outer.args.args.pop()
        outer.args.defaults.pop()
        main = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        main.args.args = main.args.args[:-3]
        kernel = next(
            n
            for n in ast.walk(main)
            if isinstance(n, ast.With)
            and ast.unparse(n.items[0].context_expr).startswith("T.Kernel(")
        )
        prelude = kernel.items[0].context_expr.keywords.pop().value
        evaluated = eval(compile(ast.Expression(prelude), "<prelude>", "eval"), {"DIAG_MODE": 2})
        self.assertIn("mode=2", evaluated)
        self.assertIn("{ return 0; }", evaluated)
        self.assertEqual(ast.dump(Strip().visit(clone)), ast.dump(Strip().visit(original)))

    def test_summary_keeps_per_round_and_same_launch_sums(self):
        cases = {
            name: {"event_samples_us": [100, 120]}
            for name in ("production", "traced", "fenced", "timed")
        }
        cases["timed"].update(
            stage_samples_ticks=[[1000] * 27, [3000] * 27], envelope_samples_ticks=[40000, 100000]
        )
        result = summarize(copy.deepcopy(cases))
        self.assertEqual(len(SLOTS), 27)
        self.assertEqual(result["timed"]["sum_of_intervals_median_us"], 54)
        self.assertEqual(result["timed"]["envelope_median_us"], 70)
        self.assertEqual(result["timed"]["intervals"][1]["round"], 0)
        self.assertEqual(result["timed"]["intervals"][25]["round"], 4)
        self.assertEqual(result["timed"]["intervals"][25]["median_us"], 2)


if __name__ == "__main__":
    unittest.main()
