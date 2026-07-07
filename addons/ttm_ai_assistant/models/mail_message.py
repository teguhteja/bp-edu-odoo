"""
mail.message override — intercept pesan chatter yang diawali "@ai"
dan jalankan AI agent di background thread.
"""
import logging
import re
import threading
import time

from markupsafe import Markup

from odoo import api, models
from odoo.orm.registry import Registry

_logger = logging.getLogger(__name__)

# Regex: cocokkan "@ai " diikuti teks perintah, case-insensitive
_AI_TRIGGER = re.compile(r'@ai\s+(.+)', re.IGNORECASE | re.DOTALL)

# XML ID user bot AI (lihat data/ai_assistant_user_data.xml)
_BOT_XMLID = 'ttm_ai_assistant.user_ai_assistant'
# Ketika user benar-benar mention "@ai-assistant-ttm" (bukan sekadar ketik teks
# "@ai "), body plain akan diawali nama tersebut — buang agar sisanya jadi command
_BOT_NAME_PREFIX = re.compile(r'^@?ai-assistant-ttm[:,]?\s*', re.IGNORECASE)

# Strip tag HTML dan decode entitas umum
_HTML_TAGS = re.compile(r'<[^>]+>')
_HTML_ENTITIES = [
    ('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'),
    ('&gt;', '>'), ('&quot;', '"'), ('&#39;', "'"),
]


def _strip_html(html: str) -> str:
    text = _HTML_TAGS.sub(' ', html or '')
    for entity, char in _HTML_ENTITIES:
        text = text.replace(entity, char)
    return ' '.join(text.split())


class MailMessage(models.Model):
    _inherit = 'mail.message'

    def _get_ai_bot_partner(self):
        try:
            return self.env.ref(_BOT_XMLID).partner_id
        except Exception:
            return None

    def _is_dm_with_bot(self, res_model, res_id, bot_partner):
        """True bila pesan dikirim di channel chat 1:1 (DM) bersama bot AI."""
        if not bot_partner or res_model != 'discuss.channel' or not res_id:
            return False
        channel = self.env['discuss.channel'].browse(res_id)
        if not channel.exists() or channel.channel_type != 'chat':
            return False
        return bot_partner.id in channel.channel_member_ids.partner_id.ids

    @api.model_create_multi
    def create(self, vals_list):
        messages = super().create(vals_list)
        bot_partner = self._get_ai_bot_partner()

        for message in messages:
            # Hanya intercept comment/email (bukan internal note atau system)
            if message.message_type not in ('comment', 'email'):
                continue

            # Jangan proses balasan dari bot itu sendiri (cegah infinite loop)
            if bot_partner and message.author_id.id == bot_partner.id:
                continue

            # Tentukan context record — chatter record biasa atau discuss.channel
            # (pesan Discuss disimpan dengan model='discuss.channel', res_id=channel id)
            res_model = message.model or None
            res_id = message.res_id or None

            body_plain = _strip_html(message.body or '')

            # Trigger 1: mention langsung ke user "ai-assistant-ttm" di Discuss
            is_mentioned = bool(bot_partner) and bot_partner.id in message.partner_ids.ids
            # Trigger 2: DM 1:1 dengan bot — semua pesan dianggap ditujukan ke AI
            is_dm = self._is_dm_with_bot(res_model, res_id, bot_partner)

            command = None
            if is_mentioned:
                command = _BOT_NAME_PREFIX.sub('', body_plain, count=1).strip()
                if not command:
                    command = body_plain.strip()
            elif is_dm:
                command = body_plain.strip()
            else:
                # Trigger 3: teks "@ai <perintah>" di chatter mana pun
                match = _AI_TRIGGER.search(body_plain)
                if match:
                    command = match.group(1).strip()

            if not command:
                continue

            _logger.info(
                'AI trigger: %r | model=%s res_id=%s | msg_type=%s | user=%s | mention=%s | dm=%s',
                command[:120], res_model, res_id, message.message_type, self.env.uid, is_mentioned, is_dm
            )

            # Spawn background thread — tidak blocking UI
            t = threading.Thread(
                target=_ai_reply_worker,
                args=(
                    self.env.cr.dbname,
                    self.env.uid,
                    command,
                    res_model,
                    res_id,
                ),
                daemon=True,
                name=f'ttm_ai_{message.id}',
            )
            t.start()

        return messages


def _ai_reply_worker(dbname: str, uid: int, command: str, res_model, res_id):
    """
    Background worker:
    1. Tunggu transaksi asal commit (2 detik)
    2. Panggil AI dengan konfigurasi dari settings
    3. Post reply di chatter record / discuss channel yang sama sebagai user "ai-assistant-ttm"
    """
    # Beri waktu transaksi asal untuk commit sebelum kita baca/tulis
    time.sleep(2)

    try:
        registry = Registry(dbname)
        with registry.cursor() as cr:
            env = api.Environment(cr, uid, {})

            # Panggil AI
            try:
                response_html = env['ai.agent'].call_from_settings(
                    command, res_model, res_id
                )
            except Exception as e:
                _logger.exception('AI call gagal untuk command: %r', command[:100])
                response_html = f'<p>Error saat memanggil AI: {e}</p>'

            # Post reply — ke chatter record atau discuss.channel
            try:
                bot_partner_id = False
                try:
                    bot_partner_id = env.ref(_BOT_XMLID).partner_id.id
                except Exception:
                    try:
                        bot_partner_id = env.ref('base.partner_root').id
                    except Exception:
                        pass

                if res_model and res_id:
                    record = env[res_model].sudo().browse(res_id)
                    if not record.exists():
                        _logger.warning('Record %s #%s tidak ditemukan saat post AI reply', res_model, res_id)
                        cr.rollback()
                        return
                    record.message_post(
                        body=Markup(response_html),
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                        author_id=bot_partner_id,
                    )
                else:
                    _logger.warning('AI reply tidak dapat dikirim: res_model/res_id kosong')
                    cr.rollback()
                    return

            except Exception:
                _logger.exception('Gagal post AI reply ke %s #%s', res_model, res_id)
                cr.rollback()
                return

            cr.commit()
            _logger.info('AI reply berhasil dipost ke %s #%s', res_model, res_id)

    except Exception:
        _logger.exception('AI worker thread error (dbname=%s, model=%s, id=%s)', dbname, res_model, res_id)
