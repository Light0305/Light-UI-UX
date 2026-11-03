# 06 — Existing Project Polish, Anti-Slop Refactoring & UX Workflow Surgery

This manual governs **Scenario B**: polishing an existing page, upgrading a legacy codebase's design system, or adding features/workflows to an existing product without breaking its visual coherence.

---

## 1. Three-Way Intent Routing for Existing Projects

When working inside an existing repository, first route by user intent:

| Sub-Scenario | Primary Goal | Execution Protocol |
| :--- | :--- | :--- |
| **1. Page-Level Visual Polish** | Eliminate AI template feel, fix alignment/contrast/spacing bugs on an existing screen | **Two-Round Non-Destructive Polish Protocol** (Diagnose + `--mark` Screenshot first; Refactor from tokens second). |
| **2. Project-Wide UI Upgrade** | Establish or upgrade the design system across multiple views | **Brand Asset vs. Default Separation** $\rightarrow$ Author `DESIGN.md` $\rightarrow$ User selects **Tidy / Upgrade / Reshape** scale. |
| **3. Workflow & Feature Surgery** | Add a new feature or streamline a clunky multi-step user flow | **Lock Existing Visuals** $\rightarrow$ **4-Ledger Path Accounting** $\rightarrow$ **5 Root-Cause Audit** $\rightarrow$ **Inline / Automatic / Dedicated** posture. |

---

## 2. Sub-Scenario 1: The Two-Round Non-Destructive Page Polish Protocol

> [!IMPORTANT]
> **Round 1 Iron Rule: Diagnose Only — Modify Zero Source Files in Round 1!**
> Never silently rewrite a user's existing page without showing them what is broken and getting confirmation on structural changes.

### Round 1: Baseline Capture, 7-Dimension Audit & Marked Callout
1. **Check for `DESIGN.md` / Theme Tokens**: Inspect `DESIGN.md`, `globals.css`, `tailwind.config.*`, or `theme.ts` to understand existing tokens.
2. **Run [`scripts/inspect_ui.py`](../scripts/inspect_ui.py)** on the target file or dev server URL:
   ```bash
   python scripts/inspect_ui.py <url_or_html_or_dir> --out-dir ./.light-ui/audit
   ```
