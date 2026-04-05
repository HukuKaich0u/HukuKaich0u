import importlib.util
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "postprocess_3d_contribution_graph.py"
RAW_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "github-metrics-raw.svg"


def load_module():
    spec = importlib.util.spec_from_file_location("postprocess_3d_contribution_graph", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Postprocess3DContributionGraphTests(unittest.TestCase):
    def test_month_to_season_mapping(self):
        module = load_module()

        self.assertEqual(module.month_to_season(3), "spring")
        self.assertEqual(module.month_to_season(6), "summer")
        self.assertEqual(module.month_to_season(9), "autumn")
        self.assertEqual(module.month_to_season(12), "winter")

    def test_visible_range_end_requires_run_date_when_not_explicit(self):
        module = load_module()
        original = os.environ.pop("METRICS_RUN_DATE", None)
        self.addCleanup(lambda: os.environ.__setitem__("METRICS_RUN_DATE", original) if original else None)

        with self.assertRaises(RuntimeError):
            module.visible_range_end()

    def test_extracts_graph_section_from_full_svg(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")

        graph_section, section_range = module.extract_graph_section(svg_text)

        self.assertIn("Contributions calendar", graph_section)
        self.assertIn('translate(12, 0)', graph_section)
        self.assertGreater(section_range[1], section_range[0])

    def test_extracts_cube_positions_from_graph_root(self):
        module = load_module()
        svg_text = RAW_FIXTURE_PATH.read_text(encoding="utf-8")
        graph_section, _ = module.extract_graph_section(svg_text)

        positions = module.enumerate_cube_positions(graph_section)

        self.assertGreater(len(positions), 300)
        self.assertEqual(positions[0][0], 0)
        self.assertEqual(positions[0][1], 0)

    def test_transform_recolors_and_relights_only_graph_section(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/><feFuncG type="linear" slope="0.6"/><feFuncB type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/><feFuncG type="linear" slope="0.2"/><feFuncB type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 0)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
      <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
      <path filter="url(#brightness2)" fill="#216e39" d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z"/>
    </g>
    <g transform="translate(-1.7, 7)">
      <path fill="#30a14e" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>
      <path fill="#30a14e" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,2.45 0,1.45 z"/>
      <path fill="#30a14e" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,1.45 1.7,2.45 z"/>
    </g>
    <g transform="translate(-3.4, 8)">
      <path fill="#40c463" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>
      <path fill="#40c463" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,2.225 0,1.225 z"/>
      <path fill="#40c463" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,1.225 1.7,2.225 z"/>
    </g>
    <g transform="translate(-5.1, 9)">
      <path fill="#9be9a8" d="M1.7,2 0,1 1.7,0 3.4,1 z"/>
      <path fill="#9be9a8" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,2.075 0,1.075 z"/>
      <path fill="#9be9a8" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,1.075 1.7,2.075 z"/>
    </g>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
<rect fill="#216e39"/>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertGreater(replacement_count, 0)
        self.assertIn("#f6d7ec", transformed_svg)
        self.assertIn("#cfb5c6", transformed_svg)
        self.assertIn("#ac96a5", transformed_svg)
        self.assertIn('slope="0.72"', transformed_svg)
        self.assertIn('slope="0.1"', transformed_svg)
        self.assertIn('<rect fill="#216e39"/>', transformed_svg)

    def test_raises_when_graph_markers_are_missing(self):
        module = load_module()

        with self.assertRaises(RuntimeError):
            module.extract_graph_section("<svg><div id=\"metrics-end\"></div></svg>")

    def test_transform_recolors_into_multiple_seasons(self):
        module = load_module()
        svg_text = RAW_FIXTURE_PATH.read_text(encoding="utf-8")
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        transformed_svg, replacement_count = module.transform_svg(svg_text)

        self.assertGreater(replacement_count, 0)
        graph_section, _ = module.extract_graph_section(transformed_svg)
        self.assertIn("#f6d7ec", graph_section)
        self.assertIn("#f7eb99", graph_section)
        self.assertIn("#f2c29b", graph_section)
        self.assertIn("#d9efff", graph_section)

    def test_transform_increases_graph_scale(self):
        module = load_module()
        svg_text = RAW_FIXTURE_PATH.read_text(encoding="utf-8")
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        transformed_svg, _ = module.transform_svg(svg_text)

        self.assertIn('transform="scale(4.6) translate(12, 0)"', transformed_svg)

    def test_transform_is_idempotent_for_already_processed_svg(self):
        module = load_module()
        svg_text = RAW_FIXTURE_PATH.read_text(encoding="utf-8")
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        transformed_svg, _ = module.transform_svg(svg_text)
        second_pass_svg, replacement_count = module.transform_svg(transformed_svg)

        self.assertEqual(second_pass_svg, transformed_svg)
        self.assertEqual(replacement_count, 0)

    def test_cube_positions_map_to_calendar_dates(self):
        module = load_module()
        svg_text = RAW_FIXTURE_PATH.read_text(encoding="utf-8")
        graph_section, _ = module.extract_graph_section(svg_text)
        positions = module.enumerate_cube_positions(graph_section)
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        range_end = module.visible_range_end()
        range_start = module.visible_range_start(range_end, max(position[0] for position in positions) + 1)

        first_date = module.cube_position_to_date(range_start, positions[0][0], positions[0][1])
        last_date = module.cube_position_to_date(range_start, positions[-1][0], positions[-1][1])

        self.assertLess(first_date, last_date)
        self.assertEqual(first_date.month, 3)
        self.assertEqual(last_date.month, 4)

    def test_raises_when_graph_root_transform_is_missing(self):
        module = load_module()

        with self.assertRaises(RuntimeError):
            module.extract_graph_section("<svg><h2>Contributions calendar</h2><div id=\"metrics-end\"></div></svg>")

    def test_raises_when_replacement_count_is_too_low_for_large_raw_svg(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-05"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg><h2>Contributions calendar</h2><svg viewBox="0,0 480,270"><filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter><filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter><g transform="scale(4) translate(12, 0)"><g transform="translate(0,0)"><g transform="translate(0,6)"><path fill="#9be9a8" d="M1.7,2 0,1 1.7,0 3.4,1 z"/><path fill="#9be9a8" filter="url(#brightness1)" d="M0,1 1.7,2 1.7,2.075 0,1.075 z"/><path fill="#9be9a8" filter="url(#brightness2)" d="M1.7,2 3.4,1 3.4,1.075 1.7,2.075 z"/></g></g></g></svg><div id="metrics-end"></div></svg>""" + (" " * 6000)

        with self.assertRaises(RuntimeError):
            module.transform_svg(sample_svg)


if __name__ == "__main__":
    unittest.main()
