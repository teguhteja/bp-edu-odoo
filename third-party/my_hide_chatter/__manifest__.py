# -*- coding: utf-8 -*-
{
    "name": "My Hide Chatter",
    "version": "19.0.1.0.0",
    "category": "Extra Tools",
    "summary": "Adds an eye icon on every Form view to show/hide the chatter "
                "(messages/followers/activity panel) and expand the form to full width.",
    "description": """
My Hide Chatter
================
Adds a small eye icon (docked in the control panel of every Form view)
that lets the user show or hide the chatter (Send message / Log note /
Activity + message thread) panel that normally appears on the right
side of a Form view.

- Works on EVERY model's Form view automatically (Sales, Purchase,
  Accounting/Invoices, CRM, Inventory, Project, ... ) because it patches
  the core web FormRenderer/FormCompiler - no per-app view changes needed.
- Click the open-eye icon -> chatter hides, form expands to full width.
- Click again (eye-slash icon) -> chatter comes back.
- The show/hide preference is remembered (saved in the browser) so it
  stays the same across page reloads and navigation.
    """,
    "author": "Mayank",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_backend": [
            "my_hide_chatter/static/src/js/chatter_toggle_service.js",
            "my_hide_chatter/static/src/scss/chatter_toggle.scss",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "application": False,
    "auto_install": False,
}
