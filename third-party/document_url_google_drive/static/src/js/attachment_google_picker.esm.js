/** @odoo-module **/
// Copyright (C) 2023 Cetmix OÜ
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
// Migrated to the Odoo 19 Chatter (OWL, non-messaging) architecture.

import { Chatter } from "@mail/chatter/web_portal/chatter";
import { loadJS } from "@web/core/assets";
import { onWillStart, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

patch(Chatter.prototype, {
    setup() {
        super.setup(...arguments);
        this.googleOrm = useService("orm");
        this.googlePicker = useState({
            pickerInited: false,
            gisInited: false,
            api_key: "",
            scopes: "",
            client_id: "",
            app_id: "",
            mime_types: "",
            accessToken: null,
            expiresDate: 0,
        });
        this.googleTokenClient = null;

        onWillStart(async () => {
            await this.getGooglePickerParams();
            if (!this.googlePickerActive) {
                return;
            }
            await loadJS("https://apis.google.com/js/api.js", {
                attrs: { async: true, defer: true },
            });
            await this.googleGapiLoaded();
            await loadJS("https://accounts.google.com/gsi/client", {
                attrs: { async: true, defer: true },
            });
            await this.googleGisLoaded();
        });
    },

    get googlePickerActive() {
        return Boolean(
            this.googlePicker.api_key &&
                this.googlePicker.scopes &&
                this.googlePicker.client_id &&
                this.googlePicker.app_id
        );
    },

    async onClickAddGoogleDrive() {
        if (
            this.googlePicker.accessToken &&
            this.googlePicker.expiresDate > Math.floor(Date.now() / 1000)
        ) {
            await this.googleCreatePicker();
        } else {
            this.googleHandleAuthClick();
        }
    },

    async onClickGoogleSignOut() {
        this.googlePicker.accessToken = null;
        await this.saveGooglePickerAccessToken();
    },

    // --------------------------------------------------------------------------
    // Private
    // --------------------------------------------------------------------------

    async getGooglePickerParams() {
        const res = await this.googleOrm.call("res.users", "get_google_picker_params", [
            user.userId,
        ]);
        if (!res) {
            return;
        }
        Object.assign(this.googlePicker, {
            client_id: res.client_id,
            api_key: res.api_key,
            app_id: res.app_id,
            scopes: res.scope,
            accessToken: res.access_token,
            expiresDate: res.expires_date,
            mime_types: res.mime_types,
        });
    },

    async saveGooglePickerAccessToken() {
        await this.googleOrm.call("res.users", "save_google_picker_access_token", [
            user.userId,
            this.googlePicker.accessToken,
            this.googlePicker.expiresDate,
        ]);
    },

    async googleGapiLoaded() {
        window.gapi.load("client:picker", this.googleInitializePicker.bind(this));
    },

    async googleInitializePicker() {
        await window.gapi.client.load(
            "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"
        );
        this.googlePicker.pickerInited = true;
    },

    async googleGisLoaded() {
        this.googleTokenClient = window.google.accounts.oauth2.initTokenClient({
            client_id: this.googlePicker.client_id,
            scope: this.googlePicker.scopes,
            callback: "",
        });
        this.googlePicker.gisInited = true;
    },

    googleHandleAuthClick() {
        this.googleTokenClient.callback = async (response) => {
            if (response.error !== undefined) {
                throw response;
            }
            this.googlePicker.accessToken = response.access_token;
            this.googlePicker.expiresDate =
                Math.floor(Date.now() / 1000) + response.expires_in;
            await this.googleCreatePicker();
            await this.saveGooglePickerAccessToken();
        };

        if (this.googlePicker.accessToken === null) {
            // Prompt the user to select a Google Account and ask for consent to
            // share their data when establishing a new session.
            this.googleTokenClient.requestAccessToken({
                prompt: "consent",
                access_type: "offline",
            });
        } else {
            // Skip display of account chooser and consent dialog for an existing session.
            this.googleTokenClient.requestAccessToken({ prompt: "", access_type: "offline" });
        }
    },

    googleCreatePicker() {
        const view = new window.google.picker.View(window.google.picker.ViewId.DOCS);
        if (this.googlePicker.mime_types) {
            view.setMimeTypes(this.googlePicker.mime_types);
        }
        const picker = new window.google.picker.PickerBuilder()
            .enableFeature(window.google.picker.Feature.NAV_HIDDEN)
            .enableFeature(window.google.picker.Feature.MULTISELECT_ENABLED)
            .setDeveloperKey(this.googlePicker.api_key)
            .setAppId(this.googlePicker.app_id)
            .setOAuthToken(this.googlePicker.accessToken)
            .addView(view)
            .addView(new window.google.picker.DocsUploadView())
            .setCallback(this.googlePickerCallback.bind(this))
            .build();
        picker.setVisible(true);
    },

    async googlePickerCallback(data) {
        if (data.action === window.google.picker.Action.PICKED) {
            for (const document of data.docs) {
                await this.createGoogleDriveAttachment(document);
            }
            this.load(this.state.thread, ["attachments"]);
        }
    },

    async createGoogleDriveAttachment(document) {
        await this.googleOrm.call("ir.attachment.add_url", "add_attachment_google_drive", [
            document.url,
            document.name,
            this.state.thread.model,
            [this.state.thread.id],
        ]);
    },
});
