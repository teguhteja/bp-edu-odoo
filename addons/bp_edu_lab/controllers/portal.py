import base64
from urllib.parse import urlencode

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

MAKS_UKURAN_BERKAS = 10 * 1024 * 1024  # 10 MB
JENIS_LABEL = {'pra': 'Pretest', 'post': 'Posttest'}


class LabPortal(CustomerPortal):
    """Portal mahasiswa: pengganti halaman user/* di lab-app (absensi, berkas, ujian, nilai)."""

    def _lab_redirect(self, pesan, status='danger'):
        return request.redirect('/my/praktikum?' + urlencode({'pesan': pesan, 'status': status}))

    def _lab_mahasiswa(self):
        return request.env.user._get_mahasiswa()

    def _lab_praktikum(self, praktikum_id):
        return request.env['bp.edu.lab.praktikum'].sudo().browse(praktikum_id).exists()

    def _lab_items(self, mahasiswa):
        peserta_list = request.env['bp.edu.lab.peserta'].sudo().search(
            [('mahasiswa_id', '=', mahasiswa.id)], order='tanggal desc, id desc')
        UserInput = request.env['survey.user_input'].sudo()
        items = []
        for peserta in peserta_list:
            praktikum = peserta.praktikum_id
            ujian = []
            for jenis in ('pra', 'post'):
                survey = praktikum._get_survey(jenis)
                sudah = bool(UserInput.search_count([
                    ('praktikum_id', '=', praktikum.id),
                    ('mahasiswa_id', '=', mahasiswa.id),
                    ('jenis_ujian', '=', jenis),
                    ('state', '=', 'done'),
                ]))
                ujian.append({
                    'jenis': jenis,
                    'label': JENIS_LABEL[jenis],
                    'ada_soal': bool(survey and survey.question_ids),
                    'sudah': sudah,
                    'boleh': not praktikum.cek_jendela_waktu(jenis),
                })
            items.append({'peserta': peserta, 'ujian': ujian})
        return items

    @http.route('/my/praktikum', type='http', auth='user', website=True)
    def portal_my_praktikum(self, pesan=None, status=None, **kw):
        mahasiswa = self._lab_mahasiswa()
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'praktikum',
            'mahasiswa': mahasiswa,
            'items': self._lab_items(mahasiswa) if mahasiswa else [],
            'pesan': pesan,
            'status': status,
        })
        return request.render('bp_edu_lab.portal_my_praktikum', values)

    @http.route('/my/praktikum/<int:praktikum_id>/presensi', type='http', auth='user',
                methods=['POST'], website=True)
    def portal_praktikum_presensi(self, praktikum_id, token=None, **kw):
        praktikum = self._lab_praktikum(praktikum_id)
        if not praktikum:
            return self._lab_redirect(_('Praktikum tidak ditemukan.'))
        try:
            praktikum.submit_presensi(self._lab_mahasiswa(), token)
        except UserError as e:
            return self._lab_redirect(str(e))
        return self._lab_redirect(_('Berhasil Presensi'), 'success')

    @http.route('/my/praktikum/<int:praktikum_id>/berkas', type='http', auth='user',
                methods=['POST'], website=True)
    def portal_praktikum_berkas(self, praktikum_id, berkas=None, **kw):
        mahasiswa = self._lab_mahasiswa()
        if not mahasiswa:
            return self._lab_redirect(_('Akun Anda belum terhubung ke data mahasiswa, hubungi admin.'))
        praktikum = self._lab_praktikum(praktikum_id)
        peserta = praktikum and praktikum._get_peserta(mahasiswa)
        if not peserta:
            return self._lab_redirect(_('Anda tidak terdaftar di praktikum ini.'))
        if not berkas or not getattr(berkas, 'filename', None):
            return self._lab_redirect(_('Pilih berkas terlebih dahulu.'))
        data = berkas.read()
        if len(data) > MAKS_UKURAN_BERKAS:
            return self._lab_redirect(_('Ukuran berkas maksimal 10 MB.'))
        peserta.write({'berkas': base64.b64encode(data), 'berkas_nama': berkas.filename})
        return self._lab_redirect(_('Berkas Berhasil Diupload'), 'success')

    @http.route('/my/praktikum/<int:praktikum_id>/ujian/<string:jenis>', type='http',
                auth='user', website=True)
    def portal_praktikum_ujian(self, praktikum_id, jenis, **kw):
        praktikum = self._lab_praktikum(praktikum_id)
        if not praktikum or jenis not in JENIS_LABEL:
            return request.not_found()
        try:
            answer = praktikum.mulai_ujian(self._lab_mahasiswa(), jenis)
        except UserError as e:
            return self._lab_redirect(str(e))
        survey = answer.survey_id
        return request.redirect(f'/survey/start/{survey.access_token}?answer_token={answer.access_token}')
