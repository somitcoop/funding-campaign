# -*- coding: utf-8 -*-
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
    )
    signature_state = fields.Selection(
        [
            ("pending", "Pending Signature"),
            ("signed", "Signed"),
        ],
        string="Signature Status",
        compute="_compute_signature_flags",
        store=True,
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
        """Override create to ensure campaign subscriptions always use increase_remunerated type"""
        # If this subscription request has a campaign_id AND is an increase, force type to be increase_remunerated
        if vals.get('campaign_id') and vals.get('type') == 'increase':
            _logger.info(f"Campaign subscription detected (campaign_id: {vals['campaign_id']}). "
                        f"Forcing type to 'increase_remunerated' (was: {vals.get('type')})")
            vals['type'] = 'increase_remunerated'
        
        subscription_request = super().create(vals)
        # The original module sends a confirmation email here.
        # We call it to preserve the original behavior for non-campaign subscriptions.
        # For campaign subscriptions, we assume this method is overridden to send the correct template.
        subscription_request._send_confirmation_mail()
        return subscription_request

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

        # Validar que solo se ejecute para suscripciones de tipo increase_remunerated
        if self.type != 'increase_remunerated':
            raise ValidationError(
                _("Digital signature is only available for remunerated subscription increases.")
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
                _("The subscription agreement signature template was not found. Please update the module.")
            )

        # Generar el PDF del reporte y asignarlo a la plantilla
        report = self.env.ref("funding_campaign_cooperator.action_report_subscription_agreement")
        pdf_document, content_type = self.env["ir.actions.report"]._render_qweb_pdf(
            report.report_name, self.ids
        )
        
        # Actualizar la plantilla con el PDF generado
        sign_template.write({
            'data': base64.b64encode(pdf_document),
            'filename': f"subscription_agreement_{self.id}.pdf"
        })

        # Crear la solicitud de firma usando la plantilla
        sign_request_vals = sign_template._prepare_sign_oca_request_vals_from_record(self)
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
        if self.campaign_id and self.type == 'increase_remunerated':
            self.action_send_campaign_confirmation_email()
        else:
            super(SubscriptionRequest, self)._send_confirmation_mail()

    def action_send_campaign_confirmation_email(self):
        for rec in self.filtered(lambda r: r.campaign_id and r.email and r.type == 'increase_remunerated'):
            template = self.env.ref(
                "funding_campaign_cooperator.email_template_campaign_subscription_confirmation",
                raise_if_not_found=False,
            )
            if not template:
                rec.message_post(body=_("No se encontró la plantilla 'email_template_campaign_subscription_confirmation'."))
                continue
            try:
                # Enviar el correo usando la plantilla
                mail_id = template.send_mail(rec.id, force_send=True)
                
                # Registrar en el chatter que se envió el correo
                rec.message_post(
                    body=_("Se envió la confirmación de campaña por correo electrónico."),
                    subject=_("Confirmación de campaña enviada"),
                    subtype_id=self.env.ref("mail.mt_comment").id,
                )
                
                _logger.info(f"Correo de confirmación de campaña enviado para subscription_request {rec.id}, mail_id: {mail_id}")
                
            except Exception as e:
                _logger.error(f"Error al enviar confirmación de campaña para subscription_request {rec.id}: {e}")
                rec.message_post(body=_("Error al enviar la confirmación de campaña: %s") % e)

    def validate_subscription_request(self):
        invoice = super().validate_subscription_request()
        # Check if auto pay is enabled in company settings
        if self.company_id.funding_campaign_auto_pay_invoice and invoice:
            if invoice.state == 'posted' and invoice.payment_state not in ('paid', 'in_payment'):
                # Create payment
                payment_register = self.env['account.payment.register'].with_context(
                    active_model='account.move',
                    active_ids=invoice.ids,
                ).create({})
                payment_register._create_payments()
        return invoice
