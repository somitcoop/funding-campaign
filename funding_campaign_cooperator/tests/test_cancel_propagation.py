# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCancelPropagation(TransactionCase):
    """Cancelling a contribution must cancel its paid subscription request.

    Gerard pointed out that cancelling a contribution did not propagate the
    cancellation to the funding side: the request stayed in ``paid``. The
    contribution closing now cancels the linked request.
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

    def _create_paid_request(self):
        request = self.env['subscription.request'].create({
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
            'lang': 'es_ES',
            'source': 'website',
            'skip_iban_control': True,
        })
        request.write({'state': 'paid'})
        return request

    def test_cancel_request_from_paid(self):
        """A paid subscription request can be cancelled."""
        request = self._create_paid_request()
        self.assertEqual(request.state, 'paid')
        request.cancel_subscription_request()
        self.assertEqual(request.state, 'cancelled')

    def test_cancel_contribution_propagates(self):
        """Cancelling the contribution cancels the linked paid request."""
        request = self._create_paid_request()
        contribution = request.contribution_id
        self.assertTrue(contribution)
        self.assertEqual(request.state, 'paid')
        contribution._close_contribution(close_reason='cancellation')
        self.assertEqual(contribution.state, 'closed')
        self.assertEqual(contribution.close_reason, 'cancellation')
        self.assertEqual(request.state, 'cancelled')

    def test_other_close_reasons_do_not_cancel(self):
        """Closing with a reason other than cancellation keeps the request."""
        request = self._create_paid_request()
        contribution = request.contribution_id
        contribution._close_contribution(close_reason='early_return')
        self.assertEqual(contribution.state, 'closed')
        self.assertEqual(request.state, 'paid')
