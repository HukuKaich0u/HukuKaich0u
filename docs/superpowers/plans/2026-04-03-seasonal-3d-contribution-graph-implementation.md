# Seasonal 3D Contribution Graph Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current 3D contribution graph post-processor so the graph uses seasonal colors across the year and renders slightly larger without changing the overall README structure.

**Architecture:** Keep the existing `lowlighter/metrics` workflow and evolve the current SVG post-processor. The script will map each cube to a calendar date, derive a season-specific palette for that date and activity level, then increase the graph root scale slightly while preserving the rest of the metrics layout.

**Tech Stack:** Python 3 standard library, GitHub Actions workflow output (`github-metrics.svg`), unittest, Git diff

---

## Chunk 1: Seasonal Palette And Date Mapping

### Task 1: Add failing tests for season selection and graph scaling

**Files:**
- Modify: `tests/test_postprocess_3d_contribution_graph.py`
- Reference: `docs/superpowers/specs/2026-04-03-seasonal-3d-contribution-graph-design.md`

- [ ] **Step 1: Add a failing test for month-to-season mapping**

Add a test like:

```python
def test_month_to_season_mapping(self):
    self.assertEqual(module.month_to_season(3), "spring")
    self.assertEqual(module.month_to_season(6), "summer")
    self.assertEqual(module.month_to_season(9), "autumn")
    self.assertEqual(module.month_to_season(12), "winter")
```

- [ ] **Step 2: Run the test to verify it fails for the missing helper**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_month_to_season_mapping -v`
Expected: FAIL because `month_to_season` does not exist yet.

- [ ] **Step 3: Add a failing test for seasonal recoloring**

Use a small sample graph with cubes that represent dates from multiple seasons, then assert that the transformed SVG contains multiple seasonal palette colors.

- [ ] **Step 4: Add a failing test for graph scale growth**

Assert that transforming a raw graph section replaces `transform="scale(4) translate(12, 0)"` with a larger scale value.

- [ ] **Step 5: Run the full test file to verify the new tests fail for the right reason**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph -v`
Expected: Existing tests may pass, but the new seasonal tests fail because the feature is not implemented yet.

- [ ] **Step 6: Commit the failing tests**

```bash
git add tests/test_postprocess_3d_contribution_graph.py
git commit -m "test: add seasonal 3D graph expectations"
```

### Task 2: Implement season mapping and palette selection

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] **Step 1: Add the season helper and seasonal palette tables**

Implement:

```python
def month_to_season(month: int) -> str:
    ...

SEASONAL_TOP_FACE_MAP = {
    "spring": {...},
    "summer": {...},
    "autumn": {...},
    "winter": {...},
}
```

Each season should define per-level colors for the existing contribution levels.

- [ ] **Step 2: Run the month-mapping test to verify it passes**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_month_to_season_mapping -v`
Expected: PASS

- [ ] **Step 3: Replace the current fixed palette logic with season-aware palette lookup**

Refactor the color selection so top/left/right face colors come from `season` and original contribution level instead of a single global palette.

- [ ] **Step 4: Run the seasonal recoloring test**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_transform_recolors_into_multiple_seasons -v`
Expected: PASS

- [ ] **Step 5: Run the full test file to confirm the script remains compatible with existing behavior**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph -v`
Expected: PASS

- [ ] **Step 6: Commit the seasonal palette implementation**

```bash
git add scripts/postprocess_3d_contribution_graph.py tests/test_postprocess_3d_contribution_graph.py
git commit -m "feat: add seasonal palettes for 3D contribution graph"
```

### Task 3: Map cubes to calendar dates

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`
- Verify: `github-metrics.svg`

- [ ] **Step 1: Define the SVG traversal and date anchor contract before implementation**

Document the contract in code comments and tests before writing the helper logic.

- enumerate week columns from the outer cube-column `<g transform="translate(...">` groups under the graph root
- enumerate day cells from the nested cube groups inside each week column
- treat the graph as a rolling full-year isocalendar generated in `Asia/Tokyo`
- anchor the visible range to the latest complete local day represented by the workflow run, then walk backward across the visible weeks

Add an explicit helper contract such as:

```python
def enumerate_cube_positions(graph_section: str) -> list[tuple[int, int, str]]:
    ...
```

where each item is `(week_index, weekday_index, cube_markup)`.

Also define how `run_date` enters the script. The plan should use one explicit source and test it:

- preferred: pass `METRICS_RUN_DATE=YYYY-MM-DD` from the workflow into the post-processor step
- local fallback: default to `date.today()` only when the env var is absent

The workflow and tests must both use the same contract so date anchoring is deterministic.

- [ ] **Step 1.5: Update the workflow contract to pass `METRICS_RUN_DATE`**

Modify `.github/workflows/metrics.yml` so the post-processing step sets an explicit run date, for example:

```yaml
      - name: Post-process 3D contribution graph
        run: python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg
        env:
          METRICS_RUN_DATE: ${{ steps.metrics_run_date.outputs.run_date }}
```

or an equivalent deterministic same-job value. The plan must include this workflow change because the script cannot infer the intended anchor date from the SVG alone.

