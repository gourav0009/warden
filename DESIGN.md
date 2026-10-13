---
name: Warden — AI Governance Console
description: Obsidian gatehouse console where every agent action is journaled, judged, and gated.
colors:
  primary: "#06B6D4"
  emerald: "#10B981"
  amber: "#F59E0B"
  ruby: "#F43F5E"
  purple: "#8B5CF6"
  obsidian-canvas: "#090E17"
  sidebar: "#0C121F"
  surface: "#101828"
  surface-elevated: "#16243C"
  surface-active: "#1C2D4A"
  text-primary: "#F8FAFC"
  text-secondary: "#94A3B8"
  text-muted: "#64748B"
typography:
  display:
    fontFamily: "'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif"
    fontSize: "1.6rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "'IBM Plex Mono', 'JetBrains Mono', monospace"
    fontSize: "1.85rem"
    fontWeight: 700
    lineHeight: 1
  body:
    fontFamily: "'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif"
    fontSize: "0.85rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'IBM Plex Sans', -apple-system, 'Segoe UI', sans-serif"
    fontSize: "0.78rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.02em"
rounded:
  sm: "4px"
  md: "6px"
  lg: "8px"
  xl: "12px"
spacing:
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
components:
  nav-active:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "0.55rem 0.75rem"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "1.15rem"
  badge-allowed:
    backgroundColor: "rgba(16, 185, 129, 0.12)"
    textColor: "{colors.emerald}"
    rounded: "{rounded.sm}"
    padding: "0.12rem 0.45rem"
  badge-escalated:
    backgroundColor: "rgba(245, 158, 11, 0.12)"
    textColor: "{colors.amber}"
    rounded: "{rounded.sm}"
    padding: "0.12rem 0.45rem"
  input-search:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "0.65rem 0.8rem"
---

# Design System: Warden — AI Governance Console

## Overview

**Creative North Star: "The Obsidian Gatehouse"**

Warden is a tactical watch console carved from deep obsidian: a near-black canvas with a faint cyan mesh glow at the top, a fixed 256px sidebar gate, and glassy slate surfaces carrying dense operational data. Every accent earns its place as a verdict — emerald allows, amber escalates, ruby denies, cyan informs, purple identifies agents. The mood is tense, precise, and mission-ready: tabular numerals, monospace hashes, 1px micro-borders, and micro-interactions that acknowledge state without celebrating themselves.

Nothing decorative lacks a status meaning. Density is high but scannable: KPI cards with sparklines, interception queues with diff previews, audit rows with hash chips. The confirmed anti-reference is marketing softness — no pastel washes, no rounded playful geometry, no glow for its own sake.

**Key Characteristics:**
- Obsidian-first dark console with a pristine light twin (same tokens, remapped).
- Verdict-driven color: rarity is the signal; the canvas stays quiet so escalations shout.
- Monospace for evidence (hashes, counts, diffs), sans for judgment (titles, decisions).
- Compact tactical controls: 6–8px radii, 1px borders, 0.2s state transitions.

## Colors

Quiet obsidian canvas with five verdict accents; each hue owns exactly one judgment.