3. **Audit Across the 7 Polish Dimensions**:
   - **① Alignment & Spatial Rhythm**: Broken left-alignment anchor lines, inconsistent card padding, headings closer to the paragraph above than the paragraph below (`heading-rhythm`), cramped borders (`< 8px`).
   - **② Typographic Hierarchy**: Flat scale (`H1` barely larger than body), CJK display line-height `< 1.2` colliding strokes, missing `tabular-nums` on numbers, measure `> 75ch` (`> 45` CJK chars).
   - **③ Color & Contrast**: Pure `#888` gray on colored surfaces (`gray-on-color`), WCAG contrast `< 4.5:1`, dark-mode surfaces using black drop-shadows instead of tonal lightness elevation, `> 10%` garish accent area.
   - **④ Interactive States & Native Surfaces**: Missing `:hover`, `:active` (`scale(0.97)`), `:focus-visible`, loading, or empty states; un-themed browser `::selection`, `caret-color`, or scrollbars.
   - **⑤ AI Slop Tells**: Kickers/eyebrows above headings, nested cards, `2–4px` colored side stripes, unrequested purple/blue gradient text, Emoji icons (`✨ 🚀`), meaningless `01 / 02 / 03` labels. Apply the [copy necessity check](02-anti-ai-slop-gates.md#31-copy-necessity) to repeated labels, subtitles, helper sentences, and CTA footnotes.
   - **⑥ Narrow-Viewport (`390×844`) Integrity**: Horizontal overflow (`scrollWidth > innerWidth`), clipped flex children, touch targets `< 44×44px`, `<input>` font-size `< 16px`.
   - **⑦ Media & Icon Fidelity**: Broken images, stretched aspect ratios, un-feathered rectangular photo seams, mismatched icon stroke weights (`1.5px` mixed with `2.5px` solid).
4. **Present the Two-Column Diagnostic Report**:
   - **`【Direct Fixes (直接修)】`**: Objective defects (contrast failures, alignment bugs, broken states, CJK line-height, nested card borders, Emoji-to-SVG replacements).
   - **`【Confirm Scope (请确认)】`**: Structural or aesthetic shifts (changing palette mood, replacing a 3-card row with a Horizontal Accordion, rewriting hero copy).
   - Attach the `--mark` callout screenshot or `file:line` compiler list and pause for confirmation.

### Round 2: Root-Cause Refactoring (Inside-Out)
Once confirmed, never patch symptoms with inline `style="..."` overrides. Refactor strictly in this order:
1. **Token Root First**: Update CSS variables (`:root` / `.dark` / `@theme`) for surface hierarchy, OKLCH hues, font stacks, and concentric radii.
2. **Shared Primitives Second**: Fix `Button`, `Card`, `Input`, `Badge`, and `Table` primitives (ensuring uniform control heights across all 11 form/action primitives).
3. **Page Composition Third**: Unbox nested cards, establish `2–3` shared vertical left-alignment anchor lines, replace Emoji with crisp SVGs from `arsenal.py icon`, and apply the 3 baseline motions. Remove auxiliary copy that fails the necessity check; clarify grouping and primary actions while retaining needed labels, scope, and recovery guidance.
4. **Before/After Verification**: Re-run `scripts/inspect_ui.py` to confirm zero lint blockers. In the rendered page, verify that the task, current state, and next action remain clear after copy removal.

---

## 3. Sub-Scenario 2: Project-Wide UI Upgrade & `DESIGN.md` Extraction

When upgrading an existing multi-page project:
1. **Separate Intentional Brand Assets from Accidental Defaults**:
   - *Brand Assets (Keep)*: Logo colors, domain-specific terminology, established navigation mental model.
   - *Accidental Defaults (Replace)*: Unstyled Tailwind `bg-blue-500` / `text-gray-500`, default `Inter` everywhere, `1px solid #e5e7eb` on every div, violations of `references/02-anti-ai-slop-gates.md`.
2. **Generate a ~100-Line `DESIGN.md`**:
   - Document the project's Visitor Mode, Color Tokens (OKLCH/Hex), Typography Scale, Spacing/Radius Formula, and Component Rules, marking each item `(Confirmed)` or `(Agent Inferred)`.
   - **Iron Rule**: Never canonize an existing anti-pattern (such as Kickers above headings or colored side stripes) into `DESIGN.md`!
3. **Offer the 3-Scale Upgrade Choice**:
   - **Scale 1 — Tidy (`整理`)**: Unify spacing rhythm, type scale, contrast, concentric radii, and icon consistency; keep existing colors and layout skeleton untouched.
   - **Scale 2 — Upgrade (`升级`)**: Upgrade typography pairings, refine OKLCH surface hierarchy, replace static card grids with high-craft components, and add spring micro-interactions while preserving the navigation skeleton.
   - **Scale 3 — Reshape (`重塑`)**: Full 5-Step `0 → 1` redesign (new hero skeleton, new visual direction).

---

## 4. Sub-Scenario 3: UX Workflow Surgery & Feature Addition

When adding a feature or fixing a frustrating user flow inside an existing app:
1. **Lock Existing Visuals**: Do not change colors, fonts, or unrelated components.
2. **Calculate the 4-Ledger Interaction Cost** on the current flow:
   - **① Step Count**: Total clicks/taps/page loads from intent to completion.
   - **② Decision Count**: Especially **Fake Decisions** (asking the user to choose something the system already knows or can infer 95% of the time).
   - **③ Memory Burden**: Requiring the user to remember a value from Screen A to type it into Screen B (Violation of Recognition over Recall).
   - **④ Backtracking & Visual Scanning**: Bouncing between list and detail pages, or hunting across a cluttered toolbar.
3. **Hunt Down the 5 UX Root Causes**:
   - *Root Cause 1*: Splitting a single continuous thought across two separate pages or modals.
   - *Root Cause 2*: Amnesia between views (losing filter/scroll/selection state on navigation).
   - *Root Cause 3*: Asking the user to re-enter what could be defaulted or remembered from last time.
   - *Root Cause 4*: Organizing screens 1:1 around database tables (`CRUD syndrome`) instead of around the user's actual job-to-be-done.
   - *Root Cause 5*: Stuffing rare 2% edge-case options onto the primary 98% main path.
4. **Select One of Three Interaction Postures**:
   - **Posture A — Inline (`顺手`)**: Handle the action right where the object lives (inline edit, hover action bar, micro-drawer, right-hand inspector) without opening a modal or new page.
   - **Posture B — Automatic (`自动`)**: Do it automatically with a smart default and provide an instant `Undo` toast (`5–8s`).
   - **Posture C — Dedicated (`专用`)**: Only when the task requires deep focus or multi-part composition, give it a dedicated clean canvas.

---

## 5. Production Hardening Checklist (`harden`)

Before shipping to production, verify these 5 resilience gates:
1. **i18n Text Expansion (`+35%`)**: Buttons, tabs, and table headers must not clip or break layout when English/Chinese strings expand by `35%–40%` (e.g., German/Russian) or when user names are 40 characters long.
2. **Logical CSS Properties (RTL Ready)**: Prefer `margin-inline-start`, `padding-inline`, `inset-inline-end`, and `text-align: start` over physical `left`/`right`.
3. **Async Concurrency & Idempotency**: Disable or show `<Spinner data-icon="inline-start" />` on submit buttons immediately on click to prevent double-submission; preserve form input values if network request fails.
4. **Gesture Interruption Recovery**: Handle `pointercancel` and `lostpointercapture` so dragged cards/drawers never freeze mid-air when a system notification interrupts touch.
5. **Accessibility Media Queries**: Respect `@media (prefers-reduced-motion: reduce)`, `@media (prefers-reduced-transparency: reduce)`, and `@media (prefers-contrast: more)`.
