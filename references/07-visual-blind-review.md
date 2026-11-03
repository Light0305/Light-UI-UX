# 07 — Multi-Viewport Evidence Capture & Dual-Subagent Isolated Blind Review Protocol

This manual governs **Step 5 (Visual Verification & Blind Review Loop)**. Because an agent that just wrote 500 lines of UI code suffers from confirmation bias, full pages and major redesigns MUST be verified through **rendered browser screenshots** and an **isolated blind-review subagent**.

---

## 1. Tiered Verification Routing

| Task Scope | Required Verification Level |
| :--- | :--- |
| **Tier 1: Small / Routine Edits** (color tweak, spacing fix, single button, copy update) | • Run `python scripts/inspect_ui.py <target>` to verify zero lint errors and take a single viewport screenshot.<br>• Skip the subagent review loop. |
| **Tier 2: Full New Pages, Major Redesigns & High-Craft Components** | • Run `python scripts/inspect_ui.py <target> --evidence --out-dir ./.light-ui/evidence` to capture the **Multi-Viewport Evidence Package** (`1440×900` desktop, `390×844` mobile, `--mask` text-masked silhouette, and `evidence-report.json`).<br>• Dispatch **Subagent A (Visual Blind Reviewer)** — target score **`≥ 9.0 / 10`** (max 3 rounds).<br>• For multi-step `Operate` workbenches, also dispatch **Subagent B (UX & Cognitive Walkthrough Reviewer)**. |

---

## 2. Strict Context Isolation Law (Preventing Confirmation Bias)

When invoking the Reviewer Subagent (`invoke_subagent`), **strictly enforce information isolation**:
- **WHAT TO PASS**:
  1. Absolute paths to the captured screenshots (`desktop.png`, `mobile.png`, `desktop-masked.png`) and `evidence-report.json`;
  2. The user's original 1–2 sentence task and Visitor Mode (`Persuade / Experience / Operate / Read`);
  3. The 1-sentence North Star concept and benchmark ID anchor;
  4. Instructions to follow `references/08-blind-reviewer-rubric.md` (Subagent-only scoring rubric) and Section 3/4 of `references/07-visual-blind-review.md`.
- **WHAT NEVER TO PASS**:
  - **NEVER pass your HTML/CSS/React source code** (the reviewer judges *only* what the human eye sees on screen plus the automated lint JSON);
  - **NEVER pass self-justifications or excuses** for why you made a compromise;
  - **NEVER pass the previous round's numeric score** during a fresh blind evaluation.

---

## 3. Subagent Role A: Visual Blind Reviewer Protocol (`10-Point Scale, Target ≥ 9.0`)

The Visual Blind Reviewer executes this **6-Step Cold-Read Protocol** in strict order:

### Step 0: The 3-Second Thumbnail & Text-Mask Gate (`≤ 7.0` Hard Ceiling!)
Inspect `desktop-masked.png` (where all text fills are rendered transparent so only layout geometry, surface hierarchy, color proportions, and imagery remain):
1. **Structural Identity**: With all text hidden, does the page still possess an unmistakable architectural rhythm and clear focal hierarchy?
2. **Hero Visual Specificity**: Is the hero visual specific to this domain, or is it a generic stock photo / abstract glowing blob / 3-column card template that could belong to any random SaaS?
3. **THE HARD CEILING RULE**:
   > **If hiding the text reduces the page to a generic template (`Hero + 3 Equal Cards`), OR if the focal visual could be swapped onto a competitor's site without anyone noticing, the TOTAL SCORE IS HARD-CAPPED AT `≤ 7.0 / 10`!**

### Step 1: Material & Benchmark Fidelity (`TYPE / MATERIAL / GROUND` Table)
Output a mandatory 3-row fidelity check against the stated direction:
- **`TYPE`**: Does the rendered typography exhibit the required scale contrast (`≥ 4:1` on Persuade), CJK line-height (`1.25–1.40`), and `tabular-nums` alignment?
- **`MATERIAL`**: Are surfaces crisp (`0.5px–1px` hairlines, concentric inner radii $R_{\text{in}} = R_{\text{out}} - G$, authentic photography/shaders)? **If the implementation substituted cheap flat SVG/CSS shapes where tactile photography or WebGL was promised, immediately issue `DISPOSITION: rebuild`!**
- **`GROUND`**: Does the color distribution obey the `≤ 10%` accent rule (or chosen `colorize` strategy) and zero `gray-on-color`?

