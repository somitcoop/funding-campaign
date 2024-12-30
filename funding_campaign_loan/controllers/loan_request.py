from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
import traceback
from odoo.addons.swagger_docs.controllers.swagger_controller import spec

_logger = logging.getLogger(__name__)


class LoanRequestApi(http.Controller):
    @http.route(
        f"/api/campaign/<int:campaign_id>/loan_request",
        type="json",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def create_loan_request(self, campaign_id, **kw):
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
                    "details": "Loan requests can only be created for active campaigns",
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
                "loan_amount",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "country_id",
                "lang",
            ]

            for field in required_fields:
                if field not in kw:
                    _logger.warning(f"Missing required field: {field}")
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error",
                    }

            # Asegurarnos de que el campaign_id del payload coincide con la ruta
            if "campaign_id" in kw and kw["campaign_id"] != campaign_id:
                return {
                    "error": "Campaign ID mismatch between URL and payload",
                    "status": "error",
                }

            # Buscar partner por VAT si existe
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

            loan_request_data = {
                "vat": kw["vat"],
                "campaign_id": campaign_id,
                "template_id": request.env["funding.campaign"]
                .sudo()
                .browse(campaign_id)
                .template_id.id,
                "loan_amount": kw["loan_amount"],
                "firstname": kw["firstname"],
                "lastname": kw["lastname"],
                "email": kw["email"],
                "address": kw["address"],
                "city": kw["city"],
                "zip_code": kw["zip_code"],
                "country_id": kw["country_id"],
                "phone": kw["phone"],
                "source": "website",
                "state": "draft",
                "lang": kw["lang"],
            }

            # Añadir partner_id solo si existe
            if partner_id:
                loan_request_data["partner_id"] = partner_id

            loan_request = request.env["funding.loan.request"].create(loan_request_data)

            _logger.info(f"Loan request created with ID: {loan_request.id}")

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": loan_request.id,
                        "name": loan_request.name,
                        "state": loan_request.state,
                        "loan_amount": loan_request.loan_amount,
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


spec.path(
    path="/api/loan/{campaign_id}/create",
    operations={
        "post": {
            "tags": ["Campaign Loans"],
            "summary": "Create a new campaign loan request",
            "description": "Create a new loan request with the provided partner and campaign information",
            "parameters": [
                {
                    "in": "header",
                    "name": "X-Odoo-Db",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Odoo database name",
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Username",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Username for authentication",
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Api-Key",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "API key for authentication",
                },
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": [
                                "partner_id",
                                "loan_amount",
                                "loan_type_id",
                                "campaign_id",
                                "country_id",
                                "firstname",
                                "lastname",
                                "email",
                                "address",
                                "city",
                                "zip_code",
                                "phone",
                                "lang",
                            ],
                            "properties": {
                                "partner_id": {
                                    "type": "integer",
                                    "description": "ID of the partner requesting the loan",
                                },
                                "loan_amount": {
                                    "type": "number",
                                    "format": "float",
                                    "description": "Amount requested for the loan",
                                },
                                "loan_type_id": {
                                    "type": "integer",
                                    "description": "ID of the loan type",
                                },
                                "campaign_id": {
                                    "type": "integer",
                                    "description": "ID of the funding campaign",
                                },
                                "country_id": {
                                    "type": "integer",
                                    "description": "ID of the country",
                                },
                                "firstname": {
                                    "type": "string",
                                    "description": "First name of the loan requester",
                                },
                                "lastname": {
                                    "type": "string",
                                    "description": "Last name of the loan requester",
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "Email address",
                                },
                                "address": {
                                    "type": "string",
                                    "description": "Street address",
                                },
                                "city": {"type": "string", "description": "City name"},
                                "zip_code": {
                                    "type": "string",
                                    "description": "Postal code",
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Phone number",
                                },
                                "lang": {
                                    "type": "string",
                                    "description": "Language code",
                                },
                            },
                        }
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "result": {
                                        "type": "object",
                                        "properties": {
                                            "status": {
                                                "type": "string",
                                                "example": "success",
                                            },
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {
                                                        "type": "integer",
                                                        "description": "ID of created loan request",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name of loan request",
                                                    },
                                                    "state": {
                                                        "type": "string",
                                                        "description": "State of loan request",
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Error response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {
                                        "type": "string",
                                        "description": "Error message",
                                    },
                                    "status": {"type": "string", "example": "error"},
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)
