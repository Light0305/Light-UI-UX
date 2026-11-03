# 02 — Three-Wave Anti-AI-Slop Iron Curtain & 67 Deterministic Lint Gates

This manual defines the **non-negotiable quality gates** that eliminate "AI-generated plastic feel" (AI Slop) before, during, and after code generation.

---

## 1. Wave 1: The 19 Zero-Tolerance Structural & Visual Bans

Any interface exhibiting the following patterns is immediately flagged as AI Slop. **If `≥ 3` items occur without an explicit user brief mandate, rebuild the layout from scratch:**

| # | Rule ID | Zero-Tolerance Ban | Mandatory Replacement |
| :---: | :--- | :--- | :--- |
| **01** | `kicker-above-heading` | **NO Kicker / Eyebrow mini-labels above headings** (e.g., uppercase `FEATURES`, `WORKSPACE`, or pill badges with pulsing dots above H1/H2). | Delete the kicker completely. Let the heading and spatial hierarchy speak for itself. |
| **02** | `nested-cards` | **NO Card-Inside-Card Nesting** (a rounded container with background/border/shadow containing `≥ 2` inner bordered/shadowed cards). | Use whitespace, `1px` hairlines (`divide-y`), or direct surface typography without inner card boxes. |
| **03** | `icon-tile-stack` | **NO 3-Equal-Icon-Card Rows** (`[Icon in tinted circle/square + Bold Title + 2-line blurb] × 3`) directly beneath the hero. | Use an asymmetric Bento slice, a staging container (`Horizontal Accordion`), or an unboxed editorial list. |
| **04** | `side-stripe` | **NO Colored Side Stripes** (`border-left: 3px solid` or `border-t-4` on rounded cards, alerts, or list items). | Use a subtle full-perimeter `1px` border (`box-shadow: 0 0 0 1px`) or a `6px` status dot. |
| **05** | `gradient-text` | **NO Unrequested Gradient Text** (`-webkit-background-clip: text; color: transparent` on purple/blue/cyan headlines). | Use high-contrast solid ink (`var(--ink)`) or subtle monochrome luminance shift only when justified by the brand. |
| **06** | `ai-color-palette` | **NO Unrequested Indigo/Violet/Cyan AI Slop Palette** (`#6366f1`, `#8b5cf6`, `#a855f7` glowing on dark slate `#0f172a`). | Derive tokens from real domain pigments via `arsenal.py industry` or `arsenal.py benchmark`. |
| **07** | `dark-glow` / `radial-halo` | **NO Zero-Offset Neon Box-Shadows** (`box-shadow: 0 0 24px rgba(...)`) or floating blurry purple/blue radial blobs in the background. | Use physical shadows with positive Y-offset (`0 8px 24px -4px`) or 1 focal WebGL shader stage. |
| **08** | `emoji-icon` | **NO Emoji or Unicode Symbols (`✨ 🚀 💡 🤖 🎯 ⚡ 🔥 ✓`) as UI icons or bullet markers.** | Extract crisp vector SVGs from the 7 compliant libraries via `python scripts/arsenal.py icon --svg <id>`. |
| **09** | `numbered-section-labels` | **NO Meaningless `01 / 02 / 03` Labels** on sections or cards that do not represent a strict sequential process. | Remove decorative numbers; use clear typographic hierarchy. |
| **10** | `fake-device-chrome` | **NO Fake Browser Window Dots** (red/yellow/green traffic lights) or fake `9:41` status bars drawn inside web cards unless specifically showcasing a desktop/mobile OS shell. | Frame product slices with clean `1px` hairlines and concentric inner radii. |
| **11** | `fake-sparklines` | **NO Meaningless Decorative Sparklines**, fake progress rings, or hardcoded `+12.4%` badges with no baseline or action. | Show realistic domain telemetry (`tabular-nums`) paired with a normal reference range and click action. |
| **12** | `pulsing-dot` / `blinking-cursor` | **NO Decorative Pulsing Dots (`animate-ping`)** on static marketing pills or fake blinking terminal cursors on non-input text. | Reserve live indicators strictly for real streaming/connection states. |
| **13** | `shape-assembled-illustration` | **NO Cheap CSS/SVG Geometric-Block Mascots** (stacking flat circles/triangles to fake a character or prop). | Use `scripts/media_gen.py` to generate authentic photography/illustration or use precision technical diagrams. |
| **14** | `organic-clip-path` | **NO Polygon/Radial `clip-path` Hacks** pretending to be torn paper or organic cutouts. | Use real alpha-channel PNG/WebP masks or SVG `feDisplacementMap`. |
| **15** | `buried-raster` | **NO Burying Generated Imagery Under `> 90%` Opaque Overlays** (`opacity < 0.1` on the image). | Use directional scrims (`linear-gradient`) over the `calm` text zone only, leaving the focal subject clear. |
| **16** | `meta-leakage` | **NO Printing Prompt Meta-Labels on Screen** (never render words like `"示例"`, `"概念图"`, `"Placeholder"`, `"Hero Section"`, `"Bento Grid"` in the UI). | Write authentic, domain-specific production copy. |
| **17** | `marketing-buzzword` | **NO Hollow AI Copywriting Clichés** (*"赋能 / 闭环 / 一站式 / 抓手 / Seamless / Empower / Supercharge / Next-Gen / Unleash"* or `"Not X. Just Y."` cadence). | Name the concrete action, tool, speed, or outcome in plain domain language. |
| **18** | `welcome-banner-in-tool` | **NO Marketing Welcome Banners Inside Logged-In Workbenches** (no giant *"Welcome back, Alex! Ready to boost productivity?"* hero inside a tool). | Start the workbench immediately with a compact `28–34px` toolbar and operable items. |
| **19** | `costumed-controls` | **NO Theatrical Costumes on `Operate` Controls** (never turn a standard dropdown into a rotary dial or a search input into a fake CLI prompt in a business workbench). | Keep operable controls standard, fast, and keyboard-accessible. |

