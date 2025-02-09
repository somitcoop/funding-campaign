from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
import logging
import traceback
from odoo.addons.swagger_docs.controllers.swagger_controller import spec


_logger = logging.getLogger(__name__)


class CooperatorVoluntaryApi(http.Controller):
    @http.route(
        "/api/campaign/<int:campaign_id>/subscription_request",
        type="json",
        auth="none",
        csrf=False,
        methods=["POST"],
    )
    def create_subscription(self, campaign_id, **kw):
        """
        Creates a new subscription request with the provided data.
        tags:
            - Subscriptions
        summary: Create a new subscription request
        description: Create a new subscription request with the provided partner and campaign information.
        parameters:
            - in: header
                name: X-Odoo-Db
                required: true
                description: Odoo database name
            - in: header
                name: X-Odoo-Username
                required: true
                description: Username for authentication
            - in: header
                name: X-Odoo-Api-Key
                required: true
                description: API key for authentication
            required: true
                            - partner_id
                            - ordered_parts
                            - share_product_id
                            - source
                            - type
                            - campaign_id
                            - country_id
                            - firstname
                            - lastname
                            - email
                            - address
                            - city
                            - zip_code
                            - phone
                            - lang
                            partner_id:
                                description: ID of the partner
                            ordered_parts:
                                description: Number of parts ordered
                            share_product_id:
                                description: ID of the share product
                            source:
                                description: Source of the subscription
                            type:
                                description: Type of subscription
                            campaign_id:
                                description: ID of the funding campaign
                            country_id:
                                description: ID of the country
                            firstname:
                                description: First name of the subscriber
                            lastname:
                                description: Last name of the subscriber
                            email:
                                description: Email address
                            address:
                                description: Street address
                            city:
                                description: City name
                            zip_code:
                                description: Postal code
                            phone:
                                description: Phone number
                            lang:
                                description: Language code
                description: Successful response
                                jsonrpc:
                                    example: "2.0"
                                    type: null
                                result:
                                        status:
                                            example: "success"
                                        data:
                                                    description: ID of created subscription
                                                    description: Name of subscription
                                                state:
                                                    description: State of subscription
            400:
                description: Error response
                                error:
                                    description: Error message
                                status:
                                    example: "error"
        """
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
                "ordered_parts",
                "type",
                "country_code",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "phone",
                "lang",
            ]

            for field in required_fields:
                if field not in kw:
                    _logger.warning(f"Missing required field: {field}")
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error",
                    }


            campaign = request.env["funding.campaign"].browse(campaign_id)
            if not campaign.exists():
                _logger.warning(f"Campaign not found: {campaign_id}")
                return {"error": "Campaign not found", "status": "error"}

            if "campaign_id" in kw and kw["campaign_id"] != campaign_id:
                return {
                    "error": "Campaign ID mismatch between URL and payload",
                    "status": "error",
                }

            if campaign.state != "open":
                _logger.warning(
                    f"Campaign {campaign.name} is not open (current state: {campaign.state})"
                )
                return {
                    "error": "Campaign is not active",
                    "status": "error",
                    "details": "Subscriptions can only be created for active campaigns",
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

            VALID_TYPES = ["increase", "increase_remunerated"]
            if kw["type"] not in VALID_TYPES:
                return {
                    "error": f"Invalid subscription type. Must be one of: {', '.join(VALID_TYPES)}",
                    "status": "error",
                }

            lang = request.env["res.lang"].search([("code", "=", kw["lang"])], limit=1)
            if not lang:
                return {
                    "error": f"Invalid language code: {kw['lang']}",
                    "status": "error",
                }

            subscription_data = {
                "vat": kw["vat"],
                "campaign_id": campaign_id,
                "share_product_id": request.env["funding.campaign"]
                .sudo()
                .browse(campaign_id)
                .share_product_id.id,
                "ordered_parts": kw["ordered_parts"],
                "type": kw["type"],
                "firstname": kw["firstname"],
                "lastname": kw["lastname"],
                "email": kw["email"],
                "address": kw["address"],
                "city": kw["city"],
                "zip_code": kw["zip_code"],
                "country_id": country.id,
                "phone": kw["phone"],
                "source": "website",
                "lang": lang.code,
            }

            if partner_id:
                subscription_data["partner_id"] = partner_id

            subscription = request.env["subscription.request"].create(subscription_data)

            _logger.info(f"Subscription created with ID: {subscription.id}")

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": subscription.id,
                        "name": subscription.name,
                        "state": subscription.state,
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
    path="/api/campaign/{campaign_id}/subscription_request",
    operations={
        "post": {
            "tags": ["Campaign Subscriptions"],
            "summary": "Create a new campaign subscription request",
            "description": "Create a new subscription request with the provided partner and campaign information",
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
                                "ordered_parts",
                                "share_product_id",
                                "source",
                                "type",
                                "campaign_id",
                                "country_code",
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
                                    "description": "ID of the partner",
                                },
                                "ordered_parts": {
                                    "type": "integer",
                                    "description": "Number of parts ordered",
                                },
                                "share_product_id": {
                                    "type": "integer",
                                    "description": "ID of the share product",
                                },
                                "source": {
                                    "type": "string",
                                    "description": "Source of the subscription",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Type of subscription request. 'increase' for increasing existing shares, 'increase_remunerated' for increasing remunerated shares.",
                                    "enum": ["increase", "increase_remunerated"],
                                    "example": "increase",
                                },
                                "campaign_id": {
                                    "type": "integer",
                                    "description": "ID of the funding campaign",
                                },
                                "country_code": {
                                    "type": "string",
                                    "description": "ISO 3166-1 alpha-2 country code (e.g. ES, FR, BE)",
                                    "minLength": 2,
                                    "maxLength": 2,
                                },
                                "firstname": {
                                    "type": "string",
                                    "description": "First name of the subscriber",
                                },
                                "lastname": {
                                    "type": "string",
                                    "description": "Last name of the subscriber",
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
                                    "description": "Language code (ISO 639-1) with optional country code (e.g. en_US, es_ES, fr_FR)",
                                    "example": "en_US",
                                    "pattern": "^[a-z]{2,3}(_[A-Z]{2})?$",
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
                                                        "description": "ID of created subscription",
                                                    },
                                                    "name": {
                                                        "type": "string",
                                                        "description": "Name of subscription",
                                                    },
                                                    "state": {
                                                        "type": "string",
                                                        "description": "State of subscription",
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
