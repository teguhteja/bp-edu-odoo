# SimplifyIT Linear Backend Theme

Backend theme for **Odoo 19** inspired by the [Linear.app](https://linear.app) design
language. Works on **Community and Enterprise** with the same module.

## What it does

- **Full-height sidebar** (Linear layout): company brand, a *Search…* trigger that
  opens Odoo's command palette (`Ctrl+K`), the list of installed apps with the
  active app expanded to its **full menu tree** (nested groups collapse/expand,
  every actionable menu is reachable), and a user footer. Collapsible to an
  icon rail with the header button or `Ctrl+B`.
- **Fully Linear header**: on desktop the navbar apps hamburger, the enterprise
  menu toggle and the section dropdowns are hidden — the sidebar and command
  palette own all navigation. Everything reverts to stock Odoo on mobile
  (<992px), where the sidebar is hidden.
- **Linear design system**: Inter variable font (shipped), indigo `#5E6AD2` accent,
  soft gray canvas, 1px hairline borders, subtle large shadows, small radii.
- **Restyled chrome**: navbar, breadcrumbs, control panel, buttons, inputs,
  dropdowns, modals, tabs, tags, notifications and the command palette.
- **Views**: list (uppercase micro-headers, hover rows), form (card sheet),
  kanban (bordered cards), search facets, settings, chatter.
- **Dark mode**: full Linear dark palette via `web.assets_web_dark`, toggled
  from a systray icon placed right before the Discuss icon. Works on
  Community too (see Technical notes).
- **Login page**: light Linear touch.

## Community vs Enterprise

The module only depends on `web`, so it installs on both editions:

- On **Community** the sidebar completely replaces the apps dropdown on desktop
  (the dropdown remains on mobile, where the sidebar is hidden).
- On **Enterprise** (`web_enterprise` present) the home menu keeps working and is
  lightly restyled; the sidebar hides automatically while the home menu is open.
  The theme variables are inserted after `web`'s primary variables, so they win
  over both editions' defaults.

## Technical notes

- Design tokens are CSS custom properties (`--slt-*`) declared in
  `static/src/scss/tokens.scss`; `tokens.dark.scss` re-declares them for the
  dark bundle only.
- The sidebar follows the proven `muk_web_appsbar` integration pattern:
  an owl component registered on `WebClient.components` and placed via a
  template extension of `web.WebClient`, laid out with a CSS grid on
  `.o_web_client`.
- Sidebar collapse state is stored in `localStorage` (`slt_sidebar_collapsed`).
- The dark mode toggle writes a `color_scheme` cookie (`light`/`dark`) and
  reloads — same cookie Odoo's own dark-aware widgets already read (ace
  editor, graphs, color picker). Core `web.ir_http.color_scheme()` always
  returns `"light"` and only `web_enterprise` reads that cookie, so
  `models/ir_http.py` overrides it to check the cookie on Community too.
  If `web_enterprise`'s own `color_scheme` service is present, the toggle
  also persists through `user.setUserSettings("color_scheme", ...)` so its
  service doesn't revert the choice back to the system preference on the
  next boot.
