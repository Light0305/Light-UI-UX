# 04 — Fluid Spring Physics, GSAP Scrollytelling, WebGL Stages & Cross-Stack 1:1 Transpilation

This manual governs **micro-interaction physics, scroll-driven narratives, staging containers, WebGL shaders, and cross-stack component transpilation**.

---

## 1. Fluid Spring Physics & Micro-Interaction Discipline

### 1.1 Emil Kowalski's Interaction Frequency Law
- **High-Frequency Workbench Actions (`Operate` mode: `Cmd+K` palette, keyboard row switch, context menu)**: Keep transitions ultra-fast (`100–150ms`) or **instant (`0ms`)**. Never make a daily power user wait for a 500ms entrance animation.
- **Adjacent Tooltip Instant Switch**: The first tooltip waits `250ms` hover delay before opening (`150ms` transition); once any tooltip in a group is open, hovering an adjacent trigger MUST switch at **`0ms` duration (`[data-instant] { transition-duration: 0ms; }`)**.
- **Never Animate From `scale(0)`**: Real objects do not appear from zero volume. All popovers, modals, and dropdowns MUST start from **`scale(0.95)` (never `< 0.90`) + `opacity: 0`** anchored to the trigger's coordinate (`transform-origin: var(--transform-origin)`).
- **Instant Press Feedback (`pointerdown`)**: Apply `transform: scale(0.97)` (`150ms cubic-bezier(0.23, 1, 0.32, 1)`) on `:active` / `pointerdown` — never wait for `click` release.
- **Blur Bridge for Shape Morphing**: When morphing between two distinct shapes/icons (e.g., `"Copy"` button $\rightarrow$ `"Checkmark"`, or pill button $\rightarrow$ expanded input bar), cross-fade with a transient **`filter: blur(2px)`** (never exceed `20px` blur on Safari GPU).
- **Fitts's Law Hit Area & Safe Triangle**: Expand small button hit areas with `::before { content: ""; position: absolute; inset: -6px; }`. For multi-level hover menus, construct a dynamic **SVG Safe Triangle** from cursor history to submenu corners so diagonal mouse movement never closes the submenu prematurely.

### 1.2 The 6 Business Spring Presets & Apple Fluid Math

| Spring Preset | Stiffness / Damping | Apple $(\zeta, T)$ Equivalent | Primary UI Use Cases |
| :--- | :---: | :---: | :--- |
| **1. Snap (`咔嗒`)** | `380 / 14` | $\zeta = 0.78,\; T = 0.25\text{s}$ | Toggle switches, checkboxes, magnetic tab indicators |
| **2. Glide (`滑入`)** | `280 / 24` | $\zeta = 1.00,\; T = 0.35\text{s}$ | Drawers, sheets, modals, side panels (critically damped, zero wobble) |
| **3. Flow (`流淌`)** | `180 / 34` | $\zeta = 1.00,\; T = 0.45\text{s}$ | Horizontal accordions, height expansion, layout reflow |
| **4. Stamp (`砸落`)** | `450 / 9` | $\zeta = 0.55,\; T = 0.22\text{s}$ | Badge drop-in, error shake, game milestone impact |
| **5. Bounce (`回弹`)** | `300 / 10` | $\zeta = 0.65,\; T = 0.35\text{s}$ | Drag release snap-back, floating PiP bubble |
| **6. Drift (`漂浮`)** | `100 / 25` | $\zeta = 1.00,\; T = 0.80\text{s}$ | Ambient background aura, parallax counter-drift (`≤ 5%–10%`) |

#### Core Mathematical Formulas for Gesture & Spring Engines
1. **Velocity Dismissal Threshold (Drawer / Sheet Swipe)**:
   $$\text{velocity} = \frac{|\Delta x|}{\Delta t} > 0.11\text{ px/ms}$$
   Dismiss the sheet immediately if release velocity exceeds `0.11 px/ms`, even if drag distance is `< 50%`.
2. **Apple Momentum Projection (Predicting Snap Anchor on Release)**:
   $$\text{project}(v, d = 0.998) = \frac{(v / 1000) \cdot d}{1 - d}, \quad x_{\text{target}} = \arg\min_{a \in \text{Anchors}} \left|x_{\text{current}} + \text{project}(v_{\text{release}}) - a\right|$$
3. **Apple Rubber-Banding Formula (Overscroll Resistance $c = 0.55$)**:
   $$\text{rubberband}(\text{overshoot}, D, c = 0.55) = \frac{\text{overshoot} \cdot D \cdot c}{D + c \cdot |\text{overshoot}|}$$

---

