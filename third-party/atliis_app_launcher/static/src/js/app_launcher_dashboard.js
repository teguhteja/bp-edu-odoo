/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { NavBar } from "@web/webclient/navbar/navbar";
import { Component, onMounted, onWillStart, onWillUnmount, useRef, useState } from "@odoo/owl";

const APP_ORDER_STORAGE_KEY = "app_launcher_dashboard.ordered_app_ids";
const LAUNCHER_ACTION_XMLID = "atliis_app_launcher.action_app_launcher_dashboard";
const LAUNCHER_ACTIVE_BODY_CLASS = "o_app_launcher_active";

class AppLauncherDashboard extends Component {
    static template = "app_launcher_dashboard.AppLauncherDashboard";

    setup() {
        this.actionService = useService("action");
        this.menuService = useService("menu");
        this.notificationService = useService("notification");
        this.ormService = useService("orm");

        this.state = useState({
            apps: [],
            loading: true,
            query: "",
            customOrder: this._loadCustomOrder(),
            searchActiveIndex: 0,
            draggingAppId: null,
            dragOverAppId: null,
        });
        this.searchInputRef = useRef("searchInput");
        this.onGlobalKeyDown = this._onGlobalKeyDown.bind(this);

        onWillStart(async () => {
            if (!this.menuService.getCurrentApp()) {
                const storedMenuId = Number(browser.sessionStorage.getItem("menu_id") || 0);
                if (storedMenuId) {
                    this.menuService.setCurrentMenu(storedMenuId);
                }
            }
            this.state.apps = await this.ormService.call("ir.module.module", "get_app_launcher_apps", []);
            this.state.customOrder = this._sanitizeCustomOrder(this.state.customOrder, this.state.apps);
            this.state.loading = false;
        });

        onMounted(() => {
            document.body.classList.add(LAUNCHER_ACTIVE_BODY_CLASS);
            window.addEventListener("keydown", this.onGlobalKeyDown);
        });
        onWillUnmount(() => {
            document.body.classList.remove(LAUNCHER_ACTIVE_BODY_CLASS);
            window.removeEventListener("keydown", this.onGlobalKeyDown);
        });
    }

    _loadCustomOrder() {
        try {
            const rawOrder = browser.localStorage.getItem(APP_ORDER_STORAGE_KEY);
            if (!rawOrder) {
                return [];
            }
            const parsedOrder = JSON.parse(rawOrder);
            if (!Array.isArray(parsedOrder)) {
                return [];
            }
            return parsedOrder.map((value) => Number(value)).filter((value) => Number.isInteger(value));
        } catch {
            return [];
        }
    }

    _saveCustomOrder() {
        browser.localStorage.setItem(APP_ORDER_STORAGE_KEY, JSON.stringify(this.state.customOrder));
    }

    _sanitizeCustomOrder(order, apps) {
        const appIds = new Set(
            (apps || [])
                .filter((app) => app.entry_type !== "menu")
                .map((app) => app.id)
        );
        const uniqueIds = [];
        const seen = new Set();
        for (const id of order || []) {
            if (appIds.has(id) && !seen.has(id)) {
                seen.add(id);
                uniqueIds.push(id);
            }
        }
        return uniqueIds;
    }

    _normalizedQuery(query) {
        return (query || "").trim().toLowerCase().replace(/^\/+/, "");
    }

    get isSearchMode() {
        return Boolean((this.state.query || "").trim());
    }

    get appCards() {
        const sourceEntries = this.state.apps.filter((app) => app.entry_type !== "menu");
        const sanitizedOrder = this._sanitizeCustomOrder(this.state.customOrder, sourceEntries);
        const orderIndex = new Map(sanitizedOrder.map((id, index) => [id, index]));
        const hasCustomOrder = sanitizedOrder.length > 0;

        return [...sourceEntries].sort((first, second) => {
            if (hasCustomOrder) {
                const firstIndex = orderIndex.has(first.id) ? orderIndex.get(first.id) : Number.MAX_SAFE_INTEGER;
                const secondIndex = orderIndex.has(second.id)
                    ? orderIndex.get(second.id)
                    : Number.MAX_SAFE_INTEGER;
                if (firstIndex !== secondIndex) {
                    return firstIndex - secondIndex;
                }
            }

            return (first.name || "").localeCompare(second.name || "");
        });

    }

