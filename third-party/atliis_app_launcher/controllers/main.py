from odoo import http
from odoo.http import request


class AppLauncherDashboardController(http.Controller):
    def _redirect_to_launcher(self):
        """Return an HTTP redirect to the launcher action."""
        action = request.env.ref(
            "atliis_app_launcher.action_app_launcher_dashboard",
            raise_if_not_found=False,
        )
        if action:
            return request.redirect(f"/odoo/action-{action.id}")
        return request.redirect("/web")

    @http.route(
        ["/apps", "/apps/", "/odoo/home", "/odoo/home/"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def app_launcher(self, **kwargs):
        """Redirect users to the app launcher client action."""
        return self._redirect_to_launcher()

    @http.route(
        ["/odoo", "/odoo/"], type="http", auth="user", website=True, sitemap=False
    )
    def odoo_launcher(self, **kwargs):
        """Load the custom launcher when users open /odoo."""
        return self._redirect_to_launcher()
