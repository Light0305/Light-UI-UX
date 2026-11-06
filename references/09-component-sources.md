# Component sources: BoardUI and LeiBox

Use these resources to solve the current interface task. The user's design, existing components and target framework remain the authority. A library is an implementation option, not a reason to add unrelated effects, rebuild the design system or install another skill.

## Choose by task

| Need | First search | Inspect before reuse |
| --- | --- | --- |
| Agent chat, prompt composer, stop control, history, thinking feedback | `component "chat thinking" --site boardui --framework react` | Transport contract, streaming/error states, server configuration, demo navigation |
| Editable spreadsheet, sortable tables, tree navigation | `component "grid table tree" --site boardui` | Controlled state, editing/selection semantics, pagination, overflow, keyboard access |
| Login, settings, notifications, application navigation | `component "settings auth notification sidebar" --site boardui` | Focus return, modal boundaries, providers and semantic theme tokens |
| Date/range selection, OTP, file upload, form controls | `component "date otp upload input" --site boardui` | React Aria semantics, validation and actual backend callbacks |
| Drag/resize, tactile navigation, animated galleries, shaders | `component "<specific gesture or use>" --site leibox` | Framework, renderer, input methods, performance and per-item source terms |
| Six-framework ASCII ocean background | `component --id leibox-ascii-sharks` | Local UI callbacks, reduced motion, pause/offscreen behavior, embedded notices |

Search by the user's task and concrete interaction, in Chinese or English. Return only relevant candidates, usually one to three; a search ranking is not a quality score. If the current component already solves the task, keep it. No suitable result means implement normally, rather than forcing a library into the page.

## Query and extract

Run tools relative to the skill's root, or use their absolute path while keeping the working directory in the target project. CLI-global `--json` precedes the subcommand.

```sh
python scripts/arsenal.py component "设置" --site boardui --framework react --mode full_source
python scripts/arsenal.py component "拖拽" --site leibox --framework vue
python scripts/arsenal.py --json component "chat" --site boardui
python scripts/arsenal.py --json component --id boardui-data-grid
python scripts/arsenal.py component --id boardui-data-grid --framework react --extract /target/staging
python scripts/arsenal.py component --id leibox-ascii-sharks --framework vue --extract /target/staging
python scripts/arsenal.py stats
```

The two imported libraries add **110 indexed entries** to the original 1,140:

- **BoardUI: 68 source entries** — 55 UI component/block entries and 13 foundations/utilities. This is the free source actually present in the inspected repository, not the separately sold Pro catalog.
- **LeiBox: 42 indexed interactions** — one explicitly MIT-attributed component with six complete framework packages; 41 reference entries with source/documentation/package URLs. Count the six packages as one component, not six separate designs.
- Complete arsenal: **1,250 entries**, including **945 with source** and **305 upstream references**. `stats` reports the actual database counts and each library's split.

`--framework` matches explicitly indexed framework metadata; legacy entries with unknown frameworks are not silently classified. `--mode full_source` requests bundled source; `--mode metadata_only` requests upstream references. Search results include mode, framework and source URL. The detailed JSON includes dependencies and provenance.

`--extract` writes `<destination>/<component-id>/`. BoardUI keeps original `components/`, `hooks/`, `utils/`, `styles/` and applicable `app/api/` paths. The source manifest is `_LIGHT_UI_SOURCE.json`. For the six-framework LeiBox bundle, use the selected framework subdirectory and its `_PACKAGE.json`; omitting `--framework` extracts all six. Existing identical files are reused; a differing file stops extraction before any writes. Choose another staging directory or merge intentionally after inspecting the target.

For a reference entry, extraction produces no source files. Read `source_metadata.detail_url`, the source statement, actual package dependencies and the component-specific terms. Where reuse is permitted and the user has requested implementation, retrieve only the selected framework package directly into the target project's staging area, validate its declared file hashes, and integrate the real entry. Do not turn an upstream-only reference into a redistributed skill bundle without a clear license. A successful download is not a successful render.

## BoardUI: source-owned product controls

The inspected snapshot uses React 19, Tailwind CSS 4 and React Aria. Each extracted entry contains its transitive local imports and three shared style files. Package versions are recorded from the inspected upstream `package.json`; install only dependencies missing from, and compatible with, the target project. Do not copy a generated manifest over the target `package.json`.

