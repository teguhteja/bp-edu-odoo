import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BpEduSap(models.Model):
    _name = 'bp.edu.sap'
    _description = 'Satuan Acara Perkuliahan'
    _rec_name = 'display_name'
    _order = 'tahun_akademik_id desc, mata_kuliah_id'

    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='restrict',
    )
    rps_id = fields.Many2one(
        'bp.edu.rps', string='RPS Terkait',
        domain="[('mata_kuliah_id', '=', mata_kuliah_id)]",
        ondelete='set null',
    )
    dosen_id = fields.Many2one(
        'bp.edu.dosen', string='Dosen Pengampu',
        ondelete='restrict',
    )
    tahun_akademik_id = fields.Many2one(
        'bp.edu.tahun.akademik', string='Tahun Akademik',
        ondelete='restrict',
    )

    kode_mk = fields.Char(related='mata_kuliah_id.kode', store=True)

    pertemuan_ids = fields.One2many('bp.edu.sap.pertemuan', 'sap_id', string='Pertemuan')

    def _compute_display_name(self):
        for rec in self:
            mk = rec.mata_kuliah_id.display_name if rec.mata_kuliah_id else '?'
            ta = rec.tahun_akademik_id.display_name if rec.tahun_akademik_id else ''
            rec.display_name = f'SAP – {mk} ({ta})' if ta else f'SAP – {mk}'

    def action_buat_pertemuan_kosong(self):
        """Buat 16 baris pertemuan kosong jika belum ada."""
        self.ensure_one()
        if self.pertemuan_ids:
            raise ValidationError('Pertemuan sudah ada. Hapus terlebih dahulu sebelum generate ulang.')
        vals = [{'sap_id': self.id, 'no': i} for i in range(1, 17)]
        self.env['bp.edu.sap.pertemuan'].create(vals)


class BpEduSapPertemuan(models.Model):
    _name = 'bp.edu.sap.pertemuan'
    _description = 'Detail Pertemuan SAP'
    _rec_name = 'no'
    _order = 'sap_id, no'

    sap_id = fields.Many2one(
        'bp.edu.sap', string='SAP',
        required=True, ondelete='cascade',
    )
    no = fields.Integer(string='No. Pertemuan', required=True)
    waktu_pertemuan = fields.Char(string='Waktu Pertemuan', help='Contoh: Kuliah TM: 2x50')

    # Capaian
    detail_cpmk = fields.Text(string='CPMK')
    detail_sub_cpmk = fields.Text(string='Sub-CPMK')

    # Indikator & Tujuan
    indikator_1 = fields.Text(string='Indikator 1')
    indikator_2 = fields.Text(string='Indikator 2')
    tujuan_pembelajaran = fields.Text(string='Tujuan Pembelajaran')

    # Materi
    pokok_bahasan = fields.Char(string='Pokok Bahasan')
    sub_pokok_bahasan_1 = fields.Char(string='Sub-Pokok Bahasan 1')
    sub_pokok_bahasan_2 = fields.Char(string='Sub-Pokok Bahasan 2')

    # Kegiatan Pembelajaran (di-flatten dari nested JSON)
    pendahuluan_pengajar = fields.Text(string='Pendahuluan – Pengajar')
    pendahuluan_mahasiswa = fields.Text(string='Pendahuluan – Mahasiswa')
    pendahuluan_media = fields.Text(string='Pendahuluan – Media')

    penyajian_pengajar = fields.Text(string='Penyajian – Pengajar')
    penyajian_mahasiswa = fields.Text(string='Penyajian – Mahasiswa')
    penyajian_media = fields.Text(string='Penyajian – Media')

    penutup_pengajar = fields.Text(string='Penutup – Pengajar')
    penutup_mahasiswa = fields.Text(string='Penutup – Mahasiswa')
    penutup_media = fields.Text(string='Penutup – Media')

    # Evaluasi & Referensi
    evaluasi_1 = fields.Text(string='Evaluasi 1')
    evaluasi_2 = fields.Text(string='Evaluasi 2')
    referensi_1 = fields.Text(string='Referensi 1')
    referensi_2 = fields.Text(string='Referensi 2')

    @api.constrains('no')
    def _check_no(self):
        for rec in self:
            if not (1 <= rec.no <= 16):
                raise ValidationError('Nomor pertemuan harus antara 1 dan 16.')
