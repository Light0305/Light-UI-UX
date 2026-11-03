# 03 — CJK & Latin Dual-Track Typography, OKLCH Color Engine & Optical Surfaces

This manual defines the quantitative laws for typography, color token derivation, dark-mode compensation, and surface geometry.

---

## 1. The CJK vs. Latin Dual-Track Typography Law

> [!CAUTION]
> **Why Western AI Skills Break Chinese UI**: Western display typography uses tight leading (`line-height: 0.95–1.05`) and negative tracking (`letter-spacing: -0.03em`) because Latin lowercase letters have ascenders/descenders and open counters. **Chinese (CJK) characters occupy a full square em-box** — applying `line-height < 1.2` or negative `letter-spacing` causes CJK strokes to collide vertically and horizontally!

### 1.1 Dual-Track Parameter Matrix

| Typographic Role | Latin (Western) Specification | Chinese / CJK Specification | Mixed CJK + Latin Engineering Rules |
| :--- | :--- | :--- | :--- |
| **Hero Display (`H1`)** | • Size: `clamp(2.75rem, 5vw, 5.5rem)`<br>• Line-height: **`0.95 – 1.10`**<br>• Tracking: **`-0.02em to -0.04em`** | • Size: `clamp(2.25rem, 4.5vw, 4.5rem)`<br>• Line-height: **`1.25 – 1.40` (NEVER `< 1.2`)**<br>• Tracking: **`0 to +0.02em` (NEVER negative!)** | • Always set `text-wrap: balance` on headings.<br>• Optical left alignment: shift giant display type `-1px to -3px` left so its visual edge aligns with body copy. |
| **Section Heading (`H2 / H3`)** | • Size: `1.5rem – 2.5rem`<br>• Line-height: `1.15 – 1.25`<br>• Tracking: `-0.015em to -0.025em` | • Size: `1.375rem – 2.25rem`<br>• Line-height: **`1.30 – 1.45`**<br>• Tracking: **`0`** | • Heading top spacing MUST exceed bottom spacing: $\text{Margin}_{\text{top}} \ge 1.35 \times \text{Margin}_{\text{bottom}}$. |
| **Reading Body (`Read` / `Persuade`)** | • Size: `16px – 18px` (`1rem – 1.125rem`)<br>• Line-height: `1.55 – 1.65`<br>• Measure: **`60 – 75ch`** (max `80ch`) | • Size: `15px – 17px`<br>• Line-height: **`1.68 – 1.80`**<br>• Measure: **`25 – 40 CJK chars`** (max `45`) | • Set `text-wrap: pretty` on body copy.<br>• Choose **either** paragraph bottom margin (`1em`) **or** first-line indent — **never both**. |
| **Workbench UI (`Operate`)** | • Dense row/body: `13px – 14px`<br>• Line-height: `1.40 – 1.50`<br>• Hard floor: **`11px`** (labels/timestamps) | • Dense row/body: `13px – 14px`<br>• Line-height: `1.45 – 1.55`<br>• Hard floor: **`12px`** (CJK below 12px blurs!) | • Mobile `<input>` / `<textarea>` MUST be **`≥ 16px`** to prevent iOS Safari auto-zooming the viewport on focus. |
| **Uppercase Micro-Labels** | • Tracking: **`+0.05em to +0.10em`** | • Do not apply wide tracking (`> 0.05em`) to Chinese body sentences. | • Never place uppercase labels as Kickers/Eyebrows above headings (`kicker-above-heading` ban). |

### 1.2 Recommended CJK + Latin Font Pairings

| Aesthetic Archetype | Chinese (CJK) Font Stack | Paired Latin Display / Body | Monospace / Telemetry |
| :--- | :--- | :--- | :--- |
| **Modern Precision / Workbench** | `'PingFang SC'`, `'HarmonyOS Sans SC'`, `'Noto Sans CJK SC'` | `'Inter'`, `'Geist'`, `'Plus Jakarta Sans'` | `'JetBrains Mono'`, `'Geist Mono'` |
| **Editorial / Cultural / Luxury** | `'Source Han Serif SC'` (`思源宋体`), `'Songti SC'`, `'LXGW WenKai'` | `'Instrument Serif'`, `'Newsreader'`, `'Cormorant Garamond'` | `'IBM Plex Mono'` |
| **Architectural / Industrial Brutalist** | `'Source Han Sans SC Heavy'`, `'Alibaba PuHuiTi 3.0'` | `'Syne'`, `'Cabinet Grotesk'`, `'Space Grotesk'` | `'Commit Mono'`, `'Space Mono'` |

### 1.3 Punctuation, Orphan Prevention & Numeric Discipline
- **Full-Width CJK Punctuation**: In Chinese copy, always use proper curly quotes `“...”` / `‘...’`, em-dashes `——`, and ellipses `……` (never straight ASCII quotes `"..."` inside Chinese sentences).
- **No Orphans & No Split Units**: Wrap numbers + units (`38 秒`, `99.98%`, `¥1,280`) in `<span class="whitespace-nowrap">` so the number and its unit never break across lines. Shrink and mute units (`0.65em`, `var(--muted)`) next to hero metrics so the numeral commands attention.
- **Tabular Numerals Everywhere**: Declare `font-variant-numeric: tabular-nums` on all tables, KPI cards, timers, prices, and animated counters.

