from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
import traceback
from odoo.addons.swagger_docs.controllers.swagger_controller import spec


_logger = logging.getLogger(__name__)


class DonationRequestApi(http.Controller):
    @http.route(
        "/api/campaign/<int:campaign_id>/donation_request",
        type="json",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def create_donation_request(self, campaign_id, **kw):
        try:
            db = request.httprequest.headers.get("X-Odoo-Db")
            username = request.httprequest.headers.get("X-Odoo-Username")
            api_key = request.httprequest.headers.get("X-Odoo-Api-Key")

            if not all([db, username, api_key]):
                _logger.warning("Missing authentication parameters.")
                return {"error": "Missing authentication parameters", "status": "error"}

            request.session.db = db

            _logger.info(f"Searching user: {username}")
            user = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", username)], limit=1)
            )

            if not user:
                _logger.warning(f"User not found: {username}")
                return {"error": "User not found", "status": "error"}

            try:
                user.ensure_one()
            except ValueError:
                _logger.error(f"Multiple users found with login: {username}")
                return {
                    "error": "Multiple users found with same login",
                    "status": "error",
                }

            campaign = request.env["funding.campaign"].browse(campaign_id)
            if not campaign.exists():
                _logger.warning(f"Campaign not found: {campaign_id}")
                return {"error": "Campaign not found", "status": "error"}

            if campaign.state != "open":
                _logger.warning(
                    f"Campaign {campaign.name} is not open (current state: {campaign.state})"
                )
                return {
                    "error": "Campaign is not active",
                    "status": "error",
                    "details": "Donation requests can only be created for active campaigns",
                }

            _logger.info(f"User found: {user.name}")

            try:
                temp_env = request.env(user=user.id)
                temp_env.user._check_credentials(api_key, {"interactive": False})
                _logger.info(f"Authentication successful for user: {user.name}")
            except AccessDenied:
                _logger.warning(f"Authentication failed for user: {username}")
                return {"error": "Authentication failed", "status": "error"}

            request.env = temp_env

            required_fields = [
                "vat",
                "donation_amount",
                "firstname",
                "lastname",
                "email",
                "address",
                "zip_code",
                "lang",
            ]

            for field in required_fields:
                if field not in kw:
                    _logger.warning(f"Missing required field: {field}")
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error",
                    }

            if "campaign_id" in kw and kw["campaign_id"] != campaign_id:
                return {
                    "error": "Campaign ID mismatch between URL and payload",
                    "status": "error",
                }

            # Validar límites de donación
            donation_amount = float(kw["donation_amount"])
            if hasattr(campaign, 'minimal_donation_amount') and campaign.minimal_donation_amount > 0:
                if donation_amount < campaign.minimal_donation_amount:
                    return {
                        "error": "Donation amount below minimum",
                        "status": "error",
                        "details": f"The minimum donation amount is {campaign.minimal_donation_amount}",
                    }

            partner_id = False
            if kw.get("vat"):
                partner = (
                    request.env["res.partner"]
                    .sudo()
                    .search([("vat", "=", kw["vat"])], limit=1)
                )
                if partner:
                    partner_id = partner.id
                    _logger.info(f"Found existing partner with VAT {kw['vat']}")

            country = request.env["res.country"].search(
                [("code", "=", kw["country_code"].upper())], limit=1
            )
            if not country:
                return {
                    "error": f"Invalid country code: {kw['country_code']}",
                    "status": "error",
                }

            lang = request.env["res.lang"].search([("code", "=", kw["lang"])], limit=1)
            if not lang:
                return {
                    "error": f"Invalid language code: {kw['lang']}",
                    "status": "error",
                }

            # Buscar el registro de zip en base_location usando el zip_code y country_id
            zip_record = False
            if kw.get("zip_code") and country:
                zip_record = request.env["res.city.zip"].sudo().search(
                    [
                        ("name", "=", kw["zip_code"]),
                        ("city_id.country_id", "=", country.id),
                    ],
                    limit=1,
                )

                # Si también tenemos la ciudad, refinamos la búsqueda
                if not zip_record and kw.get("city"):
                    # Buscar primero por ciudad y país
                    city = request.env["res.city"].sudo().search(
                        [
                            ("name", "=", kw["city"]),
                            ("country_id", "=", country.id),
                        ],
                        limit=1,
                    )

                    if city:
                        zip_record = request.env["res.city.zip"].sudo().search(
                            [
                                ("name", "=", kw["zip_code"]),
                                ("city_id", "=", city.id),
                            ],
                            limit=1,
                        )

            donation_request_data = {
                "vat": kw["vat"],
                "campaign_id": campaign_id,
                "donation_amount": kw["donation_amount"],
                "firstname": kw["firstname"],
                "lastname": kw["lastname"],
                "email": kw["email"],
                "address": kw["address"],
                "zip_code": kw["zip_code"],
                "country_id": country.id,
                "phone": kw.get("phone", False),
                "source": "website",
                "state": "draft",
                "lang": lang.code,
                "tax_receipt_option": kw.get("tax_receipt_option", "none"),
            }

            # Añadir zip_id si se encontró un registro válido
            if zip_record:
                donation_request_data["zip_id"] = zip_record.id
                # Si el registro de zip tiene ciudad, usamos esa información
                if zip_record.city_id:
                    donation_request_data["city"] = zip_record.city_id.name
                    # Si la ciudad tiene estado/provincia, lo usamos también
                    if zip_record.city_id.state_id:
                        donation_request_data["state_id"] = zip_record.city_id.state_id.id

            if partner_id:
                donation_request_data["partner_id"] = partner_id

            donation_request = request.env["donation.request"].create(donation_request_data)

            _logger.info(f"Donation request created with ID: {donation_request.id}")

            # Incluir información adicional de la campaña en la respuesta
            campaign_info = {
                "id": campaign.id,
                "name": campaign.name,
                "state": campaign.state,
                "description": campaign.description or "",
                "global_objective": float(campaign.global_objective) if hasattr(campaign, 'global_objective') else 0.0,
                "progress": float(campaign.progress) if hasattr(campaign, 'progress') else 0.0,
                "source_objective_donation": float(campaign.source_objective_donation) if hasattr(campaign, 'source_objective_donation') else 0.0,
                "donation_raised_amount": float(campaign.donation_raised_amount) if hasattr(campaign, 'donation_raised_amount') else 0.0,
                "progress_donation": float(campaign.progress_donation) if hasattr(campaign, 'progress_donation') else 0.0,
            }

            # Añadir los nuevos campos si existen
            if hasattr(campaign, 'minimal_donation_amount'):
                campaign_info["minimal_donation_amount"] = float(campaign.minimal_donation_amount)

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": donation_request.id,
                        "name": donation_request.name,
                        "state": donation_request.state,
                        "donation_amount": donation_request.donation_amount,
                        "campaign": campaign_info,
                    },
                },
            }

        except Exception as e:
            _logger.error("Unexpected error: %s", traceback.format_exc())
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": 200, "message": str(e), "data": {"status": "error"}},
            }