---

## 2. Wave 2: Stale Visual Cluster Calibration & Overused Font Denylist

### 2.1 The 4 Stale AI Visual Clusters (Do Not Default To These!)
1. **Cluster 1 — Warm Bookish Beige Cliché**: `#F5EFE6` cream background + terracotta `#D97757` + italic `Fraunces / Playfair / Instrument Serif`.
   - *Correction*: If the subject involves books/editorial/craft and the background lightness is $L > 0.88$ with chroma $C < 0.04$, shift to saturated physical pigments from the domain (e.g., deep bookbinding buckram, dyed endpapers, archival cobalt, or stark newsprint `#F4F4F0` + `#060606` ink).
2. **Cluster 2 — Dark Hacker Neon Matrix**: Near-black background + acid green / electric cyan + all-caps monospace labels everywhere + dual-axis CSS grid lines.
3. **Cluster 3 — Fake Vintage Broadsheet**: Yellowed paper + full-width `1px` black rules + fake `"ISSUE NO. 04 · EST. 2026"` masthead on a software product.
4. **Cluster 4 — Generic SaaS White Card Shell**: Soft pastel mesh gradient + `16px` rounded white cards + pill tags + 4 fake round stat blocks (`100%`, `10x`, `24/7`, `99.9%`).

### 2.2 The 16 Overused AI Default Fonts (Restricted on `Persuade` / `Experience` Heroes)
Do not reflexively pick these fonts for hero display headlines without checking `arsenal.py benchmark` or `arsenal.py blueprint --type font_pairing`:
- *Restricted List*: `Inter` (as hero display; fine for dense UI body), `Space Grotesk`, `Plus Jakarta Sans`, `Outfit`, `DM Sans`, `Syne`, `Fraunces`, `Playfair Display`, `Cormorant`, `Lora`, `Crimson`, `Newsreader`, `DM Serif`, `Instrument Sans`, `Space Mono`, `IBM Plex Mono` (when used as a "tech costume" on non-code text).

---

## 3. Wave 3: Hard Subtraction Budgets (Chanel's Rule)

Before finalizing any screen, enforce these quantitative ceilings:

| Resource Dimension | Hard Ceiling |
| :--- | :--- |
| **Font Families** | **`≤ 2`** (or `≤ 3` when pairing CJK + Latin + Monospace for tabular code/metrics) |
| **Font Size Steps** | **`4–6` distinct sizes** across the entire page |
| **Font Weights** | **`2–3` weights** (e.g., `400`, `500`, `600` — avoid `900` ultra-bold on CJK) |
| **Primary Accent Area** | **`≤ 10%`** of the visible viewport area (in Restrained mode) |
| **Semantic Color Roles** | **`≤ 4`** (`bg`, `surface`, `ink`, `muted`, `accent` + semantic status colors) |
| **Cards Per Row / Data Points** | **`≤ 3` cards per row**; **`≤ 3` data points per card**; **`≥ 25%` viewport whitespace** |
| **Heavy Visual Ornament** | **Exactly `1` primary signature technique per page** (e.g., 1 WebGL shader OR 1 SVG grain/displacement filter OR 1 3D stage — never stack all three) |
| **Narrative Copy Length** | Hero H1 **`≤ 15` CJK chars** (or `≤ 10` English words); an optional subhead **`≤ 40` CJK chars**; use a concise, explicit action label. These are ceilings, not slots that must be filled. |

### 3.1 Copy Necessity

Let layout, visual hierarchy, spacing, and a clear primary action carry the explanation. Start with the actual content or task; add secondary text only when it supplies information needed to understand, decide, or act.

