# 01 — Benchmark Selection, Visitor Mode Routing & Concept Architecture

This manual governs **Step 1 (Direction Exploration)** and **Step 2 (Architecture & Skeleton Selection)** for any new page, application, or major redesign.

---

## 1. The Opening Triad & Visitor Mode Classification

Before proposing visual directions or writing layout code, answer three foundational questions in one sentence each:
1. **What exact category and physical/cultural world does this product inhabit?**
2. **What is the visitor's primary verb and goal in the first viewport?**
3. **How do the top 2–3 real-world benchmarks in this category structure their hero and primary controls?**

Then classify the target surface into one of the **Four Visitor Modes**:

| Visitor Mode | Primary Goal | World-Building Intervention Boundary | Skeleton Strategy |
| :--- | :--- | :--- | :--- |
| **Persuade** | Convert, launch, explain value (Landing pages, brand sites, pricing) | **World owns the composition.** Every section, metaphor, and visual artifact derives from the subject's physical world. Must expose a real primary CTA in the first viewport. | Choose from the **8 Persuade Hero Skeletons** + **4 Unboxed Whole-Page Flows**. |
| **Experience** | Immerse, play, showcase craft (Portfolios, exhibitions, interactive stories, habit/game stages) | **Work or stage leads from pixel zero; UI chrome recedes.** Controls blend into the scene or float as minimal glass/tactile overlays. | Choose from the **5 Play/Stage Skeletons** or **16 WebGL Shader Stages**. |
| **Operate** | Execute high-frequency tasks (SaaS workbenches, IDEs, dashboards, admin panels) | **World lends ONLY 4 things: `Typography`, `Color Palette`, `Density`, and `1 Signature Micro-Detail`.** Standard controls (selects, inputs, tables) NEVER wear theatrical costumes. Zero marketing slogans in the first viewport. | Choose from the **10 Primary-Verb Workspace Skeletons**. |
| **Read** | Absorb long-form knowledge (Docs, blogs, research/financial reports) | **World owns the outer frame** (masthead, side navigation rail, callouts, code blocks); **the inner reading column stays dead quiet** (`60–75ch` Latin / `25–40` CJK chars, zero background texture under body copy). | Editorial Frame + Quiet Reading Column + Sticky TOC. |

---

## 2. Querying the 1,544 Real-World Benchmarks & 3-Layer Deconstruction

Run [`scripts/arsenal.py`](../scripts/arsenal.py) to pull real-world specs and industry reasoning:

```bash
# 1. Get industry semantic tokens, recommended pattern, and anti-patterns (192 industries)
python scripts/arsenal.py industry "<industry_keyword>"

# 2. Search 1,342 website specs + 202 dissected award sites
python scripts/arsenal.py benchmark "<keyword_or_mood>" --theme light|dark --limit 3

# 3. Inspect full color/font/radius/component tokens & export ready-to-use CSS/Tailwind v4
python scripts/arsenal.py benchmark --id <benchmark_id> --export-tailwind ./theme.css

# 4. Search 152 famous brand DESIGN.md systems (Linear, Stripe, Apple, Claude, Raycast, Nothing...)
python scripts/arsenal.py brand "<brand_name>"
```

### The 3-Layer Benchmark Deconstruction Rule
When analyzing retrieved benchmarks, separate observed elements into three buckets:
1. **Baseline (Must Keep)**: Functional affordances users expect on arrival (e.g., pricing period toggle, live search bar, status filter).
2. **Cliché (Invert in `≥ 1` Direction)**: Overused habits that are not functionally required (e.g., dark neon glow for AI tools, creamy beige + italic serif for book apps, 3 equal icon cards under the hero).
3. **Clone (Strictly Forbidden)**: Never copy a single benchmark's exact color + font + layout combination 1:1 unless explicitly asked to clone that brand.

---

## 3. Domain Grounding, Peer Replacement Test & 5-Subagent Brainstorming

For **Persuade** and **Experience** surfaces, generic layouts fail. Ground the concept in the subject's concrete reality:

