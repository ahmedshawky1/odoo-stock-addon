# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Override email field to have a default value
    email = fields.Char(
        string='Email',
        default='example@example.com',
        help='Email address of the partner'
    )

    @api.model
    def fix_missing_partner_emails(self):
        """Utility function to fix existing partners without email addresses."""
        try:
            # Find partners without email
            partners_without_email = self.search([
                '|', 
                ('email', '=', False), 
                ('email', '=', '')
            ])
            
            count = len(partners_without_email)
            if count > 0:
                _logger.info(f"Fixing {count} partners without email addresses")
                
                # Update all partners without email
                partners_without_email.write({'email': 'example@example.com'})
                
                _logger.info(f"Successfully updated {count} partners with default email")
                return {'success': True, 'updated_count': count}
            else:
                _logger.info("All partners already have email addresses")
                return {'success': True, 'updated_count': 0}
                
        except Exception as e:
            _logger.error(f"Error fixing partner emails: {str(e)}")
            return {'success': False, 'error': str(e)}

    @api.model
    def ensure_all_emails_set(self):
        """Comprehensive function to ensure all users and partners have emails."""
        try:
            # Fix partners first
            partner_result = self.fix_missing_partner_emails()
            
            # Fix users (call the method from res_users model)
            user_result = self.env['res.users'].fix_missing_emails()
            
            _logger.info(f"Email fix complete - Partners: {partner_result.get('updated_count', 0)}, Users: {user_result.get('updated_count', 0)}")
            
            return {
                'success': True,
                'partners_updated': partner_result.get('updated_count', 0),
                'users_updated': user_result.get('updated_count', 0)
            }
            
        except Exception as e:
            _logger.error(f"Error in comprehensive email fix: {str(e)}")
            return {'success': False, 'error': str(e)}