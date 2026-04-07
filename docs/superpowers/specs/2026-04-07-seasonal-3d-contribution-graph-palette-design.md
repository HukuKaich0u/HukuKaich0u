# Seasonal 3D Contribution Graph Palette Design

**Goal:** Make the 3D contribution graph use season-aware palettes where each season has its own hue family and contribution volume maps to darker shades within that season.

**Context:** The current stable implementation uses a single fixed five-level palette for every day of the year. The desired behavior is to keep the current robust SVG parsing and 3D geometry handling, but choose the face colors from a seasonal five-step palette derived from each cube's date.

## Seasonal Palette Direction

- Spring: thin lavender to sakura pink
- Summer: lemon to orange
- Autumn: yamabuki yellow to crimson red
- Winter: white to light aqua blue

Each season must provide five fixed contribution levels so the graph remains predictable and easy to tune. Level `0` stays the lightest tone for the season and level `4` becomes the most saturated tone.

## Rendering Behavior

- Keep the current graph root scale and geometry adjustments.
- Determine the calendar date for each cube from its week/day position.
- Choose the top face color from the season's fixed five-level palette.
- Derive left and right face colors as darker variants of the top face to preserve the 3D effect.

## Stability Requirements

- Do not reintroduce the old fragile XML substring parsing.
- Preserve support for SVG variants where the inner calendar `<svg>` attributes appear in different orders.
- Keep tests covering both seasonal color output and parser stability.
