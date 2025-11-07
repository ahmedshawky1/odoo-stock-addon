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
        
    # Create wizard lines (as defaults). Note: we also guard in create()
        line_vals = []
        for security in ipo_securities:
            # Count pending IPO orders
            # Count IPO orders regardless of session, they carry over across sessions
            pending_orders = self.env['stock.order'].search([
                ('security_id', '=', security.id),
                ('order_type', '=', 'ipo'),
                ('status', 'in', ['submitted', 'open'])
            ])
            
            line_data = {
                'security_id': security.id,
                'symbol': security.symbol,
                'security_name': security.name,
                'current_status': security.ipo_status,
                'new_status': security.ipo_status,  # Default to continue same status
                'pending_orders_count': len(pending_orders),
                'total_pending_quantity': sum(pending_orders.mapped('quantity')),
                'ipo_price': security.ipo_price or 0.0
            }
            
            # Debug log to check data
            _logger.info(f"Creating wizard line for security {security.symbol} (ID: {security.id}) with data: {line_data}")
            
            line_vals.append((0, 0, line_data))
        
        res['line_ids'] = line_vals
        return res

    def _prepare_line_dicts(self, session_id):
        """Build list of line dicts for IPO/PO securities of a session."""
        self.ensure_one()
        ipo_securities = self.env['stock.security'].search([
            ('ipo_status', 'in', ['ipo', 'po'])
        ])

        line_dicts = []
        for security in ipo_securities:
            # IPO orders should be counted regardless of originating session
            pending_orders = self.env['stock.order'].search([
                ('security_id', '=', security.id),
                ('order_type', '=', 'ipo'),
                ('status', 'in', ['submitted', 'open'])
            ])
            line_dicts.append({
                'wizard_id': self.id,
                'security_id': security.id,
                'symbol': security.symbol,
                'security_name': security.name,
                'current_status': security.ipo_status,
                'new_status': security.ipo_status,
                'pending_orders_count': len(pending_orders),
                'total_pending_quantity': sum(pending_orders.mapped('quantity')),
                'ipo_price': security.ipo_price or 0.0,
            })
        return line_dicts

    def _create_lines_if_missing(self):
        """Ensure wizard has line_ids created with security_id set."""
        for wiz in self:
            if wiz.line_ids:
                # Repair any missing security_id just in case
                for line in wiz.line_ids:
                    if not line.security_id and line.symbol:
                        sec = self.env['stock.security'].search([('symbol', '=', line.symbol)], limit=1)
                        if sec:
                            # Also sync symbol/name in case they were empty
                            vals = {'security_id': sec.id}
                            if not line.symbol:
                                vals['symbol'] = sec.symbol
                            if not line.security_name:
                                vals['security_name'] = sec.name
                            line.write(vals)
                continue
            # Create fresh lines
            line_dicts = wiz._prepare_line_dicts(wiz.session_id.id)
            if line_dicts:
                self.env['session.end.ipo.wizard.line'].create(line_dicts)

    def _rebuild_lines_preserving_user_choices(self):
        """Recreate lines from source data ensuring security_id is set, while preserving user choices.

        This guards against any client-side loss of security_id in transient records.
        """
        for wiz in self:
            # Capture user edits by symbol (fallback to name)
            edits = {}
            captured_lines = []
            for line in wiz.line_ids:
                key = False
                # Prefer stable keys first
                if line.security_id:
                    key = f"SEC:{line.security_id.id}"
                elif line.symbol:
                    key = f"SYM:{line.symbol}"
                elif line.security_name:
                    key = f"NAME:{line.security_name}"
                else:
                    key = f"ROW:{line.id}"

                valpack = {
                    'new_status': line.new_status,
                    'ipo_price': line.ipo_price,
                    'new_po_quantity': line.new_po_quantity,
                }
                edits[key] = valpack
                captured_lines.append((key, valpack))
            # Delete current lines
            wiz.line_ids.unlink()
            # Create fresh authoritative lines
            fresh = wiz._prepare_line_dicts(wiz.session_id.id)
            if fresh:
                new_lines = wiz.env['session.end.ipo.wizard.line'].create(fresh)
                # Re-apply edits: try multiple keys for robustness
                applied = set()
                for nl in new_lines:
                    # Build possible keys for this fresh line
                    poss = []
                    if nl.security_id:
                        poss.append(f"SEC:{nl.security_id.id}")
                    if nl.symbol:
                        poss.append(f"SYM:{nl.symbol}")
                    if nl.security_name:
                        poss.append(f"NAME:{nl.security_name}")
                    # Find first matching edit
                    found_vals = None
                    for p in poss:
                        if p in edits:
                            found_vals = edits[p]
                            applied.add(p)
                            break
                    # If only one edit was captured and only one new line exists, apply it regardless of key mismatch
                    if not found_vals and len(captured_lines) == 1 and len(new_lines) == 1:
                        found_vals = captured_lines[0][1]
                        applied.add(captured_lines[0][0])

                    if found_vals:
                        vals = {}
                        if found_vals.get('new_status'):
                            vals['new_status'] = found_vals['new_status']
                        if found_vals.get('ipo_price') is not None:
                            vals['ipo_price'] = found_vals['ipo_price']
                        if found_vals.get('new_po_quantity') is not None:
                            vals['new_po_quantity'] = found_vals['new_po_quantity']
                        if vals:
                            nl.write(vals)

    @api.model
    def create(self, vals):
        """Create the wizard and guarantee line_ids with security_id are present."""
        res = super().create(vals)
        try:
            res._create_lines_if_missing()
        except Exception as e:
            _logger.error(f"Failed to populate IPO wizard lines: {e}")
        return res
    
    # _ensure_security_ids removed; we ensure lines on creation and repair in _create_lines_if_missing
    
    def action_process(self):
        """Process the IPO status changes"""
        _logger.info(f"Processing wizard with {len(self.line_ids)} lines")

        # Ensure lines are populated and consistent server-side
        self._create_lines_if_missing()
        # If any line still lacks security_id, rebuild lines from source and preserve choices
        if any(not l.security_id for l in self.line_ids):
            _logger.warning("Rebuilding IPO wizard lines due to missing security_id on some rows")
            self._rebuild_lines_preserving_user_choices()

        for line in self.line_ids:
            _logger.info(f"Processing line: security_id={line.security_id.id if line.security_id else 'None'}, symbol={line.symbol if hasattr(line, 'symbol') else 'No symbol'}, new_status={line.new_status}")
            
            if not line.security_id:
                raise UserError(f"Security ID is missing for wizard line and could not be recovered")
            
            if line.new_status == 'trading':
                # Change to trading - process IPO orders and activate trading
                self._process_ipo_to_trading(line)
            elif line.new_status == 'new_po':
                # Start new PO round
                self._start_new_po_round(line)
            else:
                # Continue in IPO/PO status - just update if changed
                if line.new_status != line.current_status:
                    status_map = {
                        'ipo': 'ipo',
                        'po': 'po',
                        'trading': 'trade',
                    }
                    new_status_value = status_map.get(line.new_status)
                    if new_status_value:
                        line.security_id.write({'status': new_status_value})
        
        # Complete the session close
        self.session_id.action_force_close_after_ipo()
        
        # Close the wizard
        return {'type': 'ir.actions.act_window_close'}
    
    def _process_ipo_to_trading(self, line):
        """Process IPO orders and change security to trading status"""
        security = line.security_id
        
        if line.ipo_price <= 0:
            raise UserError(f"IPO price must be set for {security.symbol} to change to trading status")
        
        # Process IPO orders using the existing matching engine (unconditional)
        engine = self.env['stock.matching.engine']
        sym = security.symbol  # cache for safe logging even if tx aborts
        try:
            # Process all pending orders for this security. Engine will determine demand/capacity.
            engine.process_ipo_orders(
                security_id=security.id,
                ipo_quantity=line.total_pending_quantity or 0,
                ipo_price=line.ipo_price,
                session_id=self.session_id.id
            )
            _logger.info(f"IPO processing invoked for {sym} at ${line.ipo_price} with requested qty {line.total_pending_quantity or 0}")
        except Exception as e:
            # Avoid field access that triggers fetch after failure
            _logger.error("Failed to process IPO orders for %s: %s", sym, str(e))
            raise UserError(f"Failed to process IPO orders for {sym}: {str(e)}")
        
        # Change status to trading (ensure canonical 'status' is updated)
        security.write({
            'status': 'trade',
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
        required=False,
        readonly=True
    )
    
    symbol = fields.Char(
        string='Symbol',
        readonly=True,
        store=True
    )
    
    security_name = fields.Char(
        string='Name',
        readonly=True,
        store=True
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
    
    # No create/write overrides on line; we guarantee integrity from the wizard
    
    @api.model
    def create(self, vals):
        """Be tolerant when the client doesn't send security_id for inline rows.
        Try to recover it from symbol/security_name to avoid required-field errors."""
        if not vals.get('security_id'):
            sec = None
            sym = vals.get('symbol')
            if sym:
                sec = self.env['stock.security'].search([('symbol', '=', sym)], limit=1)
            if not sec and vals.get('security_name'):
                sec = self.env['stock.security'].search([('name', '=', vals['security_name'])], limit=1)
            if sec:
                vals['security_id'] = sec.id
                # Ensure symbol/name are synchronized if missing
                vals.setdefault('symbol', sec.symbol)
                vals.setdefault('security_name', sec.name)
            else:
                _logger.warning("Creating IPO wizard line without security_id; will be repaired server-side if possible. Data: %s", vals)
        return super().create(vals)

    def write(self, vals):
        """Repair missing security_id on write if possible based on symbol."""
        for rec in self:
            if not rec.security_id and not vals.get('security_id'):
                sym = vals.get('symbol') or rec.symbol
                sec = None
                if sym:
                    sec = self.env['stock.security'].search([('symbol', '=', sym)], limit=1)
                if not sec and (vals.get('security_name') or rec.security_name):
                    name = vals.get('security_name') or rec.security_name
                    sec = self.env['stock.security'].search([('name', '=', name)], limit=1)
                if sec:
                    # Also sync symbol/name if not provided
                    merged = dict(vals, security_id=sec.id)
                    if 'symbol' not in merged or not merged.get('symbol'):
                        merged['symbol'] = sec.symbol
                    if 'security_name' not in merged or not merged.get('security_name'):
                        merged['security_name'] = sec.name
                    vals = merged
        return super().write(vals)
    @api.constrains('new_status', 'ipo_price', 'new_po_quantity')
    def _check_ipo_price(self):
        """Validate IPO price and PO quantity are set when required"""
        for line in self:
            # Only validate business logic, not security_id (handled elsewhere)
            if line.new_status == 'trading' and line.ipo_price <= 0:
                raise UserError(f"IPO price must be set for {line.symbol} when changing to trading status")
            if line.new_status == 'new_po':
                if line.ipo_price <= 0:
                    raise UserError(f"PO price must be set for {line.symbol} when starting new PO round")
                if line.new_po_quantity <= 0:
                    raise UserError(f"PO quantity must be set for {line.symbol} when starting new PO round")