    isDragging(appId) {
        return this.state.draggingAppId === appId;
    }

    isDragOver(appId) {
        return this.state.dragOverAppId === appId && this.state.draggingAppId !== appId;
    }

    onAppDragStart(ev, app) {
        this.state.draggingAppId = app.id;
        this.state.dragOverAppId = null;
        if (ev.dataTransfer) {
            ev.dataTransfer.effectAllowed = "move";
            ev.dataTransfer.setData("text/plain", String(app.id));
        }
    }

    onAppDragOver(ev, app) {
        ev.preventDefault();
        this.state.dragOverAppId = app.id;
        if (ev.dataTransfer) {
            ev.dataTransfer.dropEffect = "move";
        }
    }

    onAppDrop(ev, app) {
        ev.preventDefault();
        const draggedId =
            Number(ev.dataTransfer?.getData("text/plain")) || Number(this.state.draggingAppId);
        const targetId = Number(app.id);

        if (!draggedId || !targetId || draggedId === targetId) {
            this.state.dragOverAppId = null;
            return;
        }

        const orderedIds = this.appCards.map((entry) => entry.id);
        const sourceIndex = orderedIds.indexOf(draggedId);
        const targetIndex = orderedIds.indexOf(targetId);

        if (sourceIndex < 0 || targetIndex < 0) {
            this.state.dragOverAppId = null;
            return;
        }

        const nextOrder = [...orderedIds];
        nextOrder.splice(sourceIndex, 1);
        nextOrder.splice(targetIndex, 0, draggedId);

        this.state.customOrder = nextOrder;
        this._saveCustomOrder();
        this.state.dragOverAppId = null;
    }

    onAppDragEnd() {
        this.state.draggingAppId = null;
        this.state.dragOverAppId = null;
    }

    _searchScore(app, normalizedQuery) {
        const name = (app.name || "").toLowerCase();
        const text = (app.search_text || "").toLowerCase();
        let score = 0;

        if (name.startsWith(normalizedQuery)) {
            score += 120;
        } else if (name.includes(normalizedQuery)) {
            score += 80;
        }
        if (text.startsWith(normalizedQuery)) {
            score += 50;
        } else if (text.includes(normalizedQuery)) {
            score += 25;
        }
        if (app.entry_type === "app") {
            score += 15;
        }
        return score;
    }

    _entryTypePriority(app) {
        if (app.entry_type === "app") {
            return 0;
        }
        if (app.entry_type === "menu") {
            return 1;
        }
        return 2;
    }

    get searchResults() {
        const normalizedQuery = this._normalizedQuery(this.state.query);
        if (!normalizedQuery) {
            return [];
        }

        return this.state.apps
            .filter((app) => this._matchesQuery(app, normalizedQuery))
            .map((app) => ({ app, score: this._searchScore(app, normalizedQuery) }))
            .sort((first, second) => {
                const typePriority = this._entryTypePriority(first.app) - this._entryTypePriority(second.app);
                if (typePriority) {
                    return typePriority;
                }
                if (second.score !== first.score) {
                    return second.score - first.score;
                }
                return (first.app.name || "").localeCompare(second.app.name || "");
            })
            .map((entry) => entry.app);
    }

    get activeSearchResultIndex() {
        const size = this.searchResults.length;
        if (!size) {
            return -1;
        }
        return Math.min(this.state.searchActiveIndex, size - 1);
    }

    isActiveResult(index) {
        return index === this.activeSearchResultIndex;
    }

    _resetSearchSelection() {
        this.state.searchActiveIndex = 0;
    }

    _selectSearchResult(index) {
        const size = this.searchResults.length;
        if (!size) {
            this.state.searchActiveIndex = 0;
            return;
        }
        const boundedIndex = Math.max(0, Math.min(index, size - 1));
        this.state.searchActiveIndex = boundedIndex;
    }

