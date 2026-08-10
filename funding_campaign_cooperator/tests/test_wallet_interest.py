# -*- coding: utf-8 -*-
import unittest

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestWalletInterest(TransactionCase):
    """Tests for wallet interest payment functionality in species.

    NOTE: These tests are skipped because the wallet interest feature
    (calculate_annual_wallet_interest, generate_wallet_interest_move,
    update_wallet_balance, create_usage_invoice, wallet_balance field)
    is not implemented in any module. They were committed as part of a
    planned feature that never landed. Re-enable when the feature exists.
    """

    @unittest.skip("Wallet interest feature not implemented")
    def setUp(self):
        super(TestWalletInterest, self).setUp()

        # Set up default configuration values for testing
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.wallet_interest_rate', '3.5')
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.retention_rate', '19.0')
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.wallet_iva_rate', '21.0')

        # Create test data
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })
        # Get a default journal for loans
        journal = self.env['account.journal'].search([('type', '=', 'general')], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'Test Journal',
                'type': 'general',
                'code': 'TEST',
            })

        self.loan = self.env['account.loan'].create({
            'name': 'Test Loan',
            'partner_id': self.partner.id,
            'loan_amount': 1000.0,
            'periods': 12,  # Required field
            'journal_id': journal.id,  # Required field
            'state': 'draft',  # Use draft to avoid validation issues
        })

    def test_calculate_annual_interest_wallet(self):
        """Test annual interest calculation for wallet payments (3.5% on contributed capital)."""
        # Set remuneration type to wallet
        self.loan.remuneration_type = 'wallet'

        interest_data = self.loan.calculate_annual_wallet_interest()
        expected_gross = self.loan.loan_amount * 0.035
        expected_retention = expected_gross * 0.19
        expected_net = expected_gross - expected_retention

        self.assertEqual(interest_data['gross_interest'], expected_gross)
        self.assertEqual(interest_data['retention_amount'], expected_retention)
        self.assertEqual(interest_data['net_interest'], expected_net)

    def test_calculate_annual_interest_non_wallet(self):
        """Test that no interest is calculated for non-wallet loans."""
        # Set remuneration type to cash (or leave as default)
        self.loan.remuneration_type = 'cash'

        interest_data = self.loan.calculate_annual_wallet_interest()
        self.assertEqual(interest_data, {})

    def test_generate_interest_account_move_wallet(self):
        """Test generation of account move for wallet interest calculation."""
        # Set as wallet loan
        self.loan.remuneration_type = 'wallet'
        move_data = self.loan.generate_wallet_interest_move()
        self.assertTrue(move_data['move_created'])
        self.assertIn('gross_interest', move_data)
        self.assertIn('retention_amount', move_data)
        self.assertIn('net_interest', move_data)

    def test_generate_interest_account_move_non_wallet(self):
        """Test that no account move is generated for non-wallet loans."""
        # Set as cash loan
        self.loan.remuneration_type = 'cash'
        move_data = self.loan.generate_wallet_interest_move()
        self.assertFalse(move_data['move_created'])
        self.assertEqual(move_data['reason'], 'Not a wallet loan')

    def test_wallet_balance_update_wallet(self):
        """Test update of partner wallet balance for wallet loans."""
        # Set as wallet loan
        self.loan.remuneration_type = 'wallet'
        initial_balance = self.partner.wallet_balance
        net_interest = self.loan.update_wallet_balance()
        self.assertEqual(self.partner.wallet_balance, initial_balance + net_interest)
        self.assertGreater(net_interest, 0)

    def test_wallet_balance_update_non_wallet(self):
        """Test that wallet balance is not updated for non-wallet loans."""
        # Set as cash loan
        self.loan.remuneration_type = 'cash'
        initial_balance = self.partner.wallet_balance
        net_interest = self.loan.update_wallet_balance()
        self.assertEqual(self.partner.wallet_balance, initial_balance)
        self.assertEqual(net_interest, 0.0)

    def test_invoice_usage_full_wallet(self):
        """Test usage fully covered by wallet balance - no invoice created."""
        # Set initial wallet balance
        self.partner.wallet_balance = 100.0
        usage_amount = 50.0

        result = self.loan.create_usage_invoice(usage_amount)
        self.assertFalse(result['invoice_created'])
        self.assertEqual(result['reason'], 'Full payment from wallet')
        self.assertEqual(result['wallet_deduction'], usage_amount)
        self.assertEqual(result['payable_amount'], 0.0)
        self.assertEqual(self.partner.wallet_balance, 50.0)

    def test_invoice_usage_partial_wallet(self):
        """Test usage partially covered by wallet - invoice created for difference."""
        # Set initial wallet balance
        self.partner.wallet_balance = 40.0
        usage_amount = 60.0

        result = self.loan.create_usage_invoice(usage_amount)
        self.assertTrue(result['invoice_created'])
        self.assertEqual(result['usage_amount'], usage_amount)
        self.assertEqual(result['wallet_deduction'], 40.0)  # All wallet balance used
        self.assertEqual(result['payable_amount'], 20.0)    # Difference to pay
        self.assertEqual(result['iva_amount'], 20.0 * 0.21) # IVA on payable amount
        self.assertEqual(self.partner.wallet_balance, 0.0)

    def test_configurable_rates(self):
        """Test that configurable rates are used correctly."""
        # Change configuration values
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.wallet_interest_rate', '5.0')
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.retention_rate', '15.0')
        self.env['ir.config_parameter'].sudo().set_param('funding_campaign_cooperator.wallet_iva_rate', '10.0')

        # Set remuneration type to wallet
        self.loan.remuneration_type = 'wallet'

        # Test interest calculation with new rates
        interest_data = self.loan.calculate_annual_wallet_interest()
        expected_gross = self.loan.loan_amount * 0.05  # 5%
        expected_retention = expected_gross * 0.15     # 15%
        expected_net = expected_gross - expected_retention

        self.assertEqual(interest_data['gross_interest'], expected_gross)
        self.assertEqual(interest_data['retention_amount'], expected_retention)
        self.assertEqual(interest_data['net_interest'], expected_net)

        # Test IVA calculation with new rate
        self.partner.wallet_balance = 50.0
        usage_amount = 80.0  # Exceeds wallet balance

        result = self.loan.create_usage_invoice(usage_amount)
        expected_payable = usage_amount - 50.0
        expected_iva = expected_payable * 0.10  # 10%

        self.assertEqual(result['payable_amount'], expected_payable)
        self.assertEqual(result['iva_amount'], expected_iva)
