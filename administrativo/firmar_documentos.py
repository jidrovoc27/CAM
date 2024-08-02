# # *-* coding: utf-8 *-*
import datetime
import os
import sys
# import fitz
# import qrcode
from cryptography.hazmat import backends
from cryptography.hazmat.primitives.serialization import pkcs12
from django.contrib import messages
from endesive.pdf import cms
from PIL import Image
import random
#
from endesive.signer import cert2asn
from pdf2image import convert_from_bytes
from datetime import datetime
from CAM.settings import SITE_STORAGE, SITE_POPPLER, MEDIA_URL, MEDIA_ROOT, DEBUG, BASE_DIR
from administrativo.funciones import conviert_html_to_pdf
import pyqrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
#
# URL_VALIDADOR='https://ws.firmadigital.gob.ec'
#
#
# def verificarFirmasPDF(path):
#     import base64
#     import requests
#     import json
#     from requests.exceptions import ConnectTimeout
#     header = {"Content-Type": "text/plain; charset=UTF-8"}
#     WS_VALIDACION_FIRMA_MINTEL = (
#         f"{URL_VALIDADOR}/servicio/validacionavanzadapdf"
#     )
#
#     # with open(path, "rb") as pdf_file:
#     #     encoded_string = base64.b64encode(pdf_file.read())
#     encoded_string = base64.b64encode(path.read())
#
#     try:
#         response_backup = requests.post(
#             url=WS_VALIDACION_FIRMA_MINTEL,
#             data=encoded_string.decode("utf-8"),
#             headers=header,
#         )
#         datos = json.loads(response_backup.text)
#         valido = datos['firmasValidas']
#         msg = 'documento con firmas invalidas' if not valido else ''
#         return valido, msg, datos
#     except ConnectTimeout as err:
#         return False, f"Error WS_FIRMA_MINTEL: {err=}, {type(err)=}", None
#     except Exception as err:
#         return False, f"Error WS_FIRMA_SERCOP: {err=}, {type(err)=}", None
#
#
# def qrImgFirma(request, persona, format="jpeg", paraMostrar=False):
#     text1 = 'Firmado electrónicamente por:'
#     nombres = f"{persona.nombres} {persona.apellido1} {persona.apellido2}"
#
#     qr = qrcode.QRCode(
#         box_size=8,
#         border=1
#     )
#
#     qr.add_data(
#         f"FIRMADO POR: {nombres}\nRAZON:\nLOCALIZACION:\nFECHA:{datetime.now().isoformat()}-05:00\nVALIDAR CON: www.firmadigital.gob.ec\n3.0.0")
#
#     fontsPath = os.path.join(BASE_DIR, "static", "font", "fonts_firmaelectronica")
#     qr.make(fit=True)
#     img = qr.make_image()
#     img_w, img_h = img.size
#     img_w += 5
#     backcolor = (255, 255, 255, 0)
#     mode = "RGBA"
#     if format == "jpeg":
#         backcolor = (255, 255, 255)
#         mode = "RGB"
#     result = Image.new(mode, (1100, img_h), color=backcolor)
#     result.paste(img, (0, 0))
#     draw = ImageDraw.Draw(result, mode=mode)
#
#     draw.text((img_w, 60 - 2), text1, font=ImageFont.truetype(os.path.join(fontsPath, "CourierPSRegular.ttf"), 40),
#               fill=(0, 0, 0))
#     draw.text((img_w, 120 - 2), f"{(persona.nombres or '').upper()}",
#               font=ImageFont.truetype(os.path.join(fontsPath, "CourierNewOSBold.ttf"), 80), fill=(0, 0, 0))
#     draw.text((img_w, 200 - 2), f"{(persona.apellido1 or '').upper()} {(persona.apellido2 or '').upper()}",
#               font=ImageFont.truetype(os.path.join(fontsPath, "CourierNewOSBold.ttf"), 80), fill=(0, 0, 0))
#
#     # if paraMostrar:
#     #     draw.text((img_w, 60 - 2), "PUEDES MOVER EL SELLO", font=ImageFont.truetype(os.path.join(fontsPath, "NotoSansMono-Bold.ttf"), 12),
#     #               fill=(0, 0, 0))
#     #     draw.text((img_w, 80 - 2), f"DOBLE CLIC PARA QUITAR",
#     #               font=ImageFont.truetype(os.path.join(fontsPath, "NotoSansMono-Bold.ttf"), 12), fill=(255,0,0))
#     # else:
#     #     draw.text((img_w, 30 - 2), text1, font=ImageFont.truetype(os.path.join(fontsPath, "NotoSansMono-Bold.ttf"), 18),
#     #               fill=(0, 0, 0))
#     #     draw.text((img_w, 60 - 2), f"{(persona.nombres or '').upper()}",
#     #               font=ImageFont.truetype(os.path.join(fontsPath, "Prompt-Regular.ttf"), 24), fill=(0, 0, 0))
#     #     draw.text((img_w, 90 - 2), f"{(persona.apellido1 or '').upper()} {(persona.apellido2 or '').upper()}",
#     #               font=ImageFont.truetype(os.path.join(fontsPath, "Prompt-Regular.ttf"), 24), fill=(0, 0, 0))
#     buffered = BytesIO()
#     result.save(buffered, format=format)
#     return "data:image/{};base64, {}".format(format, base64.b64encode(buffered.getvalue()).decode()), Image.open(
#         buffered)
#
#
def generarfirmaimagen(request, persona, nombrefirmante):
    try:
        data = {}
        folder_pdf = os.path.join(os.path.join(SITE_STORAGE, 'media', 'firmaelectronicapdf', ''))
        folder_images = os.path.join(os.path.join(SITE_STORAGE, 'media', 'firmaelectronicaimages', ''))
        os.makedirs(folder_pdf, exist_ok=True)
        os.makedirs(folder_images, exist_ok=True)
        qrname = 'qr_firma_{}'.format(persona.id)
        rutapdf = '{}{}.pdf'.format(folder_pdf, qrname)
        rutaimg = '{}{}.png'.format(folder_images, qrname)
        if os.path.isfile(rutapdf):
            os.remove(rutaimg)
            os.remove(rutapdf)
        url = pyqrcode.create(f'FIRMADO POR: {nombrefirmante}\nRAZON:\nLOCALIZACION: \nFECHA: {datetime.datetime.now()}\nVALIDAR CON: www.firmadigital.gob.ec\n2.10.1')
        url.png('{}/{}.png'.format(folder_pdf, qrname), 16, '#000000')  # '#1C3247'
        url_path = request.build_absolute_uri('/')[:-1].strip("/")
        data['url_path'] = url_path
        data['qrname'] = '{}'.format(qrname)
        data['persona'] = persona
        data['nombrefirmante'] = nombrefirmante
        valida = conviert_html_to_pdf('adm_firmardocumentos/firma/vistapreviafirma.html', {'data': data})
        if valida:
            images = convert_from_bytes(valida.content,
                                        output_folder=folder_images,
                                        poppler_path=SITE_POPPLER,
                                        output_file=f'{qrname}_firma',
                                        fmt="png")  # dpi=95, size=(150, 45)
            return images[0].filename, True, ''
        else:
            return f'', False, f'Intentelo nuevamente'
    except Exception as ex:
        linea_ = sys.exc_info()[-1].tb_lineno
        print(ex, linea_)
        messages.warning(request, str(ex))
        return f'/static/firmaelectronica/firma_position.jpg', False, f'{ex} - Linea: {linea_}'
