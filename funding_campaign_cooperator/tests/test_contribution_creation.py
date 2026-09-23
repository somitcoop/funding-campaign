# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestContributionCreation(TransactionCase):
    """Subscription request -> contribution creation (deterministic mapping).

    The contribution type is resolved from the share product: cash
    subscriptions use ``contribution_type_cash_id`` and wallet subscriptions
    use ``contribution_type_wallet_id`` (wallet = moneder, cash = euros).
    """

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Member',
            'email': 'member@example.com',
        })
        self.cash_type = self.env['carsharing.contribution.type'].create({
            'name': 'Cash Type',
            'duration': 12,
        })
        self.wallet_type = self.env['carsharing.contribution.type'].create({
            'name': 'Wallet Type',
            'duration': 12,
        })
        self.share_product = self.env['product.product'].create({
            'name': 'Share Product',
            'is_share': True,
            'list_price': 100.0,
            'contribution_type_cash_id': self.cash_type.id,
            'contribution_type_wallet_id': self.wallet_type.id,
        })
        self.campaign = self.env['funding.campaign'].create({
            'name': 'Test Campaign',
            'start_date': fields.Date.today(),
            'share_product_id': self.share_product.id,
        })

    def _create_request(self, remuneration_type='cash'):
        return self.env['subscription.request'].create({
            'campaign_id': self.campaign.id,
            'partner_id': self.partner.id,
            'share_product_id': self.share_product.id,
            'ordered_parts': 5,
            'type': 'increase',
            'remunerated': True,
            'remuneration_type': remuneration_type,
            'firstname': 'Test',
            'lastname': 'Member',
            'email': 'member@example.com',
            'address': 'Test Street 1',
            'zip_code': '08001',
            'city': 'Barcelona',
            'country_id': self.env.ref('base.es').id,
            'lang': 'es_ES',
            'source': 'website',
            'skip_iban_control': True,
        })

    def test_cash_subscription_creates_cash_contribution(self):
        """A cash subscription creates a contribution with the cash type."""
        request = self._create_request('cash')
        request.write({'state': 'paid'})
        contribution = request.contribution_id
        self.assertTrue(contribution)
        self.assertEqual(contribution.contribution_type, self.cash_type)
        self.assertEqual(contribution.remuneration_type, 'cash')
        self.assertEqual(contribution.campaign_id, self.campaign)
        self.assertEqual(contribution.subscription_request_id, request)

    def test_wallet_subscription_creates_wallet_contribution(self):
        """A wallet subscription creates a contribution with the wallet type."""
        request = self._create_request('wallet')
        request.write({'state': 'paid'})
        contribution = request.contribution_id
        self.assertTrue(contribution)
        self.assertEqual(contribution.contribution_type, self.wallet_type)
        self.assertEqual(contribution.remuneration_type, 'wallet')

    def test_missing_wallet_mapping_raises(self):
        """Wallet subscriptions without wallet mapping raise a clear error."""
        # Bypass the product constraint to simulate a legacy product without
        # wallet mapping
        self.env.cr.execute(
            "UPDATE product_template SET contribution_type_wallet_id = NULL "
            "WHERE id = %s",
            [self.share_product.product_tmpl_id.id],
        )
        self.env.invalidate_all()
        with self.assertRaises(UserError):
            request = self._create_request('wallet')
            request.write({'state': 'paid'})

    def test_non_remunerated_increase_creates_nothing(self):
        """Non-remunerated increases do not create contributions."""
        request = self._create_request('cash')
        request.write({'remunerated': False})
        request.write({'state': 'paid'})
        self.assertFalse(request.contribution_id)