## 2. GSAP Scrollytelling & The Dual Narrative Law

Query `python scripts/arsenal.py motion "<keyword>"` to pull from 660 motion prompts, `motion-lab` snippets, and GSAP recipes.

### 2.1 The Persuade Scroll Narrative Law
Every `Persuade` or `Experience` page MUST implement two distinct scroll behaviors (never apply to `Operate` workbenches):
- **(A) Content-Specific One-Shot Section Entrances (`once: true`)**: Duration `≤ 800ms`, stagger `40–80ms`. Never copy-paste the exact same `translateY(20px)` fade-up on every section; match the motion to the section's geometry.
- **(B) At Least `1` Continuous Scroll-Driven Narrative (`scrub: 0.6`)**:
  1. *Hero Depth Push*: Pin `100–180vh` on desktop (`80–110vh` mobile); scale or advance the hero stage `≥ 15%` across `≥ 2` depth layers (**never scale or parallax body paragraphs or CTA buttons!**).
  2. *Giant Wordmark Docks Into Topbar*: Oversized hero brand title continuously shrinks into the fixed top navigation bar over `60–100vh`.
  3. *Pinned Exploded Hardware / Architecture Reveal*: Sticky left/center stage unpeels layers as right-hand specification callouts scroll past.

### 2.2 Three Non-Negotiable GSAP Engineering Guardrails
1. **React Lifecycle Safety**: Always use `useGSAP(() => { ... }, { scope: containerRef })` from `@gsap/react`, and wrap any event handler (`onClick`, `onPointerMove`) that creates a tween in `contextSafe(...)`.
2. **ScrollTrigger Pinning & Nesting**:
   - **NEVER put `scrollTrigger: {...}` inside a child tween of a `gsap.timeline()`** — attach `scrollTrigger` strictly to the top-level `gsap.timeline({ scrollTrigger: ... })`.
   - **NEVER animate the exact DOM element being pinned (`pin: true`)** — wrap it in a `.pin-wrapper` and animate the inner child!
3. **High-Frequency Pointer Tracking**: Never call `gsap.to()` inside `mousemove`/`pointermove`; always pre-allocate `const xTo = gsap.quickTo(el, "x", { duration: 0.35, ease: "power3" })`.

---

## 3. Breaking the Grid: 4 Staging Containers & Single-Component Craft

When presenting **4–7 parallel items** that each carry rich visuals or previews, **forbid static 3×2 card grids**. Use one of the **4 Staging Containers**:

