from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth import get_user_model
from .models import Chat
from .forms import MessageForm


# Create your views here.
@login_required
def chat_home(request):
    return render(request, "chat/chat_home.html", {})


@login_required
def chat_list(request):
    chats = Chat.objects.filter(Q(user1=request.user) | Q(user2=request.user)).order_by(
        "-created_at"
    )
    return render(
        request,
        "chat/chat_list.html",
        {
            "chats": chats,
        },
    )


@login_required
def chat_detail(request, chat_hash):
    chat = get_object_or_404(Chat, chat_hash=chat_hash)

    if request.user not in [chat.user1, chat.user2]:
        return HttpResponseForbidden("You do not have permission to view this chat.")

    other_user = chat.user2 if request.user == chat.user1 else chat.user1

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.recipient = other_user
            message.save()
            return redirect("chat_detail", chat_hash=chat.chat_hash)
    else:
        form = MessageForm()

    messages_list = chat.messages.order_by("send_time")
    return render(
        request,
        "chat/chat_ui.html",
        {
            "chat": chat,
            "messages": messages_list,
            "form": form,
            "other_user": other_user,
        },
    )


User = get_user_model()


@login_required
def select_chat_partner(request):
    users = User.objects.exclude(id=request.user.id)

    if request.method == "POST":
        partner_id = request.POST.get("partner_id")
        partner = get_object_or_404(User, id=partner_id)

        if request.user.id > partner.id:
            user1, user2 = partner, request.user
        else:
            user1, user2 = request.user, partner

        chat = Chat.objects.filter(user1=user1, user2=user2).first()
        if not chat:
            chat = Chat.objects.create(user1=user1, user2=user2)

        return redirect("chat_detail", chat_hash=chat.chat_hash)

    return render(request, "chat/select_chat_partner.html", {"users": users})


@login_required
def delete_chat(request, chat_hash):
    chat = get_object_or_404(Chat, chat_hash=chat_hash)
    if request.user not in [chat.user1, chat.user2]:
        return HttpResponseForbidden("You do not have permission to delete this chat.")

    other_user = chat.user2 if request.user == chat.user1 else chat.user1

    if request.method == "POST":
        chat.delete()
        return redirect("chat_list")
    return render(
        request, "chat/delete_chat.html", {"chat": chat, "other_user": other_user}
    )