### Step 2: The 9-Point AI Slop Deduction Matrix
Deduct **`-0.8 to -1.5` points per violation** if any of the following appear:
1. Kicker / Eyebrow mini-labels or uppercase pills above headings;
2. Card-inside-card nesting or wall-to-wall uniform bordered cards;
3. `2–4px` colored side stripes (`border-left` / `border-top`);
4. Unrequested purple/blue/cyan gradients, gradient text, or zero-offset neon glow;
5. Fake browser traffic-light dots or fake `9:41` status bars on web cards;
6. Chinese display headlines with colliding strokes (`line-height < 1.2`) or system-default unstyled font;
7. Emoji (`✨ 🚀 💡`) used as UI icons;
8. Monotonous vertical spacing where every section has the exact same padding and layout;
9. Meta-labels (`"示例"`, `"Placeholder"`, `"Feature 1"`) printed on the UI.

### Step 2a: Copy Necessity & Primary Action

Apply the [copy necessity check](02-anti-ai-slop-gates.md#31-copy-necessity) to the rendered screen. Identify secondary tags, descriptions, subtitles, and helper sentences that repeat the heading, action, or visible content. Cite the exact phrase and location, then recommend deletion, merging, or disclosure when relevant. If the task is unclear, inspect hierarchy, spacing, grouping, and action labels before adding explanatory prose. Retain necessary field labels, status, recovery instructions, and decision consequences; do not request a subtitle for every section by habit.

### Step 3: Narrow-Viewport (`390×844`) & Defect Sweep
Inspect `mobile.png` and `evidence-report.json`:
- Check for horizontal overflow, text truncation/collision, broken images, or `opacity: 0` stuck entrance animations.

### Step 4: Output Format (Mode A vs. Mode B)
- **Mode A (Cold Evaluation)**:
  - **Score**: `X.X / 10.0` (`9.0–10.0` Ship-Ready | `7.0–8.9` Good but needs polish | `5.0–6.9` Mediocre/Slop — requires structural rework | `≤ 4.9` Broken)
  - **Disposition**: `SHIP` | `FIX` (list up to 6 concrete visual fixes) | `REBUILD` (hero or skeleton must be redone)
  - **Step 0 Mask Verdict**: Pass / Capped at `≤ 7.0`
  - **`TYPE / MATERIAL / GROUND` Table**
  - **Prioritized Actionable Fixes** (`#1` to `#6`)
- **Mode B (Targeted Verdict Pass — Rounds 2 & 3)**:
  - Verify each fix from the previous round as **`[RESOLVED]`**, **`[PARTIAL]`**, or **`[UNRESOLVED]`**, check for any newly introduced regressions, and update the final score.

---

## 4. Subagent Role B: UX & Cognitive Walkthrough Protocol (`40-Point Nielsen + 5 Personas`)

For interactive applications and `Operate` workbenches, evaluate usability across three quantitative lenses:

### 4.1 Nielsen's 10 Usability Heuristics (`0–4` Points Each = `40` Points Max)
Score each heuristic (`0` Violated, `1` Poor, `2` Acceptable, `3` Good, `4` Exemplary):
1. **Visibility of System Status** (clear active states, loading feedback, progress)
2. **Match Between System and the Real World** (speaks the user's domain vernacular, not database schema names)
3. **User Control and Freedom** (easy cancel, `Esc` to close, Undo support, clear back path)
4. **Consistency and Standards** (uniform control heights, predictable button placement)
5. **Error Prevention** (constraints, smart defaults, confirmation before destructive action)
6. **Recognition Rather Than Recall** (zero memory burden across views; context stays visible)
7. **Flexibility and Efficiency of Use** (keyboard shortcuts `⌘K` / `J/K`, bulk actions, dense rows for power users)
8. **Aesthetic and Minimalist Design** (85% quiet workspace surface; zero decorative chart clutter; secondary copy adds necessary information rather than repeating controls)
9. **Help Users Recognize, Diagnose, and Recover from Errors** (plain-language cause + 1-click recovery action)
10. **Help and Documentation** (contextual empty states with 1 clear starter action)

### 4.2 Cowan's Law Cognitive Load Check (`≤ 4` Chunks)
Verify that no single decision group, nav bar, or card forces the user to hold `> 4` ungrouped items in working memory simultaneously.

### 4.3 The 5 Extreme Persona Walkthroughs
Walk through the primary task as each of these 5 personas and report any friction:
- **`Alex` (Impatient Power User)**: Wants to complete the core workflow in `< 60 seconds` using keyboard shortcuts and zero modal interruptions.
- **`Jordan` (First-Time Visitor — 5-Second Test)**: Lands cold; must understand what the app does and where to click first within `5 seconds`.
- **`Sam` (Accessibility & Keyboard-Only User)**: Navigates strictly via `Tab` / `Enter` / `Space` / `Esc` at `200%` browser zoom; requires unmistakable `:focus-visible` rings and `≥ 4.5:1` contrast.
- **`Riley` (Chaos & Edge-Case Tester)**: Double-clicks submit buttons, pastes 200-character strings with Emoji, tests `0` items and `10,000` items.
- **`Casey` (One-Handed Mobile User)**: Uses a `390×844` screen with one thumb; checks that primary actions sit in the reachable thumb zone with `≥ 44×44px` hit targets.