1. **Inspect the entry and its manifest.** Preserve the original `@/` path structure or change every related alias consistently. Keep client boundaries around interactive components. Some foundations are CSS or utilities, not standalone visual components.
2. **Merge theme and typography deliberately.** `styles/theme.css` defines semantic text/surface/border/icon/chart roles and their light/dark values. `styles/typography.css` defines composite text utilities. `utils/cx.ts` configures tailwind-merge for those utilities. Use them as a coherent set, or map them to the existing product's equivalent tokens; plain class merging can silently discard a color or composite type class. Merge needed animations and resets from `styles/globals.css`, rather than importing global resets twice or overwriting the current styles.
3. **Keep React Aria behavior.** Do not mix in Radix `asChild` or Base UI `render` assumptions. Preserve labels, selected/disabled state, keyboard movement, focus rings, menu dismissal and focus return. Remix icons are often component references passed through props, not pre-rendered elements.
4. **Respect language and direction.** Where the component uses `DirectionProvider`, set the actual locale. Match full-app `lang`/`dir`, pass direction to custom portals, prefer logical start/end spacing, and mirror navigation glyphs where appropriate. Do not mirror chart coordinates, code, URLs or measured canvas geometry. For Chinese, apply the skill's CJK line-height/tracking rules when adapting upstream type tokens.
5. **Replace demo assumptions.** Source media under upstream `public/` is not bundled. Supply appropriately licensed product media, names and navigation. BoardUI marks and starter upsells are demonstration material, not the target product's brand. The agent chat includes a sample app shell; adapt it to real target routes instead of retaining links to absent pages.

### Agentic UI behavior to carry into the product

- Keep `idle`, `submitting`, `streaming`, `stopping`, `complete`, `interrupted` and `error` distinct. A thinking animation means work is pending, not that a tool succeeded.
- Keep the user's draft and attachments through retryable failures. Stop must cancel or clearly stop the actual stream, not just stop an indicator. Use existing backend contracts for retry, permissions and model selection.
- Treat the free chat transport and its server route as a reference contract. A model/permission selector is not backend authorization. Keep provider secrets server-side; do not copy local credentials into source or ask for them in chat.
- History selection, long streams, file rejection, empty states and narrow-screen composer behavior need real interaction checks. Preserve keyboard navigation and avoid announcing every streamed token through a noisy live region.

When copying a useful pattern such as a subtle scroll-edge fade, retain readable content, a stationary non-interactive overlay and an unobstructed hit area. Verify reset at scrollTop zero, both themes, and normal browser zoom. Such details are optional product decisions, not new universal design requirements.

## LeiBox: interaction discovery and native lifecycles

The indexed catalog supports React, Vue, Svelte, Solid, Preact and Vanilla where listed. The six-framework label describes available wrappers, not guaranteed native rendering or zero dependencies: some components retain a shared DOM/Canvas/WebGL engine, and some non-React packages still depend on React. Inspect the actual selected package.

For the bundled ASCII Sharks packages, preserve engine/runtime imports, embedded MIT/OFL/icon notices, usage and cleanup. Mount once, update options without recreating the engine unnecessarily, and destroy it when the page or component unmounts. Its optional composer is local UI; voice/model/backend capabilities require the target application's callbacks.

For any expressive interaction, inspect pointer, keyboard and touch behavior; resize and device pixel ratio handling; animation-frame cancellation; offscreen/document-hidden pause; reduced motion; and disposal of observers/listeners/rendering resources. Choose a static or simpler rendering when the target device cannot support the effect. Verify the real behavior before claiming it works.

The root LeiBox license retains MIT + Commons Clause restrictions inherited from Canvas UI, while individual items have different source statements. The catalog's `canRedistributeSource` flag does not replace those terms. This import bundles only the one explicitly MIT-attributed component and retains source-specific information for the rest. Do not bring reference videos, album art, logos or proprietary fonts into generated output by inference from their availability on the demo site.

## Maintaining the import

Inspected on **2026-11-06**:

- BoardUI: `ec5c5eb3e29c2441be63b9422cd54f411ef23466` — source files and dependency versions pinned to the repository snapshot.
- LeiBox catalog: `42a55345cc9f53e6ab926a62527e0bc0ad9db7bc` — package URLs are generated by the live site. The six downloaded ASCII Sharks packages have separate package and embedded per-file SHA-256 hashes; do not imply the catalog commit pins their generation.
- ASCII Sharks simulation: upstream attribution identifies `stackedlol/ascii-sharks` at `a0074c16a106f0abc665fe9712ca445f8f98ad8e`.

`scripts/import_components.py` is a maintainer tool; routine design tasks only need `arsenal.py`. It takes local inspected snapshots, executes no upstream code, validates local dependency closure and LeiBox file hashes, and updates only the selected libraries in a single database transaction. Repeating the same import does not add duplicate entries or duplicate FTS rows. Keep the full license statements under `licenses/components/` and source notices in extracted files.

```sh
python scripts/import_components.py --boardui /snapshots/boardui --leibox /snapshots/leibox
# When rebuilding the entire database from the original raw resources:
python scripts/build_arsenal.py --boardui /snapshots/boardui --leibox /snapshots/leibox
```

For LeiBox, a snapshot contains `public/ai/catalog.json` and `public/ai/packages/ascii-sharks/{framework}.json` for each of the six frameworks. Read the current component terms before refreshing packages. For a new repository revision, inspect changes and update the recorded revision constants before importing; the importer does not claim to verify an arbitrary checkout's commit. Rebuilding without the snapshot arguments produces the base dataset only. Generate notices from actual per-library database counts after a maintainer import.