    _matchesQuery(app, query) {
        const normalizedQuery = this._normalizedQuery(query);
        if (!normalizedQuery) {
            return true;
        }
        const searchable = `${app.name || ""} ${app.search_text || ""}`.toLowerCase();
        return searchable.includes(normalizedQuery);
    }

    onSearchInput(ev) {
        this.state.query = ev.target.value || "";
        this._resetSearchSelection();
    }

    closeSearchResults() {
        this.state.query = "";
        this._resetSearchSelection();
        if (this.searchInputRef.el) {
            this.searchInputRef.el.value = "";
        }
    }

    onSearchBackdropClick() {
        this.closeSearchResults();
    }

    onSearchKeyDown(ev) {
        const results = this.searchResults;
        if (!results.length) {
            if (ev.key === "Escape") {
                this.closeSearchResults();
                ev.preventDefault();
            }
            return;
        }

        if (ev.key === "ArrowDown") {
            this._selectSearchResult(this.activeSearchResultIndex + 1);
            ev.preventDefault();
            return;
        }

        if (ev.key === "ArrowUp") {
            this._selectSearchResult(this.activeSearchResultIndex - 1);
            ev.preventDefault();
            return;
        }

        if (ev.key === "Enter") {
            const selected = results[this.activeSearchResultIndex];
            if (selected) {
                void this.openApp(selected);
                ev.preventDefault();
            }
            return;
        }

        if (ev.key === "Escape") {
            this.closeSearchResults();
            ev.preventDefault();
        }
    }

    onSearchResultMouseEnter(index) {
        this._selectSearchResult(index);
    }

    _onGlobalKeyDown(ev) {
        if (ev.defaultPrevented || ev.ctrlKey || ev.altKey || ev.metaKey) {
            return;
        }

        const target = ev.target;
        if (
            target &&
            (target.isContentEditable ||
                ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) ||
                target.closest?.(".modal"))
        ) {
            return;
        }

        const searchInput = this.searchInputRef.el;
        if (!searchInput) {
            return;
        }

        const key = ev.key || "";
        if (key.length !== 1 && key !== "Backspace") {
            return;
        }

        searchInput.focus();

        if (key === "Backspace") {
            if (!this.state.query) {
                ev.preventDefault();
                return;
            }
            this.state.query = this.state.query.slice(0, -1);
            searchInput.value = this.state.query;
            this._resetSearchSelection();
            ev.preventDefault();
            return;
        }

        this.state.query = `${this.state.query}${key}`;
        searchInput.value = this.state.query;
        this._resetSearchSelection();
        ev.preventDefault();
    }

    onImageError(ev) {
        const image = ev.currentTarget;
        if (image.dataset.fallbackApplied === "1") {
            return;
        }
        image.dataset.fallbackApplied = "1";
        image.src = image.dataset.defaultIcon;
    }

    async openApp(app) {
        const menu = app.menu_id ? this.menuService.getMenu(app.menu_id) : null;
        if (menu && menu.actionID) {
            await this.menuService.selectMenu(menu);
            return;
        }

        if (!app.action_id) {
            this.notificationService.add(_t("No main action is configured for this application."), {
                type: "warning",
            });
            return;
        }

        await this.actionService.doAction(app.action_id, {
            clearBreadcrumbs: true,
            onActionReady: () => {
                if (menu) {
                    this.menuService.setCurrentMenu(menu);
                }
            },
        });
    }
}

registry.category("actions").add("app_launcher_dashboard.client_action", AppLauncherDashboard);

patch(NavBar.prototype, {
    async onAppLauncherHomeClick(ev) {
        if (ev) {
            ev.preventDefault();
            ev.stopPropagation();
        }
        const currentAction = this.actionService.currentController?.action;
        if (
            currentAction?.type === "ir.actions.client" &&
            currentAction?.tag === "app_launcher_dashboard.client_action"
        ) {
            return;
        }
        const currentApp = this.menuService.getCurrentApp();
        await this.actionService.doAction(LAUNCHER_ACTION_XMLID, {
            clearBreadcrumbs: true,
        });
        if (currentApp) {
            this.menuService.setCurrentMenu(currentApp);
        }
    },
});
