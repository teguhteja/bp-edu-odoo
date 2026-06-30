from odoo import models, fields


class TtmTenantGroup(models.Model):
    _name = 'ttm.tenant.group'
    _description = 'TTM Tenant Group'
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Nama Group', required=True)
    color = fields.Integer(string='Warna', default=0)
    description = fields.Text(string='Deskripsi')

    tenant_ids = fields.One2many(
        'ttm.tenant',
        'group_tenant_id',
        string='Tenants',
    )
    user_ids = fields.Many2many(
        'res.users',
        'ttm_tenant_group_user_rel',
        'group_id', 'user_id',
        string='Users',
        domain=[('share', '=', False)],
    )

    tenant_count = fields.Integer(compute='_compute_counts', string='Tenant')
    user_count = fields.Integer(compute='_compute_counts', string='User')

    def _compute_counts(self):
        for rec in self:
            rec.tenant_count = len(rec.tenant_ids)
            rec.user_count = len(rec.user_ids)