### 3.1 Concrete Domain Inventory & Peer Replacement Test
1. List **6–10 concrete domain specifics**: physical tools, documents/tickets/receipts, rituals, sounds, units of measurement, or domain vernacular that exist *only* in this field.
2. Formulate the core concept:
   > *"On this page, **[concrete artifact X from our inventory]** becomes **[the hero visual, section carrier, or interactive apparatus]**."*
3. **Pass the 3-Gate Peer Replacement Test**:
   - **Gate 1**: Is the headline incomplete without the visual, and the visual incomplete without the headline?
   - **Gate 2**: Does the visitor understand the value within 3 seconds without reading a paragraph of explanation?
   - **Gate 3 (The Kill Gate)**: **If you swap in a competitor's logo and name, does the concept still work?** If yes, you only have a layout template, not a concept — discard and rethink.

### 3.2 Optional 5-Subagent Isolated Concept Tournament
For high-stakes brand or launch pages, dispatch **5 independent subagents** (passing *only* factual product brief + the 6–10 concrete domain artifacts, with **zero style/layout adjectives**), assigning each a distinct angle to generate 3 concepts (15 total):
- **Agent 1 (`User Predicament`)**: The exact moment the user is stuck, anxious, or wasting time right now.
- **Agent 2 (`Borrow One Artifact`)**: Turn one physical voucher, instrument, or document from the domain into the page carrier.
- **Agent 3 (`Contrarian Inversion`)**: Everyone in this industry brags about X; lead from the exact opposite truth.
- **Agent 4 (`One Sentence + One Frame`)**: A single plain-spoken sentence paired with a single visual frame that locks together.
- **Agent 5 (`Cross-Domain Ritual`)**: Borrow a ritual or staging mechanism from an unrelated physical craft (e.g., watchmaking, cartography, darkroom printing).

---

## 4. Presenting the "3 Real-World Benchmark Briefs" & `style-explorer.html`

### 4.1 Pairwise Differentiation Gate (Hard Requirement)
When proposing **3 Candidate Directions** (`Direction A`, `Direction B`, `Direction C`):
- Across **`[Hero Skeleton, Typography, Color System, Focal Visual]`**, any two directions may overlap on **at most 1 dimension**.
- For workbenches (`Operate`), across **`[Workspace Skeleton, Object Representation, Navigation Model]`**, any two directions may overlap on **at most 1 dimension**.
- At least **1 direction** must take a bold, extreme stance, and at least **1 direction** must deliberately break the industry cliché.

### 4.2 Interactive Presentation Workflow
1. **Text Briefs First (Default)**: Present the 3 directions concisely (Name + Benchmark ID anchor + 3-line visual/spatial description + Palette/Font summary + Hero headline), state your recommended choice, and pause for user selection.
2. **Visual Explorer (`style-explorer.html`)**: Whenever the user asks to see visuals or delegates the choice (*"你定 / 看着办"*), run [`scripts/style_explorer.py`](../scripts/style_explorer.py):
   ```bash
   python scripts/style_explorer.py \
     --benchmarks "ref-b36d5c7c-9b2,ref-486c3132-9ff,ref-cc38369a-41e" \
     --product "Product Name" \
     --headline "Hero Headline" \
     --out ./style-explorer.html
   ```

---

## 5. Skeleton Catalog: Persuade vs. Operate vs. Play

### 5.1 The 8 Persuade Hero Skeletons (Pick Skeleton Before Writing Copy!)
> **Hard Limit**: In any 3-direction exploration, **at most 1 direction** may use Skeleton #8 (Left-Text / Right-Image Split). Note that asymmetric 8:4 or 9:3 left-right splits still count as Split!

