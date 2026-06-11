---
name: Executive Kinetic
colors:
  surface: '#f9f9ff'
  surface-dim: '#cfdaf2'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8ff'
  surface-container-highest: '#d8e3fb'
  on-surface: '#111c2d'
  on-surface-variant: '#464555'
  inverse-surface: '#263143'
  inverse-on-surface: '#ecf1ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#004598'
  on-tertiary: '#ffffff'
  tertiary-container: '#005cc6'
  on-tertiary-container: '#cedbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#f9f9ff'
  on-background: '#111c2d'
  surface-variant: '#d8e3fb'
  surface-gray: '#F8FAFC'
  border-subtle: '#E2E8F0'
  success-mint: '#F0FDFA'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
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
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
  max-width: 1280px
---

## Brand & Style
The design system is built for a high-stakes professional environment where efficiency and clarity are paramount. The brand personality is **trustworthy, efficient, and sophisticated**, designed to appeal to both ambitious job seekers and discerning recruiters.

The design style follows **Modern Minimalism** with a focus on data-driven density. It prioritizes high readability and organizational structure to handle complex resume data without visual fatigue. By utilizing generous whitespace, crisp typography, and subtle depth, the system evokes a sense of calm authority and professional readiness.

## Colors
The palette centers on a **Deep Indigo** (`#4F46E5`) as the primary driver of brand trust and action. A **Clean Teal** is utilized for secondary accents, particularly for indicators of growth or "live" status in application tracking.

The neutral palette leverages **High-Contrast Grays** to create a clear informational hierarchy. The background is a combination of pure white (`#FFFFFF`) for content areas and a soft gray (`#F8FAFC`) for organizational scaffolding, ensuring the interface feels airy and focused.

## Typography
This design system employs **Inter** for its exceptional legibility and systematic appearance. The hierarchy is strictly enforced to ensure that even text-heavy resumes remain scannable.

- **Headlines:** Use Semi-Bold weights with slight negative letter-spacing for a modern, compact look.
- **Body:** Standardized at 16px for primary reading, utilizing a 1.5x line-height ratio to optimize vertical rhythm.
- **Labels:** Used for metadata (dates, tags, categories), leveraging slightly tighter sizes with increased tracking for distinction.

## Layout & Spacing
The layout follows a **Fixed Grid** approach for the main content area to maintain line-length readability for professional documents, while utilizing a fluid wrapper for dashboard elements.

- **Grid:** A 12-column grid is used for desktop layouts.
- **Rhythm:** An 8px linear scale (4px base) governs all padding and margins. 
- **Responsive:** On mobile, margins shrink to 16px and multi-column forms reflow into single-column stacks. Card-based layouts are preferred for application tracking views to maintain touch-target integrity.

## Elevation & Depth
Depth is communicated through **Tonal Layers** and **Ambient Shadows**. Surfaces are layered to indicate functional importance:

- **Level 0 (Background):** Soft gray (`#F8FAFC`) used for the canvas.
- **Level 1 (Cards/Content):** Pure white with a very soft, diffused shadow (0px 4px 12px rgba(30, 41, 59, 0.05)).
- **Level 2 (Hover/Modals):** Increased shadow spread and a subtle indigo-tinted border to suggest interactivity.

Avoid heavy shadows; the goal is a "floating paper" aesthetic that mimics the tactile nature of professional documents.

## Shapes
The shape language is consistently **Rounded**, using an 8px to 12px radius. This balances professional rigidity with a modern, approachable feel.

- **Primary Components:** Buttons and Input fields use an 8px radius.
- **Containers:** Large content cards and resume sections use a 12px radius.
- **Status Indicators:** Use fully pill-shaped (rounded-full) geometry to differentiate status chips from interactive buttons.

## Components
### Buttons
Primary buttons use the Deep Indigo background with white text. Secondary buttons utilize a ghost style with a subtle border (`#E2E8F0`) and Indigo text. Padding is generous (12px 24px) to ensure a premium feel.

### Input Fields
Inputs feature a 1px border in soft gray, which transitions to a 2px Indigo border on focus. Labels are positioned above the field in `label-md` for maximum clarity during the resume-building process.

### Chips & Tags
Used for skills and application status. Skills use a light gray background, while status indicators (e.g., "Interviewing") use the Secondary Teal or Tertiary Blue in a low-opacity "success-mint" background.

### Cards
Resume and job cards are the primary vessel for information. They feature Level 1 elevation, 12px rounding, and 24px internal padding. They should include clear dividers between sections to manage data density.

### Timeline/Tracker
A custom vertical stepper component is used for job application tracking, utilizing the Secondary Teal to highlight the current progress stage.