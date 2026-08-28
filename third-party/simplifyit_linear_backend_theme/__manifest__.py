# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

{
    'name': 'SimplifyIT Linear Backend Theme',
    'summary': 'Linear.app inspired backend theme for Odoo 19 Community & Enterprise',
    'description': """
        Backend theme inspired by the Linear.app design language:
        a full-height sidebar with app navigation, Inter typography,
        a refined indigo palette, subtle borders and shadows, and a
        restyled command palette. Works on both Odoo Community and
        Odoo Enterprise (web_enterprise simply adds its home menu on top).
    """,
    'version': '19.0.1.0.1',
    'category': 'Themes/Backend',
    'license': 'OPL-1',
    'live_test_url': 'https://demo.simplifyit.com.bo',
    'support': 'support@simplifyit.com.bo',
    'author': 'SimplifyIT',
    'website': 'https://simplifyit.com.bo',
    # apps.odoo.com uses two slots. With a single entry it fills both with it:
    #   - browse card  (.loempia_theme_card): 2:1 box, background-size: contain
    #   - app page hero (.loempia_app_cover):  2:1 box, background-size: cover
    # banner.gif is exactly 700x350 (2:1), so it fits both without cropping.
    # Adding a second image switches the card to the tall theme layout
    # (padding-top: 120%, cropped to fill) and moves this one to the hero;
    # that first entry then has to be a ~0.8:1 portrait image.
    'images': ['static/description/banner.gif'],
    # Free on purpose: the theme is the way in to the paid modules and to the
    # services, not a product of its own. The store publishes it as "Free".
    'price': '0.00',
    'currency': 'EUR',
    'depends': [
        'web',
        'base_setup',
    ],
    'data': [
        'views/login_templates.xml',
        'views/res_company_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            (
                'after',
                'web/static/src/scss/primary_variables.scss',
                'simplifyit_linear_backend_theme/static/src/scss/variables.scss',
            ),
        ],
        'web.assets_backend': [
            'simplifyit_linear_backend_theme/static/src/scss/fonts.scss',
            'simplifyit_linear_backend_theme/static/src/scss/tokens.scss',
            'simplifyit_linear_backend_theme/static/src/scss/theme.scss',
            'simplifyit_linear_backend_theme/static/src/scss/views.scss',
            'simplifyit_linear_backend_theme/static/src/webclient/**/*',
        ],
        'web.assets_web_dark': [
            # Odoo's core palette has no dark values on Community: the core
            # dark bundle is just `web.assets_web` plus per-component
            # `*.dark.scss` files, and it is `web_enterprise` that recolours
            # the global palette. Without this, dark mode paints our chrome
            # and leaves every Odoo view white. Must come *before* web's
            # primary variables so `$o-webclient-background-color`,
            # `$o-main-text-color` and `$body-bg` derive from our values.
            (
                'before',
                'web/static/src/scss/primary_variables.scss',
                'simplifyit_linear_backend_theme/static/src/scss/odoo_variables_dark.scss',
            ),
            'simplifyit_linear_backend_theme/static/src/**/*.dark.scss',
        ],
        'web.assets_frontend': [
            'simplifyit_linear_backend_theme/static/src/scss/fonts.scss',
            'simplifyit_linear_backend_theme/static/src/scss/login.scss',
            'simplifyit_linear_backend_theme/static/src/js/login.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
