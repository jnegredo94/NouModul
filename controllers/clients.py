from odoo import http, _
from odoo.http import request
import logging
import json

_logger = logging.getLogger(__name__)

class Client(http.Controller):
    
    @http.route('/get_clients',type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def get_clients(self, **kw):
        try:
            _logger.info('get_clients: Parameters - %s', kw)
            id = kw.get('id', False)
            name = kw.get('name', False)
            ref = kw.get('ref', False)
            codi_intern = kw.get('codi_intern', False)
            route_id = kw.get('route_id', False)
            page = kw.get('page', 1)
            limit = kw.get('limit', 100)
            offset = (int(page) - 1) * int(limit)
            if offset <= 0:
                offset = 1
                            
            #Check if the parameters are the correct type
            if id and not id.isdigit():
                return request.make_response(json.dumps({'error': 'Invalid id'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=400)
            if route_id and not route_id.isdigit():
                return request.make_response(json.dumps({'error': 'Invalid route_id'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=400)
                   
            domain = []
            if id:
                #f
                domain.append(('id', '=', id))
            if name:
                domain.append(('name', 'ilike', name))
            if ref:
                domain.append(('ref', 'ilike', ref))
            if codi_intern:
                domain.append(('x_studio_codi_intern', 'ilike', codi_intern))
            if route_id:
                domain.append(('salesperson_route_id.id', '=', route_id))
            
            clients = request.env['res.partner'].sudo().search(domain)
            
            data = {
                'clients': []
            }
            for client in clients:
                data['clients'].append({
                    'id': client.id,
                    'name': client.name,
                    'email': client.email,
                    'phone': client.phone,
                    'mobile': client.mobile,
                    'ref': client.ref,
                    'codi_intern': client.x_studio_codi_intern,
                })
            
            return request.make_response(json.dumps(data, ensure_ascii=False), headers=[('Content-Type', 'application/json')])
        except Exception as e:
            _logger.error('Error in get_clients: %s', str(e))
            return request.make_response(json.dumps({'error': 'Internal Server Error'}, ensure_ascii=False), headers=[('Content-Type', 'application/json')], status=500)
