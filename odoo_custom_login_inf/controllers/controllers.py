# -*- encoding: utf-8 -*-

import logging
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from werkzeug.urls import url_encode, iri_to_uri
import odoo
import odoo.modules.registry
from odoo.tools.translate import _
from odoo import http, tools
from odoo.http import content_disposition, request, Response
from odoo.addons.web.controllers.home import Home as WebHome
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.portal.controllers.portal import CustomerPortal


_logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Odoo Web helpers
# ----------------------------------------------------------


def _get_login_redirect_url(uid, redirect=None):
    """ Decide if user requires a specific post-login redirect, e.g. for 2FA, or if they are
    fully logged and can proceed to the requested URL
    """
    if request.session.uid:  # fully logged
        return redirect or '/web'

    # partial session (MFA)
    url = request.env(user=uid)['res.users'].browse(uid)._mfa_url()
    if not redirect:
        return url

    parsed = werkzeug.urls.url_parse(url)
    qs = parsed.decode_query()
    qs['redirect'] = redirect
    return parsed.replace(query=werkzeug.urls.url_encode(qs)).to_url()


def abort_and_redirect(url):
    r = request.httprequest
    response = werkzeug.utils.redirect(url, 302)
    response = r.app.get_response(r, response, explicit_session=False)
    werkzeug.exceptions.abort(response)


def ensure_db(redirect='/web/database/selector'):
    db = request.params.get('db') and request.params.get('db').strip()

    # Ensure db is legit
    if db and db not in http.db_filter([db]):
        db = None

    if db and not request.session.db:
        # User asked a specific database on a new session.
        # That mean the nodb router has been used to find the route
        # Depending on installed module in the database, the rendering of the page
        # may depend on data injected by the database route dispatcher.
        # Thus, we redirect the user to the same page but with the session cookie set.
        # This will force using the database route dispatcher...
        r = request.httprequest
        url_redirect = werkzeug.urls.url_parse(r.base_url)
        if r.query_string:
            # in P3, request.query_string is bytes, the rest is text, can't mix them
            query_string = iri_to_uri(r.query_string)
            url_redirect = url_redirect.replace(query=query_string)
        request.session.db = db
        abort_and_redirect(url_redirect)

    # if db not provided, use the session one
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db

    # if no db can be found til here, send to the database selector
    # the database selector will redirect to database manager if needed
    if not db:
        werkzeug.exceptions.abort(werkzeug.utils.redirect(redirect, 303))

    # always switch the session to the computed db
    if db != request.session.db:
        request.session.logout()
        abort_and_redirect(request.httprequest.url)

    request.session.db = db

# ----------------------------------------------------------
# Odoo Web web Controllers
# ----------------------------------------------------------


