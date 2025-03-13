# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DonationRequest(models.Model):
    _name = 'donation.request'
    _description = 'Donation Request'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    @api.model
    def _lang_get(self):
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]

    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("donation.request") or "/"

    name = fields.Char(
        required=True,
        readonly=True,
        default=lambda self: self._get_default_name(),
        copy=False,
        store=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        readonly=True,
        required=False,
    )
    campaign_id = fields.Many2one(
        "funding.campaign",
        readonly=True,
        string="Campaign"
    )
    vat = fields.Char(
        string="VAT",
        required=True,
        readonly=True,
    )
    donation_amount = fields.Monetary(
        currency_field="company_currency_id",
        required=True,
        readonly=True,
        string="Donation Amount"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting", "Waiting"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )
    donation_id = fields.Many2one(
        "donation.donation",
        readonly=True,
        copy=False,
        string="Related Donation"
    )
    payment_mode_id = fields.Many2one(
        "account.payment.mode",
        domain="[('company_id', '=', company_id), ('donation', '=', True)]",
        tracking=True,
        check_company=True,
    )
    firstname = fields.Char(
        string="First name",
        readonly=True,
        required=True,
    )
    lastname = fields.Char(
        string="Last name",
        readonly=True,
        required=True,
    )
    email = fields.Char(
        required=True,
        readonly=True,
    )
    phone = fields.Char(readonly=True)
    address = fields.Char(
        required=True,
    )
    city = fields.Char(
        required=True,
    )
    zip_code = fields.Char(
        required=True,
    )
    zip_id = fields.Many2one(
        "res.city.zip",
        string="ZIP Location",
    )
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        required=True,
        readonly=True,
    )
    date = fields.Date(
        string="Request Date",
        required=True,
        readonly=True,
        default=lambda self: fields.Date.today(),
    )
    source = fields.Selection(
        [
            ("website", "Website"),
            ("manual", "Manual"),
        ],
        default="manual",
        readonly=True,
    )
    lang = fields.Selection(
        _lang_get,
        string="Language",
        required=True,
        default=lambda self: self.env.company.default_lang_id.code,
    )
    tax_receipt_option = fields.Selection(
        [
            ("none", "None"),
            ("each", "For Each Donation"),
            ("annual", "Annual Tax Receipt"),
        ],
        default="none",
        string="Tax Receipt Option",
    )
    notes = fields.Text(string="Notes")

    @api.depends("firstname", "lastname")
    def _compute_name(self):
        for request in self:
            request.name = " ".join(
                part for part in (request.firstname, request.lastname) if part
            )

    @api.onchange("partner_id")
    def onchange_partner(self):
        if self.partner_id:
            partner = self.partner_id
            self.firstname = partner.firstname if hasattr(partner, 'firstname') else partner.name
            self.lastname = partner.lastname if hasattr(partner, 'lastname') else ''
            self.email = partner.email
            self.phone = partner.phone
            self.address = partner.street
            self.city = partner.city
            self.zip_code = partner.zip
            self.country_id = partner.country_id
            self.state_id = partner.state_id
            self.vat = partner.vat
            if hasattr(partner, 'commercial_partner_id') and hasattr(partner.commercial_partner_id, 'tax_receipt_option'):
                self.tax_receipt_option = partner.commercial_partner_id.tax_receipt_option

    def _create_or_get_partner(self):
        """Create or get partner based on VAT"""
        self.ensure_one()
        ResPartner = self.env["res.partner"]

        partner = ResPartner.search([("vat", "=", self.vat)], limit=1)

        if not partner:
            partner_vals = {
                "vat": self.vat,
                "name": f"{self.firstname} {self.lastname}",
                "email": self.email,
                "street": self.address,
                "city": self.city,
                "zip": self.zip_code,
                "country_id": self.country_id.id,
                "is_company": False,
                "lang": self.lang,
            }
            if self.state_id:
                partner_vals["state_id"] = self.state_id.id
            if self.phone:
                partner_vals["phone"] = self.phone

            partner = ResPartner.create(partner_vals)
            _logger.info(f"Created new partner with VAT {self.vat}")
        else:
            _logger.info(f"Found existing partner with VAT {self.vat}")

        return partner

    def action_approve(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft requests can be approved"))
        if self.donation_amount <= 0:
            raise UserError(_("Donation amount must be greater than 0"))
        if not self.partner_id:
            partner = self._create_or_get_partner()
            self.partner_id = partner.id

        # Create donation
        donation_vals = {
            "partner_id": self.partner_id.id,
            "donation_date": fields.Date.today(),
            "amount_total": self.donation_amount,
            "currency_id": self.company_currency_id.id,
            "company_id": self.company_id.id,
            "payment_mode_id": self.payment_mode_id.id,
            "tax_receipt_option": self.tax_receipt_option,
            "campaign_id": self.campaign_id.id,
            "state": "draft",
        }

        donation = self.env["donation.donation"].create(donation_vals)

        # Create donation line
        product = self.env['product.product'].search([
            ('detailed_type', '=', 'donation'),
            ('tax_receipt_ok', '=', True)
        ], limit=1)

        if not product:
            raise UserError(_("No donation product found. Please create a product with type 'Donation'."))

        self.env['donation.line'].create({
            'donation_id': donation.id,
            'product_id': product.id,
            'quantity': 1,
            'unit_price': self.donation_amount,
        })

        self.write({"state": "approved", "donation_id": donation.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'donation.donation',
            'res_id': donation.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        for request in self:
            if request.state not in ["draft", "waiting"]:
                raise UserError(_("Only draft or waiting requests can be cancelled"))
            request.write({"state": "cancelled"})

    def action_waiting(self):
        for request in self:
            if request.state != "draft":
                raise UserError(_("Only draft requests can be put on waiting list"))
            request.write({"state": "waiting"})

    def action_reject(self):
        for request in self:
            if request.state not in ["draft", "waiting"]:
                raise UserError(_("Only draft or waiting requests can be rejected"))
            request.write({"state": "rejected"})

    def action_view_donation(self):
        self.ensure_one()
        if not self.donation_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'donation.donation',
            'res_id': self.donation_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("donation.request") or "/"
                )

        return super(DonationRequest, self).create(vals_list)
