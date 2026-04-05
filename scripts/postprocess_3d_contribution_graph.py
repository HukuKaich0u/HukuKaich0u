#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import re
import sys


SECTION_MARKER = "Contributions calendar"
SECTION_END_MARKER = 'id="metrics-end"'
GRAPH_ROOT_MARKER = 'transform="scale(4) translate(12, 0)"'
MIN_EXPECTED_REPLACEMENTS = 50

TOP_FACE_MAP = {
    "#ebedf0": "#f2f1f8",
    "#9be9a8": "#bfe7ff",
    "#40c463": "#bff3de",
    "#30a14e": "#ffd7c2",
    "#216e39": "#d8c8ff",
}

LEFT_FACE_MAP = {
    "#f2f1f8": "#d9d7e8",
    "#bfe7ff": "#93cfee",
    "#bff3de": "#8dd8bd",
    "#ffd7c2": "#f2b99b",
    "#d8c8ff": "#b39be7",
}

RIGHT_FACE_MAP = {
    "#f2f1f8": "#c8c5da",
    "#bfe7ff": "#6eb7db",
    "#bff3de": "#62c39d",
    "#ffd7c2": "#e59c74",
    "#d8c8ff": "#9277d6",
}

REQUIRED_TOKENS = [
    "brightness1",
    "brightness2",
    GRAPH_ROOT_MARKER,
]

ORIGINAL_PALETTE_TOKENS = ["#9be9a8", "#40c463", "#30a14e", "#216e39"]
TRANSFORMED_PALETTE_TOKENS = [
    "#bfe7ff",
    "#bff3de",
    "#ffd7c2",
    "#d8c8ff",
    "#93cfee",
    "#8dd8bd",
    "#f2b99b",
    "#b39be7",
]


def extract_graph_section(svg_text: str) -> tuple[str, tuple[int, int]]:
    section_start = svg_text.find(SECTION_MARKER)
    if section_start == -1:
        raise RuntimeError("Contributions calendar section not found")

    section_end = svg_text.find(SECTION_END_MARKER, section_start)
    if section_end == -1:
        raise RuntimeError("Metrics end marker not found")

    graph_section = svg_text[section_start:section_end]
    missing = [token for token in REQUIRED_TOKENS if token not in graph_section]
    if missing:
        raise RuntimeError(f"3D contribution graph markers not found: {missing}")
    if not any(token in graph_section for token in ORIGINAL_PALETTE_TOKENS + TRANSFORMED_PALETTE_TOKENS):
        raise RuntimeError("3D contribution graph color markers not found")

    return graph_section, (section_start, section_end)


def strengthen_filter_slopes(graph_section: str) -> tuple[str, int]:
    replacements = 0
    for old, new in (
        ('slope="0.6"', 'slope="0.72"'),
        ('slope="0.19999999999999996"', 'slope="0.1"'),
        ('slope="0.2"', 'slope="0.1"'),
    ):
        graph_section, count = graph_section.replace(old, new), graph_section.count(old)
        replacements += count
    return graph_section, replacements


COORD_PAIR_RE = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")


def _boost_face_height(path_data: str) -> str:
    pairs = list(COORD_PAIR_RE.finditer(path_data))
    if len(pairs) != 4:
        return path_data

    coords = [[float(match.group(1)), float(match.group(2))] for match in pairs]
    base_y = coords[0][1]
    mid_y = coords[1][1]
    far_y = coords[2][1]
    end_y = coords[3][1]
    height = far_y - mid_y
    if height <= 0:
        return path_data

    boosted_height = round(height * 1.4, 3)
    coords[2][1] = round(mid_y + boosted_height, 3)
    coords[3][1] = round(base_y + boosted_height, 3)

    formatted = []
    for x_value, y_value in coords:
        if float(x_value).is_integer():
            x_text = str(int(x_value))
        else:
            x_text = f"{x_value:.3f}".rstrip("0").rstrip(".")
        if float(y_value).is_integer():
            y_text = str(int(y_value))
        else:
            y_text = f"{y_value:.3f}".rstrip("0").rstrip(".")
        formatted.append((x_text, y_text))

    return (
        f"M{formatted[0][0]},{formatted[0][1]} "
        f"{formatted[1][0]},{formatted[1][1]} "
        f"{formatted[2][0]},{formatted[2][1]} "
        f"{formatted[3][0]},{formatted[3][1]} z"
    )


PATH_RE = re.compile(r"<path(?P<attrs>[^>]*)/?>", re.IGNORECASE)
ATTR_RE = re.compile(r'([a-zA-Z_:][\w:.-]*)="([^"]*)"')


def recolor_paths(graph_section: str) -> tuple[str, int]:
    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        attrs_text = match.group("attrs")
        attrs = dict(ATTR_RE.findall(attrs_text))
        fill = attrs.get("fill", "").lower()
        path_data = attrs.get("d")

        if not path_data:
            return match.group(0)
        top_fill = TOP_FACE_MAP.get(fill)
        if top_fill is None:
            return match.group(0)

        filter_value = attrs.get("filter", "")
        if filter_value == "url(#brightness1)":
            new_fill = LEFT_FACE_MAP[top_fill]
            new_path_data = _boost_face_height(path_data)
        elif filter_value == "url(#brightness2)":
            new_fill = RIGHT_FACE_MAP[top_fill]
            new_path_data = _boost_face_height(path_data)
        else:
            new_fill = top_fill
            new_path_data = path_data

        attrs["fill"] = new_fill
        attrs["d"] = new_path_data
        replacements += 1
        ordered_keys = []
        for attr_match in ATTR_RE.finditer(attrs_text):
            key = attr_match.group(1)
            if key not in ordered_keys:
                ordered_keys.append(key)
        for key in attrs:
            if key not in ordered_keys:
                ordered_keys.append(key)

        serialized_attrs = " ".join(f'{key}="{attrs[key]}"' for key in ordered_keys)
        return f"<path {serialized_attrs}/>"

    return PATH_RE.sub(replace, graph_section), replacements


def transform_svg(svg_text: str) -> tuple[str, int]:
    graph_section, (start, end) = extract_graph_section(svg_text)
    if not any(token in graph_section for token in ORIGINAL_PALETTE_TOKENS):
        return svg_text, 0

    graph_section, filter_replacements = strengthen_filter_slopes(graph_section)
    graph_section, path_replacements = recolor_paths(graph_section)
    replacements = filter_replacements + path_replacements
    if replacements < MIN_EXPECTED_REPLACEMENTS and len(svg_text) > 5000:
        raise RuntimeError("3D contribution graph replacement count too low")
    return f"{svg_text[:start]}{graph_section}{svg_text[end:]}", replacements


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: postprocess_3d_contribution_graph.py <svg-path>", file=sys.stderr)
        return 2

    svg_path = Path(sys.argv[1])
    svg_text = svg_path.read_text(encoding="utf-8")
    transformed_svg, _ = transform_svg(svg_text)
    svg_path.write_text(transformed_svg, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
