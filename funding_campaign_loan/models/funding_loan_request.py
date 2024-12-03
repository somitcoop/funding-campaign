# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class FundingLoanRequest(models.Model):
    _name = "funding.loan.request"
    _description = "Loan Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    def _get_default_name(self):
        return self.env["ir.sequence"].next_by_code("funding.loan.request") or "/"

    name = fields.Char(
        required=True,
        readonly=True,
        default=lambda self: self._get_default_name(),
        copy=False,
        store=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    campaign_id = fields.Many2one(
        "funding.campaign", readonly=True, states={"draft": [("readonly", False)]}
    )
    template_id = fields.Many2one(
        "funding.loan.template",
        states={"draft": [("readonly", False)]},
    )
    #TODO: Aqui copiar valor de la capaña


    loan_amount = fields.Monetary(
        currency_field="company_currency_id",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
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
        "res.company", default=lambda self: self.env.company, required=True
    )
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )
    loan_id = fields.Many2one("account.loan", readonly=True, copy=False)

    firstname = fields.Char(
        string="First name",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    lastname = fields.Char(
        string="Last name",
        readonly=True,
        required=True,
        states={"draft": [("readonly", False)]},
    )
    email = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    phone = fields.Char(readonly=True, states={"draft": [("readonly", False)]})
    address = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    city = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    zip_code = fields.Char(
        required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    date = fields.Date(
        string="Request Date",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: fields.Date.today(),
    )
    source = fields.Selection(
        [
            ("website", "Website"),
            ("manual", "Manual"),
        ],
        default="manual",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

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
            self.firstname = partner.firstname
            self.lastname = partner.lastname
            self.email = partner.email
            self.phone = partner.phone
            self.address = partner.street
            self.city = partner.city
            self.zip_code = partner.zip
            self.country_id = partner.country_id

    def action_approve(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft requests can be approved"))
        if self.loan_amount <= 0:
            raise UserError(_("Loan amount must be greater than 0"))
        if not self.template_id:
            raise UserError(_("Loan template is required"))

        loan_vals = {
            "partner_id": self.partner_id.id,
            "loan_type": self.template_id.loan_type,
            "is_permanent": self.template_id.is_permanent,
            "rate": self.template_id.rate,
            "loan_amount": self.loan_amount,
            "min_periods": self.template_id.min_periods,
            "method_period": self.template_id.method_period,
            "journal_id": self.template_id.journal_id.id,
            "interest_expenses_account_id": self.template_id.interest_expenses_account_id.id,
            "company_id": self.company_id.id,
            "periods": self.template_id.min_periods,
            "fixed_periods": (
                self.template_id.min_periods
                if self.template_id.loan_type != "interest"
                else 0
            ),
            "rate_type": "napr",
            "fixed_loan_amount": (
                self.loan_amount if self.template_id.loan_type != "interest" else 0.0
            ),
            "residual_amount": 0.0,
            "payment_on_first_period": False,
            "round_on_end": False,
            "short_term_loan_account_id": self.template_id.short_term_loan_account_id.id,
        }

        loan = self.env["account.loan"].create(loan_vals)
        loan.start_date = fields.Date.today()
        loan._compute_draft_lines()
        self.write({"state": "approved", "loan_id": loan.id})

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

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('funding.loan.request') or '/'
        return super(FundingLoanRequest, self).create(vals)
