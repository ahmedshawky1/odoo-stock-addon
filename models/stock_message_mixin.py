# -*- coding: utf-8 -*-

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class StockMessageMixin(models.AbstractModel):
    """
    Mixin class to provide centralized message posting functionality
    without email notifications for all stock market models.
    """
    _name = 'stock.message.mixin'
    _description = 'Stock Message Mixin'

    def message_post(self, **kwargs):
        """
        Override message_post to always disable email/notifications in Odoo 18
        and post a safe internal note by default.
        """
        # Context guards to suppress mail pipeline
        context = dict(self.env.context or {})
        context.setdefault('mail_notify_noemail', True)
        context.setdefault('mail_create_nosubscribe', True)
        context.setdefault('mail_post_autofollow', False)
        context.setdefault('notification_disable', True)

        # Safe defaults: post a log note without emails or pings
        kwargs.setdefault('message_type', 'comment')           # chatter note
        kwargs.setdefault('subtype_xmlid', 'mail.mt_note')     # internal note subtype
        kwargs.setdefault('author_id', False)                  # no sender required
        kwargs.setdefault('email_from', False)                 # avoid default mail sender
        kwargs.setdefault('notify', False)                     # do not notify followers

        return super(StockMessageMixin, self.with_context(context)).message_post(**kwargs)

    def safe_message_post(self, body=None, subject=None, message_type='comment', **kwargs):
        """
        Centralized method to post messages without triggering email notifications.
        
        Args:
            body (str): Message body content
            subject (str): Message subject
            message_type (str): Type of message ('comment', 'notification', etc.)
            **kwargs: Additional parameters for message_post
            
        Returns:
            mail.message: The created message record or False if failed
        """
        try:
            # Ensure we don't send emails by setting the context and safe defaults
            safe_context = dict(self.env.context or {})
            safe_context.setdefault('mail_notify_noemail', True)
            safe_context.setdefault('mail_create_nosubscribe', True)
            safe_context.setdefault('mail_post_autofollow', False)
            safe_context.setdefault('notification_disable', True)

            # Safe defaults for kwargs
            kw = dict(kwargs or {})
            kw.setdefault('message_type', message_type or 'comment')
            kw.setdefault('subtype_xmlid', 'mail.mt_note')
            kw.setdefault('author_id', False)
            kw.setdefault('email_from', False)
            kw.setdefault('notify', False)

            return self.with_context(safe_context).message_post(
                body=body,
                subject=subject,
                **kw
            )
        except Exception as e:
            _logger.error(f"Error posting message to {self._name} record {self.id}: {str(e)}")
            return False

    def log_status_change(self, old_status, new_status, additional_info=None):
        """
        Log status changes with standardized format.
        
        Args:
            old_status (str): Previous status
            new_status (str): New status
            additional_info (str): Optional additional information
        """
        body = f"Status changed from '{old_status}' to '{new_status}'"
        if additional_info:
            body += f". {additional_info}"
            
        return self.safe_message_post(
            body=body,
            subject=f"Status Update: {new_status}",
            message_type='comment'
        )

    def log_action(self, action, details=None, user=None):
        """
        Log user actions with standardized format.
        
        Args:
            action (str): Description of the action performed
            details (str): Optional additional details
            user (res.users): User who performed the action (defaults to current user)
        """
        if not user:
            user = self.env.user
            
        body = f"Action: {action}"
        if details:
            body += f"\nDetails: {details}"
        body += f"\nPerformed by: {user.name}"
        
        return self.safe_message_post(
            body=body,
            subject=f"Action: {action}",
            message_type='comment'
        )

    def log_broker_action(self, broker_user, client_user, action, details=None):
        """
        Log broker actions on behalf of clients.
        
        Args:
            broker_user (res.users): Broker performing the action
            client_user (res.users): Client on whose behalf the action is performed
            action (str): Description of the action
            details (str): Optional additional details
        """
        body = f"{action} by broker {broker_user.name} on behalf of client {client_user.name}"
        if details:
            body += f"\nDetails: {details}"
            
        return self.safe_message_post(
            body=body,
            subject=f"Broker Action: {action}",
            message_type='comment'
        )

    def log_error(self, error_message, context_info=None):
        """
        Log errors with standardized format.
        
        Args:
            error_message (str): Description of the error
            context_info (str): Optional context information
        """
        body = f"Error: {error_message}"
        if context_info:
            body += f"\nContext: {context_info}"
            
        _logger.error(f"Error in {self._name} record {self.id}: {error_message}")
        
        return self.safe_message_post(
            body=body,
            subject="Error Occurred",
            message_type='comment'
        )

    # Convenience helpers
    def log_note(self, body, subject=None):
        """Post a plain internal note (no emails)."""
        return self.safe_message_post(body=body, subject=subject or 'Log Note', message_type='comment')

    def log_note_as_system(self, body, subject=None):
        """Post as OdooBot/System partner with no emails."""
        partner = self.env.ref('base.partner_root', raise_if_not_found=False)
        author_id = partner.id if partner else False
        return self.safe_message_post(body=body, subject=subject or 'System Note', message_type='comment', author_id=author_id)

    def log_note_as_user(self, user, body, subject=None):
        """Post as a specific user's partner (no emails)."""
        author_id = getattr(user, 'partner_id', False) and user.partner_id.id or False
        return self.safe_message_post(body=body, subject=subject or f"Note by {getattr(user, 'name', 'User')}", message_type='comment', author_id=author_id)