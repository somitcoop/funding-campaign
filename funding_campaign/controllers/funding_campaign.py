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
        type="http",
        auth="none",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def get_campaign(self, campaign_id, **kwargs):
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return str(obj)

        try:
            if not isinstance(campaign_id, int) or campaign_id <= 0:
                return Response(
                    json.dumps({"status": "error", "message": "Invalid campaign ID"}),
                    status=400,
                    mimetype="application/json",
                )

            env, error = self._check_auth(request.httprequest.headers)
            if error:
                return Response(
                    json.dumps(error),
                    status=401,
                    mimetype="application/json",
                )

            request.env = env
            campaign = request.env["funding.campaign"].browse(campaign_id)

            if not campaign.exists():
                return Response(
                    json.dumps({"status": "error", "message": "Campaign not found"}),
                    status=404,
                    mimetype="application/json",
                )

            campaign_data = {
                "id": campaign.id,
                "name": campaign.name,
                "description": campaign.description or "",
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "is_permanent": campaign.is_permanent,
                "state": campaign.state,
                "global_objective": float(campaign.global_objective),
                "progress": float(campaign.progress),
                "progress_percentage": (
                    round(
                        (float(campaign.current_amount) / float(campaign.target_amount))
                        * 100,
                        2,
                    )
                    if campaign.target_amount
                    else 0
                ),
            }

            # Añadir fuentes de financiación si están disponibles
            if hasattr(campaign, 'source_ids'):
                sources = []
                for source in campaign.source_ids:
                    sources.append({
                        "id": source.id,
                        "name": source.name,
                        "source_type": source.source_type if hasattr(source, 'source_type') else "",
                        "objective": float(source.objective) if hasattr(source, 'objective') else 0.0,
                        "raised_amount": float(source.raised_amount) if hasattr(source, 'raised_amount') else 0.0,
                        "progress": float(source.progress) if hasattr(source, 'progress') else 0.0,
                    })
                campaign_data["sources"] = sources

            return Response(
                json.dumps(
                    {"status": "success", "data": campaign_data},
                    default=json_serial
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
                                                    "format": "date-time",
                                                },
                                                "end_date": {
                                                    "type": "string",
                                                    "format": "date-time",
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
                },
                "401": {
                    "description": "Authentication failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "status": {"type": "string", "example": "error"},
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
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
                    "description": "ID of the campaign to retrieve",
                },
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
                                            "description": {"type": "string"},
                                            "start_date": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
                                            "end_date": {
                                                "type": "string",
                                                "format": "date-time",
                                            },
                                            "is_permanent": {"type": "boolean"},
                                            "state": {"type": "string"},
                                            "global_objective": {"type": "number"},
                                            "progress": {"type": "number"},
                                            "progress_percentage": {"type": "number"},
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
                },
                "400": {
                    "description": "Bad request",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "401": {
                    "description": "Authentication failed",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "error": {"type": "string"},
                                    "status": {"type": "string", "example": "error"},
                                },
                            }
                        }
                    },
                },
                "404": {
                    "description": "Campaign not found",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string", "example": "error"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                },
            },
        }
    },
)
