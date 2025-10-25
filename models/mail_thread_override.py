# -*- coding: utf-8 -*-

from odoo import models
import logging

_logger = logging.getLogger(__name__)


class MailThreadOverride(models.AbstractModel):
    """
    Global override for mail.thread to suppress outgoing emails from message_post/message_notify.
    This is needed because Odoo 18 tightened mail behaviors and may try to send emails
    even when we post log/audit messages. We centralize the suppression here to avoid
    configuring SMTP during simulations.
    """
    _inherit = 'mail.thread'

    def message_post(self, **kwargs):
        """Ensure message posting never triggers emails globally.
        - Force context flags to disable notifications and auto-follow
        - Default to a plain internal note to avoid follower pings/emails
        """
        ctx = dict(self.env.context or {})
        # Hard-disable any email notifications
        ctx.setdefault('mail_notify_noemail', True)
        ctx.setdefault('mail_create_nosubscribe', True)
        ctx.setdefault('mail_post_autofollow', False)
        ctx.setdefault('notification_disable', True)

        # Default-safe kwargs to avoid notifications and emails
        kwargs.setdefault('message_type', 'comment')                # chatter note
        kwargs.setdefault('subtype_xmlid', 'mail.mt_note')          # internal note
        kwargs.setdefault('author_id', False)                       # no sender required
        kwargs.setdefault('email_from', False)                      # don't pick default sender

        return super(MailThreadOverride, self.with_context(ctx)).message_post(**kwargs)

    def message_notify(self, partner_ids=False, subject=False, body='', **kwargs):
        """Guard message_notify as well, since some flows call it directly.
        Keep signature compatible and suppress email delivery via context.
        """
        ctx = dict(self.env.context or {})
        ctx.setdefault('mail_notify_noemail', True)
        ctx.setdefault('notification_disable', True)
        
        # message_notify may try to email partners; keep it as an internal log only
        kwargs.setdefault('email_layout_xmlid', False)
        kwargs.setdefault('record_name', False)
        kwargs.setdefault('subtype_xmlid', 'mail.mt_note')
        # Note: message_notify doesn't accept message_type, that's for message_post only
        kwargs.setdefault('author_id', False)
        kwargs.setdefault('email_from', False)
        
        try:
            return super(MailThreadOverride, self.with_context(ctx)).message_notify(
                partner_ids=partner_ids, subject=subject, body=body, **kwargs
            )
        except Exception as e:
            # As a last resort, fallback to a simple message_post so we never fail order flows
            _logger.error(f"message_notify failed (suppressed): {e}")
            return super(MailThreadOverride, self.with_context(ctx)).message_post(
                body=body or (subject or ''), message_type='comment', subtype_xmlid='mail.mt_note', author_id=False, email_from=False
            )
