# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

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
            'by_individual': True,
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
            'lang': 'en_US',
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

    def test_has_contribution_false_before_payment(self):
        """A request that has not paid yet reports no contribution."""
        request = self._create_request('cash')
        self.assertFalse(request.contribution_id)
        self.assertFalse(request.has_contribution)

    def test_has_contribution_true_after_payment(self):
        """Creating the contribution flips the boolean on."""
        request = self._create_request('cash')
        request.write({'state': 'paid'})
        self.assertTrue(request.contribution_id)
        self.assertTrue(request.has_contribution)

    def test_has_contribution_follows_contribution_id(self):
        """The boolean always mirrors whether contribution_id is set."""
        request = self._create_request('cash')
        request.write({'state': 'paid'})
        request.write({'contribution_id': False})
        self.assertFalse(request.has_contribution)

    def test_repaid_does_not_duplicate_contribution(self):
        """OP #4533: re-writing paid must not duplicate the contribution."""
        request = self._create_request('cash')
        request.write({'state': 'paid'})
        first_id = request.contribution_id.id
        self.assertTrue(first_id)
        count_before = self.env['carsharing.contribution'].search_count([])
        request.write({'state': 'paid'})
        self.assertEqual(request.contribution_id.id, first_id)
        self.assertEqual(
            self.env['carsharing.contribution'].search_count([]),
            count_before,
        )

    def test_duplicate_subscription_link_raises(self):
        """OP #4533: the unique constraint rejects a second contribution
        for the same subscription request."""
        request = self._create_request('cash')
        request.write({'state': 'paid'})
        self.assertTrue(request.contribution_id)
        with self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env['carsharing.contribution'].create(
                    {
                        'associated_member': request.partner_id.id,
                        'initial_import': 100.0,
                        'initial_day': '2026-01-01',
                        'contribution_type': self.cash_type.id,
                        'subscription_request_id': request.id,
                    }
                )
