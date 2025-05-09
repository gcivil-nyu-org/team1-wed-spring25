from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_home, name="chat_home"),
    path("list/", views.chat_list, name="chat_list"),
    path("select/", views.select_chat_partner, name="select_chat_partner"),
    path("<str:chat_hash>/", views.chat_detail, name="chat_detail"),
    path("delete_chat/<str:chat_hash>/", views.delete_chat, name="delete_chat"),
    path(
        "delete_message/<int:message_id>/", views.delete_message, name="delete_message"
    ),
]
