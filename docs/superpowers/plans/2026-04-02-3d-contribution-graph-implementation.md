# 3D Contribution Graph Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a post-processing step that reshapes only the 3D contribution graph into a softer multi-color palette with stronger depth, while keeping the existing metrics generation flow intact.

**Architecture:** Keep `lowlighter/metrics` as the source of truth for `github-metrics.svg`, then run a focused post-processor against the generated SVG. The post-processor will detect the isometric contribution calendar section, remap cube colors to a pastel palette, and strengthen face contrast so the graph keeps the new look across future automated regenerations.

**Tech Stack:** GitHub Actions workflow YAML, Python 3 standard library for SVG post-processing, Git diff for verification

---

## Chunk 1: Workflow And Post-Processor

### Task 1: Add the post-processing script skeleton

**Files:**
- Create: `scripts/postprocess_3d_contribution_graph.py`
- Reference: `docs/superpowers/specs/2026-04-02-3d-contribution-graph-design.md`

- [ ] **Step 1: Inspect the current SVG structure around the 3D graph**

Run: `rg -n "Contributions calendar|brightness1|brightness2|#9be9a8|#40c463|#30a14e|#216e39|#ebedf0" github-metrics.svg`
Expected: Matches that confirm the existing color set and the relevant 3D graph markers are present.

- [ ] **Step 2: Create the script file with CLI entrypoint and file loading**

```python
#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: postprocess_3d_contribution_graph.py <svg-path>", file=sys.stderr)
        return 2

    svg_path = Path(sys.argv[1])
    svg_text = svg_path.read_text(encoding="utf-8")
    # Transformation will be added in later steps.
    svg_path.write_text(svg_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run the script against the existing SVG to verify the skeleton works**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: Exit code `0` and no file content changes yet.

- [ ] **Step 4: Verify that no diff was introduced by the skeleton**

Run: `git diff -- github-metrics.svg scripts/postprocess_3d_contribution_graph.py`
Expected: Only the new script file appears in diff output.

- [ ] **Step 5: Commit the scaffold**

```bash
git add scripts/postprocess_3d_contribution_graph.py
git commit -m "chore: add 3D contribution graph postprocessor scaffold"
```

### Task 2: Implement targeted graph detection and pastel palette remapping

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test Input: `github-metrics.svg`
- Reference: `docs/superpowers/specs/2026-04-02-3d-contribution-graph-design.md`

- [ ] **Step 1: Add a failing structural assertion for graph detection**

Implement a bounded section extractor and structural guards like:

```python
section_start = svg_text.find("Contributions calendar")
if section_start == -1:
    raise RuntimeError("Contributions calendar section not found")

section_end = svg_text.find('id="metrics-end"', section_start)
if section_end == -1:
    raise RuntimeError("Metrics end marker not found")

graph_section = svg_text[section_start:section_end]
required_tokens = [
    "brightness1",
    "brightness2",
    'transform="translate(',
    "#9be9a8",
    "#40c463",
    "#30a14e",
    "#216e39",
]
missing = [token for token in required_tokens if token not in graph_section]
if missing:
    raise RuntimeError(f"3D contribution graph markers not found: {missing}")
```

- [ ] **Step 2: Run the script to verify the assertion passes on the current SVG**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: Exit code `0` because the existing SVG still matches expected markers.

- [ ] **Step 3: Add exact color mapping for the top faces**

Implement a fixed mapping such as:

```python
TOP_FACE_MAP = {
    "#ebedf0": "#f2f1f8",
    "#9be9a8": "#bfe7ff",
    "#40c463": "#bff3de",
    "#30a14e": "#ffd7c2",
    "#216e39": "#d8c8ff",
}
```

Apply the replacements only after the `Contributions calendar` marker and only within the isometric graph section bounds.

- [ ] **Step 4: Run the script and inspect the resulting diff**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: The SVG diff shows the graph colors changing away from the original green palette, while other metrics sections remain unchanged.

- [ ] **Step 5: Verify the replacements are limited to expected colors**

Run: `rg -n "#9be9a8|#40c463|#30a14e|#216e39" github-metrics.svg`
Expected: Either no remaining matches in the 3D graph section or only non-graph occurrences that were intentionally left unchanged.

- [ ] **Step 6: Commit the palette mapping**

```bash
git add scripts/postprocess_3d_contribution_graph.py github-metrics.svg
git commit -m "feat: add pastel palette for 3D contribution graph"
```

### Task 3: Strengthen cube depth and face contrast

**Files:**
- Modify: `scripts/postprocess_3d_contribution_graph.py`
- Test Input: `github-metrics.svg`

- [ ] **Step 1: Add side-face color derivation for stronger depth**

Implement per-level face colors that intentionally increase contrast, for example:

```python
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
```

- [ ] **Step 2: Update the transformation logic so cube faces use separate top, left, and right colors**

The script should identify the three `<path>` elements per cube group and assign them deterministic colors by face role.

- [ ] **Step 3: Increase the visual height effect where the source SVG already encodes elevated cubes**

Increase perceived height conservatively by adjusting only the side-face depth for cubes that already have non-flat geometry. Do not rewrite the overall graph layout or baseline coordinates.

- [ ] **Step 4: Run the script and inspect depth-related diffs**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: The cube side faces show a larger brightness difference than before, making the terrain look more pronounced.

- [ ] **Step 5: Verify other SVG sections were not altered**

Run: `git diff -- . ':(exclude)github-metrics.svg'`
Expected: Only the intended script file is modified outside the generated SVG.

- [ ] **Step 6: Commit the depth enhancement**

```bash
git add scripts/postprocess_3d_contribution_graph.py github-metrics.svg
git commit -m "feat: deepen 3D contribution graph shading"
```

### Task 4: Wire the post-processor into GitHub Actions

**Files:**
- Modify: `.github/workflows/metrics.yml`
- Modify: `scripts/postprocess_3d_contribution_graph.py`

- [ ] **Step 1: Add a workflow step immediately after metrics generation**

Insert a step like:

```yaml
      - name: Post-process 3D contribution graph
        run: python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg
