# from odoo import http
# import base64
# from odoo.http import content_disposition, dispatch_rpc, request, \
#     serialize_exception as _serialize_exception, Response
# from odoo.addons.web.controllers.main import Binary  # Import the class
#
#
# def binary_content(xmlid=None, model='ir.attachment', id=None, field='datas', unique=False,
#                    filename=None, filename_field='datas_fname', download=False, mimetype=None,
#                    default_mimetype='application/octet-stream', access_mode=None, access_token=None,
#                    env=None):
#     return request.registry['ir.http'].binary_content(
#         xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
#         filename_field=filename_field, download=download, mimetype=mimetype,
#         default_mimetype=default_mimetype, access_mode=access_mode, access_token=access_token,
#         env=env)
#
# class CustomBinary(Binary):
#
#     @http.route(['/web/image',
#                  '/web/image/<string:xmlid>',
#                  '/web/image/<string:xmlid>/<string:filename>',
#                  '/web/image/<string:xmlid>/<int:width>x<int:height>',
#                  '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<string:model>/<int:id>/<string:field>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<int:id>',
#                  '/web/image/<int:id>/<string:filename>',
#                  '/web/image/<int:id>/<int:width>x<int:height>',
#                  '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<int:id>-<string:unique>',
#                  '/web/image/<int:id>-<string:unique>/<string:filename>',
#                  '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
#                  '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http',
#                 auth="public")
#     def content_common(self, xmlid=None, model='ir.attachment', id=None, field='datas',
#                        filename=None, filename_field='datas_fname', unique=None, mimetype=None,
#                        download=None, data=None, token=None, access_token=None, access_mode=None,
#                        **kw):
#         status, headers, content = binary_content(
#             xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
#             filename_field=filename_field, download=download, mimetype=mimetype,
#             access_token=access_token, access_mode=access_mode)
#         if status == 304:
#             response = werkzeug.wrappers.Response(status=status, headers=headers)
#         elif status == 301:
#             return werkzeug.utils.redirect(content, code=301)
#         elif status != 200:
#             response = request.not_found()
#         else:
#             content_base64 = base64.b64decode(content)
#             headers.append(('Content-Length', len(content_base64)))
#             response = request.make_response(content_base64, headers)
#         if token:
#             response.set_cookie('fileToken', token)
#         return response
#
#     @http.route(['/web/image',
#                  '/web/image/<string:xmlid>',
#                  '/web/image/<string:xmlid>/<string:filename>',
#                  '/web/image/<string:xmlid>/<int:width>x<int:height>',
#                  '/web/image/<string:xmlid>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<string:model>/<int:id>/<string:field>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<string:filename>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>',
#                  '/web/image/<string:model>/<int:id>/<string:field>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<int:id>',
#                  '/web/image/<int:id>/<string:filename>',
#                  '/web/image/<int:id>/<int:width>x<int:height>',
#                  '/web/image/<int:id>/<int:width>x<int:height>/<string:filename>',
#                  '/web/image/<int:id>-<string:unique>',
#                  '/web/image/<int:id>-<string:unique>/<string:filename>',
#                  '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>',
#                  '/web/image/<int:id>-<string:unique>/<int:width>x<int:height>/<string:filename>'], type='http',
#                 auth="public")
#     def content_image(self, xmlid=None, model='ir.attachment', id=None, field='datas',
#                       filename_field='datas_fname', unique=None, filename=None, mimetype=None,
#                       download=None, width=0, height=0, crop=False, access_mode=None,
#                       access_token=None, avoid_if_small=False, upper_limit=False, signature=False, **kw):
#         status, headers, content = binary_content(
#             xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
#             filename_field=filename_field, download=download, mimetype=mimetype,
#             default_mimetype='image/png', access_mode=access_mode, access_token=access_token)
#         if status == 304:
#             return werkzeug.wrappers.Response(status=304, headers=headers)
#         elif status == 301:
#             return werkzeug.utils.redirect(content, code=301)
#         elif status != 200 and download:
#             return request.not_found()
#
#         if headers and dict(headers).get('Content-Type', '') == 'image/svg+xml':  # we shan't resize svg images
#             height = 0
#             width = 0
#         else:
#             height = int(height or 0)
#             width = int(width or 0)
#
#         if not content:
#             content = base64.b64encode(self.placeholder(image='placeholder.png'))
#             headers = self.force_contenttype(headers, contenttype='image/png')
#             if not (width or height):
#                 suffix = field.split('_')[-1]
#                 if suffix in ('small', 'medium', 'big'):
#                     content = getattr(odoo.tools, 'image_resize_image_%s' % suffix)(content)
#
#         if crop and (width or height):
#             content = crop_image(content, type='center', size=(width, height), ratio=(1, 1))
#         elif (width or height):
#             if not upper_limit:
#                 # resize maximum 500*500
#                 if width > 500:
#                     width = 500
#                 if height > 500:
#                     height = 500
#             content = odoo.tools.image_resize_image(base64_source=content, size=(width or None, height or None),
#                                                     encoding='base64', upper_limit=upper_limit,
#                                                     avoid_if_small=avoid_if_small)
#
#         image_base64 = base64.b64decode(content)
#         headers.append(('Content-Length', len(image_base64)))
#         response = request.make_response(image_base64, headers)
#         response.status_code = status
#         return response
