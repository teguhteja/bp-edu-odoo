from collections import defaultdict

from odoo import api, models

DEFAULT_ICON_URL = "/atliis_app_launcher/static/src/img/default_app.svg"


class AtliisCommandPaletteService(models.AbstractModel):
    _name = "atliis.command.palette.service"
    _description = "Atliis Command Palette Search Service"

    @api.model
    def _normalize_mode(self, mode):
        mode = (mode or "all").strip().lower()
        return mode if mode in {"all", "apps", "menus", "actions", "settings"} else "all"

    @api.model
    def _normalize_query(self, query):
        return (query or "").strip().lower()

    @api.model
    def _is_match(self, query, *values):
        if not query:
            return True
        haystack = " ".join(value for value in values if value).lower()
        return query in haystack

    @api.model
    def _is_settings_match(self, mode, *values):
        if mode != "settings":
            return True
        haystack = " ".join(value for value in values if value).lower()
        return "setting" in haystack

    @api.model
    def search(self, query="", mode="all", limit=20):
        mode = self._normalize_mode(mode)
        query = self._normalize_query(query)
        limit = max(1, min(int(limit or 20), 100))

        Menu = self.env["ir.ui.menu"]
        Module = self.env["ir.module.module"]
        ModuleModel = self.env["ir.module.module"]

        visible_menus = Menu.search([])._filter_visible_menus()
        if not visible_menus:
            return {"apps": [], "menus": [], "actions": []}

        menu_by_id = {menu.id: menu for menu in visible_menus}
        children_map = defaultdict(list)
        for menu in visible_menus:
            if menu.parent_id and menu.parent_id.id in menu_by_id:
                children_map[menu.parent_id.id].append(menu)
        for parent_id in children_map:
            children_map[parent_id].sort(key=lambda child: (child.sequence, child.id))

        launchable_menus = visible_menus.filtered(lambda menu: bool(menu.action))

        apps = []
        if mode in {"all", "apps", "settings"}:
            installed_apps = Module.sudo().search(
                [("state", "=", "installed"), ("application", "=", True)],
                order="sequence, shortdesc, name",
                limit=max(limit * 6, 80),
            )
            module_names = installed_apps.mapped("name")
            menus_by_module = defaultdict(lambda: self.env["ir.ui.menu"])

            if module_names:
                menu_imd_records = (
                    self.env["ir.model.data"]
                    .sudo()
                    .search(
                        [
                            ("model", "=", "ir.ui.menu"),
                            ("module", "in", module_names),
                            ("res_id", "in", visible_menus.ids),
                        ]
                    )
                )
                for imd in menu_imd_records:
                    menu = menu_by_id.get(imd.res_id)
                    if menu:
                        menus_by_module[imd.module] |= menu

            for module in installed_apps:
                module_menus = menus_by_module.get(module.name, self.env["ir.ui.menu"])
                app_menu = ModuleModel._select_app_menu(module_menus)
                if not app_menu:
                    continue

                action_id, launch_menu_id = ModuleModel._resolve_launch_target(
                    app_menu[0], children_map
                )
                if not action_id:
                    continue

                app_name = app_menu[0].name or module.shortdesc or module.name
                app_path = app_menu[0].complete_name or app_menu[0].name
                if not self._is_match(query, app_name, module.name, app_path):
                    continue
                if not self._is_settings_match(mode, app_name, module.name, app_path):
                    continue

                apps.append(
                    {
                        "id": module.id,
                        "name": app_name,
                        "module": module.name,
                        "path": app_path,
                        "action_id": action_id,
                        "menu_id": launch_menu_id,
                        "icon_url": (
                            ModuleModel._menu_icon_url(app_menu[0])
                            or ModuleModel._normalize_icon_url(module.icon)
                            or f"/{module.name}/static/description/icon.png"
                        ),
                        "default_icon_url": DEFAULT_ICON_URL,
                    }
                )
                if len(apps) >= limit:
                    break

        menus = []
        if mode in {"all", "menus", "settings"}:
            for menu in launchable_menus.sorted(
                lambda item: ((item.complete_name or item.name or "").lower(), item.id)
            ):
                menu_path = menu.complete_name or menu.name or ""
                action_name = menu.action.name or ""
                if not self._is_match(query, menu.name, menu_path, action_name):
                    continue
                if not self._is_settings_match(mode, menu.name, menu_path, action_name):
                    continue

                menus.append(
                    {
                        "id": menu.id,
                        "name": menu.name or menu_path,
                        "path": menu_path,
                        "action_id": menu.action.id,
                        "menu_id": menu.id,
                    }
                )
                if len(menus) >= limit:
                    break

        actions = []
        if mode in {"all", "actions", "settings"}:
            seen_action_ids = set()
            for menu in launchable_menus.sorted(
                lambda item: ((item.complete_name or item.name or "").lower(), item.id)
            ):
                action = menu.action
                if not action or action._name != "ir.actions.act_window":
                    continue
                if action.id in seen_action_ids:
                    continue

                action_name = action.name or menu.name or ""
                menu_path = menu.complete_name or menu.name or ""
                if not self._is_match(query, action_name, menu_path):
                    continue
                if not self._is_settings_match(mode, action_name, menu_path):
                    continue

                seen_action_ids.add(action.id)
                actions.append(
                    {
                        "id": action.id,
                        "name": action_name,
                        "path": menu_path,
                        "action_id": action.id,
                        "menu_id": menu.id,
                    }
                )
                if len(actions) >= limit:
                    break

        return {"apps": apps, "menus": menus, "actions": actions}
