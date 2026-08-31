import html
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

_GDRIVE_FILE_ID_RE = re.compile(r'/file/d/([\w-]+)')


class DmsFile(models.Model):
    _inherit = 'dms.file'

    gdrive_url = fields.Char(string='Link Google Drive')
    gdrive_preview_html = fields.Html(
        string='Preview', compute='_compute_gdrive_preview_html', sanitize=False,
    )

    @api.depends('gdrive_url')
    def _compute_gdrive_preview_html(self):
        for rec in self:
            preview_url = rec._gdrive_preview_url()
            rec.gdrive_preview_html = (
                '<iframe src="%s" style="width:100%%;height:480px;border:0;"></iframe>'
                % html.escape(preview_url, quote=True)
            ) if preview_url else False

    def _gdrive_preview_url(self):
        self.ensure_one()
        if not self.gdrive_url:
            return False
        match = _GDRIVE_FILE_ID_RE.search(self.gdrive_url)
        if not match:
            return False
        return 'https://drive.google.com/file/d/%s/preview' % match.group(1)

    def action_open_gdrive_link(self):
        self.ensure_one()
        if not self.gdrive_url:
            return False
        return {
            'type': 'ir.actions.act_url',
            'url': self.gdrive_url,
            'target': 'new',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('content') and not vals.get('gdrive_url'):
                raise UserError(
                    "Sorry, we can't upload your ebook to the server. "
                    "Please put it in Google Drive instead."
                )
        return super().create(vals_list)
