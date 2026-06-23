# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class Document(models.Model):
    _name = "document.document"
    _description = 'Document'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence,id'
    _order = 'parent_id,sequence,id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    parent_path = fields.Char(index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=0)
    color = fields.Integer()
    name = fields.Char('Name', required=True)
    full_name = fields.Char('Full Name', compute='_compute_full_name')
    description = fields.Char('Description')
    content = fields.Html('Content')
    parent_id = fields.Many2one('document.document', "Parent", ondelete="cascade", index=True)
    parent_full_name = fields.Char("Path", related='parent_id.full_name')
    child_ids = fields.One2many('document.document', 'parent_id', string='Child')
    child_count = fields.Integer(compute='_compute_child_count', string='Child Count')

    _uniq_name = models.Constraint(
        'unique(parent_id, name)',
        'Name already exists!',
    )

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(_('Parent already recursive!'))

    def _compute_child_count(self):
        count_list = self.env['document.document']._read_group(
            [('parent_id', 'in', self.ids)],
            ['parent_id'],
            ['__count'],
        )
        mapped_data = {parent.id: count for parent, count in count_list}
        for record in self:
            record.child_count = mapped_data.get(record.id, 0)

    def _compute_display_name(self):
        if self.env.context.get('display_full_name', False):
            for record in self:
                parts = []
                r = record
                while r:
                    parts.append(r.name or '')
                    r = r.parent_id
                record.display_name = " / ".join(reversed(parts))
        else:
            super()._compute_display_name()

    def _compute_full_name(self):
        for record in self:
            parts = []
            r = record
            while r:
                parts.append(r.name or '')
                r = r.parent_id
            record.full_name = " / ".join(reversed(parts))

    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default=default)
        if 'name' not in default:
            for rec, vals in zip(self, vals_list):
                vals['name'] = _("%s (copy)", rec.name)
        return vals_list

    def action(self):
        self.ensure_one()
        context = self.env.context
        action_id = context.get('module_action_id')
        if action_id:
            action_dict = self.env.ref(action_id).read([
                "type", "res_model", "view_mode", "domain"
            ])[0]
            action_dict["name"] = self.name
        return action_dict
