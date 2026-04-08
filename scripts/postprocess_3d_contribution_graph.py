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
GRAPH_ROOT_TRANSLATE = "translate(12, 0)"
TARGET_GRAPH_ROOT_SCALE = 3.82
TARGET_CALENDAR_MARGIN_TOP = -118
DEFAULT_STATS_TRANSLATE_Y = -26
MIN_EXPECTED_REPLACEMENTS = 50
SVG_NS = "http://www.w3.org/2000/svg"

ORIGINAL_TOP_FACE_LEVELS = {
    "#ebedf0": 0,
    "#9be9a8": 1,
    "#40c463": 2,
    "#30a14e": 3,
    "#216e39": 4,
}

FIXED_TOP_FACE_LEVELS = {
    "#f2f1f8": 0,
    "#bfe7ff": 1,
    "#bff3de": 2,
    "#ffd7c2": 3,
    "#d8c8ff": 4,
}

LEGACY_SEASONAL_TOP_FACE_LEVELS = {
    "#f7f3ff": 0,
    "#eee3ff": 1,
    "#e8def8": 2,
    "#f0d1df": 3,
    "#f5bfd5": 4,
    "#ffffff": 0,
    "#eef8ff": 1,
    "#d9f0ff": 2,
    "#bfe7ff": 3,
    "#9fd8ff": 4,
}

SOURCE_TOP_FACE_LEVELS = ORIGINAL_TOP_FACE_LEVELS | FIXED_TOP_FACE_LEVELS | LEGACY_SEASONAL_TOP_FACE_LEVELS

SEASONAL_TOP_FACE_MAP = {
    "spring": ["#f8f1ff", "#f2ddff", "#e9c6f4", "#e7aed8", "#df8bc7"],
    "summer": ["#f5ffe8", "#d9f2b0", "#9fd97a", "#5faa55", "#2f7d32"],
    "autumn": ["#fff3db", "#ffd36b", "#f6b348", "#e07a3f", "#d64b4b"],
    "winter": ["#ffffff", "#eef8ff", "#d1e6ff", "#8dbaff", "#4b73d9"],
}

SEASONAL_LEFT_FACE_MAP = {
    "spring": ["#e5deef", "#dcc9ef", "#cfb1dd", "#cd94bd", "#c06aa4"],
    "summer": ["#ddeccf", "#bdd492", "#7fbb66", "#4a8946", "#235f28"],
    "autumn": ["#eadfc6", "#e5ba62", "#db9441", "#c76435", "#b03838"],
    "winter": ["#e2e2e2", "#d6e5f0", "#b7cde8", "#6f95df", "#3458b8"],
}

SEASONAL_RIGHT_FACE_MAP = {
    "spring": ["#cbc4d9", "#bfaed7", "#af96c1", "#b27ca1", "#9f5088"],
    "summer": ["#c8d8bc", "#9fba74", "#5f9a4e", "#366e35", "#18481d"],
    "autumn": ["#cec4ae", "#c9994e", "#bd7530", "#aa4e27", "#8f2a2a"],
    "winter": ["#cfcfcf", "#c3d2dc", "#9fb7d2", "#5378c0", "#263f90"],
}

SEASON_MONTHS = {
    "spring": {3, 4, 5},
    "summer": {6, 7, 8},
    "autumn": {9, 10, 11},
    "winter": {12, 1, 2},
}

REQUIRED_TOKENS = ["brightness1", "brightness2"]
TRANSFORMED_PALETTE_TOKENS = sorted(
    {
        color
        for palette in (
            FIXED_TOP_FACE_LEVELS.keys(),
            *SEASONAL_TOP_FACE_MAP.values(),
            *SEASONAL_LEFT_FACE_MAP.values(),
            *SEASONAL_RIGHT_FACE_MAP.values(),
        )
        for color in palette
    }
)
SEASONAL_EXCLUSIVE_TOKENS = sorted(
    set(TRANSFORMED_PALETTE_TOKENS) - set(SOURCE_TOP_FACE_LEVELS.keys()) - set(FIXED_TOP_FACE_LEVELS.keys())
)

