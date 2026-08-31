{
    'name': 'TTM AI Assistant',
    'version': '19.0.1.1.0',
    'category': 'Discuss',
    'summary': 'Integrasikan AI ke chatter Odoo via @ai trigger',
    'description': """
Ketik "@ai [perintah]" di chatter Odoo mana pun untuk memanggil AI.
AI dapat membaca, mencari, dan mengubah data Odoo melalui tool calling.

Provider didukung: Groq (gratis), OpenRouter, OpenAI.
    """,
    'author': 'TTM',
    'depends': ['mail', 'mail_bot', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'data/ai_assistant_user_data.xml',
        'data/ir_config_parameter.xml',
        'views/ai_assistant_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
