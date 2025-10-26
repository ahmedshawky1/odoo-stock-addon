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

    def _get_session_context(self):
        """Get session context data for navbar display"""
        active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
        return {
            'active_session': active_session,
        }

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
            **self._get_session_context(),
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
            **self._get_session_context(),
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
            # Get positions for all clients (for sell orders) - filter by quantity > blocked_quantity
            client_positions = request.env['stock.position'].search([
                ('user_id', 'in', clients.ids),
                ('quantity', '>', 0)
            ]).filtered(lambda p: p.available_quantity > 0)
        else:  # investor
            # Get their own positions for sell orders - filter by quantity > blocked_quantity
            client_positions = request.env['stock.position'].search([
                ('user_id', '=', user.id),
                ('quantity', '>', 0)
            ]).filtered(lambda p: p.available_quantity > 0)
        
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
        
        # Validate required fields first
        required_fields = ['security_id', 'side', 'order_type', 'quantity']
        missing_fields = []
        
        for field in required_fields:
            if not kw.get(field):
                if field == 'security_id':
                    missing_fields.append('Security')
                elif field == 'side':
                    missing_fields.append('Order Side (Buy/Sell)')
                elif field == 'order_type':
                    missing_fields.append('Order Type')
                elif field == 'quantity':
                    missing_fields.append('Quantity')
                else:
                    missing_fields.append(field)
        
        # Price is required for limit orders
        if kw.get('order_type') == 'limit' and not kw.get('price'):
            missing_fields.append('Price (required for limit orders)')
            
        if missing_fields:
            if len(missing_fields) == 1:
                return {'error': f'Missing required field: {missing_fields[0]}', 'type': 'validation'}
            else:
                return {'error': f'Missing required fields: {", ".join(missing_fields)}', 'type': 'validation'}
        
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
            # Validate and convert numeric inputs
            try:
                security_id = int(kw.get('security_id'))
                quantity = int(kw.get('quantity'))
                price = float(kw.get('price', 0)) if kw.get('price') else 0.0
            except (ValueError, TypeError) as e:
                return {'error': 'Invalid numeric values provided', 'type': 'validation'}
            
            # Validate positive values
            if quantity <= 0:
                return {'error': 'Quantity must be greater than zero', 'type': 'validation'}
            
            if kw.get('order_type') == 'limit' and price <= 0:
                return {'error': 'Price must be greater than zero for limit orders', 'type': 'validation'}
            
            # Create order on behalf of client (status decided by action_submit)
            order_vals = {
                'user_id': order_user.id,  # Client who owns the order
                'session_id': active_session.id,
                'security_id': security_id,
                'side': kw.get('side'),
                'order_type': kw.get('order_type'),
                'quantity': quantity,
                'price': price,
                'entered_by_id': user.id,
            }
            
            # Additional validation with user-friendly messages
            security = request.env['stock.security'].browse(security_id)
            side = kw.get('side')
            order_type = kw.get('order_type')
            
            # Validate security exists
            if not security.exists():
                return {'error': 'Selected security not found', 'type': 'validation'}
            
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
            # Use comprehensive mail context to prevent email issues
            mail_context = {
                'mail_create_nolog': True,
                'mail_create_nosubscribe': True,
                'mail_notify_noemail': True,
                'notification_disable': True,
                'mail_post_autofollow': False,
                'tracking_disable': True,
                'mail_auto_subscribe_no_notify': True
            }
            order = request.env['stock.order'].sudo().with_context(**mail_context).create(order_vals)
            try:
                order.with_context(**mail_context).sudo().action_submit()
            except Exception as e:
                # Rollback create if submit fails
                order.unlink()
                return {'error': f'Failed to submit order: {str(e)}'}
            
            # Log the broker action using centralized method
            order.log_broker_action(user, order_user, "Order placed")
            
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
            
            # Create order with comprehensive mail context disabled to prevent email sending
            mail_context = {
                'mail_create_nolog': True, 
                'mail_create_nosubscribe': True,
                'mail_notify_noemail': True,
                'notification_disable': True,
                'mail_post_autofollow': False,
                'tracking_disable': True,
                'mail_auto_subscribe_no_notify': True
            }
            order = request.env['stock.order'].with_context(**mail_context).create(order_data)
            # Submit to set proper status and trigger model-level validations
            try:
                order.with_context(**mail_context).sudo().action_submit()
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

    @http.route(['/market/data/update'], type='json', auth="public")
    def market_data_update(self, **kw):
        """Endpoint for frontend to fetch updated market data."""
        try:
            # Get active session
            active_session = request.env['stock.session'].sudo().search([('state', '=', 'open')], limit=1)
            if not active_session:
                return {'success': False, 'error': 'No active session'}

            # Get all active securities
            securities = request.env['stock.security'].sudo().search([('active', '=', True)])
            
            securities_data = []
            for sec in securities:
                securities_data.append({
                    'id': sec.id,
                    'symbol': sec.symbol,
                    'current_price': sec.current_price,
                    'change_amount': sec.change_amount,
                    'change_percentage': sec.change_percentage,
                    'volume_today': sec.volume_today,
                    'status': sec.status,
                })
            
            return {
                'success': True,
                'securities': securities_data,
                'session': {
                    'id': active_session.id,
                    'name': active_session.name,
                    'state': active_session.state,
                }
            }
        except Exception as e:
            _logger.error(f"Error fetching market data: {str(e)}")
            return {'success': False, 'error': str(e)}
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
            'profit_loss_percentage': user.profit_loss_percentage or 0.0,
            'active_session': active_session,
            'securities': securities,
            'top_gainers': gainers,
            'top_losers': losers,
            'page_name': 'market_home',
            **self._get_session_context(),
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
            
            # Get investor positions - filter by quantity > blocked_quantity
            positions = request.env['stock.position'].search([
                ('user_id', '=', investor_id),
                ('quantity', '>', 0)
            ]).filtered(lambda p: p.available_quantity > 0)
            
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
            # Redirect or render an error message if no session is active
            return request.render("stock_market_simulation.market_portal_layout", {
                'user': user,
                'page_name': 'trading',
                'error': 'No active trading session. Trading is currently closed.'
            })

        # Get securities by IPO status
        trading_securities = request.env['stock.security'].sudo().search([
            ('active', '=', True),
            ('ipo_status', '=', 'trading')
        ])
        
        ipo_securities = request.env['stock.security'].sudo().search([
            ('active', '=', True),
            ('ipo_status', 'in', ['ipo', 'po'])
        ])
        
        # Get all investors (clients)
        clients = request.env['res.users'].search([
            ('user_type', '=', 'investor'),
            ('active', '=', True)
        ])
        
        values = {
            'user': user,
            'trading_securities': trading_securities,
            'ipo_securities': ipo_securities,
            'clients': clients,
            'active_session': active_session,
            'page_name': 'trading',
            **self._get_session_context(),
        }
        
        return request.render("stock_market_simulation.portal_order_new", values)
    
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
        if user.user_type not in ['broker', 'admin', 'superadmin'] and not is_system_admin:
            return request.redirect('/my')
        
        # Get commission data based on user type
        trades = request.env['stock.trade'].search([])
        
        # Total commission calculation
        total_commission = sum(t.buy_commission + t.sell_commission for t in trades)
        
        # For superadmin/admin users, show broker breakdown
        broker_commissions = {}
        if user.user_type in ['admin', 'superadmin'] or is_system_admin:
            # Get all brokers and their commission data
            all_brokers = request.env['res.users'].search([
                ('user_type', 'in', ['broker', 'admin', 'superadmin'])
            ])
            
            for broker in all_brokers:
                broker_trades = trades.filtered(lambda t: 
                    (t.buy_order_id.entered_by_id.id == broker.id) or 
                    (t.sell_order_id.entered_by_id.id == broker.id)
                )
                
                broker_total = 0
                trade_count = 0
                for trade in broker_trades:
                    # Add commission based on which side the broker handled
                    if trade.buy_order_id.entered_by_id.id == broker.id:
                        broker_total += trade.buy_commission
                        trade_count += 1
                    if trade.sell_order_id.entered_by_id.id == broker.id:
                        broker_total += trade.sell_commission
                        trade_count += 1
                
                if broker_total > 0:  # Only include brokers with commissions
                    broker_commissions[broker] = {
                        'total': broker_total,
                        'trades': trade_count,
                        'recent_trades': broker_trades[:10]
                    }
        
        # Group by session
        session_commissions = {}
        for trade in trades:
            session = trade.session_id.name
            if session not in session_commissions:
                session_commissions[session] = 0
            
            session_commissions[session] += trade.buy_commission + trade.sell_commission
        
        values.update({
            'user': user,
            'total_commission': total_commission,
            'session_commissions': session_commissions,
            'broker_commissions': broker_commissions,
            'recent_trades': trades[:20],
            'page_name': 'commission',
            'is_super_user': user.user_type in ['admin', 'superadmin'] or is_system_admin,
        })
        
        return request.render("stock_market_simulation.portal_broker_commissions", values)

    # Market Commission Report - redirect to /my/commissions for compatibility
    @http.route(['/market/commissions'], type='http', auth="user", website=True)
    def market_broker_commissions(self, **kw):
        """Market portal commission view with enhanced broker breakdown for super users"""
        user = request.env.user
        
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['broker', 'admin', 'superadmin'] and not is_system_admin:
            return request.redirect('/market')
        
        # Get commission data
        values = self._prepare_portal_layout_values()
        trades = request.env['stock.trade'].search([])
        sessions = request.env['stock.session'].search([])
        
        # Total commission calculation
        total_commission = sum(t.buy_commission + t.sell_commission for t in trades)
        
        # For superadmin/admin users, show broker breakdown
        broker_commissions = {}
        if user.user_type in ['admin', 'superadmin'] or is_system_admin:
            # Get all brokers and their commission data
            all_brokers = request.env['res.users'].search([
                ('user_type', 'in', ['broker', 'admin', 'superadmin'])
            ])
            
            for broker in all_brokers:
                broker_trades = trades.filtered(lambda t: 
                    (t.buy_order_id.entered_by_id.id == broker.id) or 
                    (t.sell_order_id.entered_by_id.id == broker.id)
                )
                
                broker_total = 0
                trade_count = 0
                for trade in broker_trades:
                    # Add commission based on which side the broker handled
                    if trade.buy_order_id.entered_by_id.id == broker.id:
                        broker_total += trade.buy_commission
                        trade_count += 1
                    if trade.sell_order_id.entered_by_id.id == broker.id:
                        broker_total += trade.sell_commission
                        trade_count += 1
                
                if broker_total > 0:  # Only include brokers with commissions
                    broker_commissions[broker] = {
                        'total': broker_total,
                        'trades': trade_count,
                        'recent_trades': broker_trades[:10]
                    }
        
        # Group by session
        session_commissions = {}
        for trade in trades:
            session = trade.session_id
            if session not in session_commissions:
                session_commissions[session] = 0
            
            session_commissions[session] += trade.buy_commission + trade.sell_commission
        
        values.update({
            'user': user,
            'sessions': sessions,
            'total_commission': total_commission,
            'session_commissions': session_commissions,
            'broker_commissions': broker_commissions,
            'trades': trades,
            'page_name': 'commissions',
            'is_super_user': user.user_type in ['admin', 'superadmin'] or is_system_admin,
            **self._get_session_context(),
        })
        
        return request.render("stock_market_simulation.market_commissions_page", values)

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
            **self._get_session_context(),
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
        if user.user_type not in ['admin', 'superadmin'] and not is_system_admin:
            return request.redirect('/market')
        securities = request.env['stock.security'].search([])
        active_session = request.env['stock.session'].search([('state', '=', 'open')], limit=1)
        
        # Get list of investors for direct allocation dropdown
        investors = request.env['res.users'].search([
            ('user_type', '=', 'investor'),
            ('active', '=', True)
        ], order='name')
        
        values = {
            'user': user,
            'page_title': 'IPO & Allocations',
            'securities': securities,
            'investors': investors,
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
            if user.user_type not in ['admin', 'superadmin'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
                
            # Detailed field validation
            missing_fields = []
            if not security_id:
                missing_fields.append('Security')
            if not ipo_price:
                missing_fields.append('IPO Price')
                
            if missing_fields:
                if len(missing_fields) == 1:
                    return {'success': False, 'error': f'Missing required field: {missing_fields[0]}'}
                else:
                    return {'success': False, 'error': f'Missing required fields: {", ".join(missing_fields)}'}
            
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
            if current.user_type not in ['admin', 'superadmin'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
                
            # Detailed field validation with specific error messages
            missing_fields = []
            if not user_id:
                missing_fields.append('Investor')
            if not security_id:
                missing_fields.append('Security')
            if not quantity:
                missing_fields.append('Quantity')
            if not price:
                missing_fields.append('Price')
                
            if missing_fields:
                if len(missing_fields) == 1:
                    return {'success': False, 'error': f'Missing required field: {missing_fields[0]}'}
                else:
                    return {'success': False, 'error': f'Missing required fields: {", ".join(missing_fields)}'}
            
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
    def market_deposits(self, page=1, sortby=None, filterby=None, **kw):
        user = request.env.user
        # Investors, bankers, and admins can view deposits page
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'banker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        
        # Build domain based on user type
        domain = []
        if user.user_type == 'investor':
            # Investors see only their own deposits
            domain = [('user_id', '=', user.id)]
        elif user.user_type == 'banker':
            # Bankers see deposits they manage
            domain = [('banker_id', '=', user.id)]
        elif user.user_type == 'admin' or is_system_admin:
            # Admins see all deposits
            domain = []
        
        # Search filters
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'draft': {'label': 'Draft', 'domain': [('status', '=', 'draft')]},
            'active': {'label': 'Active', 'domain': [('status', '=', 'active')]},
            'matured': {'label': 'Matured', 'domain': [('status', '=', 'matured')]},
            'withdrawn': {'label': 'Withdrawn', 'domain': [('status', '=', 'withdrawn')]},
        }
        
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'create_date desc'},
            'amount': {'label': 'Amount', 'order': 'amount desc'},
            'interest': {'label': 'Interest Rate', 'order': 'interest_rate desc'},
            'maturity': {'label': 'Maturity', 'order': 'maturity_session_id'},
        }
        
        # Apply filters
        if not filterby:
            filterby = 'all'
        if filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        
        # Apply sorting
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings.get(sortby, searchbar_sortings['date'])['order']
        
        # Get deposits
        Deposit = request.env['stock.deposit']
        deposits = Deposit.search(domain, order=order)
        
        # Get summary statistics
        total_deposits = sum(d.amount for d in deposits)
        active_deposits = deposits.filtered(lambda d: d.status == 'active')
        total_active_value = sum(d.current_value for d in active_deposits)
        total_interest_earned = sum(d.accrued_interest for d in active_deposits)
        
        # Get all bankers for new deposit form
        bankers = request.env['res.users'].search([('user_type', '=', 'banker'), ('active', '=', True)])
        
        # Get all investors for banker/admin forms
        investors = []
        if user.user_type in ['banker', 'admin'] or is_system_admin:
            investors = request.env['res.users'].search([('user_type', '=', 'investor'), ('active', '=', True)])
        
        values = {
            'user': user,
            'page_title': 'Deposits',
            'deposits': deposits,
            'bankers': bankers,
            'investors': investors,
            'total_deposits': total_deposits,
            'total_active_value': total_active_value,
            'total_interest_earned': total_interest_earned,
            'active_count': len(active_deposits),
            'sortby': sortby,
            'filterby': filterby,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            **self._get_session_context(),
        }
        return request.render("stock_market_simulation.market_deposits_page", values)

    @http.route(['/market/loans'], type='http', auth="user", website=True)
    def market_loans(self, page=1, sortby=None, filterby=None, **kw):
        user = request.env.user
        try:
            is_system_admin = request.env.user.has_group('base.group_system')
        except Exception:
            is_system_admin = False
        if user.user_type not in ['investor', 'banker', 'admin'] and not is_system_admin:
            return request.redirect('/market')
        
        # Build domain based on user type
        domain = []
        if user.user_type == 'investor':
            # Investors see only their own loans
            domain = [('user_id', '=', user.id)]
        elif user.user_type == 'banker':
            # Bankers see loans they manage
            domain = [('banker_id', '=', user.id)]
        elif user.user_type == 'admin' or is_system_admin:
            # Admins see all loans
            domain = []
        
        # Search filters
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'draft': {'label': 'Draft', 'domain': [('status', '=', 'draft')]},
            'approved': {'label': 'Approved', 'domain': [('status', '=', 'approved')]},
            'active': {'label': 'Active', 'domain': [('status', '=', 'active')]},
            'paid': {'label': 'Paid', 'domain': [('status', '=', 'paid')]},
            'defaulted': {'label': 'Defaulted', 'domain': [('status', '=', 'defaulted')]},
        }
        
        searchbar_sortings = {
            'date': {'label': 'Date', 'order': 'create_date desc'},
            'amount': {'label': 'Amount', 'order': 'amount desc'},
            'interest': {'label': 'Interest Rate', 'order': 'interest_rate desc'},
            'outstanding': {'label': 'Outstanding', 'order': 'principal_outstanding desc'},
        }
        
        # Apply filters
        if not filterby:
            filterby = 'all'
        if filterby in searchbar_filters:
            domain += searchbar_filters[filterby]['domain']
        
        # Apply sorting
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings.get(sortby, searchbar_sortings['date'])['order']
        
        # Get loans
        Loan = request.env['stock.loan']
        loans = Loan.search(domain, order=order)
        
        # Get summary statistics
        total_loans = sum(l.amount for l in loans)
        active_loans = loans.filtered(lambda l: l.status == 'active')
        total_outstanding = sum(l.total_outstanding for l in active_loans)
        total_paid = sum(l.total_paid for l in loans)
        
        # Get all bankers for new loan form
        bankers = request.env['res.users'].search([('user_type', '=', 'banker'), ('active', '=', True)])
        
        # Get all investors for banker/admin forms
        investors = []
        if user.user_type in ['banker', 'admin'] or is_system_admin:
            investors = request.env['res.users'].search([('user_type', '=', 'investor'), ('active', '=', True)])
        
        # Get securities for collateral
        securities = request.env['stock.security'].search([('active', '=', True)])
        
        values = {
            'user': user,
            'page_title': 'Loans',
            'loans': loans,
            'bankers': bankers,
            'investors': investors,
            'securities': securities,
            'total_loans': total_loans,
            'total_outstanding': total_outstanding,
            'total_paid': total_paid,
            'active_count': len(active_loans),
            'sortby': sortby,
            'filterby': filterby,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
        }
        return request.render("stock_market_simulation.market_loans_page", values)

    # Deposits API endpoints
    @http.route(['/market/deposits/create'], type='json', auth="user", methods=['POST'])
    def create_deposit_api(self, **kw):
        """Create a new deposit"""
        try:
            user = request.env.user
            
            # Only bankers and admins can create deposits
            if user.user_type not in ['banker', 'admin']:
                return {'success': False, 'error': 'Access denied. Only bankers and admins can create deposits.'}
            
            # Validate required fields
            required_fields = ['investor_id', 'deposit_type', 'amount', 'interest_rate']
            for field in required_fields:
                if not kw.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Get investor
            investor = request.env['res.users'].sudo().browse(int(kw['investor_id']))
            if not investor.exists() or investor.user_type != 'investor':
                return {'success': False, 'error': 'Invalid investor selected'}
            
            # Determine banker
            banker_id = int(kw.get('banker_id')) if kw.get('banker_id') else user.id
            if user.user_type == 'admin' and kw.get('banker_id'):
                banker = request.env['res.users'].sudo().browse(banker_id)
                if not banker.exists() or banker.user_type != 'banker':
                    return {'success': False, 'error': 'Invalid banker selected'}
            else:
                banker_id = user.id if user.user_type == 'banker' else None
                if not banker_id:
                    # Auto-assign to first available banker
                    banker = request.env['res.users'].sudo().search([('user_type', '=', 'banker')], limit=1)
                    if banker:
                        banker_id = banker.id
                    else:
                        return {'success': False, 'error': 'No banker available'}
            
            # Validate amount
            try:
                amount = float(kw['amount'])
                if amount <= 0:
                    return {'success': False, 'error': 'Amount must be positive'}
            except ValueError:
                return {'success': False, 'error': 'Invalid amount'}
            
            # Check investor has sufficient funds
            if investor.cash_balance < amount:
                return {'success': False, 'error': f'Investor has insufficient funds. Available: ${investor.cash_balance:,.2f}'}
            
            # Validate interest rate
            try:
                interest_rate = float(kw['interest_rate'])
                if interest_rate < 0 or interest_rate > 50:
                    return {'success': False, 'error': 'Interest rate must be between 0% and 50%'}
            except ValueError:
                return {'success': False, 'error': 'Invalid interest rate'}
            
            # Prepare deposit data
            deposit_data = {
                'user_id': investor.id,
                'banker_id': banker_id,
                'deposit_type': kw['deposit_type'],
                'amount': amount,
                'interest_rate': interest_rate,
            }
            
            # Add optional fields
            if kw.get('term_sessions'):
                try:
                    term_sessions = int(kw['term_sessions'])
                    if term_sessions > 0:
                        deposit_data['term_sessions'] = term_sessions
                except ValueError:
                    pass
            
            # Create deposit with sudo (banker/admin privilege)
            deposit = request.env['stock.deposit'].sudo().create(deposit_data)
            
            # Auto-confirm if requested
            if kw.get('auto_confirm'):
                deposit.action_confirm()
                message = f'Deposit {deposit.name} created and confirmed successfully'
            else:
                message = f'Deposit {deposit.name} created successfully'
            
            return {
                'success': True,
                'message': message,
                'deposit_id': deposit.id
            }
            
        except Exception as e:
            _logger.error(f"Error creating deposit: {str(e)}")
            return {'success': False, 'error': f'Unable to create deposit: {str(e)}'}

    @http.route(['/market/deposits/action'], type='json', auth="user", methods=['POST'])
    def deposit_action_api(self, **kw):
        """Perform actions on deposits (confirm, withdraw, cancel)"""
        try:
            user = request.env.user
            
            # Get deposit
            deposit_id = kw.get('deposit_id')
            action = kw.get('action')
            
            if not deposit_id or not action:
                return {'success': False, 'error': 'Missing deposit_id or action'}
            
            deposit = request.env['stock.deposit'].sudo().browse(int(deposit_id))
            if not deposit.exists():
                return {'success': False, 'error': 'Deposit not found'}
            
            # Check permissions based on action and user type
            if action == 'confirm':
                # Only bankers and admins can confirm deposits
                if user.user_type not in ['banker', 'admin']:
                    return {'success': False, 'error': 'Access denied. Only bankers and admins can confirm deposits.'}
                
                # Additional check: banker can only confirm their own deposits
                if user.user_type == 'banker' and deposit.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only confirm your own deposits.'}
                
                deposit.action_confirm()
                message = f'Deposit {deposit.name} confirmed successfully'
                
            elif action == 'withdraw':
                # Investors can withdraw their own deposits, bankers can withdraw deposits they manage
                if user.user_type == 'investor' and deposit.user_id.id != user.id:
                    return {'success': False, 'error': 'You can only withdraw your own deposits.'}
                elif user.user_type == 'banker' and deposit.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only withdraw deposits you manage.'}
                elif user.user_type not in ['investor', 'banker', 'admin']:
                    return {'success': False, 'error': 'Access denied.'}
                
                deposit.action_withdraw()
                message = f'Deposit {deposit.name} withdrawn successfully'
                
            elif action == 'cancel':
                # Similar permission checks for cancel
                if user.user_type == 'investor' and deposit.user_id.id != user.id:
                    return {'success': False, 'error': 'You can only cancel your own deposits.'}
                elif user.user_type == 'banker' and deposit.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only cancel deposits you manage.'}
                elif user.user_type not in ['investor', 'banker', 'admin']:
                    return {'success': False, 'error': 'Access denied.'}
                
                deposit.action_cancel()
                message = f'Deposit {deposit.name} cancelled successfully'
                
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            _logger.error(f"Error performing deposit action {action} for deposit {deposit_id}: {str(e)}")
            return {'success': False, 'error': f'Unable to {action} deposit: {str(e)}'}

    # Loans API endpoints
    @http.route(['/market/loans/create'], type='json', auth="user", methods=['POST'])
    def create_loan_api(self, **kw):
        """Create a new loan"""
        try:
            user = request.env.user
            
            # Only bankers and admins can create loans
            if user.user_type not in ['banker', 'admin']:
                return {'success': False, 'error': 'Access denied. Only bankers and admins can create loans.'}
            
            # Validate required fields
            required_fields = ['investor_id', 'loan_type', 'amount', 'interest_rate', 'term_sessions']
            for field in required_fields:
                if not kw.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Get borrower
            borrower = request.env['res.users'].sudo().browse(int(kw['investor_id']))
            if not borrower.exists() or borrower.user_type != 'investor':
                return {'success': False, 'error': 'Invalid borrower selected'}
            
            # Determine lender
            lender_id = int(kw.get('lender_id')) if kw.get('lender_id') else user.id
            if user.user_type == 'admin' and kw.get('lender_id'):
                lender = request.env['res.users'].sudo().browse(lender_id)
                if not lender.exists() or lender.user_type != 'banker':
                    return {'success': False, 'error': 'Invalid lender selected'}
            else:
                lender_id = user.id if user.user_type == 'banker' else None
                if not lender_id:
                    # Auto-assign to first available banker
                    lender = request.env['res.users'].sudo().search([('user_type', '=', 'banker')], limit=1)
                    if lender:
                        lender_id = lender.id
                    else:
                        return {'success': False, 'error': 'No banker available'}
            
            # Validate amount
            try:
                principal_amount = float(kw['amount'])
                if principal_amount <= 0:
                    return {'success': False, 'error': 'Amount must be positive'}
            except ValueError:
                return {'success': False, 'error': 'Invalid amount'}
            
            # Validate interest rate
            try:
                interest_rate = float(kw['interest_rate'])
                if interest_rate < 0 or interest_rate > 50:
                    return {'success': False, 'error': 'Interest rate must be between 0% and 50%'}
            except ValueError:
                return {'success': False, 'error': 'Invalid interest rate'}
            
            # Validate term sessions
            try:
                term_sessions = int(kw['term_sessions'])
                if term_sessions <= 0:
                    return {'success': False, 'error': 'Term sessions must be positive'}
                if term_sessions > 1000:
                    return {'success': False, 'error': 'Term sessions cannot exceed 1000'}
            except ValueError:
                return {'success': False, 'error': 'Invalid term sessions'}
            
            # Prepare loan data
            loan_data = {
                'user_id': borrower.id,  # Changed from borrower_id to user_id (actual field name)
                'banker_id': lender_id,  # Changed from lender_id to banker_id (actual field name)
                'loan_type': kw['loan_type'],
                'amount': principal_amount,  # Changed from principal_amount to amount (actual field name)
                'interest_rate': interest_rate,
                'term_sessions': term_sessions,
            }
            
            # Add optional fields
            if kw.get('term_sessions'):
                try:
                    term_sessions = int(kw['term_sessions'])
                    if term_sessions > 0:
                        loan_data['term_sessions'] = term_sessions
                except ValueError:
                    pass
            
            if kw.get('collateral_amount'):
                try:
                    collateral_amount = float(kw['collateral_amount'])
                    if collateral_amount > 0:
                        loan_data['collateral_amount'] = collateral_amount
                except ValueError:
                    pass
            
            # Create loan with sudo (banker/admin privilege)
            loan = request.env['stock.loan'].sudo().create(loan_data)
            
            # Auto-approve if requested
            if kw.get('auto_approve'):
                loan.action_approve()
                message = f'Loan {loan.name} created and approved successfully'
            else:
                message = f'Loan {loan.name} created successfully'
            
            return {
                'success': True,
                'message': message,
                'loan_id': loan.id,
                'loan_name': loan.name
            }
            
        except Exception as e:
            _logger.error(f"Error creating loan: {str(e)}")
            return {'success': False, 'error': f'Unable to create loan: {str(e)}'}

    @http.route(['/market/loans/action'], type='json', auth="user", methods=['POST'])
    def loan_action_api(self, **kw):
        """Perform actions on loans (approve, disburse, repay, default)"""
        try:
            user = request.env.user
            
            # Get loan
            loan_id = kw.get('loan_id')
            action = kw.get('action')
            
            if not loan_id or not action:
                return {'success': False, 'error': 'Missing loan_id or action'}
            
            loan = request.env['stock.loan'].sudo().browse(int(loan_id))
            if not loan.exists():
                return {'success': False, 'error': 'Loan not found'}
            
            # Check permissions based on action and user type
            if action == 'approve':
                # Only bankers and admins can approve loans
                if user.user_type not in ['banker', 'admin']:
                    return {'success': False, 'error': 'Access denied. Only bankers and admins can approve loans.'}
                
                # Additional check: banker can only approve their own loans
                if user.user_type == 'banker' and loan.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only approve your own loans.'}
                
                loan.action_approve()
                message = f'Loan {loan.name} approved successfully'
                
            elif action == 'disburse':
                # Only bankers and admins can disburse loans
                if user.user_type not in ['banker', 'admin']:
                    return {'success': False, 'error': 'Access denied. Only bankers and admins can disburse loans.'}
                
                if user.user_type == 'banker' and loan.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only disburse your own loans.'}
                
                loan.action_disburse()
                message = f'Loan {loan.name} disbursed successfully'
                
            elif action == 'repay':
                # Borrowers can repay their own loans, bankers can process repayments
                if user.user_type == 'investor' and loan.user_id.id != user.id:
                    return {'success': False, 'error': 'You can only repay your own loans.'}
                elif user.user_type == 'banker' and loan.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only process repayments for your own loans.'}
                elif user.user_type not in ['investor', 'banker', 'admin']:
                    return {'success': False, 'error': 'Access denied.'}
                
                # Get repayment amount if provided
                amount = kw.get('amount')
                if amount:
                    try:
                        amount = float(amount)
                        loan.action_make_payment(amount)
                        message = f'Payment of ${amount:,.2f} made on loan {loan.name}'
                    except ValueError:
                        return {'success': False, 'error': 'Invalid repayment amount'}
                else:
                    loan.action_repay()
                    message = f'Loan {loan.name} fully repaid'
                
            elif action == 'default':
                # Only bankers and admins can mark loans as defaulted
                if user.user_type not in ['banker', 'admin']:
                    return {'success': False, 'error': 'Access denied. Only bankers and admins can mark loans as defaulted.'}
                
                if user.user_type == 'banker' and loan.banker_id.id != user.id:
                    return {'success': False, 'error': 'You can only default your own loans.'}
                
                loan.action_default()
                message = f'Loan {loan.name} marked as defaulted'
                
            else:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            _logger.error(f"Error performing loan action {action} for loan {loan_id}: {str(e)}")
            return {'success': False, 'error': f'Unable to {action} loan: {str(e)}'}

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
            **self._get_session_context(),
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
        
        # Calculate net worth: Cash + Portfolio + Deposits - Loans
        net_worth = (view_user.cash_balance or 0) + total_positions_value + total_deposits - total_loans
        
        # Build comprehensive transaction history from transaction log
        transaction_log = request.env['stock.transaction.log']
        balance_sheet_data = transaction_log.get_user_balance_sheet(user_id)
        
        # Get all transactions ordered by date
        all_transactions = balance_sheet_data['transactions']
        transaction_categories = balance_sheet_data['categories']
        
        # Prepare transaction data for template
        transaction_list = []
        for txn in all_transactions:
            transaction_list.append({
                'date': txn.transaction_date.strftime('%Y-%m-%d %H:%M') if txn.transaction_date else 'Unknown',
                'type': txn.transaction_type.upper().replace('_', ' '),
                'description': txn.description,
                'amount': txn.cash_impact,
                'running_balance': txn.running_balance,
                'category': txn.category,
                'reference': txn.reference or '',
                'badge_class': 'bg-success' if txn.cash_impact >= 0 else 'bg-danger'
            })
        
        # Calculate summary by category
        category_summaries = {}
        for cat_name, cat_data in transaction_categories.items():
            category_summaries[cat_name] = {
                'name': cat_name.replace('_', ' ').title(),
                'total_amount': cat_data['total_amount'],
                'total_cash_impact': cat_data['total_cash_impact'],
                'transaction_count': len(cat_data['transactions'])
            }
        
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
            'net_worth': net_worth,
            'all_transactions': transaction_list,
            'category_summaries': category_summaries,
            'balance_sheet_data': balance_sheet_data,
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

    @http.route(['/test/commission/data'], type='http', auth="user", website=True)
    def test_commission_data(self, **kw):
        """Test endpoint to check commission data structure"""
        try:
            user = request.env.user
            
            # Get all users who have placed orders
            orders = request.env['stock.order'].search([('entered_by_id', '!=', False)])
            brokers = orders.mapped('entered_by_id')
            
            # Get all trades
            trades = request.env['stock.trade'].search([])
            
            result = {
                'total_trades': len(trades),
                'total_orders': len(orders),
                'brokers_found': [],
                'sample_trade_data': []
            }
            
            for broker in brokers[:5]:  # First 5 brokers
                broker_orders = orders.filtered(lambda o: o.entered_by_id.id == broker.id)
                broker_trades = trades.filtered(lambda t: 
                    (t.buy_order_id.entered_by_id.id == broker.id) or 
                    (t.sell_order_id.entered_by_id.id == broker.id)
                )
                
                total_commission = 0
                for trade in broker_trades:
                    if trade.buy_order_id.entered_by_id.id == broker.id:
                        total_commission += trade.buy_commission
                    if trade.sell_order_id.entered_by_id.id == broker.id:
                        total_commission += trade.sell_commission
                
                result['brokers_found'].append({
                    'id': broker.id,
                    'name': broker.name,
                    'user_type': broker.user_type,
                    'orders_placed': len(broker_orders),
                    'trades_handled': len(broker_trades),
                    'total_commission': total_commission
                })
            
            # Sample trade data
            for trade in trades[:3]:
                result['sample_trade_data'].append({
                    'id': trade.id,
                    'security': trade.security_id.symbol,
                    'buy_broker': trade.buy_order_id.entered_by_id.name if trade.buy_order_id else 'N/A',
                    'sell_broker': trade.sell_order_id.entered_by_id.name if trade.sell_order_id else 'N/A',
                    'buy_commission': trade.buy_commission,
                    'sell_commission': trade.sell_commission,
                    'total_commission': trade.total_commission
                })
            
            return request.make_response(
                json.dumps({'success': True, 'data': result}, indent=2, default=str),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            import traceback
            return request.make_response(
                json.dumps({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}, indent=2),
                headers=[('Content-Type', 'application/json')]
            )

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

    @http.route(['/market/deposits/create'], type='json', auth="user", methods=['POST'])
    def market_deposits_create(self, **kw):
        """Create a new deposit"""
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            # Only bankers and admins can create deposits
            if user.user_type not in ['banker', 'admin'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
            
            # Validate required fields
            required = ['investor_id', 'deposit_type', 'amount', 'interest_rate']
            for field in required:
                if not kw.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Parse values
            investor_id = int(kw.get('investor_id'))
            amount = float(kw.get('amount'))
            interest_rate = float(kw.get('interest_rate'))
            term_months = int(kw.get('term_months', 0))
            
            # Validate investor
            investor = request.env['res.users'].browse(investor_id)
            if not investor.exists() or investor.user_type != 'investor':
                return {'success': False, 'error': 'Invalid investor selected'}
            
            # Validate amount
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}
            
            # Check investor has sufficient funds
            if investor.cash_balance < amount:
                return {'success': False, 'error': f'Investor has insufficient funds. Available: ${investor.cash_balance:,.2f}, Required: ${amount:,.2f}'}
            
            # Determine banker
            if user.user_type == 'banker':
                banker_id = user.id
            else:
                # Admin can specify banker or use first available
                banker_id = int(kw.get('banker_id', 0))
                if not banker_id:
                    first_banker = request.env['res.users'].search([('user_type', '=', 'banker')], limit=1)
                    if not first_banker:
                        return {'success': False, 'error': 'No banker available'}
                    banker_id = first_banker.id
            
            # Create deposit
            vals = {
                'user_id': investor_id,
                'banker_id': banker_id,
                'deposit_type': kw.get('deposit_type'),
                'amount': amount,
                'interest_rate': interest_rate,
                'term_months': term_months if term_months > 0 else None,
            }
            
            deposit = request.env['stock.deposit'].create(vals)
            
            # Auto-confirm if requested
            if kw.get('auto_confirm'):
                deposit.action_confirm()
            
            return {
                'success': True,
                'message': f'Deposit #{deposit.name} created successfully',
                'deposit_id': deposit.id,
                'deposit_name': deposit.name
            }
            
        except Exception as e:
            _logger.error(f"Error creating deposit: {str(e)}")
            return {'success': False, 'error': f'Failed to create deposit: {str(e)}'}

    @http.route(['/market/deposits/<int:deposit_id>/action'], type='json', auth="user", methods=['POST'])
    def market_deposits_action(self, deposit_id, action=None, **kw):
        """Perform actions on deposits (confirm, withdraw, etc.)"""
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            deposit = request.env['stock.deposit'].browse(deposit_id)
            if not deposit.exists():
                return {'success': False, 'error': 'Deposit not found'}
            
            # Check permissions
            can_manage = (
                user.user_type in ['banker', 'admin'] or 
                is_system_admin or 
                (user.user_type == 'investor' and deposit.user_id.id == user.id)
            )
            
            if not can_manage:
                return {'success': False, 'error': 'Access denied'}
            
            # Perform action
            if action == 'confirm':
                if user.user_type not in ['banker', 'admin'] and not is_system_admin:
                    return {'success': False, 'error': 'Only bankers can confirm deposits'}
                deposit.action_confirm()
                message = f'Deposit #{deposit.name} confirmed'
                
            elif action == 'withdraw':
                deposit.action_withdraw()
                message = f'Deposit #{deposit.name} withdrawn'
                
            elif action == 'cancel':
                deposit.action_cancel()
                message = f'Deposit #{deposit.name} cancelled'
                
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            _logger.error(f"Error in deposit action {action} for deposit {deposit_id}: {str(e)}")
            return {'success': False, 'error': f'Failed to {action} deposit: {str(e)}'}

    # Loans API endpoints
    @http.route(['/market/loans/create'], type='json', auth="user", methods=['POST'])
    def market_loans_create(self, **kw):
        """Create a new loan"""
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            # Only bankers and admins can create loans
            if user.user_type not in ['banker', 'admin'] and not is_system_admin:
                return {'success': False, 'error': 'Access denied'}
            
            # Validate required fields
            required = ['investor_id', 'loan_type', 'amount', 'interest_rate', 'term_months']
            for field in required:
                if not kw.get(field):
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Parse values
            investor_id = int(kw.get('investor_id'))
            amount = float(kw.get('amount'))
            interest_rate = float(kw.get('interest_rate'))
            term_months = int(kw.get('term_months'))
            loan_type = kw.get('loan_type')
            
            # Validate investor
            investor = request.env['res.users'].browse(investor_id)
            if not investor.exists() or investor.user_type != 'investor':
                return {'success': False, 'error': 'Invalid investor selected'}
            
            # Validate amount
            if amount <= 0:
                return {'success': False, 'error': 'Amount must be positive'}
            
            # Validate term
            if term_months <= 0:
                return {'success': False, 'error': 'Term must be positive'}
            
            # Determine banker
            if user.user_type == 'banker':
                banker_id = user.id
            else:
                # Admin can specify banker or use first available
                banker_id = int(kw.get('banker_id', 0))
                if not banker_id:
                    first_banker = request.env['res.users'].search([('user_type', '=', 'banker')], limit=1)
                    if not first_banker:
                        return {'success': False, 'error': 'No banker available'}
                    banker_id = first_banker.id
            
            # Validate collateral for secured loans
            collateral_security_id = None
            collateral_quantity = 0
            
            if loan_type in ['margin', 'secured']:
                if not kw.get('collateral_security_id') or not kw.get('collateral_quantity'):
                    return {'success': False, 'error': 'Collateral security and quantity required for secured loans'}
                
                collateral_security_id = int(kw.get('collateral_security_id'))
                collateral_quantity = int(kw.get('collateral_quantity'))
                
                # Check investor has sufficient shares
                position = request.env['stock.position'].search([
                    ('user_id', '=', investor_id),
                    ('security_id', '=', collateral_security_id)
                ], limit=1)
                
                if not position or position.available_quantity < collateral_quantity:
                    return {'success': False, 'error': 'Investor has insufficient shares for collateral'}
            
            # Create loan
            vals = {
                'user_id': investor_id,
                'banker_id': banker_id,
                'loan_type': loan_type,
                'amount': amount,
                'interest_rate': interest_rate,
                'term_months': term_months,
            }
            
            if collateral_security_id:
                vals.update({
                    'collateral_security_id': collateral_security_id,
                    'collateral_quantity': collateral_quantity,
                })
            
            loan = request.env['stock.loan'].create(vals)
            
            # Auto-approve and disburse if requested
            if kw.get('auto_approve'):
                loan.action_approve()
                if kw.get('auto_disburse'):
                    loan.action_disburse()
            
            return {
                'success': True,
                'message': f'Loan #{loan.name} created successfully',
                'loan_id': loan.id,
                'loan_name': loan.name
            }
            
        except Exception as e:
            _logger.error(f"Error creating loan: {str(e)}")
            return {'success': False, 'error': f'Failed to create loan: {str(e)}'}

    @http.route(['/market/loans/<int:loan_id>/action'], type='json', auth="user", methods=['POST'])
    def market_loans_action(self, loan_id, action=None, **kw):
        """Perform actions on loans (approve, disburse, etc.)"""
        try:
            user = request.env.user
            try:
                is_system_admin = request.env.user.has_group('base.group_system')
            except Exception:
                is_system_admin = False
            
            loan = request.env['stock.loan'].browse(loan_id)
            if not loan.exists():
                return {'success': False, 'error': 'Loan not found'}
            
            # Check permissions
            can_manage = (
                user.user_type in ['banker', 'admin'] or 
                is_system_admin or 
                (user.user_type == 'investor' and loan.user_id.id == user.id and action in ['make_payment'])
            )
            
            if not can_manage:
                return {'success': False, 'error': 'Access denied'}
            
            # Perform action
            if action == 'approve':
                if user.user_type not in ['banker', 'admin'] and not is_system_admin:
                    return {'success': False, 'error': 'Only bankers can approve loans'}
                loan.action_approve()
                message = f'Loan #{loan.name} approved'
                
            elif action == 'disburse':
                if user.user_type not in ['banker', 'admin'] and not is_system_admin:
                    return {'success': False, 'error': 'Only bankers can disburse loans'}
                loan.action_disburse()
                message = f'Loan #{loan.name} disbursed'
                
            elif action == 'make_payment':
                # Create payment record
                amount = float(kw.get('amount', 0))
                if amount <= 0:
                    return {'success': False, 'error': 'Payment amount must be positive'}
                
                if loan.user_id.cash_balance < amount:
                    return {'success': False, 'error': 'Insufficient funds for payment'}
                
                # Calculate payment components
                interest_due = loan.interest_accrued
                penalty_due = loan.penalty_amount
                
                penalty_component = min(amount, penalty_due)
                remaining = amount - penalty_component
                
                interest_component = min(remaining, interest_due)
                remaining -= interest_component
                
                principal_component = min(remaining, loan.principal_outstanding)
                
                # Create payment
                payment_vals = {
                    'loan_id': loan.id,
                    'amount': amount,
                    'principal_component': principal_component,
                    'interest_component': interest_component,
                    'penalty_component': penalty_component,
                    'payment_type': kw.get('payment_type', 'emi'),
                }
                
                payment = request.env['stock.loan.payment'].create(payment_vals)
                
                # Transfer funds
                loan.user_id.cash_balance -= amount
                loan.banker_id.cash_balance += amount
                
                message = f'Payment of ${amount:,.2f} made on loan #{loan.name}'
                
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            return {'success': True, 'message': message}
            
        except Exception as e:
            _logger.error(f"Error in loan action {action} for loan {loan_id}: {str(e)}")
            return {'success': False, 'error': f'Failed to {action} loan: {str(e)}'}