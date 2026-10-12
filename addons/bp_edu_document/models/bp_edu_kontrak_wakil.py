from odoo import api, fields, models


class BpEduKontrakWakil(models.Model):
    _inherit = 'bp.edu.kontrak.kuliah'

    wakil_mahasiswa_id = fields.Many2one(
        'bp.edu.mahasiswa', string='Wakil Mahasiswa (Data Mahasiswa)',
        compute='_compute_wakil_mahasiswa_id', store=True, readonly=False,
        ondelete='set null', tracking=True,
        domain="[('is_wakil_mahasiswa', '=', True)]",
        help='Otomatis diisi dari mahasiswa yang ditandai Wakil Mahasiswa '
             'pada program studi mata kuliah ini.',
    )

    wakil_mahasiswa_tanda_tangan = fields.Binary(
        related='wakil_mahasiswa_id.tanda_tangan', string='Tanda Tangan Wakil')

    @api.depends('mata_kuliah_id.prodi_id')
    def _compute_wakil_mahasiswa_id(self):
        for rec in self:
            if not rec.wakil_mahasiswa_id or not rec.wakil_mahasiswa_id.is_wakil_mahasiswa:
                rec.wakil_mahasiswa_id = rec._find_default_wakil()

    def _find_default_wakil(self):
        self.ensure_one()
        prodi = self.mata_kuliah_id.prodi_id
        if not prodi:
            return False
        return self.env['bp.edu.mahasiswa'].search(
            [('is_wakil_mahasiswa', '=', True), ('prodi_id', '=', prodi.id)], limit=1)


class BpEduMahasiswaWakil(models.Model):
    _inherit = 'bp.edu.mahasiswa'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered('is_wakil_mahasiswa')._sync_kontrak_wakil()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'is_wakil_mahasiswa' in vals or 'prodi_id' in vals:
            self._sync_kontrak_wakil()
        return res

    def _sync_kontrak_wakil(self):
        Kontrak = self.env['bp.edu.kontrak.kuliah'].sudo()
        # Kontrak yang wakilnya tidak lagi berstatus wakil -> cari pengganti
        lepas = Kontrak.search([('wakil_mahasiswa_id', 'in', self.filtered(lambda m: not m.is_wakil_mahasiswa).ids)])
        # Kontrak di prodi wakil baru yang belum punya wakil
        kosong = Kontrak.search([
            ('wakil_mahasiswa_id', '=', False),
            ('mata_kuliah_id.prodi_id', 'in', self.filtered('is_wakil_mahasiswa').prodi_id.ids),
        ])
        for kontrak in lepas | kosong:
            kontrak.wakil_mahasiswa_id = kontrak._find_default_wakil()
