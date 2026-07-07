"""
Override mail.bot (OdooBot) agar tidak merespons pesan yang mengandung @ai trigger
atau mention langsung ke user "ai-assistant-ttm".
"""
import re

from odoo import models

_AI_TRIGGER = re.compile(r'@ai\s', re.IGNORECASE)
_HTML_TAGS = re.compile(r'<[^>]+>')


def _extract_partner_ids(raw):
    """Normalisasi berbagai format partner_ids (list int, atau command tuples)."""
    ids = []
    for item in raw or []:
        if isinstance(item, int):
            ids.append(item)
        elif isinstance(item, (list, tuple)) and len(item) == 3:
            if item[0] == 4 and item[2]:
                ids.append(item[2])
            elif item[0] == 6 and item[2]:
                ids.extend(item[2])
    return ids


class MailBot(models.AbstractModel):
    _inherit = 'mail.bot'

    def _get_answer(self, channel, body, values, command=False):
        # Jika pesan mengandung teks "@ai ", biarkan ttm_ai_assistant yang merespons
        raw_body = values.get('body', '') or body or ''
        plain = _HTML_TAGS.sub(' ', raw_body)
        if _AI_TRIGGER.search(plain):
            return False

        # Jika pesan mention langsung user "ai-assistant-ttm", biarkan juga
        try:
            bot_partner = self.env.ref('ttm_ai_assistant.user_ai_assistant').partner_id
            partner_ids = _extract_partner_ids(values.get('partner_ids'))
            if bot_partner.id in partner_ids:
                return False
        except Exception:
            pass

        return super()._get_answer(channel, body, values, command)
