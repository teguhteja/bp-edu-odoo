from odoo import api, models, fields, _
from odoo.exceptions import UserError

from .bp_edu_lab_praktikum import JENIS_UJIAN


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    jenis_ujian = fields.Selection(JENIS_UJIAN, string='Jenis Ujian Praktikum',
                                   help='Isi bila survey ini dipakai sebagai pretest/posttest praktikum.')
    mata_kuliah_id = fields.Many2one('bp.edu.mata.kuliah', string='Mata Kuliah')

    @api.model
    def _get_lab_default_vals(self):
        """Pengaturan survey untuk ujian praktikum: hanya bisa diakses via token jawaban
        yang dibuat portal praktikum, wajib login, tanpa skor otomatis (dinilai manual)."""
        return {
            'access_mode': 'token',
            'users_login_required': True,
            'is_attempts_limited': False,
            'scoring_type': 'no_scoring',
            'questions_layout': 'one_page',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('jenis_ujian'):
                for key, value in self._get_lab_default_vals().items():
                    vals.setdefault(key, value)
        return super().create(vals_list)

    def unlink(self):
        if self.env['bp.edu.lab.praktikum'].search_count(
                ['|', ('pretest_id', 'in', self.ids), ('posttest_id', 'in', self.ids)]):
            raise UserError(_('Ujian masih digunakan oleh praktikum, tidak bisa dihapus.'))
        return super().unlink()


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    kunci_jawaban = fields.Text(string='Kunci Jawaban',
                                help='Kunci jawaban untuk penilaian manual oleh dosen/laboran.')


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    praktikum_id = fields.Many2one('bp.edu.lab.praktikum', string='Praktikum', index=True,
                                   ondelete='set null')
    mahasiswa_id = fields.Many2one('bp.edu.mahasiswa', string='Mahasiswa', index=True,
                                   ondelete='set null')
    jenis_ujian = fields.Selection(JENIS_UJIAN, string='Jenis Ujian')