class CustomAuthSignupHome(AuthSignupHome):
    """Override auth_signup controller to use custom reset password template"""

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        """Override reset password to use custom template matching login page design"""
        qcontext = self.get_auth_signup_qcontext()
        
        # Handle form submission
        if 'login' in qcontext and qcontext.get('login'):
            login = qcontext.get('login')
            assert login == request.params['login']
            _logger.info("Password reset requested for: %s", login)
            
            try:
                # Call parent method to handle the actual reset logic
                response = super(CustomAuthSignupHome, self).web_auth_reset_password(*args, **kw)
                
                # If response is a redirect, it means reset was successful
                if hasattr(response, 'status_code') and response.status_code in [301, 302]:
                    return response
                    
                # If it's not a redirect, it means we're rendering the form with a message
                # Extract any success message and use our custom template
                if hasattr(response, 'qcontext'):
                    qcontext.update(response.qcontext)
                    
            except Exception as e:
                _logger.error("Error in password reset: %s", str(e))
                qcontext['error'] = str(e)

        # Ensure we have database information
        if 'databases' not in qcontext:
            try:
                qcontext['databases'] = http.db_list()
            except odoo.exceptions.AccessDenied:
                qcontext['databases'] = None

        # Use our custom reset password template
        response = request.render('odoo_custom_login_inf.reset_password_template', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        """Override signup/change password to use custom template matching login page design"""
        qcontext = self.get_auth_signup_qcontext()
        
        # Handle form submission
        if request.httprequest.method == 'POST':
            try:
                # Call parent method to handle the actual signup/password change logic
                response = super(CustomAuthSignupHome, self).web_auth_signup(*args, **kw)
                
                # If response is a redirect, it means signup/password change was successful
                if hasattr(response, 'status_code') and response.status_code in [301, 302]:
                    return response
                    
                # If it's not a redirect, extract any error message
                if hasattr(response, 'qcontext'):
                    qcontext.update(response.qcontext)
                    
            except Exception as e:
                _logger.error("Error in signup/password change: %s", str(e))
                qcontext['error'] = str(e)

        # Ensure we have database information
        if 'databases' not in qcontext:
            try:
                qcontext['databases'] = http.db_list()
            except odoo.exceptions.AccessDenied:
                qcontext['databases'] = None

        # Use our custom change password template (fallback to default)
        try:
            response = request.render('odoo_custom_login_inf.change_password_template', qcontext)
        except ValueError:
            # If custom template doesn't exist, use the standard one
            response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


class Home(WebHome):

    def _login_redirect(self, uid, redirect=None):
        """Override to FORCE portal users to redirect to configured path.
        Portal users will ALWAYS go to the portal_redirect_path setting,
        ignoring any explicit redirect parameter.
        Internal users can still use the redirect parameter.
        """
        try:
            env = request.env
            # Read configured path (system parameter) with sudo
            param_obj = env['ir.config_parameter'].sudo()
            portal_redirect_path = (param_obj.get_param('login_background.portal_redirect_path') or '/my').strip()

            # Basic sanitation: ensure it starts with a slash
            if portal_redirect_path and not portal_redirect_path.startswith('/') and '://' not in portal_redirect_path:
                portal_redirect_path = '/' + portal_redirect_path

            # Determine user type
            user = env['res.users'].sudo().browse(uid)
            target = '/web'
            
            if user.exists():
                try:
                    if user.has_group('base.group_portal'):
                        # FORCE portal users to configured path, ignore redirect parameter
                        target = portal_redirect_path or '/my'
                        _logger.info("Portal user %s FORCED to redirect to %s (ignoring redirect param)", 
                                   user.login or uid, target)
                    else:
                        # Internal users can use redirect parameter
                        target = redirect if redirect else '/web'
                        _logger.info("Internal user %s redirected to %s", user.login or uid, target)
                except Exception as ge:
                    # If group resolution fails, default to backend
                    _logger.error("Error checking groups for uid %s: %s", uid, ge, exc_info=True)
                    target = redirect if redirect else '/web'
            else:
                _logger.warning("Login redirect: user id %s does not exist; using default backend redirect", uid)
                target = redirect if redirect else '/web'

            return _get_login_redirect_url(uid, target)

        except Exception as e:
            _logger.error("Login redirect failed for uid %s: %s", uid, e, exc_info=True)
            # Safe fallback
            return _get_login_redirect_url(uid, redirect or '/web')

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        ensure_db()
        _logger.info("Custom login page accessed")
        request.params['login_success'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            request.update_env(user=odoo.SUPERUSER_ID)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            try:
                credential = {
                    'login': request.params['login'],
                    'password': request.params['password'],
                    'type': 'password'
                }
                auth_info = request.session.authenticate(request.session.db, credential)
                request.params['login_success'] = True
                return request.redirect(self._login_redirect(auth_info['uid'], redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        param_obj = request.env['ir.config_parameter'].sudo()
        values['reset_password_enabled'] = param_obj.get_param('auth_signup.reset_password')
        values['signup_enabled'] = param_obj.get_param('auth_signup.invitation_scope') == 'b2c'
        values['disable_footer'] = param_obj.get_param('disable_footer')
        style = param_obj.get_param('login_background.style')
        background = param_obj.get_param('login_background.background')
        values['background_color'] = param_obj.get_param('login_background.color')
        
        _logger.debug("Background color: %s", param_obj.get_param('login_background.color'))
        background_image = param_obj.get_param('login_background.background_image')
        bg_src = ""
        color_1 = param_obj.get_param('login_background.bgcolor_1')
        color_2 = param_obj.get_param('login_background.bgcolor_2')
        color_3 = param_obj.get_param('login_background.bgcolor_3')
        
        if background == 'image':
            image_url = ''
            if background_image:
                base_url = param_obj.get_param('web.base.url')
                image_url = base_url + '/web/image?' + 'model=login.image&id=' + background_image + '&field=image'
                values['background_src'] = image_url or ''
                bg_src = f"background-image: url('{image_url}');"
                values['background_color'] = ''

        if background == 'color':
            values['background_src'] = ''
            color1 = param_obj.get_param('login_background.color')
            bg_src = f"background-color:{color1};"
            
        if background == 'gradient':
            bg_src = f"background-image:linear-gradient(45deg, {color_1}, {color_2}, {color_3});"
            
        values['bg_src'] = bg_src
        
        if style == 'default' or style is False:
            response = request.render('web.login', values)
        elif style == 'left':
            response = request.render('odoo_custom_login_inf.left_login_template', values)
        elif style == 'right':
            response = request.render('odoo_custom_login_inf.right_login_template', values)
        else:
            response = request.render('odoo_custom_login_inf.middle_login_template', values)

        response.headers['X-Frame-Options'] = 'DENY'
        return response


class CustomPortal(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Override portal home to redirect portal users to configured path."""
        _logger.info("CustomPortal.home() called - checking user groups")
        
        try:
            user = request.env.user
            _logger.info("Current user: %s (ID: %s)", user.login, user.id)
            
            # Check if user has portal group
            if user.has_group('base.group_portal'):
                _logger.info("User %s is a portal user - proceeding with redirect", user.login)
                
                try:
                    param_obj = request.env['ir.config_parameter'].sudo()
                    portal_redirect_path = (param_obj.get_param('login_background.portal_redirect_path') or '/unit-reservation').strip()
                    if portal_redirect_path and not portal_redirect_path.startswith('/') and '://' not in portal_redirect_path:
                        portal_redirect_path = '/' + portal_redirect_path
                        
                    _logger.info("Redirecting portal user %s from /my to %s", user.login, portal_redirect_path)
                    return werkzeug.utils.redirect(portal_redirect_path)
                except Exception as e:
                    _logger.error("Error getting redirect path: %s", e)
                    return werkzeug.utils.redirect('/unit-reservation')
            else:
                _logger.info("User %s is NOT a portal user - calling parent method", user.login)
                # Call parent method for non-portal users
                return super(CustomPortal, self).home(**kw)
                
        except Exception as e:
            _logger.error("Error in portal redirect logic: %s", e)
            # Fallback to parent method
            return super(CustomPortal, self).home(**kw)


class PortalRedirectController(http.Controller):
    """
    Alternative controller to intercept portal routes with higher priority.
    """
    
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True, csrf=False)
    def portal_home_redirect(self, **kw):
        """Intercept portal home requests and redirect portal users."""
        _logger.info("PortalRedirectController.portal_home_redirect() called")
        
        try:
            user = request.env.user
            _logger.info("Portal redirect check for user: %s (ID: %s)", user.login, user.id)
            
            # Check if user has portal group
            if user.has_group('base.group_portal'):
                _logger.info("User %s is a portal user - redirecting", user.login)
                
                try:
                    param_obj = request.env['ir.config_parameter'].sudo()
                    portal_redirect_path = (param_obj.get_param('login_background.portal_redirect_path') or '/unit-reservation').strip()
                    if portal_redirect_path and not portal_redirect_path.startswith('/') and '://' not in portal_redirect_path:
                        portal_redirect_path = '/' + portal_redirect_path
                        
                    _logger.info("Redirecting portal user %s from /my to %s", user.login, portal_redirect_path)
                    return werkzeug.utils.redirect(portal_redirect_path)
                except Exception as e:
                    _logger.error("Error getting redirect path: %s", e)
                    return werkzeug.utils.redirect('/unit-reservation')
            else:
                _logger.info("User %s is NOT a portal user - delegating to original portal", user.login)
                # For non-portal users, call the original portal controller
                from odoo.addons.portal.controllers.portal import CustomerPortal
                original_portal = CustomerPortal()
                return original_portal.home(**kw)
                
        except Exception as e:
            _logger.error("Error in portal redirect logic: %s", e)
            # Fallback to original portal controller
            from odoo.addons.portal.controllers.portal import CustomerPortal
            original_portal = CustomerPortal()
            return original_portal.home(**kw)


class RootRedirectController(http.Controller):
    """
    Controller to redirect root path (/) to configured portal path, similar to /my behavior.
    """
    
    @http.route(['/'], type='http', auth="public", website=True)
    def root_redirect(self, **kw):
        """Redirect root path to configured portal redirect path."""
        _logger.info("Root path (/) accessed - reading portal redirect path")
        
        try:
            # Read configured path from system parameter
            param_obj = request.env['ir.config_parameter'].sudo()
            portal_redirect_path = (param_obj.get_param('login_background.portal_redirect_path') or '/market').strip()
            
            # Basic sanitation: ensure it starts with a slash
            if portal_redirect_path and not portal_redirect_path.startswith('/') and '://' not in portal_redirect_path:
                portal_redirect_path = '/' + portal_redirect_path
            
            _logger.info("Root path redirect target: %s", portal_redirect_path)
            
            # Check if user is logged in
            if request.session.uid:
                user = request.env.user
                _logger.info("Logged in user %s accessing root - redirecting to %s", user.login, portal_redirect_path)
                return werkzeug.utils.redirect(portal_redirect_path)
            else:
                # Not logged in - redirect to login page with redirect parameter
                _logger.info("Anonymous user accessing root - redirecting to /web/login")
                return werkzeug.utils.redirect(f'/web/login?redirect={portal_redirect_path}')
        except Exception as e:
            _logger.error("Error getting portal redirect path: %s", e)
            # Fallback to /market
            if request.session.uid:
                return werkzeug.utils.redirect('/market')
            else:
                return werkzeug.utils.redirect('/web/login?redirect=/market')


class TestController(http.Controller):

    @http.route(['/test-redirect'], type='http', auth="user", website=True)
    def test_redirect(self, **kw):
        """Test route to verify our controller is working."""
        _logger.info("Test redirect route called")
        user = request.env.user
        if user.has_group('base.group_portal'):
            return f"<h1>Portal User Detected: {user.login}</h1><p>Redirect should work for /my</p>"
        else:
            return f"<h1>Internal User: {user.login}</h1><p>You should see portal behavior on /my</p>"
    
    @http.route(['/test-controller'], type='http', auth="none", website=True)
    def test_controller(self, **kw):
        """Test route without authentication to verify controller loading."""
        _logger.info("Test controller route called without auth")
        return "<h1>Controller is working!</h1><p>The custom login module controller is properly loaded.</p>"