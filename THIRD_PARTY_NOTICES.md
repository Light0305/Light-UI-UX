# Third-party notices

Original Light-UI-UX code and documentation are licensed under MIT. Third-party resources retain their own copyright and license terms; inclusion in the local database does not relicense them.

## Components

The component index contains 1,250 entries: 945 with bundled source and 305 with metadata and an upstream link only. Bundled components retain license files inside their source maps where available. Additional full license texts are in [licenses/components](licenses/components).

| Source | Bundled entries | License text |
| --- | ---: | --- |
| BundUI | 213 | [MIT](licenses/components/bundui.txt) |
| Animation Micro-Interactions | 176 | [MIT](licenses/components/amicro.txt) |
| Animata | 154 | [MIT](licenses/components/animata.txt) |
| Cult UI | 137 | [MIT](licenses/components/cult-ui.txt) |
| GSAP CodePen examples | 61 | [Example license](licenses/components/gsap.txt) |
| Bencho | 49 | [MIT](licenses/components/bencho.txt) |
| Open UI libraries | 49 | [MIT and dependency notices](licenses/components/libraries.txt) |
| Beautiful UI | 21 | [MIT](licenses/components/beautifului.txt) |
| Orb / shader components | 13 | [MIT](licenses/components/orb.txt) |
| Public CodePen examples | 2 | [Example license](licenses/components/codepen.txt) |
| Liquid Glass | 1 | [MIT](licenses/components/liquid-glass.txt) |

**BoardUI (68 source entries):** React components and foundations from [BoardUI/boardui](https://github.com/BoardUI/boardui), revision `ec5c5eb3e29c2441be63b9422cd54f411ef23466`, under [MIT](licenses/components/boardui.txt). Each extraction includes its transitive local imports, shared CSS, the full upstream MIT notice and a source/dependency manifest. Only source present in the public repository is bundled; Pro source and public demo media are not included.

**LeiBox (42 indexed entries; 1 with source):** catalog revision `42a55345cc9f53e6ab926a62527e0bc0ad9db7bc` from [leishifu666/LeiBox](https://github.com/leishifu666/LeiBox). The explicitly MIT-attributed ASCII Sharks component includes six framework packages, embedded font/icon notices and per-file SHA-256 verification. Its original simulation credits drewdi / [stackedlol/ascii-sharks](https://github.com/stackedlol/ascii-sharks), revision `a0074c16a106f0abc665fe9712ca445f8f98ad8e`. Live package hashes are recorded separately from the pinned catalog. Other entries retain search metadata and upstream package/documentation URLs only. LeiBox's root MIT + Commons Clause and per-item provenance do not establish a blanket redistribution license; the catalog's canRedistributeSource flag alone is not treated as one. Full statements: [root license](licenses/components/leibox-LICENSE.md), [source statement](licenses/components/leibox-COPYRIGHT.md).

Reference-only entries do not bundle component source:

- **React Bits (216):** [upstream terms](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md) restrict redistribution of the components themselves. The index retains names, search metadata, and official source URLs.
- **RareUI (25):** indexed by metadata and upstream URL; component redistribution is not included.
- **StringTune tutorials (23):** the package's MIT license does not establish a separate license for downloaded tutorial pages, so those pages are linked rather than bundled.

The database excludes AGPL/GPL components, GSAP Standard License example bundles, proprietary Unicorn Studio embeds, and Nucleo UI SVGs. Code examples can still require separately installed libraries, fonts, or media under their own terms. A CodePen example's license does not relicense GSAP itself.

## Icons

The database contains 17,130 logical icon entries and 33,253 SVG variants. Full license texts:

| Library | License |
| --- | --- |
| Tabler Icons — Paweł Kuna | [MIT](licenses/icons/tabler.txt) |
| Hugeicons Free | [MIT](licenses/icons/hugeicons.txt) |
| Phosphor Icons | [MIT](licenses/icons/phosphor.txt) |
| Bootstrap Icons — The Bootstrap Authors | [MIT](licenses/icons/bootstrap.txt) |
| Iconoir — Luca Burgio | [MIT](licenses/icons/iconoir.txt) |
| Heroicons — Tailwind Labs | [MIT](licenses/icons/heroicons.txt) |
| Solar — 480 Design | [CC BY 4.0](licenses/icons/solar.txt) |

Solar attribution: [480 Design](https://www.figma.com/@480design), [original collection](https://www.figma.com/community/file/1166831539721848736), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The archived SVGs normalize IDs and make ink colors configurable; vector geometry is retained. Preserve this attribution when redistributing Solar icons.

## Design datasets and references

| Source | Included material | License |
| --- | --- | --- |
| Impeccable | Design guidance | [Apache-2.0](licenses/methods/impeccable-LICENSE), [notice](licenses/methods/impeccable-NOTICE.md) |
| Open-Design | Shader templates, brand systems, motion and layout references | [Apache-2.0](licenses/methods/open-design-LICENSE) |
| Taste-Skill | Blueprints, palettes, font pairings, motion recipes | [MIT](licenses/methods/taste-skill-LICENSE) |
| UI/UX Pro Max | Industry mappings and stack guidance | [MIT](licenses/methods/ui-ux-pro-max-LICENSE) |
| GSAP Skills | Motion guidance | [MIT](licenses/methods/gsap-skills-LICENSE) |
| AI Design Skills | Design workflow references | [MIT](licenses/methods/ai-design-skills-LICENSE) |
| IP-as-Logo | Brand design methodology | [MIT](licenses/methods/ip-as-logo-LICENSE) |

Additional methodology references include Interface Details, Emil Kowalski's design engineering guidance, Apple fluid interfaces, mobile app design guidance, and shadcn/ui. Website benchmark records retain source URLs and structured measurements such as colors, type scales, spacing, and radii; these references do not imply affiliation or endorsement.

## Showcase

RIFT, NOCT, Meltday, and Veylo are fictional demonstration projects built with Light-UI-UX. Screenshots and original briefs are in [docs](docs); screenshots are examples of output rather than part of the reusable component library. The QR code assets in the README are supplied by the project author and reused from [Light-skills](https://github.com/Light0305/Light-skills).
