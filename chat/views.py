# from cgi import print_arguments
from django.shortcuts import render, redirect
from .models import ChatMessage, Profile, Friend
from .forms import ChatMessageForm
from django.http import JsonResponse
import json
import datetime
from datetime import datetime
from django.forms import model_to_dict

# Create your views here.
def index(request):
    user = request.user.profile
    friends = user.friends.all()
    context = {"user": user, "friends": friends}
    return render(request, "chat/index.html", context)


def detail(request,pk):
    friend = Friend.objects.get(profile_id=pk)
    user = request.user.profile
    profile = Profile.objects.get(id=friend.profile.id)
    chats = ChatMessage.objects.all()
    rec_chats = ChatMessage.objects.filter(msg_sender=profile, msg_receiver=user, seen=False)
    rec_chats.update(seen=True)
    form = ChatMessageForm()
    if request.method == "POST":
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat_message = form.save(commit=False)
            chat_message.msg_sender = user
            chat_message.msg_receiver = profile
            chat_message.save()
            return redirect("detail", pk=friend.profile.id)
    context = {"friend": friend, "form": form, "user":user,
               "profile":profile, "chats": chats, "num": rec_chats.count()}
    return render(request, "chat/detail.html", context)

def sentMessages(request, pk):
    try:
        info = {}
        user = request.user.profile
        usuario_envia = Friend.objects.filter(profile_id=user.id)
        if usuario_envia:
            usuario_envia = usuario_envia.first()
        else:
            usuario_envia = Friend(profile_id=user.id)
            usuario_envia.save(request)
        friend = Friend.objects.get(profile_id=pk)
        profile = Profile.objects.get(id=friend.profile.id)
        existe = Profile.objects.filter(user=profile.user, friends__id=usuario_envia.id).exists()
        relacion_creada = False
        if not existe:
            usuario_recibe = Profile.objects.filter(user=profile.user)
            if usuario_recibe:
                usuario_recibe = usuario_recibe.first()
                usuario_recibe.friends.add(usuario_envia)
                relacion_creada = True
        data = json.loads(request.body)
        new_chat = data["msg"]
        new_chat_message = ChatMessage.objects.create(body=new_chat, msg_sender=user, msg_receiver=profile, seen=False, fecha_creacion=datetime.now() )
        print(new_chat)
        info['new_chat_message'] = new_chat_message.body
        info['fecha_envio'] = str(new_chat_message.fecha_creacion.date()) + " " + str(new_chat_message.fecha_creacion.hour) + ":" + str(new_chat_message.fecha_creacion.minute)
        info['relacion_creada'] = relacion_creada
        return JsonResponse(info, safe=False)
    except Exception as ex:
        pass

def receivedMessages(request, pk):
    try:
        user = request.user.profile
        friend = Friend.objects.get(profile_id=pk)
        profile = Profile.objects.get(id=friend.profile.id)
        arr = []
        chats = ChatMessage.objects.filter(msg_sender=profile, msg_receiver=user, seen=False)
        for chat in chats:
            fecha = str(chat.fecha_creacion.date()) + " " + str(chat.fecha_creacion.hour) + ":" + str(chat.fecha_creacion.minute)
            arr.append(chat.body)
            arr.append(fecha)
        chats.update(seen=True)
        return JsonResponse(arr, safe=False)
    except Exception as ex:
        pass


def chatNotification(request):
    user = request.user.profile
    friends = user.friends.all()
    mensajes = ChatMessage.objects.filter(msg_receiver_id=user).order_by('msg_sender_id').distinct('msg_sender_id').values_list('msg_sender_id')
    amigos = Friend.objects.filter(id__in=mensajes)
    listado = amigos.values_list('id', flat=True)
    existe = Profile.objects.filter(id=user.id, friend__id__in=listado)
    if not existe:
        usuario_recibe = Profile.objects.filter(id=user.id)
        if usuario_recibe:
            usuario_recibe = usuario_recibe.first()
            for amigo in amigos:
                existe = Profile.objects.filter(id=user.id, friend__id=amigo.id)
                if not existe:
                    usuario_recibe.friends.add(amigo)
            relacion_creada = True
    arr = []
    for friend in friends:
        chats = ChatMessage.objects.filter(msg_sender__id=friend.profile.id, msg_receiver=user, seen=False)
        arr.append(chats.count())
    return JsonResponse(arr, safe=False)