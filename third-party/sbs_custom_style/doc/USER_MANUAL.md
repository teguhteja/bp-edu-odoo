# SBS Custom Style user manual

## Purpose

Gives the Odoo **Community** backend a consistent look and a few productivity
controls that Community does not ship with: an application sidebar, a reworked
chatter and dialog layout, a refresh control in the search bar, and a themed
login and web layout.

This module is Community-only by design. Its manifest explicitly excludes
`web_enterprise`, so it can never be installed alongside the Enterprise web
client.

## Main features

- **Apps sidebar** — the installed applications in a vertical bar beside the
  main content.
- **Themed backend** — colour palette, dialogs and control panel styling, with
  light and dark variants.
- **Chatter layout** — a reworked chatter and composer.
- **Refresh control** — a refresh action in the search control panel.
- **Login and web layout** — themed templates for the login page and the general
  web layout.
- **Server action controls** — additional handling on server action views.

## Prerequisites

- Odoo **Community**. The module must not be used with the Enterprise web
  client; Odoo will refuse to install both.
- The **Discuss** (`mail`), **Web**, **Bus** and **Automation**
  (`base_automation`) modules, which are pulled in automatically.
- No extra Python libraries.

## Installation

1. Go to **Apps**.
2. Remove the default *Apps* filter and search for `SBS Custom Style`.
3. Press **Activate**.
4. Reload the browser with a hard refresh so the new assets are fetched.

A setup hook runs on installation, and a cleanup hook runs if the module is
uninstalled, so removing it returns the interface to standard Odoo.

## Initial configuration

Options are grouped with Odoo's own settings:

**Settings → General Settings** — look for the SBS section added by this module.

Per-user preferences added by the module are on the user form:
**Settings → Users & Companies → Users →** open a user.

## User access

The module adds no groups of its own. The theme applies to every backend user.
Settings remain restricted to Odoo's own Settings administrators.

## Navigation

There is no dedicated menu. The changes are visible throughout the backend:

- The apps sidebar appears beside the content area.
- The refresh control sits in the search bar of list and kanban views.
- The chatter appears on any record that has one.

## Step-by-step usage

### Switch between applications

Use the apps sidebar rather than the apps menu. The current application is
highlighted.

### Refresh a view

Press the refresh control in the search bar to reload the current view's records
without a full browser reload.

### Dark mode

The theme ships light and dark variants. Dark mode follows Odoo's own dark mode
setting.

## Common questions and errors

| Situation | Explanation |
|---|---|
| The interface looks unchanged | The browser is serving cached assets. Do a hard refresh. |
| The module will not install | An Enterprise web client is present. This module excludes `web_enterprise` deliberately. |
| The layout looks broken after an upgrade | Regenerate assets: **Settings → Technical → Assets**, or restart Odoo with `--dev=assets` during testing. |
| A colleague sees a different layout | Their browser cache is stale, or they have a different dark-mode preference. |

## Limitations

- The module changes presentation and a small number of interface controls. It
  does not change business logic, permissions or reporting.
- It restyles the backend and the login page. Website pages are not themed.
- Because it patches web and mail assets, other themes that patch the same
  templates may conflict.

## Dependencies on other SBS modules

None. This module works on its own.
