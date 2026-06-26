# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSubscriptionAgreement(TransactionCase):
    """Tests for the subscription agreement report (contracte d'aportacions al capital social)."""

    def setUp(self):
        super(TestSubscriptionAgreement, self).setUp()

        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Soci',
            'email': 'test@somit.coop',
            'vat': 'ES12345678Z',
            'cooperator_register_number': '12345',
        })

        # Create a share product
        self.share_product = self.env['product.product'].create({
            'name': 'Test Share',
            'is_share': True,
            'list_price': 100.0,
            'default_code': 'TEST_SHARE',
        })

        # Create a funding campaign
        self.campaign = self.env['funding.campaign'].create({
            'name': 'Test Campaign',
            'share_product_id': self.share_product.id,
        })

    def _create_subscription_request(self, remuneration_type='cash', ordered_parts=10):
        """Helper to create a subscription request for testing."""
        return self.env['subscription.request'].create({
            'campaign_id': self.campaign.id,
            'partner_id': self.partner.id,
            'share_product_id': self.share_product.id,
            'ordered_parts': ordered_parts,
            'type': 'increase_remunerated',
            'firstname': 'Test',
            'lastname': 'Soci',
            'email': 'test@somit.coop',
            'address': 'Carrer Test 123',
            'zip_code': '08001',
            'city': 'Barcelona',
            'country_id': self.env.ref('base.es').id,
            'lang': 'ca_ES',
            'source': 'website',
            'remuneration_type': remuneration_type,
            'skip_iban_control': True,
        })

    def test_amount_to_text_cash(self):
        """Test _get_amount_in_words returns correct Catalan text for cash amounts."""
        sr = self._create_subscription_request('cash', 10)
        amount_text = sr._get_amount_in_words(1000.0)
        self.assertIn('mil', amount_text)
        self.assertIn('euros', amount_text)

    def test_amount_to_text_small_amount(self):
        """Test _get_amount_in_words for small amounts."""
        sr = self._create_subscription_request('cash', 1)
        amount_text = sr._get_amount_in_words(100.0)
        self.assertIn('cent', amount_text)
        self.assertIn('euros', amount_text)

    def test_amount_to_text_with_cents(self):
        """Test _get_amount_in_words includes cents."""
        sr = self._create_subscription_request('cash', 5)
        amount_text = sr._get_amount_in_words(500.50)
        self.assertIn('euros', amount_text)
        self.assertIn('cèntims', amount_text)

    def test_catalan_date_format(self):
        """Test _get_catalan_date returns correct structure."""
        sr = self._create_subscription_request('cash', 1)
        date_info = sr._get_catalan_date()
        self.assertIn('day', date_info)
        self.assertIn('month', date_info)
        self.assertIn('year', date_info)
        self.assertIsInstance(date_info['day'], int)
        self.assertIsInstance(date_info['year'], int)
        # Month should be a Catalan month name
        valid_months = ['gener', 'febrer', 'març', 'abril', 'maig', 'juny',
                        'juliol', 'agost', 'setembre', 'octubre', 'novembre', 'desembre']
        self.assertIn(date_info['month'], valid_months)

    def test_report_renders_cash_version(self):
        """Test that the report renders correctly for cash remuneration type."""
        sr = self._create_subscription_request('cash', 10)
        # Render the report
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertTrue(pdf_content)
        self.assertIn(b'application/pdf', content_type)

    def test_report_renders_wallet_version(self):
        """Test that the report renders correctly for wallet remuneration type."""
        sr = self._create_subscription_request('wallet', 10)
        # Render the report
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertTrue(pdf_content)
        self.assertIn(b'application/pdf', content_type)

    def test_report_contains_contract_title(self):
        """Test that the report contains the contract title."""
        sr = self._create_subscription_request('cash', 5)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        # The PDF should contain the contract title
        self.assertIn(b'CONTRACT', pdf_content)
        self.assertIn(b'APORTACIONS', pdf_content)

    def test_report_contains_partner_info(self):
        """Test that the report contains partner information."""
        sr = self._create_subscription_request('cash', 3)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        # The PDF should contain the partner name
        self.assertIn(b'Test Soci', pdf_content)

    def test_report_contains_campaign_name(self):
        """Test that the report contains the campaign name."""
        sr = self._create_subscription_request('cash', 3)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertIn(b'Test Campaign', pdf_content)

    def test_report_contains_subscription_amount(self):
        """Test that the report contains the subscription amount."""
        sr = self._create_subscription_request('cash', 7)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        # 7 shares * 100€ = 700.00
        self.assertIn(b'700.00', pdf_content)

    def test_report_contains_ordered_parts(self):
        """Test that the report contains the number of ordered parts."""
        sr = self._create_subscription_request('cash', 5)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertIn(b'5', pdf_content)

    def test_report_contains_victor_luna(self):
        """Test that the report contains Victor Luna as president."""
        sr = self._create_subscription_request('cash', 1)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertIn(b'Victor Luna', pdf_content)

    def test_report_contains_cooperator_number(self):
        """Test that the report contains the cooperator register number."""
        sr = self._create_subscription_request('cash', 2)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertIn(b'12345', pdf_content)

    def test_report_contains_vat(self):
        """Test that the report contains the partner VAT."""
        sr = self._create_subscription_request('cash', 2)
        report = self.env.ref('funding_campaign_cooperator.action_report_subscription_agreement')
        pdf_content, content_type = self.env['ir.actions.report']._render_qweb_pdf(
            report.report_name, sr.ids
        )
        self.assertIn(b'ES12345678Z', pdf_content)
