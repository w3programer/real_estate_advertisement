
from odoo.addons.web.controllers.main import WebClient
from odoo import http
import werkzeug.wsgi
import logging
from odoo.tools.misc import file_open
from odoo.http import request
_logger = logging.getLogger(__name__)


class OverrideLocaleLoading(WebClient):
    @http.route('/web/webclient/locale/<string:lang>', type='http', auth="none")
    def load_locale(self, lang):
        magic_file_finding = [lang.replace("_", '-').lower(), lang.split('_')[0]]
        for code in magic_file_finding:
            try:
                if code.find("ar") != -1:
                    #load our custom locale files
                    return http.Response(
                    werkzeug.wsgi.wrap_file(
                        request.httprequest.environ,
                        file_open('smart_assyrian_datepicker/static/src/js/locale/ar-iq.js', 'rb')
                    ),
                    content_type='application/javascript; charset=utf-8',
                    headers=[('Cache-Control', 'max-age=%s' % http.STATIC_CACHE)],
                    direct_passthrough=True,)
                else: 
                    return http.Response(
                    werkzeug.wsgi.wrap_file(
                        request.httprequest.environ,
                        file_open('web/static/lib/moment/locale/%s.js' % code, 'rb')
                    ),
                    content_type='application/javascript; charset=utf-8',
                    headers=[('Cache-Control', 'max-age=%s' % http.STATIC_CACHE)],
                    direct_passthrough=True,)
            except IOError:
                _logger.debug("No moment locale for code %s", code)

        return request.make_response("", headers=[
            ('Content-Type', 'application/javascript'),
            ('Cache-Control', 'max-age=%s' % http.STATIC_CACHE),
        ])