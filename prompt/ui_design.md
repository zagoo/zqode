Here are reusable prompt templates. The first is a **preamble** to prepend to every UI task; the rest are **task-specific** templates that build on it.

---

### 0. Universal preamble (prepend to every UI task)

```
Before writing any UI code, read DESIGN.md in full. All UI must strictly
adhere to it. Treat these as hard rules — not defaults to override.

Non-negotiables:
1. Reference tokens by name everywhere ({colors.canvas}, {spacing.xl},
   {typography.display-xl}, etc.). Never inline hex, raw px, or font names.
2. Background is cream {colors.canvas} — never #fff, never cool gray.
3. Display headlines: Copernicus / Tiempos Headline serif, weight 400,
   negative letter-spacing. Never sans-serif. Never bold (≥600).
4. Body: StyreneB / Inter humanist sans. Code: JetBrains Mono.
5. Coral {colors.primary} is reserved for primary CTAs and full-bleed
   callout cards only. Not for decoration, borders, icons, or accents.
6. Surface pacing alternates band-to-band: cream → cream-card →
   dark-mockup → coral-callout → dark-footer. Never two same-mode in a row.
7. Border-radius is hierarchical: md (8px) buttons/inputs, lg (12px)
   content cards, xl (16px) hero containers, pill for badges.
8. No new colors, fonts, or surface tones beyond DESIGN.md. If something
   you need isn't covered, STOP and surface it before inventing.
9. Compose from the existing components: block. Extend, don't fork.

Before reporting done, output a checklist confirming each rule above.
If any rule was bent (and why), flag it explicitly. Don't hide deviations.
```

**Why it works:** Lists the brittle rules explicitly (cream-not-white, serif-not-bold, coral-scarcity, alternation). Forces a self-audit at the end so you catch drift without me re-reviewing.

---

### 1. New component

```
[preamble above]

Task: Build a <component description> in <framework>.

Steps:
1. Find the closest existing entry in DESIGN.md `components:`. If one fits,
   extend it — don't make a parallel.
2. If nothing fits, list what's missing and propose a name + token set.
   Wait for my approval before coding.
3. Build it. All styling via tokens.

Output the final code plus the rule-check list from the preamble.
```

---

### 2. New page or full section

```
[preamble above]

Task: Build the <page name> page in <framework>.

Required band order:
- top-nav
- hero-band (h1 in {typography.display-xl})
- <list each band and which component to use>
- cta-band-coral OR cta-band-dark (pre-footer)
- footer

Constraints:
- {spacing.section} (96px) between bands.
- Surface modes must alternate. After laying out, print the band-by-band
  surface list and verify no two adjacent bands share a mode.
- Coral appears at most twice total: one primary button + one callout
  card. Surface if the design needs more.
```

---

### 3. Bootstrap design tokens into a codebase

```
[preamble above]

Task: Translate DESIGN.md into <Tailwind config | CSS variables |
styled-components theme | <other>> so future UI work can reference tokens.

Deliverables:
1. Every color, typography, spacing, and radius token in the YAML
   frontmatter, exported as named tokens.
2. A component file per entry in `components:` (button-primary,
   feature-card, code-window-card, etc.) — composed from the tokens
   above, not raw values.
3. A fonts setup with the documented fallback chains:
   - Copernicus → Tiempos Headline → Cormorant Garamond → EB Garamond
   - StyreneB → Inter → -apple-system → BlinkMacSystemFont
4. A README snippet showing how to consume a token in this codebase.

If any token in DESIGN.md is ambiguous or missing for something I asked,
stop and ask. Don't invent fillers.
```

---

### 4. Audit existing UI against DESIGN.md

```
[preamble above]

Task: Audit <file or directory> against DESIGN.md. Don't change code —
just report.

For each styling property, classify:
- OK: matches a DESIGN.md token
- DRIFT: approximates a token but uses raw value (e.g. #fafaf5 instead
  of {colors.canvas})
- VIOLATION: wrong family entirely (cool gray, sans display, bold
  serif, coral on decoration, undocumented accent color, etc.)

Specifically flag any:
- background-color: #fff / white / cool grays
- font-weight ≥ 600 on serif headings
- color: #cc785c used on anything that isn't a primary CTA or
  full-bleed callout
- Two adjacent sections with the same surface mode
- Border-radius values outside {4, 6, 8, 12, 16, 9999}
- Colors outside the documented palette

Output a table: file:line | current value | classification | suggested
token. Group by VIOLATION → DRIFT → OK.
```

---

### 5. Convert third-party / off-brand designs

```
[preamble above]

Task: I have <Figma file | screenshot | existing component library> that
uses a different style. Re-skin it to strictly match DESIGN.md.

Step 1 — Mapping (do this first, don't code yet):
Produce a table mapping every source token to a DESIGN.md token:
- Source neutrals → cream / dark-navy / hairline tones
- Source primary accent → {colors.primary} if it's a real CTA;
  remove or downgrade if decorative
- Sans-serif headlines → Copernicus serif
- Drop-shadow elevation → surface-contrast elevation (the system uses
  color-block depth, not shadows)
- Cool grays → {colors.muted} / {colors.body} family

Show me the mapping. I'll approve or correct it.

Step 2 — Only after approval, build.
```

---

### 6. Tight follow-up prompts (after the initial build)

Useful one-liners to keep in your pocket:

```
Re-check the rule list from the preamble against what you just wrote.
List any violations you missed.
```

```
Replace every inline value in <file> with the corresponding DESIGN.md
token. Show me the diff.
```

```
The <section> is two cream bands in a row. Fix the pacing per DESIGN.md
rule 6 — which band should flip to dark-mockup or coral-callout?
```

---

**Two meta-tips beyond the templates:**

- **Put DESIGN.md (or a link to it) in `CLAUDE.md`** at the repo root. Then "adhere to DESIGN.md" becomes a baseline expectation I read on every session, not something you have to re-instruct each time.
- **For high-stakes work, ask for a plan first** ("design the component, don't code yet — show me the token list and structure"). Plan-then-build catches drift before it's in the diff.