```

- [ ] **Step 2: Make the script fail loudly on missing target structure**

Add checks for:

```python
if replacements < MIN_EXPECTED_REPLACEMENTS:
    raise RuntimeError("3D contribution graph replacement count too low")
```

- [ ] **Step 3: Verify the workflow file diff is limited to the new step**

Run: `git diff -- .github/workflows/metrics.yml`
Expected: Only the new post-processing step appears, with no unrelated workflow changes.

- [ ] **Step 4: Run the script once more locally to verify it still succeeds**

Run: `python3 scripts/postprocess_3d_contribution_graph.py github-metrics.svg`
Expected: Exit code `0`.

- [ ] **Step 5: Update the workflow commit logic so the generated SVG is persisted**

Change the existing commit block so it does not discard generated artifacts before staging them.

The current block contains:

```bash
git fetch origin main
git checkout -B main origin/main
```

Update the workflow so the post-processed `github-metrics.svg` survives until commit time. Prefer removing the reset entirely from this job, or moving any branch sync logic to the start of the job before generation.

- [ ] **Step 6: Replace the README-only diff guard with an output-aware guard**

Use a guard that checks both tracked outputs instead of only `README.md`, for example:

```bash
if git diff --quiet -- README.md github-metrics.svg; then
  exit 0
fi
```

or stage both files first and use a cached diff check:

```bash
git add github-metrics.svg README.md
if git diff --cached --quiet; then
  exit 0
fi
```

- [ ] **Step 7: Verify the workflow commit block includes the SVG and no longer discards it**

Run: `sed -n '38,60p' .github/workflows/metrics.yml`
Expected: The commit block stages `github-metrics.svg`, avoids a post-generation reset, and only exits early when neither output changed.

- [ ] **Step 8: Commit the workflow integration**

```bash
git add .github/workflows/metrics.yml scripts/postprocess_3d_contribution_graph.py
git commit -m "ci: post-process 3D contribution graph after metrics generation"
```

## Chunk 2: Verification And Handoff

### Task 5: Verify final output and keep the repo clean

**Files:**
- Modify: `github-metrics.svg`
- Verify: `.github/workflows/metrics.yml`
- Verify: `README.md`

- [ ] **Step 1: Regenerate the post-processed SVG from the current file**

Create a clean copy first so verification starts from an unmodified source snapshot:

Run: `cp github-metrics.svg /tmp/github-metrics.raw.svg`
Expected: `/tmp/github-metrics.raw.svg` contains the current pre-verification source.

- [ ] **Step 2: Run the post-processor against the clean snapshot**

Run: `python3 scripts/postprocess_3d_contribution_graph.py /tmp/github-metrics.raw.svg`
Expected: Exit code `0` and a transformed `/tmp/github-metrics.raw.svg`.

- [ ] **Step 3: Compare the clean snapshot output against the repo SVG**

Run: `diff -u github-metrics.svg /tmp/github-metrics.raw.svg`
Expected: No output if the checked-in SVG matches the result of running the post-processor from a clean source snapshot.

- [ ] **Step 4: Review the final diff**

Run: `git diff -- .github/workflows/metrics.yml scripts/postprocess_3d_contribution_graph.py github-metrics.svg README.md`
Expected: Changes are limited to the workflow file, the new script, and the intended visual updates inside `github-metrics.svg`; `README.md` should remain unchanged.

- [ ] **Step 5: Verify the repo status**

Run: `git status --short`
Expected: Only the intended files are modified or staged.

- [ ] **Step 6: Capture a concise summary of what changed**

Document:

- The exact workflow step added
- The final palette used for contribution levels
- The structural guards used to detect breakage

- [ ] **Step 7: Commit the final generated SVG if needed**

```bash
git add github-metrics.svg .github/workflows/metrics.yml scripts/postprocess_3d_contribution_graph.py
git commit -m "feat: restyle 3D contribution graph"
```