1. **Full-Bleed Media + Calm-Zone Type**: Full-viewport photograph, video, or shader stage; typography sits inside a verified low-variance `calm` zone (`left`, `bottom-left`, or `top`).
2. **Centered Iconic Object**: A single tactile product/artifact commands the center; headline wraps behind, over, or around it with generous perimeter whitespace.
3. **The Stage Is the Product (`UI-as-Hero`)**: The first viewport is an immediately playable, live interactive slice of the actual tool (`ui-slice`), accompanied by a single concise headline.
4. **Typographic Monument (Full-Viewport Type)**: Zero hero illustration; architectural display typography, deliberate line breaks, and scale contrast (`≥ 5:1`) carry the entire first screen.
5. **Full-Width Vertical Stack**: Short, high-impact centered headline + CTA at the top, followed immediately by an edge-to-edge panoramic product frame rising from the bottom fold.
6. **Asymmetric Editorial Collage / Bento**: The first viewport is partitioned into 3–5 asymmetric cells showcasing live metrics, media, and value claims simultaneously.
7. **Vertical / Diagonal Axis**: Vertical CJK/editorial type (`writing-mode: vertical-rl`) or diagonal structural division for cultural, exhibition, or publishing surfaces.
8. **Left-Copy / Right-Visual Split (Restricted)**: Use *only* when the value proposition requires a multi-line explanation that must be read side-by-side with a diagram.

### 5.2 Whole-Page Flow Below the Fold (`Persuade`)
- **Adjacent Sections Never Share a Layout**: Alternate across:
  - *Staggered Editorial Two-Column* (`80–160px` vertical offset between left and right columns),
  - *Borderless Hover-Reveal Index* (`4%–6%` active tint linked to a sticky preview frame),
  - *Sticky Left Stage + Scrolling Right Narrative*,
  - *4–7 Item Staging Container* (Horizontal Accordion / Curved Depth / Stacked Deck / Orbital Lens — see `references/04-motion-and-components.md`),
  - *Full-Bleed Atmospheric Interlude*.
- **Carrying Weight Without Card Borders**: When removing card borders, prevent the page from feeling loose by enforcing: ① `4–6×` display-to-body scale contrast, ② Concrete domain specs/telemetry, ③ Alternating media and typographic density (never `> 2` consecutive text-only screens), and ④ **2–3 shared vertical left-alignment anchor lines** running down the entire page.

### 5.3 The 10 Primary-Verb Workspace Skeletons (`Operate`)
Select the workbench architecture strictly by the user's **Primary Verb**:

| Primary Verb | Workspace Skeleton | Mandatory Structural & Density Rules |
| :--- | :--- | :--- |
| **1. Triage / Process One-by-One** | **Queue / Inbox** (Split Master-Detail) | Left list (`280–360px`) + right detail pane; `J/K` keyboard navigation; completing an item auto-advances to the next. |
| **2. Compare & Filter** | **High-Density Table** | Right-align numeric columns (`tabular-nums`), left-align text; sticky header; inline cell editing; bulk selection bar on check. |
| **3. Create & Author** | **Canvas / Document** | Central canvas occupies **`≥ 80%`** of viewport area; toolbars dock to edges (`28–34px` high) or appear contextually on selection. |
| **4. Schedule Across Time** | **Timeline / Calendar** | Time axis is the primary coordinate; support drag-to-reschedule, duration resize handles, and zoom granularity (`day/week/month`). |
| **5. Locate in Space** | **Spatial Map / Floorplan** | The map/floorplan *is* the primary workspace; status pins open a non-blocking side drawer or floating card on click. |
| **6. Advance Multi-Stage Flow** | **Kanban / Pipeline** | Columns represent discrete stages; cards show `≤ 3` data points; drag-and-drop transitions with spring physics. |
| **7. Monitor & Intervene** | **Actionable Telemetry** | Quiet at rest, unmistakable on anomaly. **Every chart/metric MUST include a normal baseline reference AND a click-to-intervene action** (never stack decorative no-action charts). |
| **8. Converse to Produce** | **Chat + Independent Artifact Canvas** | Left stream (`MessageScroller` without avatars or card boxes) + right live Artifact/Code/Document canvas. |
| **9. Browse & Curate** | **Media Shelf / Text-Index Preview** | Thumbnail-first grid, or a dense numbered text directory that reveals a floating preview image at a fixed coordinate on hover. |
| **10. Play & Cultivate** | **Tactile Machine / Diorama Stage** | Layered background illustration + crisp SVG/Canvas interactive controls + 4-tier audiovisual feedback (Daily / Milestone / Rare / Charge-up). |
