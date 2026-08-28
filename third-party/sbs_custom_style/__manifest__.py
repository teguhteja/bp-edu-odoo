{
    "name": "SBS Custom Style",
    "version": "19.0.1.1.0",
    "category": "Themes/Backend",
    "summary": "Unified Community backend theme and productivity controls",
    "description": (
        "A standalone Odoo Community backend style suite with an apps sidebar, "
        "theme and color settings, chatter positioning, expandable dialogs, "
        "group controls, login-page backgrounds, and manual or automated "
        "view refresh."
    ),
    "author": "Star Bit Solutions",
    "company": "Star Bit Solutions",
    "maintainer": "Star Bit Solutions",
    "website": "https://starbitsolutions.com",
    "license": "LGPL-3",
    "depends": [
        "base_setup",
        "web",
        "mail",
        "bus",
        "base_automation",
    ],
    "excludes": ["web_enterprise"],
    "data": [
        "templates/webclient.xml",
        "templates/web_layout.xml",
        "templates/login_layout.xml",
        "views/res_users.xml",
        "views/res_config_settings.xml",
        "views/ir_actions_server_views.xml",
    ],
    "demo": [
        "demo/base_automation.xml",
        "demo/ir_actions_server.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "sbs_custom_style/static/src/appsbar/scss/variables.scss",
            (
                "after",
                "web/static/src/scss/primary_variables.scss",
                "sbs_custom_style/static/src/chatter/scss/variables.scss",
            ),
            (
                "after",
                "web/static/src/scss/primary_variables.scss",
                "sbs_custom_style/static/src/dialog/scss/variables.scss",
            ),
            (
                "prepend",
                "sbs_custom_style/static/src/colors/scss/colors.scss",
            ),
            (
                "before",
                "sbs_custom_style/static/src/colors/scss/colors.scss",
                "sbs_custom_style/static/src/colors/scss/colors_light.scss",
            ),
            (
                "after",
                "web/static/src/scss/primary_variables.scss",
                "sbs_custom_style/static/src/theme/scss/colors.scss",
            ),
            (
                "after",
                "web/static/src/scss/primary_variables.scss",
                "sbs_custom_style/static/src/theme/scss/variables.scss",
            ),
        ],
        "web._assets_backend_helpers": [
            "sbs_custom_style/static/src/appsbar/scss/mixins.scss",
        ],
        "web.assets_web_dark": [
            (
                "after",
                "sbs_custom_style/static/src/appsbar/scss/variables.scss",
                "sbs_custom_style/static/src/appsbar/scss/variables.dark.scss",
            ),
            (
                "after",
                "sbs_custom_style/static/src/colors/scss/colors.scss",
                "sbs_custom_style/static/src/colors/scss/colors_dark.scss",
            ),
        ],
        "web.assets_backend": [
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "sbs_custom_style/static/src/appsbar/webclient/webclient.js",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.xml",
                "sbs_custom_style/static/src/appsbar/webclient/webclient.xml",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "sbs_custom_style/static/src/appsbar/webclient/menus/app_menu_service.js",
            ),
            (
                "after",
                "web/static/src/webclient/webclient.js",
                "sbs_custom_style/static/src/appsbar/webclient/appsbar/appsbar.js",
            ),
            "sbs_custom_style/static/src/appsbar/webclient/webclient.scss",
            "sbs_custom_style/static/src/appsbar/webclient/appsbar/appsbar.xml",
            "sbs_custom_style/static/src/appsbar/webclient/appsbar/appsbar.scss",
            "sbs_custom_style/static/src/chatter/core/**/*.*",
            "sbs_custom_style/static/src/chatter/chatter/*.scss",
            "sbs_custom_style/static/src/chatter/chatter/*.xml",
            (
                "after",
                "mail/static/src/chatter/web_portal/chatter.js",
                "sbs_custom_style/static/src/chatter/chatter/chatter.js",
            ),
            (
                "after",
                "mail/static/src/core/common/composer.js",
                "sbs_custom_style/static/src/chatter/chatter/composer.js",
            ),
            (
                "after",
                "mail/static/src/core/common/store_service.js",
                "sbs_custom_style/static/src/chatter/chatter/store_service.js",
            ),
            (
                "after",
                "mail/static/src/chatter/web/form_compiler.js",
                "sbs_custom_style/static/src/chatter/views/form/form_compiler.js",
            ),
            "sbs_custom_style/static/src/chatter/views/form/form_renderer.js",
            (
                "after",
                "web/static/src/core/dialog/dialog.js",
                "sbs_custom_style/static/src/dialog/core/dialog/dialog.js",
            ),
            (
                "after",
                "web/static/src/core/dialog/dialog.scss",
                "sbs_custom_style/static/src/dialog/core/dialog/dialog.scss",
            ),
            (
                "after",
                "web/static/src/core/dialog/dialog.xml",
                "sbs_custom_style/static/src/dialog/core/dialog/dialog.xml",
            ),
            (
                "after",
                "web/static/src/views/view_dialogs/select_create_dialog.js",
                "sbs_custom_style/static/src/dialog/views/view_dialogs/select_create_dialog.js",
            ),
            "sbs_custom_style/static/src/group/search/**/*",
            "sbs_custom_style/static/src/refresh/core/utils.js",
            "sbs_custom_style/static/src/refresh/scss/refresh.scss",
            (
                "after",
                "web/static/src/search/control_panel/control_panel.js",
                "sbs_custom_style/static/src/refresh/search/control_panel.js",
            ),
            (
                "after",
                "web/static/src/search/control_panel/control_panel.xml",
                "sbs_custom_style/static/src/refresh/search/control_panel.xml",
            ),
            "sbs_custom_style/static/src/refresh/services/refresh_service.js",
            "sbs_custom_style/static/src/theme/webclient/**/*.xml",
            "sbs_custom_style/static/src/theme/webclient/**/*.scss",
            "sbs_custom_style/static/src/theme/webclient/**/*.js",
            "sbs_custom_style/static/src/theme/views/**/*.scss",
        ],
        "web.assets_unit_tests": [
            "sbs_custom_style/static/tests/**/*.test.js",
            "sbs_custom_style/static/src/group/search/**/*.js",
            "sbs_custom_style/static/src/group/search/**/*.xml",
        ],
    },
    "images": [
        "static/description/banner.png",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "post_init_hook": "_setup_module",
    "uninstall_hook": "_uninstall_cleanup",
}
