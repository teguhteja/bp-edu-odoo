/** @odoo-module **/

import { DefaultCommandItem } from "@web/core/commands/command_palette";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { fuzzyLookup } from "@web/core/utils/search";
import { Component } from "@odoo/owl";

const SEARCH_LIMIT = 20;
const SEARCH_CACHE_TTL = 30_000;
const SEARCH_CACHE_MAX_SIZE = 40;

const searchCache = new Map();
const commandModes = new Set(["apps", "menus", "actions", "settings"]);

const commandCategoryRegistry = registry.category("command_categories");
commandCategoryRegistry.add("apps", { namespace: "/", name: _t("Apps") }, { force: true, sequence: 10 });
commandCategoryRegistry.add(
    "menu_items",
    { namespace: "/", name: _t("Menus") },
    { force: true, sequence: 20 }
);
commandCategoryRegistry.add(
    "window_actions",
    { namespace: "/", name: _t("Actions") },
    { force: true, sequence: 30 }
);

const commandSetupRegistry = registry.category("command_setup");
commandSetupRegistry.add(
    "/",
    {
        emptyMessage: _t("No apps, menus, or actions found"),
        debounceDelay: 300,
        name: _t("resources"),
        placeholder: _t("Search apps, menus, actions or use: apps, menus, actions, settings"),
    },
    { force: true }
);

class CommandPaletteResourceItem extends Component {
    static template = "atliis_app_launcher.CommandPaletteResourceItem";
    static props = {
        iconUrl: { type: String, optional: true },
        kind: { type: String, optional: true },
        subtitle: { type: String, optional: true },
        ...DefaultCommandItem.props,
    };
}

function parseSlashQuery(searchValue) {
    const value = (searchValue || "").trim();
    if (!value) {
        return { mode: "all", query: "" };
    }
    const [token, ...remainingTokens] = value.split(/\s+/);
    const normalizedToken = token.toLowerCase();
    if (commandModes.has(normalizedToken)) {
        return {
            mode: normalizedToken,
            query: remainingTokens.join(" ").trim(),
        };
    }
    return { mode: "all", query: value };
}

function buildHref(entry) {
    if (entry.action_id && entry.menu_id) {
        return `/odoo/action-${entry.action_id}?menu_id=${entry.menu_id}`;
    }
    if (entry.action_id) {
        return `/odoo/action-${entry.action_id}`;
    }
    return undefined;
}

async function openEntry(env, entry) {
    const menuService = env.services.menu;
    const actionService = env.services.action;
    const menu = entry.menu_id ? menuService.getMenu(entry.menu_id) : null;

    if (menu && menu.actionID) {
        await menuService.selectMenu(menu);
        return;
    }

    if (!entry.action_id) {
        return;
    }

    await actionService.doAction(entry.action_id, {
        clearBreadcrumbs: true,
        onActionReady: () => {
            if (menu) {
                menuService.setCurrentMenu(menu);
            }
        },
    });
}

function mapToCommand(env, category, kind, entry, withIcon = false) {
    return {
        Component: CommandPaletteResourceItem,
        action: () => openEntry(env, entry),
        category,
        href: buildHref(entry),
        name: entry.name,
        props: {
            iconUrl: withIcon ? entry.icon_url || entry.default_icon_url : undefined,
            kind,
            subtitle: entry.path,
        },
    };
}

function fuzzyFilter(entries, query) {
    if (!query) {
        return entries;
    }
    return fuzzyLookup(query, entries, (entry) => `${entry.name || ""} ${entry.path || ""}`.trim());
}

async function fetchSearchResults(query, mode) {
    const key = `${mode}::${query}`;
    const now = Date.now();
    const cached = searchCache.get(key);
    if (cached && now - cached.timestamp <= SEARCH_CACHE_TTL) {
        return cached.payload;
    }

    const payload = await rpc("/command_palette/search", {
        query,
        mode,
        limit: SEARCH_LIMIT,
    });

    searchCache.set(key, { timestamp: now, payload });
    if (searchCache.size > SEARCH_CACHE_MAX_SIZE) {
        const oldestKey = searchCache.keys().next().value;
        if (oldestKey) {
            searchCache.delete(oldestKey);
        }
    }

    return payload;
}

const commandProviderRegistry = registry.category("command_provider");
commandProviderRegistry.add(
    "menu",
    {
        namespace: "/",
        async provide(env, options = {}) {
            const { mode, query } = parseSlashQuery(options.searchValue);
            const payload = await fetchSearchResults(query, mode);

            const apps = fuzzyFilter(payload.apps || [], query).map((entry) =>
                mapToCommand(env, "apps", _t("App"), entry, true)
            );
            const menus = fuzzyFilter(payload.menus || [], query).map((entry) =>
                mapToCommand(env, "menu_items", _t("Menu"), entry)
            );
            const actions = fuzzyFilter(payload.actions || [], query).map((entry) =>
                mapToCommand(env, "window_actions", _t("Action"), entry)
            );

            return [...apps, ...menus, ...actions];
        },
    },
    { force: true }
);
