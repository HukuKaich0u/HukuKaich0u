#!/usr/bin/env python3

from __future__ import annotations

from datetime import date, timedelta
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


SECTION_MARKER = "Contributions calendar"
SECTION_END_MARKER = 'id="metrics-end"'
GRAPH_TRANSLATE = "translate(12, 0)"
GRAPH_SCALE = 4.6
RAW_GRAPH_ROOT_MARKER = 'transform="scale(4) translate(12, 0)"'
MIN_EXPECTED_REPLACEMENTS = 50
SVG_NS = "http://www.w3.org/2000/svg"

ORIGINAL_PALETTE_TOKENS = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
LEGACY_TRANSFORMED_TOKENS = [
    "#bfe7ff",
    "#bff3de",
    "#ffd7c2",
    "#d8c8ff",
    "#93cfee",
    "#8dd8bd",
    "#f2b99b",
    "#b39be7",
    "#c8c5da",
    "#6eb7db",
    "#62c39d",
    "#e59c74",
    "#9277d6",
]

SEASONAL_TOP_FACE_MAP = {
    "spring": {
        "#ebedf0": "#fdf4f9",
        "#9be9a8": "#f6d7ec",
        "#40c463": "#efb8d9",
        "#30a14e": "#e895c2",
        "#216e39": "#d96aa7",
    },
    "summer": {
        "#ebedf0": "#fffced",
        "#9be9a8": "#f7eb99",
        "#40c463": "#f2de68",
        "#30a14e": "#e6cf3d",
        "#216e39": "#cfb223",
    },
    "autumn": {
        "#ebedf0": "#fdf1e8",
        "#9be9a8": "#f7d7ba",
        "#40c463": "#f2c29b",
        "#30a14e": "#e89b72",
        "#216e39": "#cf694c",
    },
    "winter": {
        "#ebedf0": "#f8fbff",
        "#9be9a8": "#d9efff",
        "#40c463": "#b8dcff",
        "#30a14e": "#8fc5f2",
        "#216e39": "#63a9e6",
    },
}

SEASON_MONTHS = {
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "autumn": {9, 10, 11},
    "winter": {12, 1, 2},
}

SEASONAL_PALETTE_TOKENS = sorted(
    {
        color
        for season_map in SEASONAL_TOP_FACE_MAP.values()
        for top_color in season_map.values()
        for color in (
            top_color,
            top_color,
        )
    }
)

REQUIRED_TOKENS = ["brightness1", "brightness2", GRAPH_TRANSLATE]
COORD_PAIR_RE = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")

ET.register_namespace("", SVG_NS)


def month_to_season(month: int) -> str:
    for season, months in SEASON_MONTHS.items():
        if month in months:
            return season
    raise ValueError(f"unsupported month: {month}")


def _darken(hex_color: str, factor: float) -> str:
    rgb = [int(hex_color[index : index + 2], 16) for index in range(1, 7, 2)]
    darkened = [max(0, min(255, round(channel * factor))) for channel in rgb]
    return "#" + "".join(f"{channel:02x}" for channel in darkened)


SEASONAL_LEFT_FACE_MAP = {
    season: {level: _darken(color, 0.84) for level, color in palette.items()}
    for season, palette in SEASONAL_TOP_FACE_MAP.items()
}
SEASONAL_RIGHT_FACE_MAP = {
    season: {level: _darken(color, 0.70) for level, color in palette.items()}
    for season, palette in SEASONAL_TOP_FACE_MAP.items()
}


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

    if not any(
        token in graph_section
        for token in ORIGINAL_PALETTE_TOKENS + LEGACY_TRANSFORMED_TOKENS + SEASONAL_PALETTE_TOKENS
    ):
        raise RuntimeError("3D contribution graph color markers not found")

    return graph_section, (section_start, section_end)


def _extract_calendar_svg(graph_section: str) -> tuple[str, tuple[int, int]]:
    svg_start = graph_section.find('<svg version="1.1"')
    if svg_start == -1:
        svg_start = graph_section.find('<svg viewBox="0,0 480,270">')
    if svg_start == -1:
        raise RuntimeError("Calendar SVG not found")
    svg_end = graph_section.rfind("</svg>")
    if svg_end == -1:
        raise RuntimeError("Calendar SVG end tag not found")
    svg_end += len("</svg>")
    return graph_section[svg_start:svg_end], (svg_start, svg_end)


def _parse_calendar_svg(graph_section: str) -> tuple[ET.Element, str, tuple[int, int]]:
    calendar_svg, svg_range = _extract_calendar_svg(graph_section)
    return ET.fromstring(calendar_svg), calendar_svg, svg_range


def _find_graph_root(svg_root: ET.Element) -> ET.Element:
    for group in svg_root.iter():
        if group.tag.endswith("g") and GRAPH_TRANSLATE in group.attrib.get("transform", ""):
            return group
    raise RuntimeError("3D contribution graph root transform not found")


def enumerate_cube_positions(graph_section: str) -> list[tuple[int, int, str]]:
    svg_root, _, _ = _parse_calendar_svg(graph_section)
    graph_root = _find_graph_root(svg_root)
    positions: list[tuple[int, int, str]] = []
    week_groups = [child for child in list(graph_root) if child.tag.endswith("g")]
    for week_index, week_group in enumerate(week_groups):
        cube_groups = [child for child in list(week_group) if child.tag.endswith("g")]
        if not cube_groups:
            raise RuntimeError(f"Week column {week_index} contains no cube groups")
        for weekday_index, cube_group in enumerate(cube_groups):
            positions.append((week_index, weekday_index, ET.tostring(cube_group, encoding="unicode")))
    return positions


