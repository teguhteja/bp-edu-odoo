import odoo.tests

from odoo.tests.common import tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestHoot(odoo.tests.HttpCase):


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hoot_user = new_test_user(
            cls.env,
            login='hoot_sbs_custom_style_refresh',
            password='hoot_sbs_custom_style_refresh',
            groups='base.group_user',
            context={
                'mail_create_nosubscribe': True,
                'mail_notrack': True,
                'no_reset_password': True,
            },
        )


    @odoo.tests.no_retry
    def test_hoot_sbs_custom_style_refresh(self):
        self.browser_js(
            '/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&tag=sbs_custom_style_refresh',
            "",
            "",
            login=self.hoot_user.login,
            timeout=1800,
            success_signal='[HOOT] Test suite succeeded',
            error_checker=lambda message: '[HOOT]' not in message,
        )
