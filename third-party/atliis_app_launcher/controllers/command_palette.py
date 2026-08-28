from odoo import http
from odoo.http import request


class CommandPaletteController(http.Controller):
    @http.route("/command_palette/search", type="json", auth="user")
    def command_palette_search(self, query="", mode="all", limit=20):
        """Return command palette results for apps, menus, and window actions."""
        try:
            limit = int(limit or 20)
        except (TypeError, ValueError):
            limit = 20
        limit = max(1, min(limit, 100))

        return request.env["atliis.command.palette.service"].search(
            query=query,
            mode=mode,
            limit=limit,
        )