def visible_range_end(run_date: date | None = None) -> date:
    if run_date is None:
        env_run_date = os.environ.get("METRICS_RUN_DATE")
        if not env_run_date:
            raise RuntimeError("METRICS_RUN_DATE is required for reproducible seasonal coloring")
        run_date = date.fromisoformat(env_run_date)
    return run_date - timedelta(days=1)


def visible_range_start(range_end: date, week_count: int) -> date:
    sunday_offset = (range_end.weekday() + 1) % 7
    last_week_start = range_end - timedelta(days=sunday_offset)
    return last_week_start - timedelta(weeks=week_count - 1)


def cube_position_to_date(range_start: date, week_index: int, weekday_index: int) -> date:
    return range_start + timedelta(weeks=week_index, days=weekday_index)


def _boost_face_height(path_data: str) -> str:
    pairs = list(COORD_PAIR_RE.finditer(path_data))
    if len(pairs) != 4:
        return path_data

    coords = [[float(match.group(1)), float(match.group(2))] for match in pairs]
    base_y = coords[0][1]
    mid_y = coords[1][1]
    far_y = coords[2][1]
    height = far_y - mid_y
    if height <= 0:
        return path_data

    boosted_height = round(height * 1.4, 3)
    coords[2][1] = round(coords[1][1] + boosted_height, 3)
    coords[3][1] = round(base_y + boosted_height, 3)

    formatted = []
    for x_value, y_value in coords:
        x_text = str(int(x_value)) if float(x_value).is_integer() else f"{x_value:.3f}".rstrip("0").rstrip(".")
        y_text = str(int(y_value)) if float(y_value).is_integer() else f"{y_value:.3f}".rstrip("0").rstrip(".")
        formatted.append((x_text, y_text))

    return (
        f"M{formatted[0][0]},{formatted[0][1]} "
        f"{formatted[1][0]},{formatted[1][1]} "
        f"{formatted[2][0]},{formatted[2][1]} "
        f"{formatted[3][0]},{formatted[3][1]} z"
    )


def _strengthen_filters(svg_root: ET.Element) -> int:
    replacements = 0
    slopes = {"0.6": "0.72", "0.19999999999999996": "0.1", "0.2": "0.1"}
    for element in svg_root.iter():
        if not element.tag.endswith(("feFuncR", "feFuncG", "feFuncB")):
            continue
        slope = element.attrib.get("slope")
        if slope in slopes:
            element.set("slope", slopes[slope])
            replacements += 1
    return replacements


def _scale_graph_root(graph_root: ET.Element) -> int:
    current = graph_root.attrib.get("transform", "")
    target = f"scale({GRAPH_SCALE}) {GRAPH_TRANSLATE}"
    if current == target:
        return 0
    graph_root.set("transform", target)
    return 1


def _recolor_graph(svg_root: ET.Element, graph_root: ET.Element) -> int:
    week_groups = [child for child in list(graph_root) if child.tag.endswith("g")]
    if not week_groups:
        raise RuntimeError("No week columns found in 3D contribution graph")

    range_end = visible_range_end()
    range_start = visible_range_start(range_end, len(week_groups))
    replacements = 0

    for week_index, week_group in enumerate(week_groups):
        cube_groups = [child for child in list(week_group) if child.tag.endswith("g")]
        if not cube_groups:
            raise RuntimeError(f"Week column {week_index} contains no cube groups")
        for weekday_index, cube_group in enumerate(cube_groups):
            paths = [child for child in list(cube_group) if child.tag.endswith("path")]
            if len(paths) != 3:
                raise RuntimeError("Cube group did not contain exactly three faces")

            top_path, left_path, right_path = paths
            original_fill = top_path.attrib.get("fill", "").lower()
            if original_fill not in ORIGINAL_PALETTE_TOKENS:
                continue

            cube_date = cube_position_to_date(range_start, week_index, weekday_index)
            season = month_to_season(cube_date.month)
            top_color = SEASONAL_TOP_FACE_MAP[season][original_fill]
            left_color = SEASONAL_LEFT_FACE_MAP[season][original_fill]
            right_color = SEASONAL_RIGHT_FACE_MAP[season][original_fill]

            top_path.set("fill", top_color)
            left_path.set("fill", left_color)
            right_path.set("fill", right_color)
            left_path.set("d", _boost_face_height(left_path.attrib["d"]))
            right_path.set("d", _boost_face_height(right_path.attrib["d"]))
            replacements += 3

    return replacements


def transform_svg(svg_text: str) -> tuple[str, int]:
    graph_section, (section_start, section_end) = extract_graph_section(svg_text)
    if not any(token in graph_section for token in ORIGINAL_PALETTE_TOKENS):
        return svg_text, 0

    svg_root, _, svg_range = _parse_calendar_svg(graph_section)
    graph_root = _find_graph_root(svg_root)

    replacements = 0
    replacements += _strengthen_filters(svg_root)
    replacements += _scale_graph_root(graph_root)
    replacements += _recolor_graph(svg_root, graph_root)

    if replacements < MIN_EXPECTED_REPLACEMENTS and len(svg_text) > 5000:
        raise RuntimeError("3D contribution graph replacement count too low")

    updated_calendar_svg = ET.tostring(svg_root, encoding="unicode")
    updated_graph_section = f"{graph_section[:svg_range[0]]}{updated_calendar_svg}{graph_section[svg_range[1]:]}"
    updated_svg = f"{svg_text[:section_start]}{updated_graph_section}{svg_text[section_end:]}"
    return updated_svg, replacements


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
