from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    group_tenant_ids = fields.Many2many(
        'ttm.tenant.group',
        'ttm_tenant_group_user_rel',
        'user_id', 'group_id',
        string='Tenant Groups',
    )
