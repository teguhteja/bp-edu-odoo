"""
Setiap bp.edu.mata.kuliah otomatis punya satu folder DMS sendiri di bawah
folder akar "Buku Ajar" (lihat data/dms_setup.xml), diisi oleh dosen
pengampu masing-masing. Latar belakang: notulen rapat prodi SI 28 Agustus
2026 -- kebutuhan storage buku ajar terpusat, satu folder per mata kuliah.
"""
from odoo import models, fields, api


class BpEduMataKuliahDms(models.Model):
    _inherit = 'bp.edu.mata.kuliah'

    dms_directory_id = fields.Many2one(
        'dms.directory', string='Folder Buku Ajar', readonly=True, copy=False,
    )
    dms_file_count = fields.Integer(
        string='Jumlah File', related='dms_directory_id.count_files',
    )
    gdrive_link_ids = fields.One2many(
        'bp.edu.mata.kuliah.gdrive.link', 'mata_kuliah_id',
        string='Link Google Drive Buku Ajar',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_dms_directory()
        return records

    _DMS_PRODI_TANPA = 'Tanpa Program Studi'

    def _dms_prodi_directory(self):
        """Folder per program studi di bawah folder akar "Buku Ajar".

        Dengan dua prodi atau lebih, menaruh seluruh mata kuliah langsung di
        akar membuat folder akar berisi ratusan entri bercampur. Satu tingkat
        prodi memisahkannya: Buku Ajar / S1 Sistem Informasi / [TSI...].
        """
        self.ensure_one()
        root = self.env.ref(
            'bp_edu_dms.dms_directory_buku_ajar_root', raise_if_not_found=False
        )
        if not root:
            return self.env['dms.directory']
        nama = (self.prodi_id.nama or '').strip() or self._DMS_PRODI_TANPA
        Directory = self.env['dms.directory'].sudo()
        prodi_dir = Directory.search(
            [('name', '=', nama), ('parent_id', '=', root.id)], limit=1
        )
        if not prodi_dir:
            prodi_dir = Directory.create({'name': nama, 'parent_id': root.id})
        return prodi_dir

    def _ensure_dms_directory(self):
        """Buat folder DMS untuk mata kuliah yang belum punya. Dipakai saat
        create() record baru, dan untuk backfill mata kuliah lama."""
        Directory = self.env['dms.directory'].sudo()
        for mk in self:
            if mk.dms_directory_id:
                continue
            induk = mk._dms_prodi_directory()
            if not induk:
                continue
            directory = Directory.create({
                'name': mk._dms_directory_name(),
                'parent_id': induk.id,
            })
            mk.dms_directory_id = directory.id

    def action_pindah_dms_ke_folder_prodi(self):
        """Pindahkan folder mata kuliah yang masih menempel di folder akar ke
        folder prodi masing-masing. Aman dijalankan berulang."""
        root = self.env.ref(
            'bp_edu_dms.dms_directory_buku_ajar_root', raise_if_not_found=False
        )
        if not root:
            return 0
        dipindah = 0
        for mk in self:
            folder = mk.dms_directory_id
            if not folder or folder.parent_id != root:
                continue
            induk = mk._dms_prodi_directory()
            if induk and induk != folder:
                folder.sudo().write({'parent_id': induk.id})
                dipindah += 1
        return dipindah

    def _dms_directory_name(self):
        """Nama folder DMS dari kode+nama mata kuliah, dengan karakter yang
        tidak valid untuk nama file/folder (mis. '/' pada "Kerja Praktek /
        Magang") diganti supaya tidak gagal validasi dms.directory."""
        self.ensure_one()
        safe_nama = self.nama.replace('/', '-').replace('\\', '-')
        return f'[{self.kode}] {safe_nama}'

    def action_open_dms_directory(self):
        self.ensure_one()
        if not self.dms_directory_id:
            self._ensure_dms_directory()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Buku Ajar',
            'res_model': 'dms.directory',
            'res_id': self.dms_directory_id.id,
            'view_mode': 'form',
        }

    def action_backfill_dms_directories(self):
        """Buat folder DMS untuk semua mata kuliah yang belum punya folder.
        Bisa dipanggil ulang kapan saja, aman untuk data lama maupun baru."""
        missing = self.search([('dms_directory_id', '=', False)])
        missing._ensure_dms_directory()
