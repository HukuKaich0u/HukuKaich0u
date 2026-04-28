import importlib.util
import os
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "postprocess_3d_contribution_graph.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "metrics.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("postprocess_3d_contribution_graph", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Postprocess3DContributionGraphTests(unittest.TestCase):
    def test_metrics_workflow_disables_action_managed_output_commits(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("output_action: none", workflow_text)

    def test_metrics_workflow_sets_explicit_commit_author_identifiers(self):
        workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("commits_authoring:", workflow_text)
        self.assertIn("HukuKaich0u", workflow_text)
        self.assertIn("Koki Aoyagi", workflow_text)
        self.assertIn("170926658+HukuKaich0u@users.noreply.github.com", workflow_text)
        self.assertIn("kouki0802.ao@gmail.com", workflow_text)

    def test_month_to_season_mapping(self):
        module = load_module()

        self.assertEqual(module.month_to_season(3), "spring")
        self.assertEqual(module.month_to_season(6), "summer")
        self.assertEqual(module.month_to_season(9), "autumn")
        self.assertEqual(module.month_to_season(12), "winter")

    def test_extracts_graph_section_from_full_svg(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")

        graph_section, section_range = module.extract_graph_section(svg_text)

        self.assertIn("Contributions calendar", graph_section)
        self.assertRegex(graph_section, r'transform="scale\((?:3\.82|4)\) translate\(12, 0\)"')
        self.assertGreater(section_range[1], section_range[0])

    def test_transform_recolors_and_relights_only_graph_section(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
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
        self.assertIn("#df8bc7", transformed_svg)
        self.assertIn("#c06aa4", transformed_svg)
        self.assertIn("#9f5088", transformed_svg)
        self.assertIn('slope="0.72"', transformed_svg)
        self.assertIn('slope="0.1"', transformed_svg)
        self.assertIn('<rect fill="#216e39"/>', transformed_svg)

    def test_transform_clips_outer_metrics_svg_bounds(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="446" class="">
<foreignObject x="0" y="0" width="100%" height="100%">
<div xmlns="http://www.w3.org/1999/xhtml">
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 6)">
    <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
    <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
    <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</div>
</foreignObject>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="446" class="" overflow="hidden">', transformed_svg)
        self.assertIn('<foreignObject x="0" y="0" width="100%" height="100%" overflow="hidden">', transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_transform_preserves_transparent_metrics_background(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="480" height="446" class="">
<foreignObject x="0" y="0" width="100%" height="100%">
<div xmlns="http://www.w3.org/1999/xhtml">
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 6)">
    <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
    <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
    <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</div>
</foreignObject>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertNotIn('<rect width="100%" height="100%" fill="#0d1117"/>', transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_raises_when_graph_markers_are_missing(self):
        module = load_module()

        with self.assertRaises(RuntimeError):
            module.extract_graph_section("<svg><div id=\"metrics-end\"></div></svg>")

    def test_transform_updates_root_scale_for_already_processed_svg(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        transformed_svg, replacement_count = module.transform_svg(svg_text)

        self.assertIn('transform="scale(3.82) translate(12, 0)"', transformed_svg)
        self.assertIn('style="margin-top: -118px;"', transformed_svg)
        self.assertIn('style="transform: translateY(-26px);"', transformed_svg)
        self.assertGreaterEqual(replacement_count, 0)

    def test_transform_reduces_graph_root_scale_in_newly_processed_svg(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 6)">
    <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
    <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
    <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertIn('transform="scale(3.82) translate(12, 0)"', transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_transform_preserves_week_y_drift_to_keep_metrics_layout_stable(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 0)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
      <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
      <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
    </g>
  </g>
  <g transform="translate(1.7, 1)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
      <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
      <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
    </g>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertIn('transform="scale(3.82) translate(12, 0)"', transformed_svg)
        self.assertIn('transform="translate(1.7, 1)"', transformed_svg)
        self.assertIn('transform="translate(0, 6)"', transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_transform_limits_face_height_boost_to_keep_front_edge_compact(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 0)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
      <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
      <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
    </g>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        transformed_svg, _ = module.transform_svg(sample_svg)

        self.assertIn('d="M0,1 1.7,2 1.7,2.675 0,1.675 z"', transformed_svg)
        self.assertIn('d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z"', transformed_svg)

    def test_transform_keeps_week_y_drift_stable_when_reprocessed(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(1.7, 1)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
      <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
      <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
    </g>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        transformed_svg, _ = module.transform_svg(sample_svg)
        reprocessed_svg, _ = module.transform_svg(transformed_svg)

        self.assertIn('transform="translate(1.7, 1)"', transformed_svg)
        self.assertIn('transform="translate(1.7, 1)"', reprocessed_svg)
        self.assertNotIn('transform="translate(1.7, 0.75)"', reprocessed_svg)

    def test_transform_does_not_reboost_face_heights_when_reprocessed(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.72"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.1"/></feComponentTransfer></filter>
<g transform="scale(3.82) translate(12, 0)">
  <g transform="translate(1.7, 1)">
    <g transform="translate(0, 6)">
      <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#eef8ff"/>
      <path d="M0,1 1.7,2 1.7,2.945 0,1.945 z" filter="url(#brightness1)" fill="#d6e5f0"/>
      <path d="M1.7,2 3.4,1 3.4,1.945 1.7,2.945 z" filter="url(#brightness2)" fill="#c3d2dc"/>
    </g>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        reprocessed_svg, _ = module.transform_svg(sample_svg)

        self.assertIn('d="M0,1 1.7,2 1.7,2.945 0,1.945 z"', reprocessed_svg)
        self.assertIn('d="M1.7,2 3.4,1 3.4,1.945 1.7,2.945 z"', reprocessed_svg)

    def test_transform_handles_calendar_svg_with_xmlns_first_attribute_order(self):
        module = load_module()
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)
        sample_svg = """<svg>
<h2>Contributions calendar</h2>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" style="margin-top: -130px;" viewBox="0,0 480,270">
<filter id="brightness1"><feComponentTransfer><feFuncR type="linear" slope="0.6"/></feComponentTransfer></filter>
<filter id="brightness2"><feComponentTransfer><feFuncR type="linear" slope="0.2"/></feComponentTransfer></filter>
<g transform="scale(4) translate(12, 0)">
  <g transform="translate(0, 6)">
    <path d="M1.7,2 0,1 1.7,0 3.4,1 z" fill="#216e39"/>
    <path d="M0,1 1.7,2 1.7,2.675 0,1.675 z" filter="url(#brightness1)" fill="#216e39"/>
    <path d="M1.7,2 3.4,1 3.4,1.675 1.7,2.675 z" filter="url(#brightness2)" fill="#216e39"/>
  </g>
</g>
</svg>
<div id="metrics-end"></div>
</svg>"""

        transformed_svg, replacement_count = module.transform_svg(sample_svg)

        self.assertIn('transform="scale(3.82) translate(12, 0)"', transformed_svg)
        self.assertIn('style="margin-top: -118px;"', transformed_svg)
        self.assertIn("#df8bc7", transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_transform_uses_multiple_seasonal_color_families(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")
        os.environ["METRICS_RUN_DATE"] = "2026-04-07"
        self.addCleanup(os.environ.pop, "METRICS_RUN_DATE", None)

        transformed_svg, replacement_count = module.transform_svg(svg_text)

        self.assertGreaterEqual(replacement_count, 0)
        self.assertIn("#e9c6f4", transformed_svg)
        self.assertIn("#9fd97a", transformed_svg)
        self.assertIn("#d64b4b", transformed_svg)
        self.assertIn("#8dbaff", transformed_svg)


if __name__ == "__main__":
    unittest.main()
