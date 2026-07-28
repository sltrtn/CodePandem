# Unified Design System

> Shared design language across Meluko, ContextIQ, and CodePandem.
> Each project keeps its own accent color but shares typography, spacing, radius, animation, and component patterns.

---

## Typography

**Font: Outfit** — Clean geometric sans-serif, 9 weights.

| Role | Weight | Usage |
|---|---|---|
| Display | Black (900) | Splash screens, hero text |
| Headline | ExtraBold (800) | Screen titles, section headers |
| Title | SemiBold (600) | Card titles, modal headers |
| Body | Normal (400) | Paragraphs, descriptions, labels |
| Label | Medium (500) | Buttons, chips, badges |
| Mono | JetBrains Mono | Code editors, timestamps only |

### Type Scale

| Token | Size | Line Height | Letter Spacing | Weight |
|---|---|---|---|---|
| `display-lg` | 57px/sp | 64px | -0.25px | Black |
| `display-md` | 45px | 52px | 0 | Black |
| `display-sm` | 36px | 44px | 0 | Black |
| `headline-lg` | 32px | 40px | 0 | ExtraBold |
| `headline-md` | 28px | 36px | 0 | ExtraBold |
| `headline-sm` | 24px | 32px | 0 | ExtraBold |
| `title-lg` | 22px | 28px | 0 | SemiBold |
| `title-md` | 16px | 24px | 0.15px | SemiBold |
| `title-sm` | 14px | 20px | 0.1px | SemiBold |
| `body-lg` | 16px | 24px | 0.5px | Normal |
| `body-md` | 14px | 20px | 0.25px | Normal |
| `body-sm` | 12px | 16px | 0.4px | Normal |
| `label-lg` | 14px | 20px | 0.1px | Medium |
| `label-md` | 12px | 16px | 0.5px | Medium |
| `label-sm` | 11px | 16px | 0.5px | Medium |

### Uppercase Headers

Section labels and chip text use uppercase with `letter-spacing: 0.1em` across all projects.

---

## Color System

Each project defines its own accent but shares all neutral tokens.

### Shared Neutrals (Dark Mode)

| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#0F0F12` | Page/screen background |
| `--surface` | `#18181C` | Card/panel surface |
| `--surface-raised` | `#222226` | Elevated surface, hover states |
| `--border` | `#2A2A30` | Borders, dividers, outlines |
| `--text` | `#EDE0DA` | Primary text (warm off-white) |
| `--text-dim` | `#8A8080` | Secondary/muted text |
| `--text-inverse` | `#0F0F12` | Text on accent-colored surfaces |

### Shared Neutrals (Light Mode)

| Token | Hex | Usage |
|---|---|---|
| `--bg` | `#FFFCF8` | Page/screen background |
| `--surface` | `#FAEDE6` | Card/panel surface |
| `--surface-raised` | `#F4E7DF` | Elevated surface, hover states |
| `--border` | `#D8C2BC` | Borders, dividers, outlines |
| `--text` | `#201B18` | Primary text |
| `--text-dim` | `#85736D` | Secondary/muted text |
| `--text-inverse` | `#FFFCF8` | Text on accent-colored surfaces |

### Semantic Colors (shared)

| Token | Hex | Usage |
|---|---|---|
| `--success` | `#4ade80` | Correct, won, positive |
| `--warning` | `#facc15` | Caution, partial, time low |
| `--error` | `#f87171` | Wrong, lost, danger |

### Project Accent Colors

| Project | Accent | Hex | On-Accent | Mono |
|---|---|---|---|---|
| Meluko | Sunrise Amber | `#FF8C00` | `#FFFFFF` | (none specified) |
| ContextIQ | Scholarly Navy | `#002855` | `#FFFFFF` | (none specified) |
| CodePandem | Battle Indigo | `#6c63ff` | `#FFFFFF` | JetBrains Mono |

---

## Spacing Scale

