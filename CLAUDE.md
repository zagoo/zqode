# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## Rule 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Rule 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Rule 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Rule 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Rule 5. Before writing any frontend code, read ARCHITECTURE.md in full.
All frontend code must strictly adhere to it. Treat these as hard rules — not defaults to override.

Non-negotiables:
1. Tech stack lock-in: Vue 3 (Composition API + `<script setup lang="ts">`), Vite,
   Vue Router, Pinia, Axios — and nothing else. No Vuex, no alternative HTTP clients,
   no React/Svelte patterns, no UI kits not already in package.json. If a need arises
   that isn't covered, STOP and surface it before installing anything.
2. Module-first thinking: Before creating any file, name the target
   `views/[module_name]/`. A new feature = a new module directory. Never spread one
   feature across multiple modules; never mix two features into one module.
3. Directory placement is mandatory: Files must land in the exact slots from
   ARCHITECTURE.md §2. Module-private code lives under
   `views/[module]/{api,components,hooks,store}/`. Global code lives only under
   `src/{assets,components,composables,router,store,utils}/`.
4. API isolation: Never create or grow a global `src/api.ts`. All endpoints declared
   in `views/[module]/api/index.ts`. A page may only import from its own module's
   `api/` (or an explicitly designated global service). `src/utils/request.ts` is the
   only place for the Axios base instance, interceptors, and global error handling.
5. Routing isolation: Add routes by creating `src/router/modules/[module].ts`. NEVER
   edit `src/router/index.ts` directly — it auto-aggregates via `import.meta.glob`.
6. The 3-module rule: Do not promote a component, hook, or store to a global directory
   unless it is currently consumed by ≥3 separate business modules. When in doubt,
   keep it local. Premature globalization is a regression.
7. Destruction safety: After your changes, `rm -rf src/views/[module]` plus deleting
   the module's route file MUST leave the project compiling with zero errors and zero
   dead references. If your design fails this test, you have leaked cross-module
   coupling — refactor before reporting done.
8. Logic/UI separation: Stateful logic, side effects, and non-trivial computation
   belong in composables under the module's `hooks/`. `.vue` files = template +
   minimal glue. No fetch calls or business branching inline in templates.
9. Component communication: Only `props` down / `emits` up. No cross-module imports
   of private components, no `provide/inject` across module boundaries, no global
   event bus, no reaching into another module's store.
10. TypeScript strictness: Strong types for Axios response schemas, store state,
    component props and emits. No `any` escape hatches; no `// @ts-ignore` without
    a one-line justification.
11. Don't touch global scope unprompted: Unless explicitly told to refactor, do not
    modify `src/components/`, `src/composables/`, `src/utils/`, `src/store/`,
    `src/router/index.ts`, or any other module's files.

Before reporting done, output a checklist confirming each rule above. For every file
created or modified, state: (a) which module it belongs to, (b) which directory slot
it occupies, (c) whether any file outside that module was touched and why. If any
rule was bent, flag it explicitly with the reason. Don't hide deviations.

## Rule 6. Before writing any UI code, read DESIGN.md in full.
All UI must strictly adhere to it. Treat these as hard rules — not defaults to override.
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

## Rule 7. Before writing any UI for this SPA, conform to the layout system specified in this rule.
This rule governs STRUCTURE and COMPONENT COMPOSITION only — visual tokens (colors, type, radii, and surface tones, etc.) continue to come from Rule 6 / DESIGN.md.Treat these as hard rules — not defaults to override.

App-shell structure (non-negotiable):
1. Three-pane shell: left nav (~256px) | center content (fluid) | right config
   panel (~360px). Left and right panels collapse independently; center reflows.
   There is NO top app bar spanning the panes.
2. Routing changes the center pane only. Pages never render their own shell.
3. Build one `<AppShell>` with named slots: `nav-header`, `nav-primary`,
   `nav-footer`, `content-toolbar`, `content`, `content-footer`, `panel-header`,
   `panel-body`. Every page mounts into these slots.

Left sidebar (non-negotiable):
4. Top → bottom order: product header (name + workspace switcher) → primary nav
   → spacer → utility links (e.g.,Search, What's new, Settings, etc.) → user identity chip.
5. Primary nav rows are icon + label. Parents expand INLINE to reveal children
   — no flyouts, no separate routes for hub pages. Selected state is a soft
   rounded fill on the row, never a side border.

Center pane (non-negotiable):
6. Toolbar: left cluster = sidebar-collapse button + page title; right cluster
   = contextual icon actions (e.g.,share, fullscreen, add, etc.). No tabs here.
7. Page heading is large display text per DESIGN.md. Mode toggles (e.g.,
   Models / Agents) use a right-aligned segmented pill placed in the content
   next to the heading, never in the toolbar.
8. Card grids: 3 cols at desktop, 2 at tablet, 1 at mobile. Each card composes:
   tinted square icon (~32px) top-left → title → description. Use card surface
   tokens from DESIGN.md.
9. The Center panel dynamically renders the actual content of the corresponding page 
   according to the item clicked in the Primary Navigation area on the Left sidebar.

Right configuration panel (non-negotiable):
10. Header: panel title + utility actions + close (×), the height is exactly the same as 
    that of the toolbar on the Center panel.
11. Body is a vertical stack of collapsible labeled sections. Inside a section:
    label above the control, control fills width, toggle rows have the label
    filling the row and the switch right-aligned.
12. The panel pushes content; it never overlays. On narrow viewports it
    becomes a slide-over with backdrop.

Component composition (non-negotiable):
13. Reuse a single set of primitives: `<NavItem>`, `<ToolbarIconButton>`,
    `<SegmentedControl>`, `<SettingsSection>`, `<ToggleRow>`, `<DropdownRow>`,
    `<ContentCard>`, `<PromptComposer>`. Do not fork — extend via props/slots.
14. One icon family, outline style. 16px in nav/toolbars, 20px in content.
    Never mix icon families.

Before reporting done, output a checklist confirming each rule above. For
every page or component added, state: (a) which AppShell slots it fills,
(b) which primitives it reuses, (c) any new primitive introduced and why an
existing one could not be extended. If a rule was bent, flag it explicitly.
Don't hide deviations.

## Rule 8. Use the model only for judgment calls
Use me for: classification, drafting, summarization, extraction.
Do NOT use me for: routing, retries, deterministic transforms.
If code can answer, code answers.

## Rule 9. Token budgets are not advisory
Per-task: 4,000 tokens. Per-session: 30,000 tokens.
If approaching budget, summarize and start fresh.
Surface the breach. Do not silently overrun.

## Rule 10. Surface conflicts, don't average them
If two patterns contradict, pick one (more recent / more tested).
Explain why. Flag the other for cleanup.
Don't blend conflicting patterns.

## Rule 11. Read before you write
Before adding code, read exports, immediate callers, shared utilities.
"Looks orthogonal" is dangerous. If unsure why code is structured a way, ask.

## Rule 12. Tests verify intent, not just behavior
Tests must encode WHY behavior matters, not just WHAT it does.
A test that can't fail when business logic changes is wrong.

## Rule 13. Checkpoint after every significant step
Summarize what was done, what's verified, what's left.
Don't continue from a state you can't describe back.
If you lose track, stop and restate.

## Rule 14. Match the codebase's conventions, even if you disagree
Conformance > taste inside the codebase.
If you genuinely think a convention is harmful, surface it. Don't fork silently.

## Rule 15. Fail loud
"Completed" is wrong if anything was skipped silently.
"Tests pass" is wrong if any were skipped.
Default to surfacing uncertainty, not hiding it.

---
**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
