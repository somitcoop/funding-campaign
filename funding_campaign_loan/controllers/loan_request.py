# controllers/loan_request_api.py

from odoo import http
from odoo.http import request
import json

class LoanRequestApi(http.Controller):
    @http.route(
        "/api/loan/campaign/create",
        type="json",
        auth="none",
        csrf=False,
    )
    def create_loan_request(self, **kw):
        try:
            # Validación de autenticación
            db = request.httprequest.headers.get('X-Odoo-Db')
            username = request.httprequest.headers.get('X-Odoo-Username')
            api_key = request.httprequest.headers.get('X-Odoo-Api-Key')

            if not all([db, username, api_key]):
                return {'error': 'Missing authentication parameters', 'status': 'error'}

            uid = request.session.authenticate(db, username, api_key)
            if not uid:
                return {'error': 'Authentication failed', 'status': 'error'}

            # Validar campos requeridos
            required_fields = [
                "partner_id",
                "campaign_id",
                "template_id",
                "loan_amount",
                "firstname",
                "lastname",
                "email",
                "address",
                "city",
                "zip_code",
                "country_id",
            ]

            for field in required_fields:
                if field not in kw:
                    return {
                        "error": f"Missing required field: {field}",
                        "status": "error"
                    }

            # Validaciones específicas para préstamos
            template = request.env['funding.loan.template'].browse(kw['template_id'])
            if template.min_amount and kw['loan_amount'] < template.min_amount:
                return {
                    "error": f"Loan amount cannot be less than {template.min_amount}",
                    "status": "error"
                }
            if template.max_amount and kw['loan_amount'] > template.max_amount:
                return {
                    "error": f"Loan amount cannot be greater than {template.max_amount}",
                    "status": "error"
                }

            # Crear loan request
            loan_request = request.env['funding.loan.request'].create({
                'partner_id': kw['partner_id'],
                'campaign_id': kw['campaign_id'],
                'template_id': kw['template_id'],
                'loan_amount': kw['loan_amount'],
                'firstname': kw['firstname'],
                'lastname': kw['lastname'],
                'email': kw['email'],
                'address': kw['address'],
                'city': kw['city'],
                'zip_code': kw['zip_code'],
                'country_id': kw['country_id'],
                'source': kw.get('source', 'api'),
                'state': 'draft',
            })

            return {
                "jsonrpc": "2.0",
                "id": None,
                "result": {
                    "status": "success",
                    "data": {
                        "id": loan_request.id,
                        "name": loan_request.name,
                        "state": loan_request.state,
                        "loan_amount": loan_request.loan_amount
                    }
                }
            }

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": 200,
                    "message": str(e),
                    "data": {"status": "error"}
                }
            }
