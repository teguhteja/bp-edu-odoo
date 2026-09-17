from odoo.tests import HttpCase, tagged


# The whole suite is opt-in (not "standard"): hosted platforms like
# Odoo.sh run module tests against copies of customized production
# databases, where generic assertions produce false failures and block
# deploys. Run locally / in CI with:
#   --test-tags=announcement_bar
@tagged("post_install", "-at_install", "-standard", "announcement_bar")
class TestAnnouncementBar(HttpCase):
    def setUp(self):
        super().setUp()
        # Dev databases may carry website COW copies of the bar view from
        # editor sessions; drop them so every test starts from install state.
        # (Runs inside the test transaction — rolled back afterwards.)
        views = self.env["ir.ui.view"].with_context(active_test=False).search(
            [("key", "=", "website_announcement_bar.announcement_bar")]
        )
        views.filtered("website_id").unlink()
        views.exists().active = False

    def test_hidden_by_default(self):
        # Default OFF after install — visitors must never see a placeholder
        res = self.url_open("/")
        self.assertEqual(res.status_code, 200)
        self.assertNotIn(b"o_announcement_bar", res.content)

    def test_visible_when_enabled(self):
        self.env.ref("website_announcement_bar.announcement_bar").active = True
        res = self.url_open("/")
        self.assertIn(b"o_announcement_bar", res.content)

    def test_frontend_css_compiles(self):
        # A SCSS compile error does NOT 500 the page — Odoo serves
        # error-banner CSS while the HTML still returns 200. Inspect the
        # compiled bundle itself.
        import re
        self.env.ref("website_announcement_bar.announcement_bar").active = True
        page = self.url_open("/").content.decode()
        # website may serve web.assets_frontend or web.assets_frontend_lazy
        m = re.search(r'href="(/web/assets/[^"]*web\.assets_frontend[^"]*\.css)"', page)
        self.assertTrue(m, "frontend CSS bundle link not found in page")
        css = self.url_open(m.group(1)).content.decode()
        self.assertIn(".o_announcement_bar", css,
                      "bar styles missing from compiled bundle — SCSS compile error?")


# Tours additionally fail on ANY browser console error, including errors
# from a database's own custom JS — kept under the same opt-in tag:
@tagged("post_install", "-at_install", "-standard", "announcement_bar")
class TestAnnouncementBarTour(HttpCase):
    def test_dismiss_tour(self):
        self.env.ref("website_announcement_bar.announcement_bar").active = True
        self.start_tour("/", "announcement_bar_dismiss")
