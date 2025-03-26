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
            _logger.info(f"Received data: {kw}")
            _logger.info(f"Request body: {request.httprequest.get_data()}")
            _logger.info(f"Request headers: {request.httprequest.headers}")
            _logger.info(f"Request content type: {request.httprequest.content_type}")
            _logger.info(f"Request params: {request.params}")

            # Obtener los datos del body
            try:
                body = request.httprequest.get_data().decode('utf-8')
                _logger.info(f"Raw request data: {body}")
                import json
                data = json.loads(body)
                _logger.info(f"Parsed JSON data: {data}")

                # Si los datos vienen en el formato JSON-RPC, extraerlos de params
                if isinstance(data, dict) and 'params' in data:
                    kw.update(data['params'])
                    _logger.info(f"Updated kw with params: {kw}")
            except Exception as e:
                _logger.error(f"Error parsing JSON: {str(e)}")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": 200,
                        "message": f"Invalid JSON data: {str(e)}",
                        "data": {"status": "error"}
                    }
                }

            db = request.httprequest.headers.get("X-Odoo-Db")
            username = request.httprequest.headers.get("X-Odoo-Username")
            api_key = request.httprequest.headers.get("X-Odoo-Api-Key")

            if not all([db, username, api_key]):
                _logger.warning("Missing authentication parameters.")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": 200,
                        "message": "Missing authentication parameters",
                        "data": {"status": "error"}
                    }
                }

            request.session.db = db

            _logger.info(f"Searching user: {username}")
            user = (
                request.env["res.users"]
                .sudo()
                .search([("login", "=", username)], limit=1)
            )

            if not user:
                _logger.warning(f"User not found: {username}")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": 200,
                        "message": "User not found",
                        "data": {"status": "error"}
                    }
                }

            try:
                user.ensure_one()
            except ValueError:
                _logger.error(f"Multiple users found with login: {username}")
                return {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": 200,
                        "message": "Multiple users found with same login",
                        "data": {"status": "error"}
                    }
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
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": 200,
                        "message": f"Invalid language code: {kw['lang']}",
                        "data": {"status": "error"}
                    }
                }

            donation_request_data = {
                "vat": kw["vat"],
                "campaign_id": campaign_id,
                "donation_amount": kw["donation_amount"],
                "firstname": kw["firstname"],
                "lastname": kw["lastname"],
                "email": kw["email"],
                "address": kw["address"],
                "zip_code": kw["zip_code"],
                "city": kw.get("city", False),
                "country_id": country.id,
                "phone": kw.get("phone", False),
                "source": "website",
                "state": "draft",
                "lang": lang.code,
                "tax_receipt_option": kw.get("tax_receipt_option", "none"),
            }

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


