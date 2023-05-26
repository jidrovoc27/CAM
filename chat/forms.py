from socket import fromshare
from django import forms
from django.forms import ModelForm
from chat.models import ChatMessage


class ChatMessageForm(ModelForm):
    body = forms.CharField(widget=forms.Textarea(attrs={"class":"forms", "rows":3, "colspan": 2, "style": "height:40%;margin-top:15px" , "placeholder": "Escribe un mensaje"}))
    class Meta:
        model = ChatMessage
        fields = ["body",]