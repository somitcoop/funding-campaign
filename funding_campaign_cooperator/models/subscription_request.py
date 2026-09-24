# Copyright 2026 Som IT Cooperatiu SCCL
# Nicolás Ramos https://github.com/nicolasramos
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    campaign_id = fields.Many2one(
        "funding.campaign",
        store=True,
        string="Campaign",
        tracking=True,
        help="Campaign associated with this subscription request",
    )

    contribution_id = fields.Many2one(
        "carsharing.contribution",
        string="Contribution",
        copy=False,
        help="Contribution created from this subscription request",
    )

    remunerated = fields.Boolean(
        string="Remunerated",
        default=False,
        tracking=True,
        help="Whether the subscription increase is remunerated (eligible for "
        "interest). Replaces the legacy 'increase_remunerated' type.",
    )

    skip_iban_control = fields.Boolean(
        string="Skip IBAN Control",
        help="Skip IBAN validation for automatic validation",
    )

    # Campos para integración con sign_oca
    signed_contract = fields.Binary(
        string="Signed Document",
        tracking=False,
        help="The signed subscription agreement document"
    )
    signed_contract_filename = fields.Char(
        string="Signed Document Filename",
        help="Filename of the signed document"
    )
    sign_request_ids = fields.One2many(
        comodel_name="sign.oca.request",
        inverse_name="subscription_request_id",
        string="Sign Requests",
        help="Digital signature requests for this subscription"
    )
    sign_request_count = fields.Integer(
        string="Sign request count",
        compute="_compute_sign_request_count",
        compute_sudo=True,
        store=True,
        help="Number of digital signature requests sent for this subscription.",
    )
    partner_signed_date = fields.Datetime(
        string="Partner Signed Date",
        help="Date when the partner signed the document"
    )
    partner_signed_user_id = fields.Many2one(
        'res.partner',
        string="Partner Signatory",
        help="Partner who signed the document"
    )
    company_signed_date = fields.Datetime(
        string="Company Signed Date",
        help="Date when the company signed the document"
    )
    company_signed_user_id = fields.Many2one(
        'res.users',
        string="Company Signatory",
        help="Company user who signed the document"
    )
    is_signed = fields.Boolean(
        string="Signed",
        compute="_compute_signature_flags",
        store=True,
        help=(
            "Whether the subscription contract has been signed "
            "(by the member or the company)."
        ),
    )
    signature_state = fields.Selection(
        [
            ("pending", "Pending Signature"),
            ("signed", "Signed"),
        ],
        string="Signature Status",
        compute="_compute_signature_flags",
        store=True,
        help="Signature status of the subscription contract: pending or signed.",
    )

    @api.depends("sign_request_ids")
    def _compute_sign_request_count(self):
        request_data = self.env["sign.oca.request"].read_group(
            [("subscription_request_id", "in", self.ids)],
            ["subscription_request_id"],
            ["subscription_request_id"],
        )
        mapped_data = {
            x["subscription_request_id"][0]: x["subscription_request_id_count"]
            for x in request_data
        }
        for item in self:
            item.sign_request_count = mapped_data.get(item.id, 0)

    @api.model
    def create(self, vals):
        """Normalize remunerated increases and campaign subscriptions.

        The legacy ``increase_remunerated`` type is converted to ``increase``
        plus ``remunerated = True``. Campaign subscriptions are always
        remunerated increases.
        """
        vals = self._normalize_remunerated_vals(vals)
        subscription_request = super().create(vals)
        # The original module sends a confirmation email here.
        # We call it to preserve the original behavior for non-campaign subscriptions.
        # For campaign subscriptions, this method is overridden to send
        # the correct template.
        subscription_request._send_confirmation_mail()
        return subscription_request

    def _normalize_remunerated_vals(self, vals):
        """Normalize the legacy ``increase_remunerated`` type.

        Applied on both ``create`` and ``write`` so the legacy type cannot be
        reintroduced by editing the ``type`` of an existing subscription.
        """
        if vals.get("type") == "increase_remunerated":
            _logger.info(
                "Normalizing legacy type 'increase_remunerated' to "
                "'increase' + remunerated (campaign_id: %s)",
                vals.get("campaign_id"),
            )
            vals = dict(vals, type="increase", remunerated=True)
        if vals.get("campaign_id") and vals.get("type") == "increase":
            vals["remunerated"] = True
        return vals

    def get_invoice_vals(self, partner):
        """Override to prevent campaign_id from being copied to account.move"""
        invoice_vals = super().get_invoice_vals(partner)
        # Explicitly set campaign_id to False to prevent copying funding.campaign ID
        # to account.move.campaign_id which expects utm.campaign ID
        invoice_vals['campaign_id'] = False
        return invoice_vals

    def action_send_for_signature(self):
        """Send subscription agreement for digital signature using sign_oca template"""
        self.ensure_one()

        # Only remunerated increases can be sent for digital signature
        if not self.remunerated:
            raise ValidationError(
                _(
                    "Digital signature is only available for remunerated "
                    "subscription increases."
                )
            )

        # Validaciones
        if not self.partner_id:
            raise ValidationError(
                _("The subscription request must have an assigned partner.")
            )
        if not self.partner_id.email:
            raise ValidationError(
                _("The partner does not have an email configured.")
            )

        # Obtener la plantilla de firma predefinida
        sign_template = self.env.ref(
            "funding_campaign_cooperator.subscription_agreement_sign_template",
            raise_if_not_found=False
        )
        if not sign_template:
            raise ValidationError(
                _(
                    "The subscription agreement signature template was not "
                    "found. Please update the module."
                )
            )

        # Generar el PDF del reporte y asignarlo a la plantilla
        report = self.env.ref(
            "funding_campaign_cooperator.action_report_subscription_agreement"
        )
        pdf_document, content_type = self.env["ir.actions.report"]._render_qweb_pdf(
            report.report_name, self.ids
        )

        # Actualizar la plantilla con el PDF generado
        sign_template.write({
            'data': base64.b64encode(pdf_document),
            'filename': f"subscription_agreement_{self.id}.pdf"
        })

        # Crear la solicitud de firma usando la plantilla
        sign_request_vals = (
            sign_template._prepare_sign_oca_request_vals_from_record(self)
        )
        sign_request_vals.update({
            "name": f"Acord de Subscripció - {self.name or self.partner_id.name}",
            "user_id": self.env.user.id,
        })

        sign_request = self.env["sign.oca.request"].create(sign_request_vals)

        # Retornar acción para abrir la solicitud de firma
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        action.update({
            "views": [
                [self.env.ref("sign_oca.sign_oca_request_form_view").id, "form"]
            ],
            "res_id": sign_request.id,
        })
        return action

    def action_view_sign_requests(self):
        """View all sign requests for this subscription"""
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "sign_oca.sign_oca_request_act_window"
        )
        result["domain"] = [("id", "in", self.sign_request_ids.ids)]
        ctx = dict(self.env.context)
        ctx.update({
            "default_subscription_request_id": self.id,
            "search_default_subscription_request_id": self.id,
        })
        result["context"] = ctx
        return result

    @api.depends(
        "signed_contract",
        "partner_signed_date",
        "company_signed_date",
        "sign_request_count",
        "sign_request_ids.state",
    )
    def _compute_signature_flags(self):
        for rec in self:
            signed = bool(
                rec.signed_contract
                or rec.partner_signed_date
                or rec.company_signed_date
            )
            state = "signed" if signed else "pending"
            rec.is_signed = signed
            rec.signature_state = state

    def _send_confirmation_mail(self):
        if self.campaign_id and self.remunerated:
            self.action_send_campaign_confirmation_email()
        else:
            super()._send_confirmation_mail()

    def action_send_campaign_confirmation_email(self):
        for rec in self.filtered(lambda r: r.campaign_id and r.email and r.remunerated):
            template = self.env.ref(
                "funding_campaign_cooperator."
                "email_template_campaign_subscription_confirmation",
                raise_if_not_found=False,
            )
            if not template:
                rec.message_post(
                    body=_(
                        "No se encontró la plantilla "
                        "'email_template_campaign_subscription_confirmation'."
                    )
                )
                continue
            try:
                # Enviar el correo usando la plantilla
                mail_id = template.send_mail(rec.id, force_send=True)

                # Registrar en el chatter que se envió el correo
                rec.message_post(
                    body=_(
                        "Se envió la confirmación de campaña por correo "
                        "electrónico."
                    ),
                    subject=_("Confirmación de campaña enviada"),
                    subtype_id=self.env.ref("mail.mt_comment").id,
                )

                _logger.info(
                    "Correo de confirmación de campaña enviado para "
                    "subscription_request %s, mail_id: %s",
                    rec.id,
                    mail_id,
                )

            except Exception as e:
                _logger.error(
                    "Error al enviar confirmación de campaña para "
                    "subscription_request %s: %s",
                    rec.id,
                    e,
                )
                rec.message_post(
                    body=_("Error al enviar la confirmación de campaña: %s") % e
                )

    def validate_subscription_request(self):
        invoice = super().validate_subscription_request()
        # Check if auto pay is enabled in company settings
        if self.company_id.funding_campaign_auto_pay_invoice and invoice:
            if (
                invoice.state == 'posted'
                and invoice.payment_state not in ('paid', 'in_payment')
            ):
                # Create payment
                payment_register = self.env['account.payment.register'].with_context(
                    active_model='account.move',
                    active_ids=invoice.ids,
                ).create({})
                payment_register._create_payments()
        return invoice

    def write(self, vals):
        vals = self._normalize_remunerated_vals(vals)
        res = super().write(vals)
        if vals.get("state") == "paid":
            for subscription in self:
                if (
                    subscription.remunerated
                    and subscription.campaign_id
                    and not subscription.contribution_id
                ):
                    subscription._create_contribution_from_subscription()
        return res

    def cancel_subscription_request(self):
        """Allow cancelling subscription requests in the ``paid`` state.

        In the funding/contribution integration a request reaches ``paid``
        once its contribution has been created, so cancelling that
        contribution must be able to cancel the request as well. Requests in
        any other state are delegated to the base implementation.
        """
        paid = self.filtered(lambda req: req.state == "paid")
        if paid:
            paid.write({"state": "cancelled"})
        rest = self - paid
        if rest:
            return super(SubscriptionRequest, rest).cancel_subscription_request()
        return True

    def _create_contribution_from_subscription(self):
        """Create a carsharing.contribution from this subscription request.

        The contribution type is resolved deterministically from the share
        product configured in the campaign: ``contribution_type_cash_id``
        for cash subscriptions and ``contribution_type_wallet_id`` for
        wallet subscriptions (fixed correspondence: wallet = moneder,
        cash = euros).
        """
        self.ensure_one()
        Contribution = self.env["carsharing.contribution"]

        share_product = self.share_product_id
        if not share_product:
            raise UserError(
                _(
                    "Cannot create the contribution: the subscription request "
                    "has no share product assigned."
                )
            )

        remuneration_type = (
            self.remuneration_type
            if hasattr(self, "remuneration_type") and self.remuneration_type
            else "cash"
        )
        if remuneration_type == "wallet":
            contribution_type = share_product.contribution_type_wallet_id
        else:
            contribution_type = share_product.contribution_type_cash_id
        if not contribution_type:
            raise UserError(
                _(
                    "Cannot create the contribution: the share product '%s' has "
                    "no contribution type configured for %s subscriptions. "
                    "Configure it in the product form (Contributions section)."
                )
                % (share_product.display_name, remuneration_type)
            )

        vals = {
            "associated_member": self.partner_id.id,
            "initial_import": self.subscription_amount,
            "initial_day": self.date,
            "contribution_type": contribution_type.id,
            "campaign_id": self.campaign_id.id if self.campaign_id else False,
            "subscription_request_id": self.id,
            "remuneration_type": remuneration_type,
        }

        # Warn if the mapped contribution type has no interest fiche for the
        # remuneration mode of this subscription in the current year.
        mode = "moneder" if remuneration_type == "wallet" else "euros"
        current_year = fields.Date.today().year
        if not contribution_type.historical.filtered(
            lambda interest: interest.remuneration_mode == mode
            and interest.year == current_year
        ):
            _logger.warning(
                "Contribution type '%s' has no '%s' interest fiche for %s; "
                "the contribution line will fall back to the closest "
                "previous year.",
                contribution_type.display_name,
                mode,
                current_year,
            )

        # Copy signed contract if available
        if hasattr(self, "signed_contract") and self.signed_contract:
            vals["upload_file"] = self.signed_contract
        if hasattr(self, "signed_contract_filename") and self.signed_contract_filename:
            vals["file_name"] = self.signed_contract_filename

        # Use campaign-specific email template if available
        if self.campaign_id and self.campaign_id.contribution_email_template_id:
            vals["contribution_email_template_id"] = (
                self.campaign_id.contribution_email_template_id.id
            )

        contribution = Contribution.create(vals)
        self.contribution_id = contribution.id
        _logger.info(
            "Created contribution %s from subscription %s (mode: %s)",
            contribution.id,
            self.id,
            mode,
        )
        return contribution

    def _get_amount_in_words(self, amount):
        """Convert amount to words in Catalan for the subscription agreement.
        Uses Odoo's currency amount_to_text if available, otherwise falls back
        to a manual implementation.

        NOTE: num2words does not support Catalan, and currency.amount_to_text
        silently falls back to English when the language is not supported.
        For Catalan partners we therefore always use the manual converter.
        """
        self.ensure_one()
        lang = (self.lang or self.env.lang or 'ca_ES').lower()
        if lang.startswith('ca'):
            return self._amount_to_text_ca(amount)
        currency = self.company_id.currency_id or self.env.company.currency_id
        if currency and hasattr(currency, 'amount_to_text'):
            try:
                return currency.amount_to_text(amount)
            except Exception:
                pass
        # Fallback: manual conversion to Catalan
        return self._amount_to_text_ca(amount)

    def _amount_to_text_ca(self, amount):
        """Manual conversion of amount to words in Catalan."""
        units = [
            '', 'un', 'dos', 'tres', 'quatre', 'cinc', 'sis', 'set',
            'vuit', 'nou',
        ]
        tens = [
            '', 'deu', 'vint', 'trenta', 'quaranta', 'cinquanta', 'seixanta',
            'setanta', 'vuitanta', 'noranta',
        ]
        teens = [
            'deu', 'onze', 'dotze', 'tretze', 'catorze', 'quinze', 'setze',
            'disset', 'divuit', 'dinou',
        ]

        def _convert_hundreds(n):
            result = ''
            if n >= 100:
                if n == 100:
                    result += 'cent'
                elif n < 200:
                    result += 'cent ' + _convert_tens(n % 100)
                else:
                    result += units[n // 100] + '-cents ' + _convert_tens(n % 100)
                return result.strip()
            return _convert_tens(n)

        def _convert_tens(n):
            if n < 10:
                return units[n]
            if n < 20:
                return teens[n - 10]
            if n < 100:
                t = n // 10
                u = n % 10
                if t == 2 and u == 0:
                    return 'vint'
                elif t == 2:
                    return 'vint-i-' + units[u]
                else:
                    result = tens[t]
                    if u > 0:
                        result += '-' + units[u]
                    return result
            return ''

        integer_part = int(amount)
        decimal_part = int(round((amount - integer_part) * 100))

        if integer_part == 0:
            result = 'zero'
        elif integer_part < 1000000:
            if integer_part >= 1000:
                thousands = integer_part // 1000
                remainder = integer_part % 1000
                if thousands == 1:
                    result = 'mil'
                else:
                    result = _convert_hundreds(thousands) + ' mil'
                if remainder > 0:
                    result += ' ' + _convert_hundreds(remainder)
            else:
                result = _convert_hundreds(integer_part)
        else:
            # For millions and above, use a simpler approach
            millions = integer_part // 1000000
            remainder = integer_part % 1000000
            if millions == 1:
                result = 'un milió'
            else:
                result = _convert_hundreds(millions) + ' milions'
            if remainder > 0:
                result += ' ' + _convert_hundreds(remainder)

        result += ' euros'
        if decimal_part > 0:
            result += f' amb {decimal_part:02d} cèntims'

        return result

    def _get_catalan_date(self):
        """Return current date in Catalan format for the subscription agreement."""
        months_ca = {
            1: 'gener', 2: 'febrer', 3: 'març', 4: 'abril',
            5: 'maig', 6: 'juny', 7: 'juliol', 8: 'agost',
            9: 'setembre', 10: 'octubre', 11: 'novembre', 12: 'desembre',
        }
        now = fields.Datetime.now()
        return {
            'day': now.day,
            'month': months_ca[now.month],
            'year': now.year,
        }
