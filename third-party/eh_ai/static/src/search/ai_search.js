/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { Domain } from "@web/core/domain";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

// Adds an "Ask AI" suggestion to the search bar that turns the typed text into a
// filter on the current view, matching Enterprise's natural-language search.
patch(SearchBar.prototype, {
    async computeState(options = {}) {
        await super.computeState(options);
        const query = (this.state.query || "").trim();
        if (query) {
            // this.items is a reactive useState array mutated in place by the
            // base class; unshift (do NOT reassign) so reactivity is preserved.
            this.items.unshift({
                id: "eh_ai_ask",
                label: _t("Ask AI: %s", query),
                isEhAiAsk: true,
                unselectable: false,
            });
        }
    },

    async selectItem(item) {
        if (item && item.isEhAiAsk) {
            const query = (this.state.query || "").trim();
            const searchModel = this.env.searchModel;
            const fields = Object.keys(searchModel.searchViewFields || {});
            const close = () => {
                this.inputDropdownState && this.inputDropdownState.close();
                this.resetState();
            };
            let domain = [];
            try {
                const result = await rpc("/eh_ai/nl_search", {
                    model: searchModel.resModel,
                    query,
                    fields,
                });
                domain = result.domain || [];
            } catch (error) {
                const message = (error && error.data && error.data.message) || error.message || String(error);
                this.env.services.notification.add(_t("AI search failed: %s", message), { type: "danger" });
                close();
                return;
            }
            if (domain.length) {
                searchModel.splitAndAddDomain(new Domain(domain).toString());
            } else {
                this.env.services.notification.add(
                    _t("The AI could not turn that into a filter."), { type: "warning" });
            }
            close();
            return;
        }
        return super.selectItem(item);
    },
});
