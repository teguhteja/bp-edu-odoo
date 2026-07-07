"""
Extend res.config.settings untuk konfigurasi TTM AI Assistant.
Semua field disimpan ke ir.config_parameter via config_parameter= kwarg.
"""
from odoo import models, fields

_DEFAULT_SYSTEM_PROMPT = (
    "Kamu adalah asisten AI yang terintegrasi dalam Odoo ERP. "
    "Kamu dapat membantu pengguna dengan mencari data, membaca record, "
    "memperbarui field, dan membuat record baru menggunakan tools yang tersedia. "
    "Selalu jawab dalam bahasa yang sama dengan pertanyaan pengguna. "
    "Berikan jawaban yang jelas dan akurat. "
    "Saat mengubah data, konfirmasi operasi yang telah dilakukan."
)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ttm_ai_provider = fields.Selection([
        ('groq', 'Groq (Llama — Free Tier)'),
        ('openrouter', 'OpenRouter (DeepSeek, Llama, dst)'),
        ('openai', 'OpenAI (GPT-4o, dst)'),
    ], string='AI Provider', config_parameter='ttm_ai.api_provider', default='groq')

    ttm_ai_api_key = fields.Char(
        string='API Key',
        config_parameter='ttm_ai.api_key',
        help='API Key dari provider. Disimpan di ir.config_parameter (plain text).',
    )

    ttm_ai_model_name = fields.Char(
        string='Nama Model',
        config_parameter='ttm_ai.model_name',
        help=(
            'Groq: llama-3.3-70b-versatile (default)\n'
            'OpenRouter: deepseek/deepseek-chat (default)\n'
            'OpenAI: gpt-4o-mini (default)\n'
            'Kosongkan untuk menggunakan default provider.'
        ),
    )

    ttm_ai_system_prompt = fields.Char(
        string='System Prompt',
        config_parameter='ttm_ai.system_prompt',
    )

    ttm_ai_max_tokens = fields.Integer(
        string='Max Tokens',
        config_parameter='ttm_ai.max_tokens',
        default=2048,
    )

    ttm_ai_temperature = fields.Float(
        string='Temperature',
        config_parameter='ttm_ai.temperature',
        default=0.7,
        help='0.0 = deterministik, 1.0 = kreatif. Rekomendasi: 0.3–0.7',
    )
