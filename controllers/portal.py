# -*- coding: utf-8 -*-

from odoo import http, _, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import UserError, ValidationError, AccessError
from collections import OrderedDict
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from datetime import timedelta
import logging
import json

_logger = logging.getLogger(__name__)

class StockMarketPortal(CustomerPortal):
    
    _items_per_page = 20

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        
        if 'order_count' in counters:
            values['order_count'] = request.env['stock.order'].search_count([
                ('user_id', '=', user.id)
            ]) if user.user_type == 'investor' else 0
        
        if 'position_count' in counters:
            values['position_count'] = request.env['stock.position'].search_count([
                ('user_id', '=', user.id)
            ]) if user.user_type == 'investor' else 0
        
        if 'trade_count' in counters:
            trade_domain = ['|', ('buyer_id', '=', user.id), ('seller_id', '=', user.id)]
            # Removed broker-specific trade filtering since default broker functionality removed
            values['trade_count'] = request.env['stock.trade'].search_count(trade_domain)
        
        if 'deposit_count' in counters:
            deposit_domain = [('user_id', '=', user.id)]
            if user.user_type == 'banker':
                deposit_domain = [('banker_id', '=', user.id)]
            values['deposit_count'] = request.env['stock.deposit'].search_count(deposit_domain)
        
        if 'loan_count' in counters:
            loan_domain = [('user_id', '=', user.id)]
            if user.user_type == 'banker':
                loan_domain = [('banker_id', '=', user.id)]
            values['loan_count'] = request.env['stock.loan'].search_count(loan_domain)
        
        return values

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Redirect /my to /market to make it the main entry point"""
        return request.redirect('/market')

    # Portfolio View
    @http.route(['/my/portfolio', '/my/portfolio/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_portfolio(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'banker'] and not is_system_admin:
            return request.redirect('/my')
        
        Position = request.env['stock.position']
        domain = [('user_id', '=', user.id)]
        
        searchbar_sortings = {
            'security': {'label': _('Security'), 'order': 'security_id'},
            'value': {'label': _('Market Value'), 'order': 'market_value desc'},
            'pnl': {'label': _('P&L'), 'order': 'unrealized_pnl desc'},
        }
        
        if not sortby:
            sortby = 'value'
        order = searchbar_sortings[sortby]['order']
        
        # Position count
        position_count = Position.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/portfolio",
            url_args={'sortby': sortby},
            total=position_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        positions = Position.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'user': user,
            'positions': positions,
            'page_name': 'portfolio',
            'pager': pager,
            'default_url': '/my/portfolio',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
        })
        
        return request.render("stock_market_simulation.portal_my_portfolio", values)

    # Orders View
    @http.route(['/my/orders', '/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type != 'investor' and not is_system_admin:
            return request.redirect('/my')
        
        Order = request.env['stock.order']
        domain = [('user_id', '=', user.id)]
        
        searchbar_sortings = {
            'date': {'label': _('Order Date'), 'order': 'order_date desc'},
            'name': {'label': _('Order Number'), 'order': 'name'},
            'status': {'label': _('Status'), 'order': 'status'},
        }
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'submitted': {'label': _('Submitted'), 'domain': [('status', '=', 'submitted')]},
            'filled': {'label': _('Filled'), 'domain': [('status', '=', 'filled')]},
            'cancelled': {'label': _('Cancelled'), 'domain': [('status', '=', 'cancelled')]},
        }
        
        # Default values
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
        
        domain += searchbar_filters[filterby]['domain']
        
        # Date filter
        if date_begin and date_end:
            domain += [('order_date', '>', date_begin), ('order_date', '<=', date_end)]
        
        order = searchbar_sortings[sortby]['order']
        
        # Order count
        order_count = Order.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/orders",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=order_count,
            page=page,
            step=self._items_per_page
        )
        
        # Content
        orders = Order.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'user': user,
            'date': date_begin,
            'orders': orders,
            'page_name': 'order',
            'pager': pager,
            'default_url': '/my/orders',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        
        return request.render("stock_market_simulation.portal_my_orders", values)

    # Order Entry
    @http.route(['/my/order/new'], type='http', auth="user", website=True)
    def portal_order_new(self, **kw):
        """Order creation page - for investors, brokers, and admins"""
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Allow investors, brokers, and admins
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'broker', 'admin'] and not is_system_admin:
            return request.redirect('/my')
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        if not active_session:
            values['error'] = "No active trading session"
            return request.render("stock_market_simulation.portal_order_new", values)
        
        # Get securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # For brokers and admins: Get all investors (can place orders for any investor)
        clients = []
        client_positions = []
        if user.user_type in ['broker', 'admin']:
            clients = request.env['res.users'].search([
                ('user_type', '=', 'investor'),
                ('active', '=', True)
            ])
            # Get positions for all clients (for sell orders)
            client_positions = request.env['stock.position'].search([
                ('user_id', 'in', clients.ids),
                ('available_quantity', '>', 0)
            ])
        else:  # investor
            # Get their own positions for sell orders
            client_positions = request.env['stock.position'].search([
                ('user_id', '=', user.id),
                ('available_quantity', '>', 0)
            ])
        
        values.update({
            'user': user,
            'securities': securities,
            'clients': clients,
            'client_positions': client_positions,
            'active_session': active_session,        })
        
        return request.render("stock_market_simulation.portal_order_new", values)

    @http.route(['/my/order/create'], type='json', auth="user", website=True)
    def portal_order_create(self, **kw):
        user = request.env.user
        
        # Check if current user is blocked
        block_check = request.env['stock.user.block'].check_user_blocked(user.id)
        if block_check['is_blocked']:
            return {'error': f"Access denied: {block_check['reason']}. Blocked until: {block_check['blocked_until']}", 'type': 'blocked'}
        
        # Allow brokers and admins to place orders on behalf of clients
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type in ['broker', 'admin'] or is_system_admin:
            client_id = kw.get('client_id')
            if not client_id:
                return {'error': 'Client must be selected'}
            
            client = request.env['res.users'].browse(int(client_id))
            if not client or client.user_type != 'investor':
                return {'error': 'Invalid client selected'}
            
            # Check if client is blocked
            client_block_check = request.env['stock.user.block'].check_user_blocked(client.id)
            if client_block_check['is_blocked']:
                return {'error': f"Client is blocked: {client_block_check['reason']}. Blocked until: {client_block_check['blocked_until']}", 'type': 'blocked'}
            
            # Use client for order creation
            order_user = client
        elif user.user_type == 'investor':
            return {'error': 'Investors cannot place orders directly. Please contact your broker.'}
        else:
            return {'error': 'Unauthorized'}
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        if not active_session:
            return {'error': 'No active trading session'}
        
        try:
            # Create order on behalf of client (status decided by action_submit)
            order_vals = {
                'user_id': order_user.id,  # Client who owns the order
                'session_id': active_session.id,
                'security_id': int(kw.get('security_id')),
                'side': kw.get('side'),
                'order_type': kw.get('order_type'),
                'quantity': int(kw.get('quantity')),
                'price': float(kw.get('price', 0)),
                'entered_by_id': user.id,
            }
            
            # Additional validation with user-friendly messages
            security = request.env['stock.security'].browse(int(kw.get('security_id')))
            quantity = int(kw.get('quantity'))
            price = float(kw.get('price', 0))
            side = kw.get('side')
            order_type = kw.get('order_type')
            
            # IPO order specific validations
            if order_type == 'ipo':
                # Validate security is in IPO/PO status
                if security.ipo_status not in ['ipo', 'po']:
                    return {'error': f'{security.symbol} is not available for IPO orders (status: {security.ipo_status})', 'type': 'validation'}
                
                # IPO orders are always buy orders
                if side != 'buy':
                    return {'error': 'IPO orders can only be buy orders', 'type': 'validation'}
                
                # For IPO orders, price is not used (set during allocation)
                order_vals['price'] = 0.0
                
                # Basic cash check (will be validated again during allocation with actual IPO price)
                if security.ipo_price > 0:
                    estimated_cost = security.ipo_price * quantity
                    if order_user.cash_balance < estimated_cost:
                        return {'error': f'Client insufficient funds for estimated IPO cost. Estimated: ${estimated_cost:,.2f}, Available: ${order_user.cash_balance:,.2f}', 'type': 'validation'}
            else:
                # Regular order validations
                # Check price limits (±20% of current market price as per User Stories)
                current_price = security.current_price
                if current_price > 0:
                    price_limit_low = current_price * 0.8
                    price_limit_high = current_price * 1.2
                    
                    if price < price_limit_low or price > price_limit_high:
                        return {'error': f'Price ${price:.2f} is outside allowed range (${price_limit_low:.2f} - ${price_limit_high:.2f}). Current market price: ${current_price:.2f}', 'type': 'validation'}
                
                # Check minimum order value
                if price * quantity < 100:  # Assuming min order value of $100
                    return {'error': f'Order value (${price * quantity:.2f}) is below minimum required ($100.00)', 'type': 'validation'}
                
                # Check client cash balance for buy orders (include broker fees)
                if side == 'buy':
                    broker_fee_rate = active_session.broker_commission_rate or 0.0
                    total_cost = price * quantity * (1 + broker_fee_rate / 100)
                    if order_user.cash_balance < total_cost:
                        return {'error': f'Client insufficient funds (including {broker_fee_rate}% broker fee). Required: ${total_cost:,.2f}, Available: ${order_user.cash_balance:,.2f}', 'type': 'validation'}
            
            # Check client position for sell orders
            if side == 'sell':
                position = request.env['stock.position'].search([
                    ('user_id', '=', order_user.id),
                    ('security_id', '=', int(kw.get('security_id')))
                ], limit=1)
                
                # Calculate available quantity (total - pending sell orders)
                total_quantity = position.quantity if position else 0
                pending_sell_orders = request.env['stock.order'].search([
                    ('user_id', '=', order_user.id),
                    ('security_id', '=', int(kw.get('security_id'))),
                    ('side', '=', 'sell'),
                    ('status', 'in', ['draft', 'submitted', 'open', 'partial'])
                ])
                pending_sell_quantity = sum(pending_sell_orders.mapped('remaining_quantity'))
                available_quantity = total_quantity - pending_sell_quantity
                
                if available_quantity < quantity:
                    return {'error': f'Client insufficient shares. Required: {quantity:,}, Available: {available_quantity:,} (Total: {total_quantity:,}, Pending Sells: {pending_sell_quantity:,})', 'type': 'validation'}
            
            # Create the order, then submit to set correct status (open/submitted)
            # Use sudo for creation but explicitly set entered_by_id to current user
            order = request.env['stock.order'].sudo().create(order_vals)
            try:
                order.sudo().action_submit()
            except Exception as e:
                # Rollback create if submit fails
                order.unlink()
                return {'error': f'Failed to submit order: {str(e)}'}
            
            # Log the broker action
            order.message_post(
                body=f"Order placed by broker {user.name} on behalf of client {order_user.name}",
                message_type='comment'
            )
            
            return {
                'success': True,
                'message': f'Order #{order.name} placed successfully for client {order_user.name}',
                'order_id': order.id
            }
            
        except Exception as e:
            return {'error': str(e)}

    @http.route(['/my/order/submit'], type='http', auth="user", methods=['POST'], website=True, csrf=False)
    def portal_order_submit(self, **kw):
        """HTTP endpoint for order submission with better error handling"""
        _logger.info(f"ORDER SUBMIT ENDPOINT CALLED - User: {request.env.user.name} ({request.env.user.user_type})")
        _logger.info(f"ORDER SUBMIT DATA: {kw}")
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            # Validate required fields
            required_fields = ['security_id', 'side', 'order_type', 'quantity']
            for field in required_fields:
                if not kw.get(field):
                    return request.make_response(
                        json.dumps({'success': False, 'error': f'Missing required field: {field}'}),
                        headers=[('Content-Type', 'application/json')]
                    )
            
            # Allow brokers and admins to place orders on behalf of clients/investors
            if user.user_type in ['broker', 'admin'] or is_system_admin:
                # Support both client_id (old) and investor_id (new) parameters
                client_id = kw.get('client_id') or kw.get('investor_id')
                if not client_id:
                    return request.make_response(
                        json.dumps({'success': False, 'error': 'Investor must be selected'}),
                        headers=[('Content-Type', 'application/json')]
                    )
                
                client = request.env['res.users'].browse(int(client_id))
                if not client or client.user_type != 'investor':
                    return request.make_response(
                        json.dumps({'success': False, 'error': 'Invalid investor selected'}),
                        headers=[('Content-Type', 'application/json')]
                    )
                
                # Use client for order creation
                order_user = client
            elif user.user_type == 'investor':
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Investors cannot place orders directly. Please contact your broker.'}),
                    headers=[('Content-Type', 'application/json')]
                )
            else:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Unauthorized'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Get active session
            active_session = request.env['stock.session'].search([('state', '=', 'open')], limit=1)
            if not active_session:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'No active trading session'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Validate order data
            side = kw.get('side')
            order_type = kw.get('order_type')
            quantity = int(kw.get('quantity', 0))
            price = float(kw.get('price', 0)) if order_type == 'limit' else 0.0
            
            # Additional validations
            if quantity <= 0:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Quantity must be greater than 0'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            if order_type == 'limit' and price <= 0:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Price must be greater than 0 for limit orders'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Check buy order cash requirements
            if side == 'buy' and order_type == 'limit':
                required_cash = price * quantity
                if order_user.cash_balance < required_cash:
                    return request.make_response(
                        json.dumps({
                            'success': False, 
                            'error': f'Insufficient funds. Required: ${required_cash:,.2f}, Available: ${order_user.cash_balance:,.2f}'
                        }),
                        headers=[('Content-Type', 'application/json')]
                    )
            
            # Check sell order position requirements
            if side == 'sell':
                position = request.env['stock.position'].search([
                    ('user_id', '=', order_user.id),
                    ('security_id', '=', int(kw.get('security_id')))
                ], limit=1)
                
                if not position or position.available_quantity < quantity:
                    available = position.available_quantity if position else 0
                    return request.make_response(
                        json.dumps({
                            'success': False,
                            'error': f'Insufficient shares to sell. Requested: {quantity}, Available: {available}'
                        }),
                        headers=[('Content-Type', 'application/json')]
                    )
            
            # Create the order (status decided by action_submit)
            order_data = {
                'user_id': order_user.id,
                'security_id': int(kw.get('security_id')),
                'session_id': active_session.id,
                'side': side,
                'order_type': order_type,
                'quantity': quantity,
                'entered_by_id': user.id,
            }
            
            if order_type == 'limit':
                order_data['price'] = price
            elif order_type == 'market':
                order_data['price'] = 0.0
            # Optional stop_price passthrough if provided
            if kw.get('stop_price'):
                try:
                    order_data['stop_price'] = float(kw.get('stop_price'))
                except Exception:
                    pass
            
            # Create order with mail context disabled to prevent email sending
            order = request.env['stock.order'].with_context(mail_create_nolog=True, mail_create_nosubscribe=True).create(order_data)
            # Submit to set proper status and trigger model-level validations
            try:
                order.sudo().action_submit()
            except Exception as e:
                order.unlink()
                return request.make_response(
                    json.dumps({'success': False, 'error': f'Failed to submit order: {str(e)}'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            return request.make_response(
                json.dumps({
                    'success': True,
                    'message': f'Order #{order.name} placed successfully for {order_user.name}',
                    'order_id': order.id
                }),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Error submitting order: {str(e)}")
            return request.make_response(
                json.dumps({'success': False, 'error': f'Failed to submit order: {str(e)}'}),
                headers=[('Content-Type', 'application/json')]
            )

    # Market Data
    @http.route(['/market', '/market/home'], type='http', auth="user", website=True)
    def market_home(self, **kw):
        """Custom market portal entry point with custom layout"""
        user = request.env.user
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        # Get all active securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Get market movers
        gainers = securities.filtered(lambda s: s.change_percentage > 0).sorted('change_percentage', reverse=True)[:5]
        losers = securities.filtered(lambda s: s.change_percentage < 0).sorted('change_percentage')[:5]
        
        # Financial data with fallbacks
        values = {
            'user': user,
            'user_type': user.user_type,
            'cash_balance': user.cash_balance or 0.0,
            'portfolio_value': user.portfolio_value or 0.0,
            'total_assets': user.total_assets or 0.0,
            'profit_loss': user.profit_loss or 0.0,
            'profit_loss_percentage': user.profit_loss_percentage or 0.0,            'active_session': active_session,
            'securities': securities,
            'top_gainers': gainers,
            'top_losers': losers,
            'page_name': 'market_home',
        }
        
        return request.render("stock_market_simulation.market_portal_layout", values)
    
    @http.route(['/market/portfolio'], type='http', auth="user", website=True)
    def market_portfolio(self, page=1, **kw):
        """Portfolio view in market portal"""
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type != 'investor' and not is_system_admin:
            return request.redirect('/market')
        
        # Get positions
        positions = request.env['stock.position'].search([
            ('user_id', '=', user.id),
            ('quantity', '>', 0)
        ])
        
        values = {
            'user': user,
            'positions': positions,
            'cash_balance': user.cash_balance or 0.0,
            'portfolio_value': user.portfolio_value or 0.0,
            'total_assets': user.total_assets or 0.0,            'page_name': 'portfolio',
        }
        
        return request.render("stock_market_simulation.market_portfolio_view", values)
    
    @http.route(['/my/investor/<int:investor_id>/positions'], type='http', auth="user", methods=['GET'], website=True)
    def get_investor_positions(self, investor_id, **kw):
        """Get positions for a specific investor (for brokers/admins)"""
        try:
            user = request.env.user
            
            # Check permissions - only brokers and admins can access this
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            if user.user_type not in ['broker', 'admin'] and not is_system_admin:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Unauthorized access'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Get the investor
            investor = request.env['res.users'].browse(investor_id)
            if not investor.exists() or investor.user_type != 'investor':
                return request.make_response(
                    json.dumps({'success': False, 'error': 'Invalid investor'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Get investor positions
            positions = request.env['stock.position'].search([
                ('user_id', '=', investor_id),
                ('available_quantity', '>', 0)
            ])
            
            position_data = []
            for pos in positions:
                position_data.append({
                    'security_id': pos.security_id.id,
                    'symbol': pos.security_id.symbol,
                    'name': pos.security_id.name,
                    'quantity': pos.quantity,
                    'available_quantity': pos.available_quantity,
                    'current_price': pos.security_id.current_price or 0.0,
                    'market_value': pos.market_value or 0.0
                })
            
            return request.make_response(
                json.dumps({
                    'success': True,
                    'positions': position_data,
                    'investor_name': investor.name
                }),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Error getting investor positions: {str(e)}")
            return request.make_response(
                json.dumps({'success': False, 'error': f'Error loading positions: {str(e)}'}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route(['/market/trading'], type='http', auth="user", website=True)
    def market_trading(self, **kw):
        """Trading view in market portal - for brokers and admins to place orders on behalf of clients"""
        _logger.info(f"TRADING PAGE CALLED - Method: {request.httprequest.method}, User: {request.env.user.name} ({request.env.user.user_type})")
        if request.httprequest.method == 'POST':
            _logger.error(f"TRADING PAGE RECEIVED POST REQUEST! Data: {kw}")
            _logger.error("THIS SHOULD NOT HAPPEN - Forms should submit to /my/order/submit")
        
        user = request.env.user
        
        # Allow brokers and admins to access trading interface
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['broker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        
        # Get active session
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        if not active_session:
            return request.redirect('/market')
        
        # Get securities by IPO status
        # Regular trading securities
        trading_securities = request.env['stock.security'].sudo().search([
            ('active', '=', True),
            ('ipo_status', '=', 'trading')
        ])
        
        # IPO/PO securities
        ipo_securities = request.env['stock.security'].sudo().search([
            ('ipo_status', 'in', ['ipo', 'po'])
        ])
        
        # All securities for compatibility
        securities = trading_securities + ipo_securities
        
        # Get all investors (any broker can place orders for any investor)
        clients = request.env['res.users'].search([
            ('user_type', '=', 'investor'),
            ('active', '=', True)
        ])
        
        # Get positions for all clients (for sell orders)
        client_positions = request.env['stock.position'].search([
            ('user_id', 'in', clients.ids),
            ('available_quantity', '>', 0)
        ])
        
        values = {
            'user': user,
            'securities': securities,
            'trading_securities': trading_securities,
            'ipo_securities': ipo_securities,
            'clients': clients,
            'client_positions': client_positions,
            'active_session': active_session,            'page_name': 'trading',
        }
        
        return request.render("stock_market_simulation.market_trading_view", values)
    
    @http.route(['/market/orders'], type='http', auth="user", website=True)
    def market_orders(self, **kw):
        """Orders view in market portal"""
        user = request.env.user
        
        # Allow investors, brokers, and admins to view orders
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'broker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        
        # Determine scope: current session or all
        scope = kw.get('scope') or 'current'  # default to current session

        # Build domain based on user type (treat technical Administrators as admins regardless of user_type)
        domain = []
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type == 'investor':
            # Investors see only their own orders
            domain.append(('user_id', '=', user.id))
        elif user.user_type == 'broker':
            # Brokers see orders they entered
            domain = ['|', ('entered_by_id', '=', user.id), ('create_uid', '=', user.id)]
        elif user.user_type == 'admin' or is_system_admin:
            # Admins see all orders by default
            pass
        else:
            # Default safe fallback: restrict to own orders
            domain.append(('user_id', '=', user.id))

        # Get active session (used for optional filtering and display)
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)

        # If scope is current and there's an active session, filter by it
        if scope == 'current' and active_session:
            domain.append(('session_id', '=', active_session.id))

        _logger.info(f"[portal] /market/orders user={user.id}({user.user_type}) scope={scope} is_sys_admin={is_system_admin} domain={domain}")

        # Fetch orders
        limit = 50 if user.user_type in ['investor', 'broker'] else 100
        orders = request.env['stock.order'].with_context(skip_portal_order_filter=True).search(domain, order='create_date desc', limit=limit)
        try:
            _logger.info(f"[portal] /market/orders result count={len(orders)} ids={orders.ids}")
        except Exception:
            pass
        
        values = {
            'user': user,
            'orders': orders,
            'active_session': active_session,
            'scope': scope,            'page_name': 'orders',
        }
        
        return request.render("stock_market_simulation.market_orders_view", values)
    
    @http.route(['/my/market'], type='http', auth="user", website=True)
    def portal_market_data(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Get all active securities
        securities = request.env['stock.security'].sudo().search([('active', '=', True)])
        
        # Group by type
        grouped_securities = {}
        for k, g in groupbyelem(securities, itemgetter('security_type')):
            grouped_securities[k] = list(g)
        
        values.update({
            'user': user,
            'securities': securities,
            'grouped_securities': grouped_securities,
            'page_name': 'market',
        })
        
        return request.render("stock_market_simulation.portal_market_data", values)

    # Broker Commission Report
    @http.route(['/my/commissions'], type='http', auth="user", website=True)
    def portal_broker_commissions(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['broker', 'admin'] and not is_system_admin:
            return request.redirect('/my')
        
        # Get commission data based on user type
        # Since default broker functionality removed, all users see all trades
        trades = request.env['stock.trade'].search([])
        
        # Total commission calculation simplified (no broker-specific logic)
        total_commission = sum(t.buy_commission + t.sell_commission for t in trades)
        
        # Group by session
        session_commissions = {}
        for trade in trades:
            session = trade.session_id.name
            if session not in session_commissions:
                session_commissions[session] = 0
            
            # Add both buy and sell commissions for all trades (no broker filtering)
            session_commissions[session] += trade.buy_commission + trade.sell_commission
        
        values.update({
            'user': user,
            'total_commission': total_commission,
            'session_commissions': session_commissions,
            'recent_trades': trades[:20],
            'page_name': 'commission',
        })
        
        return request.render("stock_market_simulation.portal_broker_commissions", values)

    # Placeholder routes for sidebar links (securities, session, reports, deposits, loans, clients)
    @http.route(['/market/securities'], type='http', auth="public", website=True)
    def market_securities(self, **kw):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("=== MARKET SECURITIES ROUTE CALLED ===")
        
        try:
            user = request.env.user
            _logger.info(f"User: {user.name} ({user.id})")
        except Exception as e:
            _logger.info(f"Error getting user: {e}")
            user = request.env['res.users'].sudo().browse(1)  # admin user
            _logger.info(f"Using fallback user: {user.name} ({user.id})")
        
        # Get all securities with their latest prices  
        securities = request.env['stock.security'].sudo().search([])
        securities_data = []
        
        for security in securities:
            latest_price = request.env['stock.price.history'].sudo().search([
                ('security_id', '=', security.id)
            ], order='change_date desc', limit=1)
            
            # Calculate daily change
            previous_price = request.env['stock.price.history'].sudo().search([
                ('security_id', '=', security.id),
                ('change_date', '<', latest_price.change_date if latest_price else fields.Datetime.now())
            ], order='change_date desc', limit=1)
            
            change = 0.0
            change_percent = 0.0
            if latest_price and previous_price:
                change = latest_price.new_price - previous_price.new_price
                change_percent = (change / previous_price.new_price) * 100 if previous_price.new_price else 0.0
            
            securities_data.append({
                'security': security,
                'latest_price': latest_price,
                'previous_price': previous_price,
                'change': change,
                'change_percent': change_percent,
            })
        
        values = {
            'user': user,
            'page_title': 'Securities',
            'securities_data': securities_data,
        }
        _logger.info(f"Rendering template with {len(securities_data)} securities")
        return request.render("stock_market_simulation.market_securities_page", values)

    @http.route(['/market/session'], type='http', auth="public", website=True)
    def market_session_info(self, **kw):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("=== MARKET SESSION ROUTE CALLED ===")
        
        try:
            user = request.env.user
            _logger.info(f"User: {user.name} ({user.id})")
        except Exception as e:
            _logger.info(f"Error getting user: {e}")
            user = request.env['res.users'].sudo().browse(1)  # admin user
            _logger.info(f"Using fallback user: {user.name} ({user.id})")
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        # Get session statistics
        session_stats = {}
        if active_session:
            # Get trades count and volume for current session
            trades = request.env['stock.trade'].sudo().search([
                ('session_id', '=', active_session.id)
            ])
            
            session_stats = {
                'trades_count': len(trades),
                'total_volume': sum(trades.mapped('quantity')),
                'total_value': sum(trades.mapped('value')),
                'unique_securities': len(trades.mapped('security_id')),
                'unique_traders': len(set(trades.mapped('buyer_id').ids + trades.mapped('seller_id').ids)),
            }
        
        # Get all sessions for history
        all_sessions = request.env['stock.session'].sudo().search([], order='actual_start_date desc', limit=10)
        
        values = {
            'user': user,
            'active_session': active_session,
            'session_stats': session_stats,
            'all_sessions': all_sessions,
            'page_title': 'Session Info',
        }
        return request.render("stock_market_simulation.market_session_page", values)

    @http.route(['/market/session/details/<int:session_id>'], type='json', auth="public", website=True)
    def market_session_details(self, session_id, **kw):
        """Get detailed information about a specific session"""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"=== SESSION DETAILS ROUTE CALLED for session_id: {session_id} ===")
        
        try:
            # Get the session
            session = request.env['stock.session'].sudo().browse(session_id)
            if not session.exists():
                return {'success': False, 'error': 'Session not found'}
            
            # Get session orders
            orders = request.env['stock.order'].sudo().search([
                ('session_id', '=', session_id)
            ], order='create_date desc')
            
            # Get session trades
            trades = request.env['stock.trade'].sudo().search([
                ('session_id', '=', session_id)
            ], order='trade_date desc')
            
            # Calculate session statistics
            total_orders = len(orders)
            total_trades = len(trades)
            total_volume = sum(trades.mapped('quantity'))
            total_value = sum(trade.quantity * trade.price for trade in trades)
            
            # Top trading securities in this session
            security_trades = {}
            for trade in trades:
                sec_id = trade.security_id.id
                if sec_id not in security_trades:
                    security_trades[sec_id] = {
                        'security': trade.security_id,
                        'volume': 0,
                        'value': 0,
                        'trades': 0
                    }
                security_trades[sec_id]['volume'] += trade.quantity
                security_trades[sec_id]['value'] += trade.quantity * trade.price
                security_trades[sec_id]['trades'] += 1
            
            # Sort by volume
            top_securities = sorted(security_trades.values(), key=lambda x: x['volume'], reverse=True)[:5]
            
            # Order statistics by type
            order_stats = {}
            for order in orders:
                order_type = order.order_type
                if order_type not in order_stats:
                    order_stats[order_type] = {'count': 0, 'total_quantity': 0}
                order_stats[order_type]['count'] += 1
                order_stats[order_type]['total_quantity'] += order.quantity
            
            # Price movements during session
            price_changes = request.env['stock.price.history'].sudo().search([
                ('session_id', '=', session_id)
            ], order='change_date')
            
            return {
                'success': True,
                'session': {
                    'id': session.id,
                    'name': session.name,
                    'state': session.state,
                    'actual_start_date': session.actual_start_date.strftime('%Y-%m-%d %H:%M:%S') if session.actual_start_date else None,
                    'actual_end_date': session.actual_end_date.strftime('%Y-%m-%d %H:%M:%S') if session.actual_end_date else None,
                    'planned_start_date': session.planned_start_date.strftime('%Y-%m-%d %H:%M:%S') if session.planned_start_date else None,
                    'planned_end_date': session.planned_end_date.strftime('%Y-%m-%d %H:%M:%S') if session.planned_end_date else None,
                    'actual_duration': session.actual_duration,
                    'broker_commission_rate': session.broker_commission_rate,
                    'price_change_threshold': session.price_change_threshold,
                    'circuit_breaker_upper': session.circuit_breaker_upper,
                    'circuit_breaker_lower': session.circuit_breaker_lower,
                },
                'statistics': {
                    'total_orders': total_orders,
                    'total_trades': total_trades,
                    'total_volume': total_volume,
                    'total_value': total_value,
                    'order_stats': order_stats,
                },
                'top_securities': [{
                    'symbol': sec['security'].symbol,
                    'name': sec['security'].name,
                    'volume': sec['volume'],
                    'value': sec['value'],
                    'trades': sec['trades'],
                } for sec in top_securities],
                'recent_trades': [{
                    'id': trade.id,
                    'security_symbol': trade.security_id.symbol,
                    'security_name': trade.security_id.name,
                    'quantity': trade.quantity,
                    'price': trade.price,
                    'value': trade.quantity * trade.price,
                    'trade_date': trade.trade_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'buyer': trade.buyer_id.name,
                    'seller': trade.seller_id.name,
                } for trade in trades[:10]],  # Last 10 trades
                'price_changes': [{
                    'security_symbol': pc.security_id.symbol,
                    'old_price': pc.old_price,
                    'new_price': pc.new_price,
                    'change_percent': ((pc.new_price - pc.old_price) / pc.old_price * 100) if pc.old_price else 0,
                    'change_date': pc.change_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'change_reason': pc.change_reason,
                } for pc in price_changes[:10]]  # Last 10 price changes
            }
            
        except Exception as e:
            _logger.error(f"Error in session details for session {session_id}: {str(e)}")
            return {'success': False, 'error': f'Error loading session details: {str(e)}'}

    @http.route(['/market/reports'], type='http', auth="public", website=True)
    def market_reports(self, **kw):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("=== MARKET REPORTS ROUTE CALLED ===")
        
        try:
            user = request.env.user
            _logger.info(f"User: {user.name} ({user.id})")
        except Exception as e:
            _logger.info(f"Error getting user: {e}")
            user = request.env['res.users'].sudo().browse(1)  # admin user
            _logger.info(f"Using fallback user: {user.name} ({user.id})")
        
        # Market Summary
        total_securities = request.env['stock.security'].sudo().search_count([])
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        
        # Today's trading stats
        today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        today_trades = request.env['stock.trade'].sudo().search([
            ('trade_date', '>=', today_start),
            ('trade_date', '<', today_end)
        ])
        
        # Overall market stats
        market_stats = {
            'total_securities': total_securities,
            'total_users': request.env['res.users'].sudo().search_count([('user_type', '!=', False)]),
            'total_trades_today': len(today_trades),
            'total_volume_today': sum(today_trades.mapped('quantity')),
            'total_value_today': sum(today_trades.mapped('value')),
        }
        
        # User-specific stats (if investor)
        user_stats = {}
        if hasattr(user, 'user_type') and user.user_type == 'investor':
            user_positions = request.env['stock.position'].sudo().search([('user_id', '=', user.id)])
            user_trades = request.env['stock.trade'].sudo().search([
                '|', ('buyer_id', '=', user.id), ('seller_id', '=', user.id)
            ])
            
            user_stats = {
                'total_positions': len(user_positions),
                'portfolio_value': sum(user_positions.mapped('market_value')),
                'total_trades': len(user_trades),
                'total_pnl': sum(user_positions.mapped('unrealized_pnl')),
            }
        
        # Top performers (securities)
        top_securities = request.env['stock.security'].sudo().search([], limit=5)
        
        values = {
            'user': user,
            'page_title': 'Market Reports',
            'market_stats': market_stats,
            'user_stats': user_stats,
            'top_securities': top_securities,
            'active_session': active_session,
        }
        return request.render("stock_market_simulation.market_reports_page", values)

    # IPO: Render page (admin/banker only)
    @http.route(['/market/ipo'], type='http', auth="user", website=True)
    def market_ipo_page(self, **kw):
        user = request.env.user
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['admin', 'banker'] and not is_system_admin:
            return request.redirect('/market')
        securities = request.env['stock.security'].search([])
        active_session = request.env['stock.session'].search([('state', '=', 'open')], limit=1)
        values = {
            'user': user,
            'page_title': 'IPO & Allocations',
            'securities': securities,
            'active_session': active_session,
        }
        return request.render("stock_market_simulation.portal_ipo_page", values)

    # IPO: Create or price IPO for a security and process IPO orders
    @http.route(['/market/ipo/create'], type='json', auth="user", methods=['POST'])
    def market_ipo_create(self, security_id=None, ipo_price=None, total_shares=None, ipo_quantity=None):
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            if user.user_type not in ['admin', 'banker'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
            if not security_id or not ipo_price:
                return {'success': False, 'error': 'Missing security_id or ipo_price'}
            # Parse inputs
            try:
                sec_id = int(security_id)
                price = float(ipo_price)
                qty = int(ipo_quantity) if ipo_quantity not in (None, '', False) else 0
                total_sh = int(total_shares) if total_shares not in (None, '', False) else None
            except Exception:
                return {'success': False, 'error': 'Invalid numeric values for IPO inputs'}

            if price <= 0:
                return {'success': False, 'error': 'IPO price must be greater than zero'}

            sec = request.env['stock.security'].browse(sec_id)
            if not sec.exists():
                return {'success': False, 'error': 'Security not found'}
            # Update IPO details
            vals = {'ipo_price': price}
            if total_sh is not None:
                if total_sh < 0:
                    return {'success': False, 'error': 'Total shares cannot be negative'}
                vals['total_shares'] = total_sh
            sec.write(vals)
            # Process IPO allocations if quantity provided
            if qty:
                # Enforce total_shares cap if provided
                if sec.total_shares and sec.total_shares > 0:
                    existing_qty = sum(request.env['stock.position'].search([
                        ('security_id', '=', sec.id)
                    ]).mapped('quantity'))
                    remaining_cap = max(sec.total_shares - existing_qty, 0)
                    if remaining_cap <= 0:
                        return {'success': False, 'error': 'No remaining shares to allocate based on total_shares cap'}
                    if qty > remaining_cap:
                        qty = remaining_cap
                engine = request.env['stock.matching.engine']
                engine.cron_run_matching()  # ensure env ready
                engine.process_ipo_orders(sec.id, qty, price)
            return {'success': True, 'data': 'IPO processed'}
        except Exception as e:
            _logger.error(f"Error IPO create: {str(e)}")
            return {'success': False, 'error': str(e)}

    # Direct allocation: grant shares directly to an investor (admin/banker)
    @http.route(['/market/allocation/direct'], type='json', auth="user", methods=['POST'])
    def market_direct_allocation(self, user_id=None, security_id=None, quantity=None, price=None):
        try:
            current = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            if current.user_type not in ['admin', 'banker'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
            if not user_id or not security_id or not quantity or not price:
                return {'success': False, 'error': 'Missing required fields'}
            # Parse numeric inputs safely
            try:
                inv_id = int(user_id)
                sec_id = int(security_id)
                qty = int(quantity)
                px = float(price)
            except Exception:
                return {'success': False, 'error': 'Invalid numeric values'}
            investor = request.env['res.users'].browse(inv_id)
            if not investor.exists() or investor.user_type != 'investor':
                return {'success': False, 'error': 'Invalid investor'}
            sec = request.env['stock.security'].browse(sec_id)
            if not sec.exists():
                return {'success': False, 'error': 'Security not found'}
            if qty <= 0 or px <= 0:
                return {'success': False, 'error': 'Quantity and price must be positive'}
            # Enforce total_shares cap if defined
            if sec.total_shares and sec.total_shares > 0:
                existing_qty = sum(request.env['stock.position'].search([
                    ('security_id', '=', sec.id)
                ]).mapped('quantity'))
                remaining_cap = max(sec.total_shares - existing_qty, 0)
                if remaining_cap <= 0:
                    return {'success': False, 'error': 'No remaining shares available to allocate'}
                if qty > remaining_cap:
                    qty = remaining_cap
            # Upsert position
            position = request.env['stock.position'].search([
                ('user_id', '=', investor.id),
                ('security_id', '=', sec.id)
            ], limit=1)
            if position:
                position.update_position(qty, px, transaction_type='buy')
            else:
                request.env['stock.position'].create({
                    'user_id': investor.id,
                    'security_id': sec.id,
                    'quantity': qty,
                    'average_cost': px,
                    'first_purchase_date': fields.Datetime.now(),
                    'last_transaction_date': fields.Datetime.now(),
                })
            # Optional: record a synthetic IPO trade for audit
            session = request.env['stock.session'].search([('state', '=', 'open')], limit=1) or request.env['stock.session'].search([], limit=1)
            buy_order = request.env['stock.order'].create({
                'user_id': investor.id,
                'session_id': session.id if session else False,
                'security_id': sec.id,
                'side': 'buy',
                'order_type': 'limit',
                'price': px,
                'quantity': qty,
                'status': 'filled',
                'entered_by_id': current.id,
            })
            request.env['stock.trade'].create({
                'buy_order_id': buy_order.id,
                'sell_order_id': False,
                'session_id': session.id if session else False,
                'security_id': sec.id,
                'quantity': qty,
                'price': px,
                'value': qty * px,
                'trade_type': 'block',
            })
            return {'success': True, 'data': 'Allocation completed'}
        except Exception as e:
            _logger.error(f"Direct allocation error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @http.route(['/market/deposits'], type='http', auth="user", website=True)
    def market_deposits(self, **kw):
        user = request.env.user
        # Investors, bankers, and admins can view deposits page
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'banker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        values = {
            'user': user,
            'page_title': 'Deposits',
        }
        return request.render("stock_market_simulation.market_portal_layout", values)

    @http.route(['/market/loans'], type='http', auth="user", website=True)
    def market_loans(self, **kw):
        user = request.env.user
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'banker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        values = {
            'user': user,
            'page_title': 'Loans',
        }
        return request.render("stock_market_simulation.market_portal_layout", values)

    @http.route(['/market/clients'], type='http', auth="user", website=True)
    def market_clients(self, **kw):
        user = request.env.user
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['broker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        values = {
            'user': user,
            'page_title': 'Clients',
        }
        return request.render("stock_market_simulation.market_portal_layout", values)

    # API Endpoints for AJAX calls
    @http.route(['/api/market/quotes'], type='json', auth="user", methods=['POST'])
    def api_market_quotes(self, **kw):
        """Get real-time market quotes for specified securities"""
        try:
            symbol_list = kw.get('symbols', [])
            if not symbol_list:
                return {'success': False, 'error': 'No symbols provided'}
                
            securities = request.env['stock.security'].sudo().search([
                ('symbol', 'in', symbol_list),
                ('active', '=', True)
            ])
            
            quotes = []
            for security in securities:
                # Calculate change from session start
                price_change = security.current_price - security.session_start_price
                change_percentage = (price_change / security.session_start_price * 100) if security.session_start_price else 0
                
                quotes.append({
                    'symbol': security.symbol,
                    'name': security.name,
                    'current_price': security.current_price,
                    'session_start_price': security.session_start_price,
                    'price_change': price_change,
                    'change_percentage': round(change_percentage, 2),
                    'last_update': security.write_date.strftime('%H:%M:%S') if security.write_date else '',
                })
            
            return {'success': True, 'quotes': quotes}
            
        except Exception as e:
            _logger.error(f"Error in market quotes API: {str(e)}")
            return {'success': False, 'error': 'Failed to retrieve market data'}

    @http.route(['/api/portfolio/summary'], type='json', auth="user", methods=['POST'])  
    def api_portfolio_summary(self, **kw):
        """Get portfolio summary for current user or specified user (admin only)"""
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            # Determine which user's portfolio to query
            if user.user_type == 'investor':
                target_user = user
            elif user.user_type == 'admin' or is_system_admin:
                # Admins can query specific users or their own
                user_id = kw.get('user_id')
                if user_id:
                    target_user = request.env['res.users'].browse(int(user_id))
                    if not target_user.exists() or target_user.user_type != 'investor':
                        return {'success': False, 'error': 'Invalid investor user specified'}
                else:
                    # If no user specified, admins get overall market summary
                    return {'success': False, 'error': 'Admin must specify user_id parameter'}
            else:
                return {'success': False, 'error': 'Only investors and admins can access portfolio data'}
                
            # Get positions for target user
            positions = request.env['stock.position'].search([('user_id', '=', target_user.id)])
            
            portfolio_value = sum(pos.market_value for pos in positions)
            total_assets = target_user.cash_balance + portfolio_value
            profit_loss = total_assets - target_user.initial_capital
            profit_loss_percentage = (profit_loss / target_user.initial_capital * 100) if target_user.initial_capital else 0
            
            # Get recent orders for target user
            recent_orders = request.env['stock.order'].search([
                ('user_id', '=', target_user.id)
            ], order='create_date desc', limit=5)
            
            orders_data = []
            for order in recent_orders:
                orders_data.append({
                    'name': order.name,
                    'symbol': order.security_id.symbol,
                    'side': order.side,
                    'quantity': order.quantity,
                    'price': order.price,
                    'status': order.status,
                    'create_date': order.create_date.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return {
                'success': True,
                'cash_balance': user.cash_balance,
                'portfolio_value': portfolio_value,
                'total_assets': total_assets,
                'profit_loss': profit_loss,
                'profit_loss_percentage': round(profit_loss_percentage, 2),
                'recent_orders': orders_data,
                'positions_count': len(positions)
            }
            
        except Exception as e:
            _logger.error(f"Error in portfolio summary API: {str(e)}")
            return {'success': False, 'error': 'Failed to retrieve portfolio data'}

    # Banker Dashboard
    @http.route(['/my/banking'], type='http', auth="user", website=True)
    def portal_banking_dashboard(self, **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['banker', 'admin'] and not is_system_admin:
            return request.redirect('/my')
        
        # Get banking statistics based on user type
        if user.user_type == 'banker':
            # Bankers see only their own operations
            deposits = request.env['stock.deposit'].search([('banker_id', '=', user.id)])
            loans = request.env['stock.loan'].search([('banker_id', '=', user.id)])
        else:  # admin or system admin
            # Admins see all banking operations
            deposits = request.env['stock.deposit'].search([])
            loans = request.env['stock.loan'].search([])
        
        total_deposits = sum(d.current_value for d in deposits.filtered(lambda d: d.status == 'active'))
        total_loans = sum(l.principal_outstanding for l in loans.filtered(lambda l: l.status == 'active'))
        
        values.update({
            'user': user,
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'active_deposits': deposits.filtered(lambda d: d.status == 'active'),
            'active_loans': loans.filtered(lambda l: l.status == 'active'),
            'page_name': 'banking',
        })
        
        return request.render("stock_market_simulation.portal_banking_dashboard", values)
    
    # ========== ADMIN / SUPERADMIN ROUTES ==========
    
    # Admin Users List
    @http.route(['/market/admin/users', '/market/admin/users/page/<int:page>'], type='http', auth="user", website=True)
    def admin_users_list(self, page=1, sortby=None, filterby=None, search=None, **kw):
        """List all users for admin/superadmin with 360 view access"""
        values = self._prepare_portal_layout_values()
        user = request.env.user
        
        # Check authorization
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        
        if user.user_type not in ['admin', 'superadmin'] and not is_system_admin:
            return request.redirect('/my')
        
        ResUsers = request.env['res.users']
        domain = [('id', '!=', 1)]  # Exclude super user (id=1)
        
        # Filter by user type
        searchbar_filters = {
            'all': {'label': _('All Users'), 'domain': []},
            'investor': {'label': _('Investors'), 'domain': [('user_type', '=', 'investor')]},
            'banker': {'label': _('Bankers'), 'domain': [('user_type', '=', 'banker')]},
            'broker': {'label': _('Brokers'), 'domain': [('user_type', '=', 'broker')]},
            'admin': {'label': _('Admins'), 'domain': [('user_type', 'in', ['admin', 'superadmin'])]},
        }
        
        searchbar_sortings = {
            'name': {'label': _('Name'), 'order': 'name'},
            'login': {'label': _('Login'), 'order': 'login'},
            'cash': {'label': _('Cash Balance'), 'order': 'cash_balance desc'},
            'capital': {'label': _('Initial Capital'), 'order': 'initial_capital desc'},
        }
        
        # Apply filters and search
        if not filterby:
            filterby = 'all'
        if filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        
        if search:
            domain += ['|', ('name', 'ilike', search), ('login', 'ilike', search)]
        
        # Apply sorting
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings.get(sortby, searchbar_sortings['name'])['order']
        
        # Count total users
        user_count = ResUsers.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/market/admin/users",
            url_args={'sortby': sortby, 'filterby': filterby, 'search': search},
            total=user_count,
            page=page,
            step=self._items_per_page
        )
        
        # Get users
        users = ResUsers.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        
        values.update({
            'page_name': 'admin_users',
            'users': users,
            'user_count': user_count,
            'pager': pager,
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'search': search,
        })
        
        return request.render("stock_market_simulation.admin_users_list", values)
    
    # Admin User 360 View
    @http.route(['/market/admin/user/<int:user_id>/360'], type='http', auth="user", website=True)
    def admin_user_360_view(self, user_id, **kw):
        """360-degree view of a user showing all financial data"""
        values = self._prepare_portal_layout_values()
        current_user = request.env.user
        
        # Check authorization
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        
        if current_user.user_type not in ['admin', 'superadmin'] and not is_system_admin:
            return request.not_found()
        
        # Get the user to view
        view_user = request.env['res.users'].browse(user_id)
        if not view_user.exists():
            return request.not_found()
        
        # Get user's financial data
        positions = request.env['stock.position'].search([('user_id', '=', user_id)])
        orders = request.env['stock.order'].search([('user_id', '=', user_id)], order='order_date desc', limit=20)
        
        # Get deposits and loans
        if view_user.user_type in ['investor', 'banker']:
            deposits = request.env['stock.deposit'].search([('user_id', '=', user_id)])
            loans = request.env['stock.loan'].search([('user_id', '=', user_id)])
        else:
            deposits = request.env['stock.deposit'].browse()
            loans = request.env['stock.loan'].browse()
        
        # Get trades where user is involved
        trades = request.env['stock.trade'].search([
            '|', ('buyer_id', '=', user_id), ('seller_id', '=', user_id)
        ], order='trade_date desc', limit=20)
        
        # Calculate summary statistics
        total_positions_value = sum(p.market_value for p in positions)
        total_positions_cost = sum(p.cost_basis for p in positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in positions)
        
        total_deposits = sum(d.current_value for d in deposits.filtered(lambda d: d.status == 'active'))
        total_loans = sum(l.principal_outstanding for l in loans.filtered(lambda l: l.status == 'active'))
        
        total_assets = view_user.cash_balance + total_positions_value
        
        values.update({
            'page_name': 'user_360',
            'view_user': view_user,
            'positions': positions,
            'orders': orders,
            'deposits': deposits,
            'loans': loans,
            'trades': trades,
            'total_positions_value': total_positions_value,
            'total_positions_cost': total_positions_cost,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_deposits': total_deposits,
            'total_loans': total_loans,
            'total_assets': total_assets,
        })
        
        return request.render("stock_market_simulation.admin_user_360_view", values)
    
    @http.route(['/market/admin/user/<int:user_id>/data'], type='json', auth="user", website=True)
    def admin_user_data_json(self, user_id, **kw):
        """Get user 360 view data as JSON for dynamic updates"""
        current_user = request.env.user
        
        # Check authorization
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        
        if current_user.user_type not in ['admin', 'superadmin'] and not is_system_admin:
            return {'success': False, 'error': 'Unauthorized'}
        
        try:
            view_user = request.env['res.users'].browse(user_id)
            if not view_user.exists():
                return {'success': False, 'error': 'User not found'}
            
            # Get financial data
            positions = request.env['stock.position'].search([('user_id', '=', user_id)])
            deposits = request.env['stock.deposit'].search([('user_id', '=', user_id), ('status', '=', 'active')])
            loans = request.env['stock.loan'].search([('user_id', '=', user_id), ('status', '=', 'active')])
            
            # Calculate totals
            total_positions = sum(p.market_value for p in positions)
            total_deposits = sum(d.current_value for d in deposits)
            total_loans = sum(l.principal_outstanding for l in loans)
            
            return {
                'success': True,
                'data': {
                    'user_id': view_user.id,
                    'name': view_user.name,
                    'login': view_user.login,
                    'user_type': view_user.user_type,
                    'cash_balance': view_user.cash_balance,
                    'initial_capital': view_user.initial_capital,
                    'positions_count': len(positions),
                    'total_positions_value': round(total_positions, 2),
                    'deposits_count': len(deposits),
                    'total_deposits': round(total_deposits, 2),
                    'loans_count': len(loans),
                    'total_loans': round(total_loans, 2),
                    'total_assets': round(view_user.cash_balance + total_positions, 2),
                }
            }
        except Exception as e:
            _logger.error(f"Error getting user data for {user_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @http.route(['/market/data/update'], type='http', auth="user", methods=['GET', 'POST'])
    def market_data_update(self, **kw):
        """Get real-time market data updates for dashboard"""
        try:
            # Get current session
            current_session = request.env['stock.session'].search([
                ('state', '=', 'open')
            ], limit=1)
            
            if not current_session:
                return request.make_response(
                    json.dumps({'success': False, 'error': 'No active session'}),
                    headers=[('Content-Type', 'application/json')]
                )
            
            # Get all active securities with current prices
            securities = request.env['stock.security'].search([
                ('active', '=', True)
            ])
            
            securities_data = []
            for security in securities:
                price_change = security.current_price - security.session_start_price
                change_percentage = (price_change / security.session_start_price * 100) if security.session_start_price else 0
                
                securities_data.append({
                    'id': security.id,
                    'symbol': security.symbol,
                    'name': security.name,
                    'current_price': security.current_price,
                    'session_start_price': security.session_start_price,
                    'price_change': round(price_change, 2),
                    'change_percentage': round(change_percentage, 2),
                    'volume': security.volume_today,
                    'last_update': security.write_date.strftime('%H:%M:%S') if security.write_date else '',
                })
            
            # Get market statistics
            total_volume = sum(s.volume_today for s in securities)
            total_value = sum(s.value_today for s in securities)
            gainers = len([s for s in securities if s.current_price > s.session_start_price])
            losers = len([s for s in securities if s.current_price < s.session_start_price])
            
            stats = {
                'total_securities': len(securities),
                'total_volume': total_volume,
                'total_value': round(total_value, 2),
                'gainers': gainers,
                'losers': losers,
                'unchanged': len(securities) - gainers - losers,
                'session_name': current_session.name,
                'session_status': current_session.state,
            }
            
            response_data = {
                'success': True,
                'data': {
                    'securities': securities_data,
                    'stats': stats,
                    'timestamp': fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            
            return request.make_response(
                json.dumps(response_data),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            _logger.error(f"Error updating market data: {str(e)}")
            return request.make_response(
                json.dumps({'success': False, 'error': 'Failed to update market data'}),
                headers=[('Content-Type', 'application/json')]
            )

    @http.route(['/test/user/fields'], type='http', auth="user", website=True)
    def test_user_fields(self, **kw):
        """Test route to check user computed fields"""
        user = request.env.user
        
        try:
            result = {
                'user_id': user.id,
                'user_type': user.user_type,
                'cash_balance': user.cash_balance,
                'portfolio_value': user.portfolio_value,
                'total_assets': user.total_assets,
                'profit_loss': user.profit_loss,
                'profit_loss_percentage': user.profit_loss_percentage,
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"

    @http.route(['/test/public/health'], type='http', auth="public", website=True)
    def test_public_health(self, **kw):
        """Public test route to check system health"""
        try:
            # Test basic database connectivity
            user_count = request.env['res.users'].sudo().search_count([])
            session_count = request.env['stock.session'].sudo().search_count([])
            
            result = {
                'status': 'ok',
                'user_count': user_count,
                'session_count': session_count,
                'routes_working': True
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            import traceback
            return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"