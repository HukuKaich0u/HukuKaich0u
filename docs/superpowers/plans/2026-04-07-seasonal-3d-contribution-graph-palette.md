# Seasonal 3D Contribution Graph Palette Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore seasonal 3D contribution colors using fixed per-season five-step palettes while keeping the current stable SVG post-processing logic.

**Architecture:** Extend the current string-based graph transformer with date-aware palette selection per cube. Keep the current parser and scale handling, compute seasonal top-face colors from cube dates, and derive darker side faces from the chosen top-face color.

**Tech Stack:** Python 3, unittest, GitHub Actions, SVG post-processing

---

## Chunk 1: Tests

### Task 1: Add seasonal palette regression coverage

**Files:**
- Modify: `tests/test_postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] Step 1: Write a failing test for season-to-palette mapping.
- [ ] Step 2: Run `python3 -m unittest tests.test_postprocess_3d_contribution_graph` and confirm the new test fails for the expected reason.
- [ ] Step 3: Add a failing test that checks multiple seasons appear in one transformed SVG.
- [ ] Step 4: Run `python3 -m unittest tests.test_postprocess_3d_contribution_graph` and confirm the new test fails.

## Chunk 2: Implementation

### Task 2: Add seasonal palette selection to the stable transformer

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test: `tests/test_postprocess_3d_contribution_graph.py`

- [ ] Step 1: Add fixed five-level palettes for spring, summer, autumn, and winter.
- [ ] Step 2: Add date helpers to map cube positions to seasons.
- [ ] Step 3: Update the recolor logic to choose colors from the correct seasonal palette.
- [ ] Step 4: Keep side faces as darker variants of the selected top-face color.
- [ ] Step 5: Run `python3 -m unittest tests.test_postprocess_3d_contribution_graph` and confirm all tests pass.

## Chunk 3: Output Verification

### Task 3: Regenerate the checked-in metrics SVG

**Files:**
- Modify: `github-metrics.svg`
- Modify: `README.md` if the cache-busting URL changes later via workflow

- [ ] Step 1: Run `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`.
- [ ] Step 2: Confirm the output contains multiple seasonal families in the graph section.
- [ ] Step 3: Run `python3 -m unittest tests.test_postprocess_3d_contribution_graph` again.
- [ ] Step 4: Commit the seasonal palette update.
