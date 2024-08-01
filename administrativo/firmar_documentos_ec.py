import json
import os
import subprocess
from datetime import datetime
from django.db import models
from administrativo.funciones import customgetattr

import CAM.settings
from CAM.settings import BASE_DIR, MEDIA_ROOT


class JavaFirmaEc:
    def __init__(self, archivo_a_firmar, archivo_certificado, extension_certificado, password_certificado: str, page="1", reason="", type_file="pdf",
                    lx="10", ly="100", type_sign="QR"):
        self.archivo_a_firmar = archivo_a_firmar
        self.archivo_certificado = archivo_certificado
        self.password_certificado = password_certificado
        self.extension_certificado = extension_certificado
        self.page = str(int(page) + 1)
        self.reason = reason
        self.type_file = type_file
        self.lx = str(int(lx))
        self.ly = str(int(ly))
        self.type_sign = type_sign
        self.jar_file = os.path.join(BASE_DIR, "FIRMA_EC.jar")
        self.java_path = f"{hasattr(CAM.settings, 'JAVA_V20') and customgetattr(CAM.settings, 'JAVA_V20') or ''}java"
        self.datos_del_certificado = self.__obtener_datos_del_certificado()

    def __generar_nombre_archivo_temporal(self):
        return datetime.now().strftime("%Y%m%d%H%M%S%f")

    def __crear_archivo_temporal(self, bytes_to_write: bytes, extension: str):
        directorio = os.path.join(MEDIA_ROOT, 'archivos_temporales')
        not os.path.exists(directorio) and os.mkdir(directorio)
        path_archivo_temporal = os.path.join(directorio, f"{self.__generar_nombre_archivo_temporal()}.{extension}")
        while os.path.exists(path_archivo_temporal):
            path_archivo_temporal = os.path.join(directorio, self.__generar_nombre_archivo_temporal())
        io_archivo_temporal = open(path_archivo_temporal, "wb")
        io_archivo_temporal.write(bytes_to_write)
        io_archivo_temporal.close()
        return path_archivo_temporal

    def guardar_archivo_a_firmar_en_el_disco_and_get_path(self) -> str:
        bytes_archivo = self.archivo_a_firmar.read() if type(self.archivo_a_firmar).__name__.lower() != "bytes" else self.archivo_a_firmar
        return self.__crear_archivo_temporal(bytes_archivo, self.type_file.lower())

    def guardar_archivo_certificado_en_el_disco_and_get_path(self) -> str:
        bytes_archivo = self.archivo_certificado.read() if type(self.archivo_certificado).__name__.lower() != "bytes" else self.archivo_certificado
        return self.__crear_archivo_temporal(bytes_archivo, self.extension_certificado)

    def __validar_certificado(self):
        return self.datos_del_certificado["certificadoDigitalValido"]

    def __obtener_datos_del_certificado(self):
        datos_del_certificado = {}
        path_certificate = self.guardar_archivo_certificado_en_el_disco_and_get_path()
        try:
            jar_file = self.jar_file
            java_path = self.java_path
            completed_process = subprocess.run(
                [
                    java_path, "-jar", jar_file, "-path_certificate", path_certificate,
                    "-password_certificate", self.password_certificado, "-type_file", "validar_certificado"
                ], timeout=10000, text=True,
                capture_output=True
            )
            datos_del_certificado = json.loads(completed_process.stdout)
        except Exception as ex:
            raise ValueError(f"{ex}")
        finally:
            os.remove(path_certificate)
        return datos_del_certificado

    def sign_and_get_content_bytes(self):
        certificado_es_valido = self.__validar_certificado()

        if not certificado_es_valido:
            raise ValueError("Certificado no es válido")

        path_file_to_sign = self.guardar_archivo_a_firmar_en_el_disco_and_get_path()
        path_certificate = self.guardar_archivo_certificado_en_el_disco_and_get_path()
        path_signed_file = ""

        try:
            jar_file = self.jar_file
            java_path = self.java_path
            completed_process = subprocess.run(
                [
                    java_path, "-jar", jar_file, "-path_file", path_file_to_sign, "-path_certificate", path_certificate,
                    "-password_certificate", self.password_certificado, "-page", self.page, "-type_file",
                    self.type_file, "-lx", self.lx, "-ly", self.ly, "-type_sign", self.type_sign
                ] + (["-reason",
                    self.reason] if self.reason else []), timeout=10000, text=True,
                capture_output=True
            )
            data = json.loads(completed_process.stdout)
            path_signed_file = data["path_signed_file"]
            archivo_firmado = open(path_signed_file, "rb").read()
            return archivo_firmado
        except Exception as ex:
            raise ValueError(f"{ex}")
        finally:
            os.remove(path_file_to_sign)
            os.remove(path_certificate)
            path_signed_file and os.remove(path_signed_file)