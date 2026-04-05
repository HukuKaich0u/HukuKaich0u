import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "postprocess_3d_contribution_graph.py"


def load_module():
    spec = importlib.util.spec_from_file_location("postprocess_3d_contribution_graph", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class Postprocess3DContributionGraphTests(unittest.TestCase):
    def test_extracts_graph_section_from_full_svg(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")

        graph_section, section_range = module.extract_graph_section(svg_text)

        self.assertIn("Contributions calendar", graph_section)
        self.assertRegex(graph_section, r'transform="scale\((?:3\.6|4)\) translate\(12, 0\)"')
        self.assertGreater(section_range[1], section_range[0])

    def test_transform_recolors_and_relights_only_graph_section(self):
        module = load_module()
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
        self.assertIn("#d8c8ff", transformed_svg)
        self.assertIn("#b39be7", transformed_svg)
        self.assertIn("#9277d6", transformed_svg)
        self.assertIn('slope="0.72"', transformed_svg)
        self.assertIn('slope="0.1"', transformed_svg)
        self.assertIn('<rect fill="#216e39"/>', transformed_svg)

    def test_raises_when_graph_markers_are_missing(self):
        module = load_module()

        with self.assertRaises(RuntimeError):
            module.extract_graph_section("<svg><div id=\"metrics-end\"></div></svg>")

    def test_transform_updates_root_scale_for_already_processed_svg(self):
        module = load_module()
        svg_text = (ROOT / "github-metrics.svg").read_text(encoding="utf-8")

        transformed_svg, replacement_count = module.transform_svg(svg_text)

        self.assertIn('transform="scale(3.6) translate(12, 0)"', transformed_svg)
        self.assertGreaterEqual(replacement_count, 0)

    def test_transform_reduces_graph_root_scale_in_newly_processed_svg(self):
        module = load_module()
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

        self.assertIn('transform="scale(3.6) translate(12, 0)"', transformed_svg)
        self.assertGreater(replacement_count, 0)

    def test_transform_handles_calendar_svg_with_xmlns_first_attribute_order(self):
        module = load_module()
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

        self.assertIn('transform="scale(3.6) translate(12, 0)"', transformed_svg)
        self.assertIn("#d8c8ff", transformed_svg)
        self.assertGreater(replacement_count, 0)


if __name__ == "__main__":
    unittest.main()
