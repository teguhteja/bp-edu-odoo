import { browser } from '@web/core/browser/browser';
import { useBus } from '@web/core/utils/hooks';
import { patch } from '@web/core/utils/patch';

import { ControlPanel } from '@web/search/control_panel/control_panel';

import { getAutoLoadInterval } from '@sbs_custom_style/refresh/core/utils';
import { REFRESH_VIEW_EVENT } from '@sbs_custom_style/refresh/services/refresh_service';

import { useState, onWillDestroy, useEffect } from '@odoo/owl';

function useRefreshAnimation(timeout) {
    let timeoutId = null;

    function contentClassList() {
        const content = document.querySelector('.o_content');
        return content ? content.classList : null;
    }

    function clearAnimationTimeout() {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }
        timeoutId = null;
    }

    function animate() {
        clearAnimationTimeout();
        const classList = contentClassList();
        if (classList) {
            classList.add('sbs_refresh');
            timeoutId = setTimeout(() => {
                classList.remove('sbs_refresh');
                clearAnimationTimeout();
            }, timeout);
        }
    }

    return animate;
}

patch(ControlPanel.prototype, {
    setup() {
        super.setup();
        this._sbsClickTimeout = null;
        this.sbsRefreshAnimation = useRefreshAnimation(600);
        useBus(this.env.bus, REFRESH_VIEW_EVENT, () => {
            this.sbsRefreshView();
        });
        this.sbsAutoLoadState = useState({
            active: (
                this.sbsCheckAutoLoadAvailability() &&
                !!this.sbsGetAutoLoadStorageValue()
            ),
            counter: 0,
        });
        onWillDestroy(() => {
            if (this._sbsClickTimeout) {
                clearTimeout(this._sbsClickTimeout);
            }
        });
        useEffect(
            () => {
                if (!this.sbsAutoLoadState.active) {
                    return;
                }
                this.sbsAutoLoadState.counter = (
                    this.sbsGetAutoLoadRefreshInterval()
                );
                const interval = browser.setInterval(
                    () => {
                        this.sbsAutoLoadState.counter = (
                            this.sbsAutoLoadState.counter ?
                            this.sbsAutoLoadState.counter - 1 :
                            this.sbsGetAutoLoadRefreshInterval()
                        );
                        if (this.sbsAutoLoadState.counter <= 0) {
                            this.sbsAutoLoadState.counter = (
                                this.sbsGetAutoLoadRefreshInterval()
                            );
                            this.sbsRefreshView();
                        }
                    },
                    1000
                );
                return () => browser.clearInterval(interval);
            },
            () => [this.sbsAutoLoadState.active]
        );
    },
    sbsCheckAutoLoadAvailability() {
        return ['kanban', 'list'].includes(
            this.env.config.viewType
        );
    },
    sbsCheckRefreshAvailability() {
        return !['base_settings'].includes(
            this.env.config.viewSubType
        );
    },
    sbsGetAutoLoadRefreshInterval() {
        return getAutoLoadInterval() / 1000;
    },
    sbsGetAutoLoadStorageKey() {
        const keys = [
            this.env?.config?.actionId ?? '',
            this.env?.config?.viewType ?? '',
            this.env?.config?.viewId ?? '',
        ];
        return `sbs_custom_style.pager_autoload:${keys.join(',')}`;
    },
    sbsGetAutoLoadStorageValue() {
        return browser.localStorage.getItem(
            this.sbsGetAutoLoadStorageKey()
        );
    },
    sbsSetAutoLoadStorageValue() {
        browser.localStorage.setItem(
            this.sbsGetAutoLoadStorageKey(), true
        );
    },
    sbsRemoveAutoLoadStorageValue() {
        browser.localStorage.removeItem(
            this.sbsGetAutoLoadStorageKey()
        );
    },
    sbsToggleAutoLoad() {
        this.sbsAutoLoadState.active = (
            !this.sbsAutoLoadState.active
        );
        if (this.sbsAutoLoadState.active) {
            this.sbsSetAutoLoadStorageValue();
        } else {
            this.sbsRemoveAutoLoadStorageValue();
        }
    },
    async sbsRefreshView() {
        if (this.pagerProps?.onUpdate) {
            await this.pagerProps.onUpdate({
                offset: this.pagerProps.offset,
                limit: this.pagerProps.limit,
            });
            return true;
        }
        if (typeof this.env.searchModel?.search === 'function') {
            this.env.searchModel.search();
            return true;
        }
        return false;
    },
    onClickSbsRefresh() {
        if (this._sbsClickTimeout) {
            clearTimeout(this._sbsClickTimeout);
            this._sbsClickTimeout = null;
        }
        this._sbsClickTimeout = setTimeout(
            async () => {
                this._sbsClickTimeout = null;
                if (await this.sbsRefreshView()) {
                    this.sbsRefreshAnimation();
                }
            },
            300
        );
    },
    onDblClickSbsRefresh() {
        if (this._sbsClickTimeout) {
            clearTimeout(this._sbsClickTimeout);
            this._sbsClickTimeout = null;
        }
        if (this.sbsCheckAutoLoadAvailability()) {
            this.sbsToggleAutoLoad();
        }
    },
});
