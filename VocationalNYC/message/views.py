from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from .models import Chat, Message, MessageVisibility
from users.models import Provider
from .forms import MessageForm

timezone.activate(settings.TIME_ZONE)


@login_required
def chat_home(request):
    user = request.user
    from django.db.models import OuterRef, Subquery, DateTimeField, TextField

    visible_messages = Message.objects.filter(
        chat=OuterRef("pk"), visibilities__user=user, visibilities__is_visible=True
    ).order_by("-send_time")

    chats = (
        Chat.objects.filter(Q(user1=user) | Q(user2=user))
        .annotate(
            last_time=Subquery(
                visible_messages.values("send_time")[:1], output_field=DateTimeField()
            ),
            last_message=Subquery(
                visible_messages.values("content")[:1], output_field=TextField()
            ),
        )
        .order_by("-last_time", "-id")
    )

    def get_display_name(u):
        if u.role == "training_provider":
            try:
                return u.provider_profile.name
            except Provider.DoesNotExist:
                return u.username
        else:
            return u.username

    def get_student_full_name(u):
        if u.role == "career_changer":
            # If the user is a student or any other role, return their full name
            return u.get_full_name()

    for c in chats:
        other = c.user2 if c.user1 == user else c.user1
        c.display_name = get_display_name(other)
        c.student_full_name = get_student_full_name(other)

    context = {"chats": chats, "welcome_message": True}

    return render(request, "chat/chat_ui.html", context)


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
    # Get the current user's chats and annotate with the last message time
    user = request.user
    from django.db.models import OuterRef, Subquery, DateTimeField, TextField

    visible_messages = Message.objects.filter(
        chat=OuterRef("pk"), visibilities__user=user, visibilities__is_visible=True
    ).order_by("-send_time")

    chats = (
        Chat.objects.filter(Q(user1=user) | Q(user2=user))
        .annotate(
            last_time=Subquery(
                visible_messages.values("send_time")[:1], output_field=DateTimeField()
            ),
            last_message=Subquery(
                visible_messages.values("content")[:1], output_field=TextField()
            ),
        )
        .order_by("-last_time", "-id")
    )

    # If the URL contains a chat_hash, filter the chats to find the current chat
    current_chat = get_object_or_404(Chat, chat_hash=chat_hash)

    # If the chat_hash doesn't match the user, return a forbidden response
    if user not in [current_chat.user1, current_chat.user2]:
        return HttpResponseForbidden("You do not have permission to view this chat.")

    def get_display_name(u):
        if u.role == "training_provider":
            try:
                # If the user is a provider, return business name
                return u.provider_profile.name
            except Provider.DoesNotExist:
                # Fallback to username if provider profile doesn't exist
                return u.username
        else:
            # If the user is a student or any other role, return their username
            return u.username

    def get_student_full_name(u):
        if u.role == "career_changer":
            # If the user is a student or any other role, return their full name
            return u.get_full_name()

    for c in chats:
        other = c.user2 if c.user1 == user else c.user1
        c.display_name = get_display_name(other)
        c.student_full_name = get_student_full_name(other)

    other_user = (
        current_chat.user2 if user == current_chat.user1 else current_chat.user1
    )
    current_chat.display_name = get_display_name(other_user)

    current_chat.student_full_name = get_student_full_name(other_user)

    # send message
    if request.method == "POST":
        form = MessageForm(request.POST)
        # set the chat, sender, and recipient and check if the form is valid
        # form.instance.chat = current_chat
        # form.instance.sender = user
        # form.instance.recipient = other_user
        # if form.is_valid():
        #     msg = form.save(commit=False)
        #     msg.save()
        #     return redirect("chat_detail", chat_hash=current_chat.chat_hash)
        if form.is_valid():
            create_message_with_visibility(
                current_chat, user, other_user, form.cleaned_data["content"]
            )
            return redirect("chat_detail", chat_hash=current_chat.chat_hash)
    else:
        form = MessageForm()

    # messages = current_chat.messages.order_by("send_time")
    messages = get_visible_messages(current_chat, user)
    for message in messages:
        message.local_send_time = timezone.localtime(message.send_time)

    # render
    context = {
        "chats": chats,
        "current_chat": current_chat,
        "messages": messages,
        "form": form,
        "other_user": other_user,
    }
    return render(request, "chat/chat_ui.html", context)


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


def create_message_with_visibility(chat, sender, recipient, content):
    message = Message.objects.create(
        chat=chat,
        sender=sender,
        recipient=recipient,
        content=content,
        send_time=timezone.now(),
    )

    MessageVisibility.objects.create(user=sender, message=message, is_visible=True)
    MessageVisibility.objects.create(user=recipient, message=message, is_visible=True)

    return message


def get_visible_messages(chat, user):
    return Message.objects.filter(
        chat=chat, visibilities__user=user, visibilities__is_visible=True
    ).order_by("send_time")


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    chat = message.chat

    # Check if the user is part of the chat
    if request.user not in [chat.user1, chat.user2]:
        return HttpResponseForbidden(
            "You do not have permission to access this message."
        )

    if request.method == "POST":
        # Update the visibility of the message for the user
        MessageVisibility.objects.update_or_create(
            user=request.user, message=message, defaults={"is_visible": False}
        )

    return redirect("chat_detail", chat_hash=chat.chat_hash)


@login_required
def delete_chat(request, chat_hash):
    chat = get_object_or_404(Chat, chat_hash=chat_hash)

    if request.user not in [chat.user1, chat.user2]:
        return HttpResponseForbidden("You do not have permission to clear this chat.")

    if request.method == "POST":
        messages = Message.objects.filter(chat=chat)

        for message in messages:
            MessageVisibility.objects.update_or_create(
                user=request.user, message=message, defaults={"is_visible": False}
            )

    return redirect("chat_detail", chat_hash=chat.chat_hash)
