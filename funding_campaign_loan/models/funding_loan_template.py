from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FundingLoanTemplate(models.Model):
    _name = "funding.loan.template"
    _description = "Loan Template"

    name = fields.Char(
        "Name",
        required=True,
    )
    active = fields.Boolean(
        default=True,
    )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    loan_type = fields.Selection(
        [
            ("fixed-annuity", "Fixed Annuity"),
            ("fixed-annuity-begin", "Fixed Annuity Begin"),
            ("fixed-principal", "Fixed Principal"),
            ("interest", "Only interest"),
        ],
        required=True,
        default="interest",
    )
    is_permanent = fields.Boolean(
        "Is Permanent Loan",
        default=True,
    )
    rate = fields.Float(
        "Interest Rate (%)",
        required=True,
    )
    min_periods = fields.Integer(
        "Minimum Periods",
        default=60,
    )
    method_period = fields.Integer(
        "Period Length (months)",
        default=1,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    company_currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id"
    )
    journal_id = fields.Many2one(
        "account.journal",
        string="Loan Journal",
        required=True,
        domain="[('company_id', '=', company_id)]",
    )
    interest_expenses_account_id = fields.Many2one(
        "account.account",
        string="Interest Expenses Account",
        required=True,
        domain="[('company_id', '=', company_id)]",
    )
    short_term_loan_account_id = fields.Many2one(
        "account.account",
        string="Short Term Loan Account",
        required=True,
        domain="[('company_id', '=', company_id)]",
    )
    long_term_loan_account_id = fields.Many2one(
        "account.account",
        string="Long Term Loan Account",
        domain="[('company_id', '=', company_id)]",
    )
    description = fields.Text(
        "Description",
    )

    @api.constrains("rate")
    def _check_rate(self):
        for template in self:
            if template.rate <= 0:
                raise ValidationError(_("Interest rate must be greater than 0"))