COORD_PAIR_RE = re.compile(r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?),(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)")
GRAPH_ROOT_TRANSFORM_RE = re.compile(
    r'transform="scale\((?P<scale>-?\d+(?:\.\d+)?)\)\s+translate\(12,\s*0\)"'
)
CALENDAR_SVG_START_RE = re.compile(r'<svg\b[^>]*viewBox="0(?:,|\s)0(?:,|\s)480(?:,|\s)270"[^>]*>')
STATS_SECTION_RE = re.compile(
    r'(<div class="row">\s*<section>\s*</section>\s*<section)(?P<attrs>[^>]*)>',
    re.DOTALL,
)
H2_H3_MARGIN_RE = re.compile(r"h2,h3\{[^}]*margin:(?P<top>-?\d+(?:\.\d+)?)px\s+0\s+(?P<bottom>-?\d+(?:\.\d+)?)px")
H2_FONT_SIZE_RE = re.compile(r"h2\{[^}]*font-size:(?P<size>-?\d+(?:\.\d+)?)px")

ET.register_namespace("", SVG_NS)


def month_to_season(month: int) -> str:
    for season, months in SEASON_MONTHS.items():
        if month in months:
            return season
    raise ValueError(f"unsupported month: {month}")


def visible_range_end(run_date: date | None = None) -> date:
    if run_date is None:
        env_run_date = os.environ.get("METRICS_RUN_DATE")
        if not env_run_date:
            raise RuntimeError("METRICS_RUN_DATE is required for seasonal coloring")
        run_date = date.fromisoformat(env_run_date)
    return run_date - timedelta(days=1)


def visible_range_start(range_end: date, week_count: int) -> date:
    sunday_offset = (range_end.weekday() + 1) % 7
    last_week_start = range_end - timedelta(days=sunday_offset)
    return last_week_start - timedelta(weeks=week_count - 1)


def cube_position_to_date(range_start: date, week_index: int, weekday_index: int) -> date:
    return range_start + timedelta(weeks=week_index, days=weekday_index)


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
    if GRAPH_ROOT_TRANSFORM_RE.search(graph_section) is None:
        raise RuntimeError("3D contribution graph root transform not found")
    if not any(token in graph_section.lower() for token in SOURCE_TOP_FACE_LEVELS.keys() | set(TRANSFORMED_PALETTE_TOKENS)):
        raise RuntimeError("3D contribution graph color markers not found")

    return graph_section, (section_start, section_end)


def strengthen_filter_slopes(svg_root: ET.Element) -> int:
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


def _extract_calendar_svg(graph_section: str) -> tuple[str, tuple[int, int]]:
    match = CALENDAR_SVG_START_RE.search(graph_section)
    if match is None:
        raise RuntimeError("Calendar SVG not found")

    svg_start = match.start()
    svg_end = graph_section.rfind("</svg>")
    if svg_end == -1:
        raise RuntimeError("Calendar SVG end tag not found")
    svg_end += len("</svg>")
    return graph_section[svg_start:svg_end], (svg_start, svg_end)


def _parse_calendar_svg(graph_section: str) -> tuple[ET.Element, tuple[int, int]]:
    calendar_svg, svg_range = _extract_calendar_svg(graph_section)
    return ET.fromstring(calendar_svg), svg_range


def _find_graph_root(svg_root: ET.Element) -> ET.Element:
    for group in svg_root.iter():
        if group.tag.endswith("g") and GRAPH_ROOT_TRANSLATE in group.attrib.get("transform", ""):
            return group
    raise RuntimeError("3D contribution graph root transform not found")


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
    coords[2][1] = round(mid_y + boosted_height, 3)
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


def adjust_graph_root_scale(graph_root: ET.Element) -> int:
    current = graph_root.attrib.get("transform", "")
    target = f"scale({TARGET_GRAPH_ROOT_SCALE}) {GRAPH_ROOT_TRANSLATE}"
    if current == target:
        return 0
    graph_root.set("transform", target)
    return 1


