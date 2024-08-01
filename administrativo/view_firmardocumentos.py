# -*- coding: UTF-8 -*-
import io
import json
import os
import sys
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.db import transaction


from administrativo.models import Persona
from administrativo.firmar_documentos import firmar, generarfirmaimagen, qrImgFirma, verificarFirmasPDF
from administrativo.firmar_documentos_ec import JavaFirmaEc
from administrativo.funciones import generar_nombre, quitar_caracteres, remover_caracteres_tildes_unicode, \
add_data_aplication

@login_required(redirect_field_name='next', login_url='/login')
@transaction.atomic()
def view_firmardocumentos(request):
    global folder_pdf, qrname
    data = {}
    add_data_aplication(request, data)
    usuario_logeado = request.user
    if Persona.objects.filter(usuario=usuario_logeado, status=True).exists():
        persona_logeado = Persona.objects.get(usuario=usuario_logeado, status=True)
    else:
        persona_logeado = 'CAM'
    data['persona_logeado'] = persona_logeado
    if request.method == 'POST':
        action = request.POST['action']

        if action == 'firmardocumento':
            try:
                documento_a_firmar = request.FILES["archivo"]
                certificado = request.FILES["firma"]
                contrasenaCertificado = request.POST['palabraclave']
                razon = request.POST['razon'] if 'razon' in request.POST else ''
                jsonFirmas = json.loads(request.POST['txtFirmas'])
                name_documento_a_firmar, extension_documento_a_firmar = os.path.splitext(documento_a_firmar.name)
                extension_certificado = os.path.splitext(certificado.name)[1][1:]
                bytes_certificado = certificado.read()
                if not jsonFirmas:
                    messages.error(request, "Error: Debe seleccionar ubicación de la firma")
                    return redirect(request.path)
                for membrete in jsonFirmas:
                    datau = JavaFirmaEc(
                        archivo_a_firmar=documento_a_firmar, archivo_certificado=bytes_certificado, extension_certificado=extension_certificado,
                        password_certificado=contrasenaCertificado,
                        page=int(membrete["numPage"]), reason=razon, lx=membrete["x"], ly=membrete["y"]
                    ).sign_and_get_content_bytes()
                    documento_a_firmar = io.BytesIO()
                    documento_a_firmar.write(datau)
                    documento_a_firmar.seek(0)
                nombrefile_ = remover_caracteres_tildes_unicode(quitar_caracteres(name_documento_a_firmar)).replace('-', '_').replace('.pdf', '')
                _name = generar_nombre(f'{request.user.username}', nombrefile_)
                response = HttpResponse(documento_a_firmar, content_type="application/pdf")
                response['Content-Disposition'] = f'attachment; filename="{nombrefile_}_firmado.pdf"'
                return response
            except Exception as ex:
                messages.error(request, f"{ex} - {sys.exc_info()[-1].tb_lineno}")
                return redirect(request.path)

        elif action == 'verificarfirmas':
            try:
                archivo = request.FILES['archivo_verificar']
                valido, msg, diccionario = verificarFirmasPDF(archivo)
                return JsonResponse({'result': True, 'context': diccionario})
            except Exception as ex:
                return JsonResponse({'result': False, "mensaje": 'Error: {}'.format(ex)}, safe=False)

        elif action == 'firmardocumentoold':
            try:
                pdf = request.FILES["pdf"]
                firma = request.FILES["firma"]
                passfirma = request.POST['palabraclave']
                txtFirmas = json.loads(request.POST['txtFirmas'])
                if not txtFirmas:
                    messages.error(request, "Error: Debe seleccionar ubicación de la firma")
                    return redirect(request.path)
                    # return JsonResponse({'result': True, "mensaje": "Error: Debe seleccionar ubicación de la firma"}, safe=False)
                generar_archivo_firmado = io.BytesIO()
                x = txtFirmas[-1]
                datau, datas = firmar(request, passfirma, firma, pdf, x["numPage"], x["x"], x["y"], x["width"], x["height"])
                if not datau:
                    messages.error(request, f"Error: {datas}")
                    return redirect(request.path)
                    # return JsonResponse({'result': True, "mensaje": datas}, safe=False)
                generar_archivo_firmado.write(datau)
                generar_archivo_firmado.write(datas)
                generar_archivo_firmado.seek(0)
                extension = pdf._name.split('.')
                tam = len(extension)
                exte = extension[tam - 1]
                nombrefile_ = remover_caracteres_tildes_unicode(quitar_caracteres(pdf._name)).replace('-', '_').replace('.pdf', '')
                _name = generar_nombre(f'{request.user.username}', nombrefile_)
                response = HttpResponse(generar_archivo_firmado, content_type="application/pdf")
                response['Content-Disposition'] = f'attachment; filename="{nombrefile_}_firmado.pdf"'
                # messages.success(request, f'Documento firmado con exito')
                return response
                # return JsonResponse({"result": False, "mensaje": "Guardado con exito", "response": response}, safe=False)
            except Exception as ex:
                messages.error(request, "Error: {}".format(ex))
                return redirect(request.path)
                # return JsonResponse({'result': True, "mensaje": "Error: {}".format(ex)}, safe=False)

        return JsonResponse({"result": "bad", "mensaje": u"Solicitud Incorrecta."})
    else:
        try:
            qr = qrImgFirma(request, persona_logeado, "png", paraMostrar=True)
            data["qrBase64"] = qr[0]

            if 'action' in request.GET:
                data['action'] = action = request.GET['action']

            data['title'] = f'Firmar documentos (Firma EC)'
            return render(request, 'administrativo/firmardocumentos/view.html', data)
        except Exception as ex:
            texto_notify = 'Error al acceder, {} error en la linea: {}'.format(str(ex), sys.exc_info()[-1].tb_lineno)
            print("FALLO : " + texto_notify)