### Primary
- **Gatehouse Cyan** (#06B6D4): info, links, selection, focus rings, primary telemetry sparkline. Wherever the system speaks without judging — search, navigation aids, total-actions card.

### Secondary
- **Allow Emerald** (#10B981): allowed actions, healthy states, success deltas. Badge form is 12% tint background with bright text (#34D399 dark mode).

### Tertiary
- **Escalate Amber** (#F59E0B): escalated / pending-human states, warning deltas, interception queue markers. Never used for decoration; its appearance means someone must decide.

### Neutral
- **Obsidian Canvas** (#090E17): app background with ambient mesh (6% cyan radial at top, 3% emerald at corner).
- **Gate Sidebar** (#0C121F): fixed 256px navigation rail, 1px right border.
- **Slate Surface** (#101828): cards, panels, inputs at rest.
- **Elevated Surface** (#16243C): hover / raised panels, active nav background.
- **Active Surface** (#1C2D4A): pressed / selected fills.
- **Ink Primary** (#F8FAFC): headings, KPI values, body emphasis.
- **Ink Secondary** (#94A3B8): subtitles, descriptions.
- **Ink Muted** (#64748B): labels, metadata, placeholders.
- **Deny Ruby** (#F43F5E) and **Agent Purple** (#8B5CF6) complete the verdict set: ruby is terminal denial only, purple marks agent identity (icons, avatars). Both follow the same 12%-tint badge grammar.

### Named Rules (optional, powerful)
**The One Verdict Rule.** A hue's appearance is a claim about an action's fate. Cyan informs, emerald allows, amber escalates, ruby denies, purple identifies — never borrow one for decoration.
**The 90% Obsidian Rule.** Roughly 90% of any screen is canvas, surface, or text. Accents together stay near 10%; their rarity is the point.

## Typography

**Display Font:** IBM Plex Sans (with -apple-system, Segoe UI fallback)
**Body Font:** IBM Plex Sans (with -apple-system, Segoe UI fallback)
**Label/Mono Font:** IBM Plex Mono (with JetBrains Mono fallback) — evidence only: hashes, counts, diffs, versions.

**Character:** Engineered and tabular. Sans carries judgment with tight tracking on titles; mono carries evidence with tabular numerals so hashes and counts align in queues.

### Hierarchy
- **Display** (700, 1.6rem, 1.2, -0.025em): page titles only (e.g. Command Center).
- **Headline** (700, 1.85rem mono, 1.0): KPI values and intro-strong numbers; tabular-nums always.
- **Title** (600, 1.0–1.35rem): card and panel headings, empty-state headings.
- **Body** (400, 0.85rem, 1.5): descriptions, table content, queue rows; line length capped by panel width (~68ch in descriptions).
- **Label** (600, 0.78rem, 0.02em): KPI labels, nav links (0.85rem in nav), badges, metadata; uppercase only for pills (DEMO DATA) and queue status badges.

### Named Rules (optional)
**The Evidence-in-Mono Rule.** Anything a judge could cite — hashes, counts, versions, diff lines — is set in IBM Plex Mono with tabular numerals. Prose never impersonates evidence.

## Layout

Fixed gatehouse shell: 256px sticky sidebar (full viewport height, own scroll) + fluid main column with topbar and page body. Content rhythm is card-grid led: KPI grid uses auto-fit minmax(220px, 1fr) with 16px gaps; queues stack full-width intro card above filterable lists; detail views (blast radius) split impact vectors beside diff canvases. Density is comfortable-tactical: card padding 1.15rem, section gaps 12–20px, sidebar item padding ~0.55rem 0.75rem. Responsive behavior: grids collapse to single column under ~220px minimums; sidebar persists (sticky) while main scrolls; light/dark themes share identical spacing.

## Elevation & Depth

Flat-by-default obsidian with inset light; glow and shadow appear only as responses to state.

### Shadow Vocabulary (if applicable)
- **Inset crown** (`box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06)`): the resting depth of every card — a top inner highlight, not a drop shadow.
- **Sticky weight** (`box-shadow: 0 20px 40px rgba(0, 0, 0, 0.7)`): docked/sticky panels.
- **Dropdown lift** (`box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.55)`): menus and popovers.
- **Verdict glow** (`0 0 16px rgba(accent, 0.25)` per emerald/amber/ruby/cyan): hovered or active status elements only; disabled entirely in light mode (`none`).

### Named Rules (optional)
**The Flat-By-Default Rule.** Surfaces are flat at rest with only the inset crown. Drop shadows and neon glow signal hover, focus, escalation, or denial — never idle decoration.

## Shapes

Tactical rectilinear with softened corners: cards and panels at 8px, controls and icon pills at 6px, deltas and chips at 4px, pills and avatars fully round (9999px / 50%). Borders are 1px precision micro-borders (8% white dark mode, slate-200 light mode); highlighted or status borders step to 11–20% white or the verdict's 32–45% tint. No clipping tricks, no oversized radii — the gatehouse reads as engineered, not friendly. Dot-grid texture (4% white dots) sits behind canvas content at negligible contrast.

## Components

### Navigation links
- **Shape:** 6px radius rows, full-width, icon + label + optional counter pill.
- **Primary:** rest text secondary; **Hover:** surface-hover fill; **Active:** surface-elevated fill, primary text, icon brightens; counter pill (amber-tinted) shows pending count.
- **Behavior:** sticky rail; 0.2s background transition; focus-visible gets 2px cyan outline offset 2px.

### KPI cards
- **Corner Style:** 8px radius, 1px card border, inset crown shadow.
- **Background:** slate surface; icon pill tinted per verdict (12% tint + bright text, 28px box, 6px radius).
- **Shadow Strategy:** flat at rest; hover lifts 1px and brightens border (see Elevation).
- **Internal Padding:** 1.15rem; sparkline row pinned to bottom (76×28 SVG).

### Status badges / deltas
- **Style:** 4px radius, 12% verdict tint background, bright verdict text, 600 weight mono, tabular numerals.
- **State:** allowed (emerald), escalated (amber), denied (ruby), info (cyan); queue badges add 1px subtle border and uppercase 0.68rem type.

### Inputs / Fields
- **Style:** surface fill, 1px subtle border, 8px radius, 0.65rem 0.8rem padding, primary text.
- **Focus:** 2px cyan outline via global focus-visible; no glow fill.
- **Error / Disabled:** not yet systematized — use ruby border + ruby-tinted message when introduced; do not invent a new hue.

### Diff viewer (Signature Component)
GitHub-grade line diffs on near-black canvas (#060A12): deleted lines ruby-tinted, added lines emerald-tinted, hunk headers muted mono; binary files collapse to warning callouts. The diff canvas is the evidence exhibit — highest mono density in the system.

## Do's and Don'ts

### Do:
- **Do** keep every verdict hue mapped: cyan informs, emerald allows, amber escalates, ruby denies, purple identifies.
- **Do** set hashes, counts, and versions in IBM Plex Mono with tabular numerals.
- **Do** keep cards flat with the inset crown at rest; reserve glow/shadow for hover, focus, or verdict state.
- **Do** use the 12%-tint + bright-text badge grammar for all status chips.
- **Do** preserve the 256px sticky sidebar + fluid main shell and the 220px-minimum card grid.

### Don't:
- **Don't** use amber or ruby for decoration, illustration, or brand moments — they assert a fate.
- **Don't** add glow or drop shadow to idle surfaces; flat-by-default is the system.
- **Don't** set evidence (hashes, diffs, counts) in sans or non-tabular figures.
- **Don't** introduce a new accent hue without retiring or reassigning an existing verdict role.
- **Don't** round tactical controls past 8px or body cards past 12px — the gatehouse stays rectilinear.
