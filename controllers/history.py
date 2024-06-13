import datetime
from odoo import http, _
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)


class History(http.Controller):

    # Get the history for a partner
    @http.route('/get_history', type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def get_history(self, **kw):
        try:
            _logger.info('get_history: Parameters - %s', kw)
            page = int(kw.get('page', 1))
            limit = int(kw.get('limit', 5))
            offset = (page - 1) * limit
            
            partner_id = kw.get('partner_id')
            if not partner_id:
                return request.make_response(json.dumps({'error': 'Parameter partner_id is required', 'status': 400}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=400)

            domain = [('partner_id', '=', int(partner_id))]
            
            # Count total records without fetching all data
            total_records = request.env['factures.salesperson.history'].sudo().search_count(domain)
            
            # Fetch limited records
            history = request.env['factures.salesperson.history'].sudo().search(domain, offset=offset, limit=limit, order='date desc')

            data = []
            for h in history:
                history_data = {
                    'partner_id': h.partner_id.id,
                    'salesperson_route_id': h.salesperson_route_id.id,
                    'date': h.date.strftime('%d-%m-%Y'),
                    'total_pages': (total_records // limit) + (1 if total_records % limit else 0),
                    'company_id': h.salesperson_route_id.salesperson_id.company_id.id,
                    'lines': []
                }
                for line in h.factures_salesperson_history_lines:
                    history_data['lines'].append({
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.name,
                        'product_code': line.product_id.default_code,
                        'product_qty': line.product_qty,
                        'product_packaging_qty': line.product_packaging_qty,
                        'product_packaging_id': line.product_id.packaging_ids[0].id if line.product_id.packaging_ids else '',
                        'product_packaging_name': line.product_id.packaging_ids[0].name if line.product_id.packaging_ids else '',
                        'qty_packaging': line.product_id.packaging_ids[0].qty if line.product_id.packaging_ids else 1,
                                                             
                    })
                data.append(history_data)

            return request.make_response(json.dumps(data, ensure_ascii=False), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error('Error in get_history: %s', str(e))
            return request.make_response(json.dumps({'error': str(e), 'status':500}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=500)

       

    @http.route('/update_quantity', type='http', auth='public', website=True, methods=['PUT'], csrf=False)
    def update_quantity(self, **kw):
        _logger.info('update_quantity: Parameters - %s', kw)
        try:
            request_data = json.loads(request.httprequest.data)
            
            required_fields = ['partner_id', 'salesperson_route_id', 'date', 'product_id', 'quantity']
            for field in required_fields:
                if field not in request_data:
                    return request.make_response(json.dumps({'error': f'Missing required field: {field}'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=400)
            
            partner_id = request_data.get('partner_id')
            salesperson_route_id = request_data.get('salesperson_route_id')
            date = request_data.get('date')
            product_id = request_data.get('product_id')
            quantity = request_data.get('quantity')
            
            domain = [('partner_id', '=', int(partner_id)),
                      ('salesperson_route_id', '=', int(salesperson_route_id)),
                      ('date', '=', date)]
            history = request.env['factures.salesperson.history'].sudo().search(domain)

            if not history:
                history = request.env['factures.salesperson.history'].sudo().create({
                    'partner_id': int(partner_id),
                    'salesperson_route_id': int(salesperson_route_id),
                    'date': date
                })
                
            line = history.factures_salesperson_history_lines.filtered(lambda l: l.product_id.id == int(product_id))
            
            if line:
                # If quantity is empty, delete the line
                line.write({'quantity': quantity})
                if line.quantity == "":
                    line.unlink()
            elif quantity != "":
                request.env['factures.salesperson.history.line'].sudo().create({
                    'factures_salesperson_history_id': history.id,
                    'product_id': int(product_id),
                    'quantity': quantity
                })
            
            return request.make_response(json.dumps({'message': 'Quantity updated successfully'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error('Error in update_quantity: %s', str(e))
            return request.make_response(json.dumps({'error': str(e)}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=500)


    @http.route('/update_all', type='json', auth='public', website=True, methods=['POST'], csrf=False)
    def update_all(self, **kw):
        try:
            request_data = json.loads(request.httprequest.data)

            # Ensure all required fields are present in the JSON data
            required_fields = ['quantities', 'client_id', 'route_id', 'client_name', 'client_code', 'page', 'route_name']
            for field in required_fields:
                if field not in request_data:
                    return {'error': f'Missing required field: {field}', 'status': 400}

            quantities = request_data['quantities']
            client_id = int(request_data['client_id'])
            route_id = int(request_data['route_id'])


            for product_id, quantities_per_date in quantities.items():
                # Extract qty_packaging value
                unit = float(quantities_per_date.pop('unit', 1))

                for date, quantity in quantities_per_date.items():
                    # Extract date in the correct format
                    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

                    product_id = int(product_id)
                    
                    # Check if quantity is not an empty string
                    if quantity:
                        quantity = float(quantity)  # Extract the product_packaging_qty value
                    else:
                        quantity = 0.0  # Default to 0 if quantity is empty string

                    # Find or create history
                    history = request.env['factures.salesperson.history'].sudo().search([
                        ('partner_id', '=', client_id),
                        ('salesperson_route_id', '=', route_id),
                        ('date', '=', date)
                    ], limit=1)

                    if not history:
                        history = request.env['factures.salesperson.history'].sudo().create({
                            'partner_id': client_id,
                            'salesperson_route_id': route_id,
                            'date': date
                        })

                    # Find history line
                    line = history.factures_salesperson_history_lines.filtered(lambda l: l.product_id.id == product_id)
                    if line:
                        # If quantity is empty in the payload, remove the value
                        if quantity == 0:
                            line.unlink()
                        else:
                            line.write({'product_packaging_qty': quantity, 'qty_packaging': unit})
                    elif quantity != 0:
                        request.env['factures.salesperson.history.line'].sudo().create({
                            'factures_salesperson_history_id': history.id,
                            'product_id': product_id,
                            'product_packaging_qty': quantity,
                            'qty_packaging': unit
                        })
            for product_id, quantities_per_date in quantities.items():
                for date, quantity in quantities_per_date.items():
                    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                    history = request.env['factures.salesperson.history'].sudo().search([
                        ('partner_id', '=', client_id),
                        ('salesperson_route_id', '=', route_id),
                        ('date', '=', date)
                    ], limit=1)
                    if history and not history.factures_salesperson_history_lines:
                        history.unlink()
                    

            return {'message': 'Quantities updated successfully', 'status': 200}, 200

        except Exception as e:
            _logger.error('Error in update_all: %s', str(e))
            return {'error': str(e), 'status': 500}, 500

