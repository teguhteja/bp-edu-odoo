from collections import defaultdict, deque

from odoo import api, models

DEFAULT_ICON_URL = "/atliis_app_launcher/static/src/img/default_app.svg"


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def _normalize_icon_url(self, icon_path):
        if not icon_path:
            return False
        if icon_path.startswith(("http://", "https://", "/")):
            return icon_path
        return f"/{icon_path}"

    @api.model
    def _menu_icon_url(self, menu):
        """Build a static icon URL from menu.web_icon when available."""
        if not menu.web_icon:
            return False
        parts = [part.strip() for part in menu.web_icon.split(",")]
        if len(parts) != 2:
            return False
        module_name, icon_relative_path = parts
        if not module_name or not icon_relative_path:
            return False
        return f"/{module_name}/{icon_relative_path.lstrip('/')}"

    @api.model
    def _select_app_menu(self, menus):
        if not menus:
            return self.env["ir.ui.menu"]

        root_menus = menus.filtered(lambda menu: not menu.parent_id)
        if root_menus:
            return root_menus.sorted(lambda menu: (menu.sequence, menu.id))[:1]

        return menus.sorted(
            lambda menu: ((menu.parent_path or "").count("/"), menu.sequence, menu.id)
        )[:1]

    @api.model
    def _resolve_launch_target(self, app_menu, children_map):
        """Return (action_id, menu_id) using app_menu then visible descendants."""
        if not app_menu:
            return False, False

        queue = deque([app_menu])
        while queue:
            current = queue.popleft()
            if current.action:
                return current.action.id, current.id
            queue.extend(children_map.get(current.id, []))

        return False, app_menu.id

    @api.model
    def _build_special_card(
        self,
        entry_id,
        key,
        label,
        launch_menu,
        children_map,
        default_icon,
        icon_url=False,
        fallback_action=False,
    ):
        """Build non-module launcher card (e.g. Apps, Settings) from a visible menu."""
        if not launch_menu:
            return False
        action_id, launch_menu_id = self._resolve_launch_target(
            launch_menu, children_map
        )
        action_id = action_id or fallback_action
        return {
            "id": entry_id,
            "module": f"__{key}__",
            "name": label,
            "action_id": action_id,
            "menu_id": launch_menu_id,
            "icon_url": icon_url or self._menu_icon_url(launch_menu) or default_icon,
            "default_icon_url": DEFAULT_ICON_URL,
            "entry_type": "app",
            "search_text": label,
        }

    @api.model
    def get_app_launcher_apps(self):
        """Return launcher entries for installed apps plus searchable visible menus."""
        Menu = self.env["ir.ui.menu"]
        Module = self.env["ir.module.module"]

        visible_menus = Menu.search([])._filter_visible_menus()
        if not visible_menus:
            return []

        menu_by_id = {menu.id: menu for menu in visible_menus}
        children_map = defaultdict(list)
        for menu in visible_menus:
            if menu.parent_id and menu.parent_id.id in menu_by_id:
                children_map[menu.parent_id.id].append(menu)
        for parent_id in children_map:
            children_map[parent_id].sort(key=lambda child: (child.sequence, child.id))

        def get_visible_menu(xmlid):
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            return menu_by_id.get(menu.id) if menu else False

        special_entries = []
        special_menu_specs = [
            (
                -1001,
                "apps",
                "Apps",
                "base.menu_management",
                "base.menu_module_tree",
                "base.open_module_tree",
                "/base/static/description/modules.png",
            ),
            (
                -1002,
                "settings",
                "Settings",
                "base.menu_administration",
                "base_setup.menu_config",
                "base_setup.action_general_configuration",
                "/base/static/description/settings.png",
            ),
        ]
        for (
            entry_id,
            key,
            label,
            root_menu_xmlid,
            launch_menu_xmlid,
            action_xmlid,
            default_icon,
        ) in special_menu_specs:
            root_menu = get_visible_menu(root_menu_xmlid)
            if not root_menu:
                continue
            launch_menu = get_visible_menu(launch_menu_xmlid) or root_menu
            action = self.env.ref(action_xmlid, raise_if_not_found=False)
            entry = self._build_special_card(
                entry_id=entry_id,
                key=key,
                label=label,
                launch_menu=launch_menu,
                children_map=children_map,
                default_icon=default_icon,
                icon_url=self._menu_icon_url(root_menu),
                fallback_action=action.id if action else False,
            )
            if entry:
                special_entries.append(entry)

        installed_apps = Module.sudo().search(
            [("state", "=", "installed"), ("application", "=", True)],
            order="sequence, shortdesc, name",
        )

        module_names = installed_apps.mapped("name")
        menu_imd_records = (
            self.env["ir.model.data"]
            .sudo()
            .search(
                [
                    ("model", "=", "ir.ui.menu"),
                    ("module", "in", module_names),
                    ("res_id", "in", list(menu_by_id.keys())),
                ]
            )
        )

        menus_by_module = defaultdict(lambda: self.env["ir.ui.menu"])
        for imd in menu_imd_records:
            menu = menu_by_id.get(imd.res_id)
            if menu:
                menus_by_module[imd.module] |= menu

        launcher_apps = list(special_entries)
        app_menu_ids = {
            entry["menu_id"] for entry in special_entries if entry.get("menu_id")
        }
        for module in installed_apps:
            module_menus = menus_by_module.get(module.name, self.env["ir.ui.menu"])
            app_menu = self._select_app_menu(module_menus)
            if not app_menu:
                continue

            action_id, launch_menu_id = self._resolve_launch_target(
                app_menu[0], children_map
            )

            module_action_id = False
            if "action_id" in module._fields and module.action_id:
                module_action_id = module.action_id.id

            app_menu_ids.add(app_menu[0].id)
            if launch_menu_id:
                app_menu_ids.add(launch_menu_id)

            app_name = app_menu[0].name or module.shortdesc or module.name
            launcher_apps.append(
                {
                    "id": module.id,
                    "module": module.name,
                    "name": app_name,
                    "action_id": module_action_id or action_id,
                    "menu_id": launch_menu_id,
                    "icon_url": (
                        self._menu_icon_url(app_menu[0])
                        or self._normalize_icon_url(module.icon)
                        or f"/{module.name}/static/description/icon.png"
                    ),
                    "default_icon_url": DEFAULT_ICON_URL,
                    "entry_type": "app",
                    "search_text": " ".join(
                        part
                        for part in [
                            app_name,
                            module.shortdesc,
                            module.name,
                            app_menu[0].complete_name,
                        ]
                        if part
                    ),
                }
            )

        menu_entries = []
        for menu in visible_menus.sorted(
            lambda item: ((item.complete_name or item.name or "").lower(), item.id)
        ):
            if menu.id in app_menu_ids:
                continue

            action_id, launch_menu_id = self._resolve_launch_target(menu, children_map)
            if not action_id:
                continue

            menu_entries.append(
                {
                    "id": -1000000000 - menu.id,
                    "module": "__menu__",
                    "name": menu.complete_name or menu.name,
                    "action_id": action_id,
                    "menu_id": launch_menu_id or menu.id,
                    "icon_url": self._menu_icon_url(menu) or DEFAULT_ICON_URL,
                    "default_icon_url": DEFAULT_ICON_URL,
                    "entry_type": "menu",
                    "search_text": " ".join(
                        part
                        for part in [menu.name, menu.complete_name]
                        if part
                    ),
                }
            )

        return launcher_apps + menu_entries
