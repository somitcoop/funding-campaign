# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later

from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConfirmationMail(TransactionCase):
    """One single confirmation email per subscription request (OP #4537)."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Member',
            'email': 'member@example.com',
        })
        self.share_product = self.env['product.product'].create({
            'name': 'Share Product',
            'is_share': True,
            'by_individual': True,
            'list_price': 100.0,
        })
        self.campaign = self.env['funding.campaign'].create({
            'name': 'Test Campaign',
            'start_date': fields.Date.today(),
            'share_product_id': self.share_product.id,
        })

    def _create_request(self):
        return self.env['subscription.request'].create({
            'campaign_id': self.campaign.id,
            'partner_id': self.partner.id,
            'share_product_id': self.share_product.id,
            'ordered_parts': 5,
            'type': 'increase',
            'remunerated': True,
            'remuneration_type': 'cash',
            'firstname': 'Test',
            'lastname': 'Member',
            'email': 'member@example.com',
            'address': 'Test Street 1',
            'zip_code': '08001',
            'city': 'Barcelona',
            'country_id': self.env.ref('base.es').id,
            'lang': 'en_US',
            'source': 'website',
            'skip_iban_control': True,
        })

    def test_create_sends_single_confirmation_mail(self):
        """Creating a request must send the confirmation email exactly once."""
        send_path = (
            'odoo.addons.mail.models.mail_template.MailTemplate.send_mail'
        )
        with patch(send_path, return_value=1) as mock_send:
            self._create_request()
        self.assertEqual(mock_send.call_count, 1)
