# Metrics Postprocess No-Op For Seasonal SVG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the metrics workflow green by treating already-seasonal 3D contribution SVGs as valid no-op input instead of failing reprocessing.

**Architecture:** Add a regression test around `transform_svg()` using the checked-in `github-metrics.svg`, then narrow the recolor trigger so only genuinely source-colored graphs enter recolor + replacement-threshold enforcement. Existing layout normalization should still run for both raw and already-processed SVGs.

**Tech Stack:** Python 3, `unittest`, existing metrics workflow scripts

---

### Task 1: Lock The Regression

**Files:**
- Modify: `tests/test_postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] **Step 1: Write the failing test**
Add a test that loads `github-metrics.svg`, runs `transform_svg()`, and asserts it does not raise while preserving stable processed markers such as `scale(3.82)`, `margin-top: -118px;`, and seasonal colors.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_transform_accepts_already_seasonal_svg_without_recolor_failure`
Expected: FAIL with `RuntimeError: 3D contribution graph replacement count too low`

### Task 2: Narrow Recolor Detection

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] **Step 1: Write minimal implementation**
Introduce a helper that inspects actual top-face fills in the parsed graph and returns whether enough cubes still use source palettes to justify recoloring. Use that helper to gate both `recolor_graph()` and the minimum-replacement failure.

- [ ] **Step 2: Run targeted tests to verify fix**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph.Postprocess3DContributionGraphTests.test_transform_accepts_already_seasonal_svg_without_recolor_failure`
Expected: PASS

### Task 3: Verify End To End

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Modify: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] **Step 1: Run focused suite**

Run: `python3 -m unittest tests.test_postprocess_3d_contribution_graph`
Expected: PASS

- [ ] **Step 2: Reproduce on the real asset**

Run: `cp github-metrics.svg /tmp/github-metrics.svg && METRICS_RUN_DATE=2026-06-17 python3 scripts/postprocess_3d_contribution_graph.py /tmp/github-metrics.svg`
Expected: exit 0

