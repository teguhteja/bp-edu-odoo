# Part of the EH AI Suite by ERP Heritage.
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestEhAiAccount(TransactionCase):

    def test_customer_balance_tool(self):
        self.env["res.partner"].create({"name": "Zeta Industries"})
        tool = self.env.ref("eh_ai_account.tool_customer_balance")
        output, error = tool._eh_ai_run_tool({"customer_name": "Zeta"})
        self.assertFalse(error)
        self.assertIn("Zeta Industries", output)
        self.assertIn("0.00", output)

    def test_customer_balance_not_found(self):
        tool = self.env.ref("eh_ai_account.tool_customer_balance")
        output, error = tool._eh_ai_run_tool({"customer_name": "Nonexistent XYZ"})
        self.assertFalse(error)
        self.assertIn("No customer found", output)
