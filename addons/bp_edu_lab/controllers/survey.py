from odoo import http
from odoo.http import request

from odoo.addons.survey.controllers.main import Survey


class LabSurvey(Survey):
    """Ujian praktikum hanya punya satu jawaban per mahasiswa; "Take Again" bawaan survey
    membuat jawaban baru tanpa praktikum sehingga tidak terlihat oleh dosen. Mengerjakan ulang
    harus lewat /my/praktikum (memakai jawaban yang sama)."""

    @http.route()
    def survey_retry(self, survey_token, answer_token, **post):
        answer = request.env['survey.user_input'].sudo().search(
            [('access_token', '=', answer_token)], limit=1)
        if answer.praktikum_id:
            return request.redirect('/my/praktikum')
        return super().survey_retry(survey_token, answer_token, **post)