1. **Horizontal Accordion**: Item 1 expanded by default (`55%–65%` width); collapsed strips show *only* index number + vertical title (`writing-mode: vertical-rl`) — **never cram truncated paragraphs into collapsed strips**. Add `70ms` hover debounce; fade in body copy only after width reaches `> 60%`.
2. **Curved Depth Carousel**: Center card faces camera at `scale(1)`; flanking cards rotate along Y-axis (`rotateY(±18deg)`) with reduced contrast.
3. **Stacked Tactile Deck**: Active card in front; 2–3 cards peek from behind with offset top/right edges; swiping springs the front card away and promotes the next.
4. **Orbital Lens**: Items travel along an arc/ring and expand details when passing the focal lens zone.
- **In-Card Micro-Drawer**: For secondary specs inside a card, slide up an `absolute`-positioned half-height drawer inside the card bottom edge using `transform: translateY(...)` only (**never expand the card's outer height or trigger page reflow!**).

### Single Component Craft Rules
- **Single-Ruler Law**: Never render both a read-only progress bar and a separate range slider for the same quantity — merge them into one interactive ruler.
- **Number-Deduplication Law**: Never display the exact same number in the card header, the gauge center, and the footer caption simultaneously.
- **16 Standalone WebGL2 / Three.js Shader Stages**: Run `python scripts/arsenal.py shader` to list and `--extract` any of the 16 zero-dependency single-file shaders (`webgl-liquid-metal`, `webgl-aurora-veil`, `webgl-caustic-pool`, `webgl-holographic-foil`, `webgl-raymarched-hero`, etc.). Always pause `requestAnimationFrame` via `IntersectionObserver` when scrolled off-screen!

---

## 4. Cross-Stack 1:1 Source Transpilation Protocol

When extracting a component from `light-arsenal.db` (`python scripts/arsenal.py component --id <id> --extract <dir>`) and adapting it to the user's target stack, enforce these stack-specific contracts:

For BoardUI or LeiBox resources, first read [component sources](09-component-sources.md). Use an existing native framework package before writing a port. BoardUI is a separate **React Aria** component family: preserve its providers, keyboard behavior, focus handling, `cx()` utility and semantic tokens; do not substitute Base UI or Radix trigger props. Map tokens into the target design rather than applying the upstream brand or agent rules globally. LeiBox wrappers can share an engine or retain React dependencies, so inspect the selected package's manifest.

### 4.1 React 19 / Next.js App Router / Tailwind v4 / `shadcn`
Run `python scripts/arsenal.py stack shadcn` and `python scripts/arsenal.py stack nextjs`.
1. **Base UI (`@base-ui/react`) vs. Radix UI (`radix-ui`) Strict Separation**:
   - Inspect `components.json` or `package.json`:
   - If **Base UI**: Use `render={<Link href="..." />}` + `nativeButton={false}` on triggers; pass `items={...}` to `<Select>`; use boolean `multiple` on `<Accordion>`/`<ToggleGroup>` (**never mix Radix `asChild` or `type="single"`!**).
   - If **Radix UI**: Use `asChild` on `<Button asChild>` / `<TooltipTrigger asChild>`.
2. **Tailwind & `shadcn` Styling Rules**:
   - Always use `flex flex-col gap-*` instead of `space-y-*`; use `size-*` instead of `w-* h-*`.
   - Inside `<Button>`, `<Badge>`, `<DropdownMenuItem>`, place `data-icon="inline-start"` or `"inline-end"` on icons and **never hardcode `size-4` / `w-4 h-4`**.
   - Define custom typography classes with `@utility type-display { ... }` instead of `--text-*` variables so `tailwind-merge` (`cn()`) does not wipe out `text-primary` colors!
   - Keep Next.js pages as **Server Components by default**; isolate `'use client'` strictly to interactive leaf components.

### 4.2 Vue 3 / Nuxt 3 (`<script setup lang="ts">`)
- Map React `useRef` $\rightarrow$ `const rootRef = ref<HTMLElement | null>(null)`.
- Map `useGSAP` / `useEffect` $\rightarrow$ `let ctx: gsap.Context; onMounted(() => { ctx = gsap.context(() => {...}, rootRef.value!); }); onScopeDispose(() => ctx?.revert());`.
- **Never wrap static copy or static configuration arrays in `ref()` or `reactive()`**.

### 4.3 React Native / Expo (The 6 Silent Crash Traps)
Run `python scripts/arsenal.py stack react-native`.
1. **Trap 1 — Flex Direction Inversion**: Web `display: flex` defaults to `row`, whereas React Native `<View>` defaults to **`flexDirection: 'column'`**! Explicitly add `flex-row` on every horizontal row when transpiling from HTML/React.
2. **Trap 2 — Bare Text Nodes Crash Production**: Every string, number, conditional branch (`count > 0 && <Text>...</Text>`), or space MUST be wrapped inside `<Text>`.
3. **Trap 3 — Safe Area Double-Padding**: Import `SafeAreaView` / `useSafeAreaInsets` strictly from `react-native-safe-area-context` (never from core `react-native`). **Inset each edge once**: if a screen has a native Stack Header, only apply `edges={['bottom']}`.
4. **Trap 4 — Navigation Chrome Deduplication**: Never copy HTML prototype topbars or bottom tab bars into individual screen components; hoist them once into Expo Router `app/_layout.tsx` (`<Stack>` / `<Tabs>`).
5. **Trap 5 — NativeWind v4 vs. v5 Color Compatibility**: NativeWind v4 (`react-native-css-interop`) **silently drops `oklch()` colors** and defaults `1rem = 14px`! For NativeWind v4, convert `oklch()` tokens to Hex/`rgb()` in `global.css` and set `inlineRem: 16` in `metro.config.js`. NativeWind v5 and Uniwind support `oklch()` natively.
6. **Trap 6 — GPU Thread Animations**: Transpile Framer Motion / CSS springs to `react-native-reanimated` (`useSharedValue`, `useAnimatedStyle`, `withSpring({ stiffness, damping })`) + `Pressable` `({ pressed })` scale feedback.

### 4.4 iOS SwiftUI & Flutter
- **SwiftUI**: Map spring presets to `.animation(.spring(response: 0.35, dampingFraction: 0.82), value: state)`; enforce `44×44pt` minimum hit target (`.contentShape(Rectangle())`), Dynamic Type, and `.safeAreaInset`.
- **Flutter**: Map springs to `SpringSimulation(SpringDescription(mass: 1, stiffness: 280, damping: 24), ...)`, use `CustomScrollView` + `SliverAppBar` for scroll narratives, and `RepaintBoundary` around custom shaders/painters.
