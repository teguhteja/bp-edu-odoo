# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2026 — Atliis 360
#    Developed by Atliis 360
#    All rights reserved.
#
##############################################################################
{
    "name": "Odoo Quick Launcher – Command Palette & Fast Navigation",
    "version": "19.0.0.0.0",
    "summary": "Navigate Odoo faster with a smart app launcher and Ctrl+K command palette",
    "description": """
Stop clicking through menus. Navigate Odoo instantly.

Odoo Quick Launcher adds a modern app dashboard and a powerful command palette to speed up your daily workflow.

🚀 Key Benefits
--------------
- Open apps, menus, and actions instantly
- Save time with keyboard-first navigation
- Improve productivity for daily Odoo users
- Reduce repetitive clicks and navigation delays

⚡ Main Features
--------------
- Smart app launcher dashboard with search
- Drag-and-drop app ordering for personalization
- Powerful command palette (Ctrl + K)
- Search across:
  - Apps
  - Menus
  - Actions
- Keyboard navigation for fast access
- Quick open workflows for power users

🎯 Perfect For
--------------
- Odoo Community users
- Teams working daily inside Odoo
- Power users who want faster navigation

💡 Result
---------
Access anything in seconds and significantly improve your daily efficiency inside Odoo.

🛠️ Technical Highlights
-----------------------
- Built with modern OWL components
- Optimized search with debounce and result limits
- Access-aware results based on user permissions
- Lightweight and fast performance

""",
    "category": "Tools",
    "author": "Atliis 360",
    "maintainer": "Atliis 360",
    "website": "https://atliis.com",
    "support": "helpdesk@atliis.com",
    "live_test_url": "https://demov19.atliis.com/web/login?utm_source=odoo_apps&utm_medium=live_preview&utm_campaign=atliis_app_launcher",
    "price": 0.0,
    "currency": "USD",
    "license": "OPL-1",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/app_launcher_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "atliis_app_launcher/static/src/js/app_launcher_dashboard.js",
            "atliis_app_launcher/static/src/js/command_palette_provider.js",
            "atliis_app_launcher/static/src/xml/app_launcher_dashboard.xml",
            "atliis_app_launcher/static/src/xml/command_palette.xml",
            "atliis_app_launcher/static/src/scss/app_launcher_dashboard.scss",
            "atliis_app_launcher/static/src/scss/command_palette.scss",
        ],
    },
    "installable": True,
    "application": False,
    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],
}
