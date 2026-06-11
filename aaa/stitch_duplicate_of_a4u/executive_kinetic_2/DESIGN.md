---
name: Executive Kinetic
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#464555'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#565e74'
  on-secondary: '#ffffff'
  secondary-container: '#dae2fd'
  on-secondary-container: '#5c647a'
  tertiary: '#005338'
  on-tertiary: '#ffffff'
  tertiary-container: '#006e4b'
  on-tertiary-container: '#67f4b7'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#dae2fd'
  secondary-fixed-dim: '#bec6e0'
  on-secondary-fixed: '#131b2e'
  on-secondary-fixed-variant: '#3f465c'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
---

## Brand & Style

The design system is engineered for high-performance enterprise environments where clarity, speed, and authority are paramount. It targets executive leadership and power users who require data-dense interfaces that remain legible and aesthetically sophisticated.

The aesthetic follows a **Corporate / Modern** direction. It prioritizes a systematic approach to hierarchy, utilizing a restrained but purposeful use of color to drive action. The "Kinetic" aspect of the brand is expressed through subtle micro-interactions and a layout that feels responsive and agile, rather than static and heavy. The goal is to evoke a sense of controlled momentum and institutional reliability.

## Colors

The palette is anchored by a deep Indigo primary, signaling intelligence and stability. 

- **Primary (#4f46e5):** Used for primary actions, active states, and brand-critical signifiers.
- **Secondary (#0f172a):** A deep slate used for high-contrast text and navigation backgrounds to provide a grounded, executive feel.
- **Tertiary (#10b981):** A vibrant emerald reserved for success states, positive trends, and "go" signals.
- **Neutral (#64748b):** A balanced gray-blue used for secondary text, borders, and UI scaffolding to maintain a calm, professional atmosphere.

The default mode is **Light**, utilizing off-white surfaces (`#f8fafc`) to reduce eye strain during long working sessions while maintaining a crisp, paper-like contrast.

## Typography

This design system exclusively utilizes **Inter** to leverage its exceptional legibility and systematic weight distribution. 

The scale is designed for high-density information environments. Display and Headline levels use tighter letter-spacing and heavier weights to command attention, while body text maintains generous line-heights to facilitate rapid scanning of complex data. 

For mobile devices, `display-lg` scales down to ensure headers do not overwhelm the viewport. Label styles are set in medium-to-bold weights with slight tracking (letter-spacing) to ensure small-caps or all-caps metadata remains accessible.

## Layout & Spacing

The layout is built on a **12-column fluid grid** for desktop, transitioning to a 4-column grid for mobile devices. 

A strictly enforced **8px linear scale** governs all spacing decisions. This ensures mathematical harmony across the UI. 
- **Desktop:** 32px outer margins with 24px gutters.
- **Tablet:** 24px outer margins with 16px gutters.
- **Mobile:** 16px outer margins with 16px gutters.

Components should align to the 8px grid. Use `md (16px)` for standard padding within cards and containers, and `xs (4px)` or `sm (8px)` for internal element grouping (e.g., icon-to-text spacing).

## Elevation & Depth

Hierarchy is established through **Tonal Layers** and **Ambient Shadows**. This design system avoids heavy gradients, favoring a clean "stacking" metaphor.

1.  **Level 0 (Base):** The primary background surface (`#f8fafc`).
2.  **Level 1 (Card/Surface):** White surfaces (`#ffffff`) with a subtle 1px border in a neutral-light tone.
3.  **Level 2 (Interactive/Floating):** Used for menus and dropdowns. These elements feature a soft, diffused ambient shadow (Color: `Primary-Dark`, Opacity: 8%, Blur: 12px) to suggest height without creating visual clutter.

This approach ensures that the "Executive" feel remains light and modern, avoiding the dated look of heavy drop shadows.

## Shapes

The design system employs a **Rounded (8px)** shape language. This specific radius (0.5rem) strikes a balance between the friendliness of a consumer app and the precision of an enterprise tool.

- **Standard Elements:** Buttons, Input fields, and small cards use the base 8px (`rounded-md`).
- **Large Containers:** Content sections and large modals use 16px (`rounded-lg`).
- **Data Indicators:** Chips and status tags may use the pill-shape for maximum distinction from square-format data cells.

## Components

### Buttons
- **Primary:** Solid Indigo (`#4f46e5`) with white text. High contrast, 8px radius.
- **Secondary:** Tonal slate background or outlined. Used for auxiliary actions.
- **Ghost:** No background, primary-colored text. Used for tertiary actions in toolbars.

### Input Fields
Inputs use a white background with a 1px border (`neutral-300`). On focus, the border transitions to Primary Indigo with a subtle 2px outer glow (halo) of the same color at 20% opacity.

### Cards
Cards are the primary container for data. They feature a white background, 8px radius, and a 1px neutral border. No shadow is applied unless the card is "Hoverable" or "Draggable."

### Chips & Badges
Small, low-profile indicators used for status or filtering. Status badges (Success, Warning, Error) use a light background tint of their respective color with high-contrast text for accessibility.

### Lists & Tables
Data density is high. Row heights are standardized to 48px for standard lists and 40px for "compact" views. Alternating row stripes (zebra striping) are used only in complex data tables to assist horizontal tracking.