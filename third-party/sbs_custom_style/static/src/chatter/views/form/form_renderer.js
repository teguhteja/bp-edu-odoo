import { useState, useRef } from '@odoo/owl';
import { patch } from '@web/core/utils/patch';
import { browser } from "@web/core/browser/browser";

import { FormRenderer } from '@web/views/form/form_renderer';

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        this.sbsChatterState = useState({
            width: browser.localStorage.getItem('sbs_custom_style.width'),
        });
        this.sbsChatterContainer = useRef('sbsChatterContainer');
    },
    onStartSbsChatterResize(ev) {
        if (ev.button !== 0) {
            return;
        }
        const initialX = ev.pageX;
        const chatterElement = this.sbsChatterContainer.el;
        const initialWidth = chatterElement.offsetWidth;
        const resizeStoppingEvents = [
            'keydown', 'mousedown', 'mouseup'
        ];
        const resizePanel = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            const newWidth = Math.min(
                Math.max(50, initialWidth - (ev.pageX - initialX)),
                Math.max(chatterElement.parentElement.offsetWidth - 250, 250)
            );
            browser.localStorage.setItem('sbs_custom_style.width', newWidth);
            this.sbsChatterState.width = newWidth;
        };
        const stopResize = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            if (ev.type === 'mousedown' && ev.button === 0) {
                return;
            }
            document.removeEventListener('mousemove', resizePanel, true);
            resizeStoppingEvents.forEach((stoppingEvent) => {
                document.removeEventListener(stoppingEvent, stopResize, true);
            });
            document.activeElement.blur();
        };
        document.addEventListener('mousemove', resizePanel, true);
        resizeStoppingEvents.forEach((stoppingEvent) => {
            document.addEventListener(stoppingEvent, stopResize, true);
        });
    },
    onDoubleClickSbsChatterResize(ev) {
        browser.localStorage.removeItem('sbs_custom_style.width');
        this.sbsChatterState.width = false;
    },
});
