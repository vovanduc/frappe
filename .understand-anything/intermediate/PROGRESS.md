# Knowledge Graph Rebuild — Progress Tracking

Full rebuild of `.understand-anything/knowledge-graph.json` for Frappe Framework to achieve complete codebase coverage. Work is split into sequential sessions to avoid token exhaustion.

## Source State

- **Base commit**: `8c3708a87a` (develop branch)
- **Previous graph**: 659 nodes, 668 edges, 153 files (~7.4% coverage)
- **Target**: 2,160 total source files (python, javascript, vue, shell)
- **Scan result**: `intermediate/scan-result.json`

## Pipeline

Using the `/understand` skill from the `understand-anything` plugin (v1.1.0). Pipeline phases:
1. **SCAN** (done) → `scan-result.json`
2. **ANALYZE** (in progress, batched) → `batch-N.json` files
3. **ASSEMBLE** (pending) → merge batches, dedupe
4. **ARCHITECTURE** (pending) → identify layers
5. **TOUR** (pending) → generate learning tour
6. **REVIEW** (pending) → validate graph
7. **SAVE** (pending) → final `knowledge-graph.json` + `meta.json`

Each batch = 10 files. Each batch dispatched as a background subagent with a prompt-template task. Up to 3 concurrent agents at a time. Results saved individually in `batch-N.json` so they survive across sessions.

## Session Plan

| Session | Scope | Files | Batch Range | Status |
|---------|-------|-------|-------------|--------|
| 1 | `frappe/` root + `core/` + `model/` | 456 | 0–45 | ✅ Done |
| 2 | `frappe/utils/`, `frappe/database/` | 94 | 46–55 | ✅ Done |
| 3 | `frappe/public/js/` (JS + Vue) | 351 | 56–91 | ✅ Done |
| 4 | `frappe/email/`, `workflow/`, `printing/`, `website/` | 346 | 92–126 | 🟡 **13/35** (92–104 done) — rate limit hit at 105, resume after reset |
| 5 | `frappe/integrations/`, `automation/`, `desk/` | ~250 | TBD | ⏳ Pending |
| 6 | Remaining + Phases 3–7 (merge, layers, tour, save) | ~700 | TBD | ⏳ Pending |

## Cumulative Results (through Session 4 partial)

| Metric | Session 1 | Session 2 | Session 3 | Session 4 (partial) | **Total** |
|--------|-----------|-----------|-----------|---------------------|-----------|
| Batches | 46 | 10 | 36 | 13 / 35 | **105** |
| Files | 456 | 94 | 351 | ~130 | **~1,031 / 2,160** |
| Nodes | 1,301 | 412 | 1,868 | 443 | **4,024** |
| Edges | 1,587 | 582 | 2,180 | 1,028 | **5,377** |
| Coverage | 21.1% | 4.4% | 16.3% | ~6.0% | **~47.7%** |

### Session 4 Resume Point

- **Remaining batches**: 105–126 (22 batches, ~216 files)
- **Covers**: rest of `frappe/website/` (doctypes, pages, templates, web_page, web_form, etc.)
- **Next batch to dispatch**: 105 (starts at `frappe/website/doctype/about_us_settings/test_about_us_settings.py`)
- **Batch definitions**: `intermediate/session4-batches.json` (batches[13] through batches[34])
- **Rate limit**: Hit at 2026-04-13 during batch 105 dispatch; resets 10am Asia/Saigon

## Batch Definitions

- `session1-files.json` — Session 1 batch definitions (created inline)
- `session2-batches.json` — Session 2 batch definitions (10 batches, files in `utils/`, `database/`)
- `session3-batches.json` — Session 3 batch definitions (36 batches, files in `public/js/`)

## Critical Notes

- **Do NOT delete `intermediate/`** between sessions — batch files must persist for final merge in Session 6.
- Session 6 will run the full merge, then invoke Phases 3–7 via the `/understand` skill to produce the final graph.
- The existing `knowledge-graph.json` and `meta.json` at `.understand-anything/` are from the previous partial analysis (153 files). They will be overwritten in Session 6.
- Each batch prompt follows the `file-analyzer-prompt.md` template from the plugin at `~/.claude/plugins/cache/understand-anything/understand-anything/1.1.0/skills/understand/`.

## Resume Instructions

To continue from Session 4:
1. Filter Session 4 files from `scan-result.json` (paths starting with `frappe/email/`, `frappe/workflow/`, `frappe/printing/`, `frappe/website/`)
2. Split into batches of 10, save as `session4-batches.json`, continue numbering from batch 92
3. Dispatch subagents 3 at a time using the same prompt shape as Sessions 1–3
4. Each batch writes to `intermediate/batch-N.json`
