# -*- coding: UTF-8 -*-
from _decimal import Decimal

from django import template

from CAM.settings import *
from administrativo.funciones import *
from administrativo.models import *
from datetime import datetime, timedelta, date

register = template.Library()

@register.simple_tag
def get_verbose_field_name(instance, field_name):
    return instance._meta.get_field(field_name).verbose_name.title()

@register.simple_tag
def ver_valor_dict(dicionario, llave):
    return dicionario[llave]

def callmethod(obj, methodname):
    method = getattr(obj, methodname)
    if "__callArg" in obj.__dict__:
        ret = method(*obj.__callArg)
        del obj.__callArg
        return ret
    return method()

@register.simple_tag
def setvar(value):
    return value

def args(obj, arg):
    if "__callArg" not in obj.__dict__:
        obj.__callArg = []
    obj.__callArg.append(arg)
    return obj


def suma(var, value=1):
    try:
        return var + value
    except Exception as ex:
        pass


def resta(var, value=1):
    return var - value

def restanumeros(var, value):
    return var - value

def multiplicanumeros(var, value):
    return Decimal(Decimal(var).quantize(Decimal('.01')) *  Decimal(value).quantize(Decimal('.01'))).quantize(Decimal('.01'))

def divide(value, arg):
    return int(value) / int(arg) if arg else 0


def porciento(value, arg):
    return round(value * 100 / float(arg), 2) if arg else 0


def calendarbox(var, dia):
    return var[dia]

def times(number):
    return range(number)

def substraer(value, rmostrar):
    return "%s" % value[:rmostrar]


def fechapermiso(fecha):
    if datetime.now().date() >= fecha:
        return True
    else:
        return False


def entrefechas(finicio,ffin):
    if datetime.now().date() >= finicio and datetime.now().date() <= ffin :
        return True
    else:
        return False


def datename(fecha):
    return u"%s de %s del %s" % (str(fecha.day).rjust(2, "0"), nombremes(fecha=fecha).capitalize(), fecha.year)


def encrypt(value):
    myencrip = ""
    if type(value) is int:
        value = str(value)
    i = 1
    for c in value.zfill(20):
        myencrip = myencrip + chr(int(44450/350) - ord(c) + int(i/int(9800/4900)))
        i = i + 1
    return myencrip

def is_int_or_char(value):
    try:
        if type(value) is int:
            return 1
        elif type(value) is str:
            return 2
        else:
            return 3
    except:
        return 3

def splitcadypre(string, sep):
    a= string.split(sep)
    b=int(a[0])
    return b

def splitcadyprestr(string, sep):
    a= string.split(sep)
    b=a[1]
    return b

def solo_caracteres(texto):
    acentos = [u'á', u'é', u'í', u'ó', u'ú', u'Á', u'É', u'Í', u'Ó', u'Ú', u'ñ', u'Ñ']
    alfabeto = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '.', '/', '#', ',', ' ']
    resultado = ''
    for letra in texto:
        if letra in alfabeto:
            resultado += letra
        elif letra in acentos:
            if letra == u'á':
                resultado += 'a'
            elif letra == u'é':
                resultado += 'e'
            elif letra == u'í':
                resultado += 'i'
            elif letra == u'ó':
                resultado += 'o'
            elif letra == u'ú':
                resultado += 'u'
            elif letra == u'Á':
                resultado += 'A'
            elif letra == u'É':
                resultado += 'E'
            elif letra == u'Í':
                resultado += 'I'
            elif letra == u'Ó':
                resultado += 'O'
            elif letra == u'Ú':
                resultado += 'U'
            elif letra == u'Ñ':
                resultado += 'N'
            elif letra == u'ñ':
                resultado += 'n'
        else:
            resultado += '?'
    return resultado


def ceros(numero, cantidad):
    return str(numero).zfill(cantidad)


def fechamayor(fecha1, fecha2):
    if fecha1.date() > fecha2:
        return True
    else:
        return False


def transformar_mes(n):
    arreglo = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return arreglo[n - 1] if n else "SIN MES"


def diaenletra(dia):
    arreglo = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']
    return arreglo[dia -1 ]


def sumar_pagineo(totalpagina, contador):
    suma = totalpagina + contador
    return suma
# AQUI TERMINA LAS FUNCIONES NO REUTILIZABLES :(

def rangonumeros(_min, args=None):
    _max, _step = None, None
    if args:
        if not isinstance(args, int):
            _max, _step = map(int, args.split(','))
        else:
            _max = args
    args = filter(None, (_min, _max+1, _step))
    return range(*args)

def splitcadena(string, sep):
    return string.split(sep)

def obtenernumerosdecadena(cadena):
    import re
    cadena = re.sub("\D", "", cadena)
    return cadena

def convertirentero(cadena):
    return int(cadena)

@register.simple_tag
def traducir_mes(value):
    return ' '.join(str(value).lower().replace('january', 'Ene') \
                    .replace('february', 'Feb') \
                    .replace('march', 'Mar') \
                    .replace('april', 'Abr') \
                    .replace('may', 'May') \
                    .replace('june', 'Jun') \
                    .replace('july', 'Jul') \
                    .replace('august', 'Ago') \
                    .replace('september', 'Sep') \
                    .replace('october', 'Oct') \
                    .replace('november', 'Nov') \
                    .replace('december', 'Dic').split(' ')[0:2])

@register.simple_tag
def traducir_mes_completo(value):
    return ' '.join(str(value).lower().replace('january', 'Enero') \
                    .replace('february', 'Febrero') \
                    .replace('march', 'Marzo') \
                    .replace('april', 'Abril') \
                    .replace('may', 'Mayo') \
                    .replace('june', 'Junio') \
                    .replace('july', 'Julio') \
                    .replace('august', 'Agosto') \
                    .replace('september', 'Septiembre') \
                    .replace('october', 'Octubre') \
                    .replace('november', 'Noviembre') \
                    .replace('december', 'Diciembre').split(' ')[0:2])


@register.simple_tag
def formatnamerubro(value):
    try:
        valor = str(value).lower().capitalize().replace('valor inscripcion', '').replace('valor matricula', '')
    except Exception as ex:
        valor = str(value).lower().capitalize()
    return valor



register.filter('diaenletra', diaenletra)
register.filter('ceros', ceros)
register.filter('fechamayor', fechamayor)
register.filter('times', times)
register.filter("call", callmethod)
register.filter("args", args)
register.filter("setvar", setvar)
register.filter("transformar_mes", transformar_mes)
register.filter("suma", suma)
register.filter("sumar_pagineo", sumar_pagineo)
register.filter("resta", resta)
register.filter("restanumeros", restanumeros)
register.filter("multiplicanumeros", multiplicanumeros)
register.filter("entrefechas", entrefechas)
register.filter("porciento", porciento)
register.filter("substraer", substraer)
register.filter("fechapermiso", fechapermiso)
register.filter("datename", datename)
register.filter("divide", divide)
register.filter("calendarbox", calendarbox)
register.filter("solo_caracteres", solo_caracteres)
register.filter("rangonumeros", rangonumeros)
register.filter("splitcadena", splitcadena)
register.filter("encrypt", encrypt)
register.filter("is_int_or_char", is_int_or_char)
register.filter("splitcadypre", splitcadypre)
register.filter("splitcadyprestr", splitcadyprestr)
register.filter("obtenernumerosdecadena", obtenernumerosdecadena)
register.filter("convertirentero", convertirentero)