- [ ] **Step 2: Add a failing test for date assignment across graph positions**

Write a test that feeds a synthetic sequence of cubes and asserts the derived months change in the expected order across the year.

- [ ] **Step 3: Run the new date-mapping test to verify it fails**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_cube_positions_map_to_calendar_dates -v`
Expected: FAIL because the date-mapping helper does not exist yet.

- [ ] **Step 4: Implement helpers that derive the visible date range and map cube positions to dates**

Add helpers such as:

```python
def visible_range_end(run_date: date) -> date:
    ...

def visible_range_start(range_end: date, week_count: int) -> date:
    ...

def cube_position_to_date(range_start: date, week_index: int, weekday_index: int) -> date:
    ...
```

The implementation should follow the explicit traversal contract from Step 1 rather than relying on implicit index guessing.

- [ ] **Step 5: Connect the date mapping to seasonal palette selection**

The recoloring logic should determine each cube's week/weekday position, derive the calendar date, then select the season before applying colors.

- [ ] **Step 6: Extend idempotence detection for seasonal output**

Update the script's "already transformed" detection so it recognizes the seasonal palette families, then add a regression test that a second run on an already-seasonal SVG returns unchanged.

- [ ] **Step 7: Add fail-fast tests for missing transform, missing date anchor input handling, and low replacement counts**

Add negative-path tests that assert the script raises on:

- missing graph root transform
- irrecoverable cube/date mapping structure
- replacement count below the seasonal minimum for a real-sized raw graph

Use an explicit raw fixture for the replacement-count negative path. If the repo does not already contain one, add a small raw SVG fixture captured before post-processing, rather than relying on the already-transformed `github-metrics.svg`.

- [ ] **Step 8: Run the full test file**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph -v`
Expected: PASS

- [ ] **Step 9: Verify real SVG output contains colors from all four seasonal families in the graph section**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: Exit code `0`.

Then run a focused verification helper that extracts the graph section and asserts at least one color from each seasonal family is present there, not just elsewhere in the SVG.

- [ ] **Step 10: Commit the date mapping**

```bash
git add scripts/postprocess_3d_contribution_graph.py tests/test_postprocess_3d_contribution_graph.py github-metrics.svg
git commit -m "feat: map 3D graph colors by season"
```

## Chunk 2: Sizing And Final Verification

### Task 4: Increase graph scale without breaking layout

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`
- Verify: `github-metrics.svg`

- [ ] **Step 1: Implement a named constant for the enlarged graph scale**

Add something like:

```python
GRAPH_SCALE = 4.6
GRAPH_TRANSLATE = (12, 0)
```

- [ ] **Step 2: Update the transform rewrite logic**

The transformed graph root should use the new scale while preserving the translate offset unless a small translate adjustment is needed for fit.

- [ ] **Step 3: Run the scale test**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_transform_increases_graph_scale -v`
Expected: PASS

- [ ] **Step 4: Rebuild the graph and inspect layout-related diff**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg && git diff -- github-metrics.svg | sed -n '1,220p'`
Expected: The graph root transform changes and the graph visibly grows without changing surrounding metrics content.

- [ ] **Step 5: Commit the scale adjustment**

```bash
git add .github/workflows/metrics.yml scripts/postprocess_3d_contribution_graph.py tests/test_postprocess_3d_contribution_graph.py github-metrics.svg tests/fixtures/github-metrics-raw.svg
git commit -m "feat: enlarge seasonal 3D contribution graph"
```

### Task 5: Final verification on current workflow output

**Files:**
- Verify: `scripts/postprocess_3d_contribution_graph.py`
- Verify: `tests/test_postprocess_3d_contribution_graph.py`
- Verify: `github-metrics.svg`
- Verify: `.github/workflows/metrics.yml`

- [ ] **Step 1: Run the full test suite for the post-processor**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph -v`
Expected: PASS

- [ ] **Step 2: Verify idempotence on the real SVG**

Run: `cp github-metrics.svg /tmp/github-metrics.seasonal.svg && python3 scripts/postprocess_3d_contribution_graph.py /tmp/github-metrics.seasonal.svg && diff -u github-metrics.svg /tmp/github-metrics.seasonal.svg`
Expected: No output

- [ ] **Step 3: Verify workflow integration remains intact**

Run: `sed -n '1,120p' .github/workflows/metrics.yml`
Expected: The existing post-processing step is still present, still targets `github-metrics.svg`, and now passes the agreed `METRICS_RUN_DATE` contract.

- [ ] **Step 4: Review the final diff**

Run: `git diff -- scripts/postprocess_3d_contribution_graph.py tests/test_postprocess_3d_contribution_graph.py github-metrics.svg .github/workflows/metrics.yml README.md`
Expected: Only the seasonal styling, the workflow contract update, and any intentional fixture additions appear; README should remain unchanged unless intentionally updated.

- [ ] **Step 5: Commit the final seasonal output**

```bash
git add .github/workflows/metrics.yml scripts/postprocess_3d_contribution_graph.py tests/test_postprocess_3d_contribution_graph.py github-metrics.svg tests/fixtures/github-metrics-raw.svg
git commit -m "feat: add seasonal styling to 3D contribution graph"
```
