import json
from datetime import datetime, date
from odoo import http
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
import logging
import traceback
from odoo.addons.swagger_docs.controllers.swagger_controller import spec

_logger = logging.getLogger(__name__)


class FundingCampaignApi(http.Controller):
    def _check_auth(self, headers):
        """Helper method for authentication"""
        db = headers.get("X-Odoo-Db")
        username = headers.get("X-Odoo-Username")
        api_key = headers.get("X-Odoo-Api-Key")

        if not all([db, username, api_key]):
            return None, {
                "error": "Missing authentication parameters",
                "status": "error",
            }

        request.session.db = db
        user = (
            request.env["res.users"].sudo().search([("login", "=", username)], limit=1)
        )

        if not user:
            return None, {"error": "User not found", "status": "error"}

        try:
            temp_env = request.env(user=user.id)
            temp_env.user._check_credentials(api_key, {"interactive": False})
            return temp_env, None
        except AccessDenied:
            return None, {"error": "Authentication failed", "status": "error"}

    @http.route("/api/campaign", type="http", auth="none", csrf=False, methods=["GET"])
    def list_campaigns(self, **kw):
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        try:
            env, error = self._check_auth(request.httprequest.headers)
            if error:
                return error

            request.env = env
            campaigns = request.env["funding.campaign"].search([])

            campaign_data = [
                {
                    "id": campaign.id,
                    "name": campaign.name,
                    "start_date": campaign.start_date,
                    "end_date": campaign.end_date,
                    "is_permanent": campaign.is_permanent,
                    "state": campaign.state,
                    "global_objective": float(campaign.global_objective),
                    "progress": float(campaign.progress),
                }
                for campaign in campaigns
            ]

            return Response(
                json.dumps(
                    {"status": "success", "data": campaign_data}, default=json_serial
                ),
                mimetype="application/json",
            )

        except Exception as e:
            _logger.error("Unexpected error: %s", traceback.format_exc())
            return Response(
                json.dumps({"status": "error", "message": str(e)}),
                status=500,
                mimetype="application/json",
            )

    @http.route(
        "/api/campaign/<int:campaign_id>",
        type="http",  # Cambiado de 'json' a 'http'
        auth="none",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_campaign(self, campaign_id, **kwargs):
        if not isinstance(campaign_id, int) or campaign_id <= 0:
            return json.dumps({"error": "Invalid campaign ID"}), 400
        try:
            campaign = request.env["funding.campaign"].sudo().browse(campaign_id)
            if not campaign.exists():
                return json.dumps({"error": "Campaign not found"}), 404

            data = {
                "id": campaign.id,
                "name": campaign.name,
                # Añade aquí más campos según necesites
            }
            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)}), 500


# Documentación Swagger
spec.path(
    path="/api/campaign",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "List all campaigns",
            "description": "Get a list of all funding campaigns with basic information",
            "parameters": [
                {
                    "in": "header",
                    "name": "X-Odoo-Db",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Username",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Api-Key",
                    "required": True,
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of campaigns",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "data": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer"},
                                                "name": {"type": "string"},
                                                "start_date": {
                                                    "type": "string",
                                                    "format": "date",
                                                },
                                                "end_date": {
                                                    "type": "string",
                                                    "format": "date",
                                                },
                                                "is_permanent": {"type": "boolean"},
                                                "state": {"type": "string"},
                                                "global_objective": {"type": "number"},
                                                "progress": {"type": "number"},
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                }
            },
        }
    },
)

spec.path(
    path="/api/campaign/{campaign_id}",
    operations={
        "get": {
            "tags": ["Campaigns"],
            "summary": "Get campaign details",
            "description": "Get detailed information about a specific campaign",
            "parameters": [
                {
                    "in": "path",
                    "name": "campaign_id",
                    "required": True,
                    "schema": {"type": "integer"},
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Db",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Username",
                    "required": True,
                    "schema": {"type": "string"},
                },
                {
                    "in": "header",
                    "name": "X-Odoo-Api-Key",
                    "required": True,
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "Campaign details",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "success"},
                                    "data": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                            "start_date": {
                                                "type": "string",
                                                "format": "date",
                                            },
                                            "end_date": {
                                                "type": "string",
                                                "format": "date",
                                            },
                                            "is_permanent": {"type": "boolean"},
                                            "state": {"type": "string"},
                                            "global_objective": {"type": "number"},
                                            "progress": {"type": "number"},
                                            "sources": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"},
                                                        "source_type": {
                                                            "type": "string"
                                                        },
                                                        "objective": {"type": "number"},
                                                        "raised_amount": {
                                                            "type": "number"
                                                        },
                                                        "progress": {"type": "number"},
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                }
            },
        }
    },
)