#
#
def firmar(request, password, certificado, pdf, numPagina=1, x=0, y=0, width=0, height=0):
    # pass
    persona = request.session['persona']
    date = datetime.datetime.now()
    date = (datetime.datetime.now() + datetime.timedelta(hours=5)).strftime("D:%Y%m%d%H%M%S+00'00'")
    p12 = pkcs12.load_key_and_certificates(certificado.read(), password.encode("ascii"), backends.default_backend())
    # VALIDACION DE FIRMA
    cert = cert2asn(p12[1])
    entevalidador = cert.issuer.native
    sujeto = cert.subject.native
    nombrefirmante_ = cert.subject.native['common_name']
    # if not nombrefirmante_ == persona.nombre_completo():
    #     return False, f'Propietario de la firma ({nombrefirmante_}) no coincide con el usuario de la sesión actual {persona.nombre_completo()}'
    if datetime.datetime.now().date() >= p12[1].not_valid_after.date():
        return False, f'Firma caduco el {p12[1].not_valid_after.date()}'
    url_img, resp_img, msg_img = generarfirmaimagen(request, persona, nombrefirmante_)
    if not resp_img:
        return False, f'Fallo al generar firma. {msg_img}'
    imgFirma = Image.open(url_img)
    dct = {
        "aligned": 0,
        "sigflags": 1,
        "sigflagsft": 132,
        "sigpage": numPagina,  # NUM PAGINA
        "auto_sigfield": True,
        "sigandcertify": True,  # 612 - width, 792 - height
        "signaturebox": (x, y, x + width, y + height),  # UBICACION X, Y, TAMAÑO X, Y
        # "signature": f'firmado Fecha',
        "signature_img_distort": False,
        "signature_img": imgFirma,
        "contact": persona.emailinst,
        "location": f"",
        "signingdate": date,
        "reason": "",
        "password": password,
    }
    datau = pdf.read() if type(pdf).__name__.lower() != "bytes" else pdf
    datas = cms.sign(datau, dct, p12[0], p12[1], p12[2], "sha256")
    return datau, datas
#
# def obtener_posicion_x_y_saltolinea(urlpdf, palabras, ultima_pagina=True, exacta=False, horizontal=False):
#     # COORDENADAS QUE SE OBTIENE ES X Y SUPERIOR IZQUIERDO
#     pdf = SITE_STORAGE + urlpdf
#     documento = fitz.open(pdf)
#     numpaginafirma = int(documento.page_count) - 1
#     with fitz.open(pdf) as document:
#         words_dict = {}
#         for page_number, page in enumerate(document):
#             if page_number == numpaginafirma or not ultima_pagina:
#                 words_blocks = page.get_text("blocks")
#                 words_text = list(page.get_text("dict").values())
#                 words_dict[page_number] = words_blocks + words_text
#     valor = x = y = None
#     for page_number, page_text in words_dict.items():
#         for cadena in page_text:
#             try:
#                 if palabras in cadena[4].replace('\n', ' '):
#                     valor = cadena
#                     if valor:
#                         x = int(valor[0])
#                         if horizontal:
#                             y = words_text[1]-int(valor[3])+70
#                         else:
#                             y = 890 - int(valor[3])
#                     if exacta:
#                         t_saltos = cadena[4].count('\n')
#                         if not horizontal:
#                             y += int(f'{t_saltos}0')
#                         # Dividir la cadena en líneas usando '\n' como delimitador
#                         lineas, palabra_l = cadena[4].split('\n'), ''
#                         for linea in lineas:
#                             if len(linea) > len(palabra_l):
#                                 palabra_l = linea
#                         x += len(palabra_l) + 10
#                     return x, y, page_number
#             except Exception as ex:
#                 break
#     return x, y, numpaginafirma
