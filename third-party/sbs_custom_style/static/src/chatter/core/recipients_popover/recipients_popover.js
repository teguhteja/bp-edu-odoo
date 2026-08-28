import { Component } from '@odoo/owl';

export class RecipientsListPopover extends Component {
    static template = 'sbs_custom_style.RecipientsListPopover';
    static props = {
        recipients: { type: Array },
        close: { type: Function, required: true },
    };
}