- **Deletion check**: If removing a label, subtitle, caption, description, or helper sentence leaves the task equally clear, remove it. Judge meaning in its local context, not total word count or font size.
- **No default scaffolding**: A heading does not automatically need a category tag, subtitle, and paragraph. A clear button does not need a nearby sentence explaining that it can be clicked.
- **One useful statement**: Merge repeated facts near the object or action they qualify. Keep distinct information such as units, scope, or billing terms.
- **Fix the structure first**: If users need prose to find the next action, improve grouping, hierarchy, spacing, or the action label. Do not disguise clutter with smaller or lower-contrast text.
- **Reveal details when relevant**: Put optional instructions and advanced details behind a clear help/disclosure control or show them in the applicable state. Keep information needed before a decision visible.
- **Preserve usability**: Keep necessary visible field labels, accessible names, units, meaningful status, error/recovery guidance, and material action consequences. Placeholder-only fields and color-only status do not satisfy this rule. Reading content and requested editorial descriptions are not auxiliary clutter.

| Context | Decision |
| :--- | :--- |
| `Billing` tag + `Billing` heading + “Manage your billing settings here.” | Keep the heading and billing controls; remove the repeated tag and sentence. |
| `Save changes` button + “Click here to save your changes.” | Keep the button; remove the explanation. |
| `Export CSV` button + “Includes filtered rows only.” | Keep the scope statement when the exported set would otherwise be ambiguous. |

---

## 4. The 67 Deterministic Static & DOM Lint Rules (`scripts/inspect_ui.py`)

Our automated inspection engine ([`scripts/inspect_ui.py`](../scripts/inspect_ui.py)) combines **53 static/computed anti-pattern checks** and **14 live DOM geometry checks**:

### 4.1 Immediate-Tier Blockers (12 Rules — Must Be Zero Before Delivery)
1. `broken-image`: `<img>` with `naturalWidth === 0` or failed network load.
2. `script-error`: Uncaught JS runtime exception or WebGL shader compile failure on load.
3. `content-hidden-at-rest` (`stuck`): `> 35%` of block elements in the first `1.5` viewports have `opacity < 0.08` at rest (broken entrance animation).
4. `text-overflow` / `horizontal-scroll`: `document.documentElement.scrollWidth > window.innerWidth` on `1440px` desktop or `390px` mobile.
5. `text-occlusion`: Text bounding box overlapped by another opaque sibling or colliding due to negative line-height.
6. `body-text-viewport-edge`: Visible text within `< 16px` of viewport edge on desktop (`< 12px` on mobile).
7. `low-contrast`: Computed text-to-background WCAG contrast `< 4.5:1` for body text (`< 3.0:1` for large display text `≥ 24px`).
8. `gray-on-color`: Achromatic gray text (saturation `< 0.08`) placed on a saturated colored surface (saturation `> 0.18`).
9. `tiny-text` / `undersized-ui-text`: Any functional UI text (button, tab, table cell, timestamp) `< 11px` or body text `< 12px`.
10. `kicker-above-heading` / `eyebrow`: Uppercase or wide-tracked mini-label `< 13px` positioned directly above a heading `≥ 22px`.
11. `gradient-text`: Headline using `-webkit-background-clip: text` with transparent fill unless explicitly whitelisted.
12. `dark-glow`: Box shadow with `0px` X/Y offset and colored blur radius `≥ 12px` on a dark surface.

### 4.2 Typography, Rhythm & Layout Geometry Checks
- `tight-leading`: Multi-line text (`≥ 2` lines) with computed `line-height / font-size < 1.25`.
- `long-measure`: Paragraph `≥ 2` lines exceeding `80` Latin characters or `46` CJK characters per line.
- `heading-rhythm` (`headingSpacing`): `≥ 2` subheadings whose top margin/gap to the preceding block is `< 85%` of their bottom gap to the following paragraph ($\text{Gap}_{\text{top}}$ must be $> \text{Gap}_{\text{bottom}}$).
- `skipped-heading`: DOM heading levels jump (e.g., `<h1>` directly to `<h3>`).
- `cramped-padding`: Text inside a bordered or tinted container sitting `< 8px` from the container border.
- `edge-flush-cards`: Cards inside a horizontal scroll track flush against the viewport clip edge without scroll padding.
- `first-viewport-column-overflow`: One column in a multi-column hero overflows far below the fold while its sibling column hangs empty.
- `repeated-container-text`: The exact same number or string rendered `≥ 3` times inside a single card/component.

### 4.3 Contextual Copy Review

Copy necessity is a contextual review, not a deterministic lint result. `inspect_ui.py` can flag some labels and stock phrases; a clean report does not establish that every sentence is useful. Apply Section 3.1 to the rendered interface, cite the exact redundant text and location, and verify that removal preserves comprehension and operation. Do not add regex bans for ordinary helper text or treat required labels as clutter.
