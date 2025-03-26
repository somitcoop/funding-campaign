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
                "ordered_parts",
                "type",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "phone",
                "lang",
            ]

            _logger.info(f"Validating required fields. Current kw: {kw}")
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

            # Validar límites de suscripción
            ordered_amount = float(kw["ordered_parts"]) * campaign.share_product_id.list_price
            if hasattr(campaign, 'minimal_subscription_amount') and campaign.minimal_subscription_amount > 0:
                if ordered_amount < campaign.minimal_subscription_amount:
                    return {
                        "error": "Subscription amount below minimum",
                        "status": "error",
                        "details": f"The minimum subscription amount is {campaign.minimal_subscription_amount}",
                    }

            if hasattr(campaign, 'maximal_subscription_amount') and campaign.maximal_subscription_amount > 0:
                if ordered_amount > campaign.maximal_subscription_amount:
                    return {
                        "error": "Subscription amount above maximum",
                        "status": "error",
                        "details": f"The maximum subscription amount is {campaign.maximal_subscription_amount}",
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

            # Obtener todos los idiomas disponibles
            available_langs = request.env["res.lang"].search([])
            _logger.info(f"Available languages: {[(lang.code, lang.name) for lang in available_langs]}")

            lang = request.env["res.lang"].search([("code", "=", kw["lang"])], limit=1)
            if not lang:
                return {
                    "error": f"Invalid language code: {kw['lang']}. Available languages: {', '.join([lang.code for lang in available_langs])}",
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

            # Incluir información adicional de la campaña en la respuesta
            campaign_info = {
                "id": campaign.id,
                "name": campaign.name,
                "state": campaign.state,
                "description": campaign.description or "",
                "global_objective": float(campaign.global_objective) if hasattr(campaign, 'global_objective') else 0.0,
                "progress": float(campaign.progress) if hasattr(campaign, 'progress') else 0.0,
            }

            # Añadir los nuevos campos si existen
            if hasattr(campaign, 'minimal_subscription_amount'):
                campaign_info["minimal_subscription_amount"] = float(campaign.minimal_subscription_amount)
            if hasattr(campaign, 'maximal_subscription_amount'):
                campaign_info["maximal_subscription_amount"] = float(campaign.maximal_subscription_amount)

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": subscription.id,
                        "name": subscription.name,
                        "state": subscription.state,
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


spec.path(
    path="/api/campaign/{campaign_id}/subscription_request",
    operations={
        "post": {
            "tags": ["Campaign Subscriptions"],
            "summary": "Create a new campaign subscription request",
            "description": "Create a new subscription request with the provided partner and campaign information. The API integrates with the OCA base_location module to automatically find and set the zip_id based on the provided zip_code and country_code.",
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
                                "ordered_parts",
                                "type",
                                "firstname",
                                "lastname",
                                "email",
                                "address",
                                "zip_code",
                                "phone",
                                "lang",
                                "country_code",
                            ],
                            "properties": {
                                "vat": {
                                    "type": "string",
                                    "description": "VAT number of the subscriber",
                                },
                                "ordered_parts": {
                                    "type": "integer",
                                    "description": "Number of parts ordered",
                                },
                                "type": {
                                    "type": "string",
                                    "description": "Type of subscription request. 'increase' for increasing existing shares, 'increase_remunerated' for increasing remunerated shares.",
                                    "enum": ["increase", "increase_remunerated"],
                                    "example": "increase",
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
                                "zip_code": {
                                    "type": "string",
                                    "description": "Postal code. Used to find the corresponding zip_id from the base_location module.",
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
                                "country_code": {
                                    "type": "string",
                                    "description": "ISO 3166-1 alpha-2 country code (e.g. ES, FR, BE). Used with zip_code to find the corresponding location data.",
                                    "minLength": 2,
                                    "maxLength": 2,
                                    "required": False,
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
                                    "id": {"type": "null"},
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
                                                    "campaign": {
                                                        "type": "object",
                                                        "properties": {
                                                            "id": {
                                                                "type": "integer",
                                                                "description": "ID of the campaign",
                                                            },
                                                            "name": {
                                                                "type": "string",
                                                                "description": "Name of the campaign",
                                                            },
                                                            "state": {
                                                                "type": "string",
                                                                "description": "State of the campaign",
                                                            },
                                                            "description": {
                                                                "type": "string",
                                                                "description": "Description of the campaign",
                                                            },
                                                            "global_objective": {
                                                                "type": "number",
                                                                "description": "Global objective of the campaign",
                                                            },
                                                            "progress": {
                                                                "type": "number",
                                                                "description": "Progress of the campaign",
                                                            },
                                                            "minimal_subscription_amount": {
                                                                "type": "number",
                                                                "description": "Minimum subscription amount for the campaign",
                                                            },
                                                            "maximal_subscription_amount": {
                                                                "type": "number",
                                                                "description": "Maximum subscription amount for the campaign",
                                                            },
                                                        },
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
                                    "jsonrpc": {"type": "string", "example": "2.0"},
                                    "id": {"type": "null"},
                                    "error": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer"},
                                            "message": {"type": "string"},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "status": {"type": "string", "example": "error"},
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)
