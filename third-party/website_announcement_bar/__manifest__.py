{
    "name": "Website Announcement Bar",
    "version": "18.0.1.0.6",
    "category": "Website/Website",
    "summary": "Rotating, dismissible, schedulable announcement bar above the website header",
    "author": "19 Prince",
    "website": "https://www.19prince.com",
    "license": "LGPL-3",
    "depends": ["website"],
    "data": [
        "views/templates.xml",
        "views/snippets/options.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            "website_announcement_bar/static/src/scss/primary_variables.scss",
        ],
        "web.assets_frontend": [
            "website_announcement_bar/static/src/scss/announcement_bar.scss",
            "website_announcement_bar/static/src/js/announcement_bar.js",
        ],
        "web.assets_tests": [
            "website_announcement_bar/static/tests/tours/announcement_bar_tour.js",
        ],
    },
    "installable": True,
}