---

## 2. Dark-Mode Perceptual Compensation (3-Axis Halation Fix)

Light text rendered on a dark background suffers from **optical halation (blooming)**, making characters appear heavier and tighter than dark text on a light background. Whenever building or switching to a dark theme (`.dark`), apply **3-Axis Perceptual Compensation**:

1. **Axis 1 — Loosen Line Height**: Increase body `line-height` by **`+0.05 to +0.10`** (e.g., `1.60` $\rightarrow$ `1.68`).
2. **Axis 2 — Loosen Tracking**: Add **`+0.005em to +0.015em`** to `letter-spacing` on small text (`12–14px`).
3. **Axis 3 — Soften Ink & Elevate Surfaces by Lightness (Tonal Elevation)**:
   - Never use pure `#FFFFFF` for long-form dark-mode body text (use `#ECEEEF` or `oklch(0.93 0.01 H)`).
   - Never express elevation in dark mode by making drop shadows darker; express elevation by **stepping up surface lightness** (e.g., Canvas `#090A0D` $\rightarrow$ Card `#12141A` $\rightarrow$ Popover `#1A1D24` + `1px` top inner specular highlight `rgba(255,255,255,0.07)`).

---

## 3. The OKLCH Color Engine & 4 Color Strategies

Query `python scripts/arsenal.py industry "<domain>"` or `python scripts/arsenal.py blueprint --type color_palette` to retrieve verified palettes, then refine in **OKLCH (`oklch(L C H)`)**:

### 3.1 The 4 Intentional Color Strategies (`colorize`)
Choose one explicit strategy per surface:
1. **Restrained (90% Neutral + 10% Accent)**: Hue-tinted neutrals (`C = 0.008–0.018` sharing the brand hue angle $H$) + **1 high-conviction accent color occupying `≤ 10%` of viewport area**. Best for SaaS workbenches, fintech, developer tools, and luxury retail.
2. **Committed (30%–60% Dominant Brand Field)**: One rich color block carries the hero or primary structural band, balanced by crisp neutral typography surfaces.
3. **Full Palette (3–4 Named Chromatic Roles)**: Coordinated multi-hue editorial system (e.g., Dusty Rose + Mustard Cream + Burgundy Ink) with strict role assignment.
4. **Drenched (100% Atmospheric Immersion)**: The entire canvas is saturated pigment (`L = 0.22–0.45` or vibrant `L = 0.78`), with all controls derived as tonal steps of that single hue.

### 3.2 Hue-Tinted Neutrals & The "No Gray on Color" Law
- **Never place pure achromatic gray (`#888888`, `C = 0`) on a colored background!** Pure gray on a warm or cool surface looks muddy and dead.
- Derive muted text and borders using `color-mix(in oklch, var(--ink) 62%, var(--bg))` or by keeping the background's hue angle $H$ with reduced chroma ($C \approx 0.02–0.04$).
- **WCAG Contrast Floor**:
  - Body text & input placeholders: **`≥ 4.5:1`** (AA)
  - Large display headlines (`≥ 24px` or `≥ 19px bold`): **`≥ 3.0:1`**
  - Interactive control boundaries & focus rings: **`≥ 3.0:1`**

---

## 4. Optical Surface Physics, Concentric Radii & Native Browser Theming

### 4.1 The Concentric Nested Radius Formula
When an outer container has border-radius $R_{\text{outer}}$ and padding $G$ (where $G < 32\text{px}$), any inner card, image, or button sitting near the corner **MUST** use a reduced concentric radius:

$$R_{\text{inner}} = \max\left(2\text{px},\; R_{\text{outer}} - G\right)$$

- *Example*: Outer Bento card `border-radius: 20px` + `padding: 8px` $\Rightarrow$ Inner media frame MUST be `border-radius: 12px` (never `20px`, which creates pinched, swollen corner gaps!).

### 4.2 `box-shadow` Hairlines Over CSS `border`
For cards, avatars, and media frames, prefer `box-shadow: 0 0 0 1px rgba(...)` or `outline: 1px solid rgba(...); outline-offset: -1px` over `border: 1px solid`:
- Does not alter layout box dimensions;
- Blends seamlessly over semi-transparent surfaces and images;
- Pair with a dual-layer ambient shadow tinted with the surface hue:
  ```css
  box-shadow:
    0 0 0 1px color-mix(in oklch, var(--ink) 8%, transparent),
    0 2px 4px -1px color-mix(in oklch, var(--ink) 5%, transparent),
    0 12px 24px -6px color-mix(in oklch, var(--ink) 8%, transparent);
  ```

### 4.3 Mandatory Native Browser Surface Theming (Lowest-Cost High-Craft Signal)
Every production page MUST theme the browser's built-in interactive surfaces to match the active palette:
```css
::selection {
  background-color: color-mix(in oklch, var(--accent) 24%, transparent);
  color: var(--ink);
}
input, textarea {
  caret-color: var(--accent);
}
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
a {
  text-underline-offset: 0.22em;
  text-decoration-thickness: 1px;
}
```
