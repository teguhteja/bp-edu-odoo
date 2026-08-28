/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";

export class LanguageSwitcher extends Component {
    setup() {
        this.orm = useService("orm");
        this.user = useService("user");
        this.state = useState({
            languages: [],
            currentLang: null,
        });

        onWillStart(async () => {
            await this._loadLanguages();
        });
    }

    async _loadLanguages() {
        const langs = await this.orm.searchRead(
            "res.lang",
            [["active", "=", true]],
            ["code", "name", "flag_image_url"],
            { order: "name asc" }
        );
        this.state.languages = langs;
        const currentCode = this.user.lang;
        this.state.currentLang = langs.find((l) => l.code === currentCode) || langs[0];
    }

    get currentFlagUrl() {
        if (this.state.currentLang) {
            return this.state.currentLang.flag_image_url;
        }
        return null;
    }

    get currentLangCode() {
        if (this.state.currentLang) {
            return this.state.currentLang.code.split("_")[0].toUpperCase();
        }
        return "";
    }

    async switchLanguage(lang) {
        if (lang.code === this.user.lang) {
            return;
        }
        await this.orm.write("res.users", [this.user.userId], { lang: lang.code });
        browser.location.reload();
    }
}

LanguageSwitcher.template = "fast_language_switcher.LanguageSwitcher";
LanguageSwitcher.components = { Dropdown, DropdownItem };
LanguageSwitcher.props = {};

registry.category("systray").add(
    "fast_language_switcher.language_switcher",
    { Component: LanguageSwitcher },
    { sequence: 1 }
);
