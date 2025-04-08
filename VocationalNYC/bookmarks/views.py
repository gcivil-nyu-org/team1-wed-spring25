from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.contrib import messages
from django.db import IntegrityError, transaction
from .models import BookmarkList, Bookmark, Course


class BookmarkListView(LoginRequiredMixin, generic.ListView):
    model = BookmarkList
    template_name = "bookmarks/bookmark_list.html"
    context_object_name = "lists"
    ordering = ["list_id"]
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_queryset(self):
        return BookmarkList.objects.filter(user=self.request.user)


class BookmarkListDetailView(LoginRequiredMixin, generic.DetailView):
    """
    Displays the details of the specified bookmark list and all the courses belong to the list.
    """

    model = BookmarkList
    template_name = "bookmarks/bookmark_list_detail.html"
    context_object_name = "bookmark_list"
    pk_url_kwarg = "list_id"

    def get_queryset(self):
        return BookmarkList.objects.filter(user=self.request.user)


@login_required
def add_bookmark(request, course_id):
    """
    Add bookmark to a Bookmark List
    """
    course = get_object_or_404(Course, course_id=course_id)
    bookmark_lists = BookmarkList.objects.filter(user=request.user)
    default_bookmark_list = bookmark_lists.filter(name__iexact="default").first()

    if request.method == "POST":
        selected_list_id = request.POST.get("bookmark_list")
        selected_list = get_object_or_404(
            BookmarkList, list_id=selected_list_id, user=request.user
        )
        try:
            with transaction.atomic():
                Bookmark.objects.create(
                    bookmark_list=selected_list,
                    course=course,
                    time=timezone.now().date(),
                )
            return redirect("course_list")
        except IntegrityError:
            messages.error(request, "This course is already in the bookmark list.")

    # GET request, show the bookmark list
    context = {
        "course": course,
        "bookmark_lists": bookmark_lists,
        "default_bookmark_list": default_bookmark_list,
    }
    return render(request, "bookmarks/add_bookmark.html", context)


@login_required
def delete_bookmark(request, list_id, bookmark_id):
    bookmark = get_object_or_404(
        Bookmark,
        id=bookmark_id,
        bookmark_list__list_id=list_id,
        bookmark_list__user=request.user,
    )
    if request.method == "POST":
        bookmark.delete()
        return redirect("bookmark_list_detail", list_id=list_id)

    # 🧹 no more confirmation page — just redirect back
    return redirect("bookmark_list_detail", list_id=list_id)


@login_required
def create_bookmark_list(request):
    """
    Create new Bookmark List
    """
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            try:
                with transaction.atomic():
                    BookmarkList.objects.create(user=request.user, name=name)
                messages.success(request, "Bookmark list created successfully.")
                return redirect("bookmark_list")
            except IntegrityError:
                messages.error(
                    request, "A bookmark list with the same name already exists."
                )
        else:
            messages.error(request, "Please enter a name for the list.")
    lists = BookmarkList.objects.filter(user=request.user)
    return render(request, "bookmarks/bookmark_list.html", {"lists": lists})


@login_required
def delete_bookmark_list(request, list_id):
    bookmark_list = get_object_or_404(BookmarkList, list_id=list_id, user=request.user)

    if bookmark_list.name.lower() == "default":
        messages.error(request, "Default bookmark list cannot be deleted.")
        return redirect("bookmark_list")

    if request.method == "POST":
        bookmark_list.delete()
        messages.success(request, "Bookmark list deleted successfully.")

    return redirect("bookmark_list")  # ← remove render() and always redirect