Base unit: **4px**. All spacing is a multiple of 4.

| Token | Value | Usage |
|---|---|---|
| `xs` | 4px | Tight gaps, icon padding |
| `sm` | 8px | Inline gaps, small padding |
| `md` | 12px | Card inner padding (compact) |
| `lg` | 16px | Card padding, input padding |
| `xl` | 20px | Section gaps |
| `2xl` | 24px | Large section gaps |
| `3xl` | 32px | Screen horizontal padding |
| `4xl` | 40px | Major vertical gaps |
| `5xl` | 48px | Hero spacing |

---

## Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 8px / 8dp | Small elements (chips, badges) |
| `radius-md` | 12px / 12dp | Cards, inputs |
| `radius-lg` | 16px / 16dp | Large cards, modals |
| `radius-xl` | 20px / 20dp | Buttons, bottom sheets |
| `radius-full` | 9999px | Pill shapes, avatars |

---

## Component Patterns

### Cards
- **Elevation:** 0 (flat, no shadow)
- **Border:** 1px solid `--border`
- **Radius:** `radius-md` (12px) to `radius-lg` (16px)
- **Padding:** `lg` (16px) to `xl` (20px)
- **Background:** `--surface`

### Buttons
- **Height:** 48px (standard) to 56px (prominent)
- **Radius:** `radius-xl` (20px)
- **Font:** Outfit Medium (500), `label-lg` (14px)
- **Padding:** 0 24px
- **Fill:** Accent color background, white text
- **Hover:** 8% lighter or `--surface-raised` for outline variant
- **Disabled:** 40% opacity
- **Transition:** background 150ms ease

### Inputs
- **Radius:** `radius-md` (12px)
- **Border:** 1px solid `--border`, accent on focus
- **Padding:** 12px 16px
- **Font:** Outfit Normal (400), `body-md` (14px)
- **Background:** `--bg`

### Bottom Sheets / Modals
- **Top radius:** `radius-xl` (20px)
- **Background:** `--surface`
- **No drag handle** (Meluko/ContextIQ convention)

---

## Animation Language

### Android (Compose)
- **Spring-based press** on all interactive elements
- Default: scale to 0.94, `DampingRatioNoBouncy`, `StiffnessMedium`
- Chips: scale to 0.92, `DampingRatioLowBouncy`
- FABs: scale to 0.90, `DampingRatioMediumBouncy`, lower stiffness
- Implementation: `Animatable` + `graphicsLayer` (avoid recomposition)

### Web (CSS)
- **Hover transitions:** 150ms ease for background/color changes
- **Scale on press:** `transform: scale(0.97)` with `transition: transform 100ms ease`
- **Focus rings:** 2px accent outline, 2px offset
- **Loading states:** CSS spinner (40px, accent border-top, 0.8s linear infinite)
- **Low-time pulse:** opacity 1 -> 0.5, 0.5s ease-in-out infinite alternate

---

## Dark Mode Approach

- **Default:** Dark mode
- **Background:** `#0F0F12` (shared near-black, NOT true black)
- **Surface hierarchy:** bg -> surface -> surface-raised (3-tier)
- **Text:** Warm off-white `#EDE0DA` (not pure white)
- **Borders:** Subtle `#2A2A30` (not harsh white/gray)
- **Light mode:** Warm cream tones (see light neutrals above)

---

## Logo Treatment

All projects use their name as a wordmark in **Outfit Black** with `letter-spacing: 0.05em`. No icon/logo mark — the typography IS the brand.

---

## What Does NOT Change Per Project

| Stays Shared | Changes Per Project |
|---|---|
| Outfit font | Accent color |
| Type scale | App-specific components |
| Spacing scale | Content and copy |
| Border radius tokens | Illustrations/icons |
| Neutral color tokens | — |
| Semantic colors | — |
| Component patterns | — |
| Animation language | — |
| Dark mode approach | — |
| Uppercase header convention | — |
