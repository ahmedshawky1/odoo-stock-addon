# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class SessionEndIpoWizard(models.TransientModel):
    _name = 'session.end.ipo.wizard'
    _description = 'Session End IPO Status Management'
    
    session_id = fields.Many2one(
        'stock.session',
        string='Session',
        required=True,
        readonly=True
    )
    
    line_ids = fields.One2many(
        'session.end.ipo.wizard.line',
        'wizard_id',
        string='IPO Securities'
    )
    
    @api.model
    def default_get(self, fields_list):
        """Populate wizard with current IPO/PO securities"""
        res = super().default_get(fields_list)
        
        # Get the session being closed
        session_id = self.env.context.get('active_id')
        if not session_id:
            raise UserError("No session context provided")
            
        session = self.env['stock.session'].browse(session_id)
        res['session_id'] = session_id
        
        # Find all securities in IPO or PO status
        ipo_securities = self.env['stock.security'].search([
            ('ipo_status', 'in', ['ipo', 'po'])
        ])
        
        # Create wizard lines
        line_vals = []
        for security in ipo_securities:
            # Count pending IPO orders
            pending_orders = self.env['stock.order'].search([
                ('security_id', '=', security.id),
                ('order_type', '=', 'ipo'),
                ('status', 'in', ['submitted', 'open']),
                ('session_id', '=', session_id)
            ])
            
            line_vals.append((0, 0, {
                'security_id': security.id,
                'current_status': security.ipo_status,
                'new_status': security.ipo_status,  # Default to continue same status
                'pending_orders_count': len(pending_orders),
                'total_pending_quantity': sum(pending_orders.mapped('quantity')),
                'ipo_price': security.ipo_price or 0.0
            }))
        
        res['line_ids'] = line_vals
        return res
    
    def action_process(self):
        """Process the IPO status changes"""
        for line in self.line_ids:
            if line.new_status == 'trading':
                # Change to trading - process IPO orders and activate trading
                self._process_ipo_to_trading(line)
            elif line.new_status == 'new_po':
                # Start new PO round
                self._start_new_po_round(line)
            else:
                # Continue in IPO/PO status - just update if changed
                if line.new_status != line.current_status:
                    line.security_id.write({
                        'ipo_status': line.new_status
                    })
        
        # Complete the session close
        self.session_id.action_force_close_after_ipo()
        
        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}
    
    def _process_ipo_to_trading(self, line):
        """Process IPO orders and change security to trading status"""
        security = line.security_id
        
        if line.ipo_price <= 0:
            raise UserError(f"IPO price must be set for {security.symbol} to change to trading status")
        
        # Process IPO orders using the existing matching engine
        if line.total_pending_quantity > 0:
            engine = self.env['stock.matching.engine']
            try:
                # Process all pending orders for this security
                engine.process_ipo_orders(
                    security_id=security.id,
                    ipo_quantity=line.total_pending_quantity,  # Use total requested quantity
                    ipo_price=line.ipo_price
                )
                _logger.info(f"Processed {line.total_pending_quantity} IPO shares for {security.symbol} at ${line.ipo_price}")
            except Exception as e:
                _logger.error(f"Failed to process IPO orders for {security.symbol}: {str(e)}")
                raise UserError(f"Failed to process IPO orders for {security.symbol}: {str(e)}")
        
        # Change status to trading (this is also done in process_ipo_orders but ensuring it's set)
        security.write({
            'ipo_status': 'trading',
            'active': True,
            'current_price': line.ipo_price,
            'session_start_price': line.ipo_price
        })
    
    def _start_new_po_round(self, line):
        """Start a new PO round for additional shares"""
        security = line.security_id
        
        if line.ipo_price <= 0:
            raise UserError(f"PO price must be set for {security.symbol} to start new PO round")
        
        if line.new_po_quantity <= 0:
            raise UserError(f"PO quantity must be set for {security.symbol} to start new PO round")
        
        # Start new PO round using the security method
        security.start_po_round(line.new_po_quantity, line.ipo_price)
        
        _logger.info(f"Started new PO round for {security.symbol}: {line.new_po_quantity} shares at ${line.ipo_price}")


class SessionEndIpoWizardLine(models.TransientModel):
    _name = 'session.end.ipo.wizard.line'
    _description = 'IPO Security Line'
    
    wizard_id = fields.Many2one(
        'session.end.ipo.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    security_id = fields.Many2one(
        'stock.security',
        string='Security',
        required=True,
        readonly=True
    )
    
    symbol = fields.Char(
        string='Symbol',
        related='security_id.symbol',
        readonly=True
    )
    
    security_name = fields.Char(
        string='Name',
        related='security_id.name',
        readonly=True
    )
    
    current_status = fields.Selection([
        ('ipo', 'IPO - Initial Public Offering'),
        ('po', 'PO - Public Offering'),
        ('trading', 'Trading - Normal Market')
    ], string='Current Status', readonly=True)
    
    new_status = fields.Selection([
        ('ipo', 'Continue IPO - Initial Public Offering'),
        ('po', 'Continue PO - Public Offering'),
        ('trading', 'Change to Trading - Normal Market'),
        ('new_po', 'Start New PO Round - Additional Shares')
    ], string='New Status', required=True)
    
    pending_orders_count = fields.Integer(
        string='Pending Orders',
        readonly=True,
        help='Number of pending IPO orders'
    )
    
    total_pending_quantity = fields.Integer(
        string='Total Pending Quantity',
        readonly=True,
        help='Total quantity requested in pending IPO orders'
    )
    
    ipo_price = fields.Float(
        string='IPO/PO Price',
        digits=(16, 4),
        help='IPO/PO price for distribution (required if changing to trading or starting new PO)'
    )
    
    new_po_quantity = fields.Integer(
        string='New PO Quantity',
        help='Additional quantity for new PO round (required if selecting new PO)'
    )
    
    @api.constrains('new_status', 'ipo_price', 'new_po_quantity')
    def _check_ipo_price(self):
        """Validate IPO price and PO quantity are set when required"""
        for line in self:
            if line.new_status == 'trading' and line.ipo_price <= 0:
                raise UserError(f"IPO price must be set for {line.symbol} when changing to trading status")
            if line.new_status == 'new_po':
                if line.ipo_price <= 0:
                    raise UserError(f"PO price must be set for {line.symbol} when starting new PO round")
                if line.new_po_quantity <= 0:
                    raise UserError(f"PO quantity must be set for {line.symbol} when starting new PO round")