def adjust_calendar_position(svg_root: ET.Element) -> int:
    current_style = svg_root.attrib.get("style", "")
    target_style = f"margin-top: {TARGET_CALENDAR_MARGIN_TOP}px;"
    if current_style == target_style:
        return 0
    svg_root.set("style", target_style)
    return 1


def compute_stats_translate_y(graph_section: str) -> int:
    margin_match = H2_H3_MARGIN_RE.search(graph_section)
    font_size_match = H2_FONT_SIZE_RE.search(graph_section)
    if not margin_match or not font_size_match:
        return DEFAULT_STATS_TRANSLATE_Y

    top_margin = float(margin_match.group("top"))
    bottom_margin = float(margin_match.group("bottom"))
    font_size = float(font_size_match.group("size"))
    return -round(top_margin + font_size + bottom_margin)


def adjust_stats_position(graph_section: str) -> tuple[str, int]:
    stats_translate_y = compute_stats_translate_y(graph_section)
    target_style = f'transform: translateY({stats_translate_y}px);'

    def replace(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        if 'style="' in attrs:
            attrs = re.sub(r'style="[^"]*"', f'style="{target_style}"', attrs, count=1)
            return f"{match.group(1)}{attrs}>"
        return f'{match.group(1)}{attrs} style="{target_style}">'

    updated_section, count = STATS_SECTION_RE.subn(replace, graph_section, count=1)
    return updated_section, count


def recolor_graph(graph_root: ET.Element) -> int:
    week_groups = [child for child in list(graph_root) if child.tag.endswith("g")]
    if not week_groups:
        raise RuntimeError("No week columns found in 3D contribution graph")

    if week_groups and all(
        len([child for child in list(group) if child.tag.endswith("path")]) == 3 for group in week_groups
    ):
        week_groups = [graph_root]

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
            level = SOURCE_TOP_FACE_LEVELS.get(top_path.attrib.get("fill", "").lower())
            if level is None:
                continue

            cube_date = cube_position_to_date(range_start, week_index, weekday_index)
            season = month_to_season(cube_date.month)

            top_path.set("fill", SEASONAL_TOP_FACE_MAP[season][level])
            left_path.set("fill", SEASONAL_LEFT_FACE_MAP[season][level])
            right_path.set("fill", SEASONAL_RIGHT_FACE_MAP[season][level])
            left_path.set("d", _boost_face_height(left_path.attrib["d"]))
            right_path.set("d", _boost_face_height(right_path.attrib["d"]))
            replacements += 3

    return replacements


def transform_svg(svg_text: str) -> tuple[str, int]:
    graph_section, (start, end) = extract_graph_section(svg_text)
    graph_section_lower = graph_section.lower()
    has_source_top_faces = any(token in graph_section_lower for token in SOURCE_TOP_FACE_LEVELS)
    svg_root, svg_range = _parse_calendar_svg(graph_section)
    graph_root = _find_graph_root(svg_root)

    replacements = 0
    replacements += strengthen_filter_slopes(svg_root)
    replacements += adjust_calendar_position(svg_root)
    replacements += adjust_graph_root_scale(graph_root)
    if has_source_top_faces:
        replacements += recolor_graph(graph_root)

    if has_source_top_faces and replacements < MIN_EXPECTED_REPLACEMENTS and len(svg_text) > 5000:
        raise RuntimeError("3D contribution graph replacement count too low")

    updated_calendar_svg = ET.tostring(svg_root, encoding="unicode")
    updated_graph_section = f"{graph_section[:svg_range[0]]}{updated_calendar_svg}{graph_section[svg_range[1]:]}"
    updated_graph_section, stats_replacements = adjust_stats_position(updated_graph_section)
    replacements += stats_replacements
    return f"{svg_text[:start]}{updated_graph_section}{svg_text[end:]}", replacements


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
