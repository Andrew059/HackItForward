from app.forms import ProfileUpdateForm, UserUpdateForm, SocialLinkFormSet, PasswordUpdateForm, OnboardingForm
from app.models import Challenge, Profile, Project, SocialLinkAttachement, Tag, User, UserFollowing, BookmarkChallenge, UpvoteChallenge, UpvoteComment, UpvoteProject

from django.core import files
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView, ContextMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormMixin, FormView, UpdateView

from django.http import JsonResponse
import requests
import tempfile


class AboutView(TemplateView):
    template_name = "about.html"


class IndexView(TemplateView):
    '''Default page. Allows site visitors to see challenges.'''
    template_name = "explore.html"

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("type") not in ["challenge", None]:
            return redirect("index")
        return super(IndexView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["tags"] = Tag.objects.all()

        if "type" not in self.request.GET or (
            "q" not in self.request.GET and "tag" not in self.request.GET
        ):
            context["challenges"] = Challenge.objects.all()
            return context

        queryset = Challenge.objects.all()

        context["selected_tags"] = Tag.objects.filter(
            name__in=self.request.GET.getlist("tag"))
        for tag in context["selected_tags"]:
            queryset = queryset.filter(tags__in=[tag])

        search = context["q"] = self.request.GET.get("q", "")
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search))

        context["challenges"] = queryset.distinct()
        return context


class GalleryView(TemplateView):
    '''Gallery view displays projects rather than challenges.'''
    template_name = "gallery.html"

    def dispatch(self, request, *args, **kwargs):
        if request.GET.get("type") not in ["project", None]:
            return redirect("index")
        return super(GalleryView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["tags"] = Tag.objects.all()

        if "type" not in self.request.GET or (
            "q" not in self.request.GET and "tag" not in self.request.GET
        ):
            context["projects"] = Project.objects.all()
            return context

        queryset = Project.objects.all()

        context["selected_tags"] = Tag.objects.filter(
            name__in=self.request.GET.getlist("tag"))
        for tag in context["selected_tags"]:
            queryset = queryset.filter(tags__in=[tag])

        search = context["q"] = self.request.GET.get("q", "")
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(description__icontains=search))

        context["projects"] = queryset.distinct()
        return context


class UserView(DetailView):
    template_name = "userprofile.html"
    model = Profile
    context_object_name = "user"

    def get_object(self):
        UserName = self.kwargs.get("username")
        if "username" in self.kwargs:
            return get_object_or_404(User, username=UserName)
        if self.request.user.is_authenticated:
            return self.request.user
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = (
            Project.objects.filter(
                Q(creators__in=[self.object.pk]) | Q(
                    contributors__in=[self.object.pk])
            )
            .distinct()
            .order_by("-created")
        )
        context["links"] = SocialLinkAttachement.objects.filter(
            object_id=self.object.pk,
            content_type=ContentType.objects.get_for_model(Profile),
        )
        context["following"] = self.get_object().following.all()
        context["followers"] = self.get_object().followers.all()
        context["is_following_user"] = UserFollowing.objects.filter(user_id=self.request.user.id, following_user_id=self.get_object().id).count() > 0
        return context


class GenericUserView(DetailView):
    model = Profile
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["projects"] = (
            Project.objects.filter(
                Q(creators__in=[self.object.pk]) | Q(
                    contributors__in=[self.object.pk])
            )
            .distinct()
            .order_by("-created")
        )
        context["links"] = SocialLinkAttachement.objects.filter(
            object_id=self.object.pk,
            content_type=ContentType.objects.get_for_model(Profile),
        )
        return context


class DashboardView(LoginRequiredMixin, GenericUserView):
    template_name = "dashboard.html"

    def get_object(self, queryset=None):
        return self.request.user.profile


class SocialLinkFormMixin(FormMixin):
    def get_class_name(self):
        return (
            self.model if self.model else self.object.__class__ if self.object else self.classname
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["has_social_links_form"] = True

        initial_data = {
            "object_id": 0 if not self.object else self.object.pk,
            "content_type": ContentType.objects.get_for_model(self.get_class_name()),
        }
        queryset = (
            SocialLinkAttachement.objects.none()
            if not self.object
            else SocialLinkAttachement.objects.filter(
                object_id=initial_data["object_id"],
                content_type=initial_data["content_type"],
            )
        )

        context["formset"] = (
            kwargs.pop("social_formset")
            if "social_formset" in kwargs
            else SocialLinkFormSet(
                prefix="social_links",
                queryset=queryset,
            )
        )

        SocialLinkFormSet.form.base_fields["content_type"].initial = initial_data["content_type"]
        SocialLinkFormSet.form.base_fields["object_id"].initial = initial_data["object_id"]

        return context

    def form_invalid(self, form, formset, **kwargs):
        return self.render_to_response(self.get_context_data(form=form, social_formset=formset))

    def form_valid(self, form):
        resp = super().form_valid(form)

        social_link_formset = SocialLinkFormSet(
            self.request.POST,
            prefix="social_links",
            form_kwargs={"obj": self.object},
        )

        if social_link_formset.is_valid():
            social_link_formset.save()
        else:
            return self.form_invalid(form, social_link_formset)
        return resp


class EditProfileView(LoginRequiredMixin, SocialLinkFormMixin, UpdateView):
    template_name = "edit_profile.html"
    form_class = ProfileUpdateForm
    success_url = reverse_lazy("profile")

    def get_object(self, queryset=None):
        return self.request.user.profile


class OnboardingView(LoginRequiredMixin, SocialLinkFormMixin, UpdateView):
    template_name = "onboarding.html"
    form_class = ProfileUpdateForm
    success_url = reverse_lazy("index")

    def get_object(self, queryset=None):
        return self.request.user.profile


class SettingsView(LoginRequiredMixin, UpdateView):
    template_name = "settings.html"
    form_class = UserUpdateForm
    success_url = reverse_lazy("profile")
    classname = User

    def get_object(self, queryset=None):
        return self.request.user


class PasswordChangeConfirmationView(TemplateView):
    template_name = "password_change_confirmation.html"


class PasswordResetConfirmationView(TemplateView):
    template_name = "password_reset_confirmation.html"


class RegisterView(FormView):
    template_name = "register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("edit_profile")

    def form_valid(self, form):
        form.save()
        login(self.request, form.instance,
              backend='django.contrib.auth.backends.ModelBackend')
        return super().form_valid(form)


class GenericFormMixin(LoginRequiredMixin, ContextMixin):
    template_name = "base_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["header"] = (
            "Edit %s" if self.object else "Create %s") % self.model.__name__
        context["submit"] = "Save" if self.object else "Create"
        return context


class InitiativeFormView(GenericFormMixin, SocialLinkFormMixin):
    pass


class ChallengeFormView(InitiativeFormView):
    model = Challenge
    fields = ["name", "image", "one_liner",
              "description", "creators", "start", "end", "tags"]

    def get_form_class(self, *args, **kwargs):
        form_class = super().get_form_class(*args, **kwargs)
        form_class.base_fields["start"].widget.attrs["placeholder"] = "YYYY-MM-DD HH:MM"
        form_class.base_fields["end"].widget.attrs["placeholder"] = "YYYY-MM-DD HH:MM"
        for field in form_class.base_fields:
            form_class.base_fields[field].widget.attrs['class'] = 'form-input-field'
        return form_class


class ChallengeCreateView(PermissionRequiredMixin, ChallengeFormView, CreateView):
    permission_required = "app.add_challenge"


class ChallengeUpdateView(ChallengeFormView, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().can_edit(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

# TO DELETE LATER
class InitiativeViewMixin(ContextMixin):
    classname = None
    initiative = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        self.initiative = self.classname.objects.get(pk=pk)

        context["initiative"] = self.initiative
        context["links"] = SocialLinkAttachement.objects.filter(
            object_id=pk, content_type=ContentType.objects.get_for_model(
                self.classname)
        )
        return context

class ChallengeView(TemplateView, ContextMixin):
    template_name = "challenge.html"
    classname = Challenge
    challenge = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs["pk"]
        self.challenge = self.classname.objects.get(pk=pk)
        context["challenge"] = self.challenge

        context["links"] = SocialLinkAttachement.objects.filter(
            object_id=pk, content_type=ContentType.objects.get_for_model(
                self.classname)
        )

        if self.challenge.start and self.challenge.end:
            context["time_labels"] = [
                {"label": "Start Time", "time": self.challenge.start},
                {"label": "End Time", "time": self.challenge.end},
            ]
        context["projects"] = Project.objects.filter(challenge=self.challenge)
        context["related_challenges"] = Challenge.objects.all()[:3]
        return context


class ProjectFormView(InitiativeFormView):
    model = Project
    fields = ["name", "image", "one_liner",
              "description", "creators", "contributors", "tags"]


class ProjectCreateView(ProjectFormView, CreateView):
    pass


class ProjectChallengeCreateView(ProjectCreateView):
    def dispatch(self, *args, **kwargs):
        self.challenge = get_object_or_404(Challenge, pk=kwargs["pk"])
        if not self.challenge.is_open():
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["header"] = "Create Project for '%s'" % self.challenge.name
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.challenge = self.challenge
        self.object.save()
        return super().form_valid(form)


class ProjectUpdateView(ProjectFormView, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().can_edit(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return "/challenge/" + str(self.get_object().challenge.pk) + "/#" + str(self.get_object().name)
        

# TO DELETE LATER
class ProjectView(InitiativeViewMixin, TemplateView):
    template_name = "project.html"
    classname = Project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["time_labels"] = [
            {"label": "Creation Time", "time": self.initiative.created}]
        return context


def get_challenges_ajax(request):
    if request.method == "POST":
        filter_id = request.POST['filter_id']
        try:
            final_list = []
            challenges = []
            if (filter_id == 'default'):
                challenges = list(Challenge.objects.all())
            elif (filter_id == 'most_submissions'):
                challenges = sorted(
                    Challenge.objects.all(), key=lambda t: t.submission_count, reverse=True)
            else:
                challenges = list(Challenge.objects.filter(tags=filter_id))
            for c in challenges:
                challenge = {
                    'id': c.id,
                    'name': c.name,
                    'image_url': 'false',
                    'first_creator': c.creators.first().username,
                    'first_creator_profile': c.creators.first().image.url,
                    'submission_count': c.submission_count,
                }
                if c.image:
                    challenge['image_url'] = c.image.url
                final_list.append(challenge)
        except Exception:
            data['error_message'] = 'error'
            return JsonResponse(data)
        return JsonResponse(final_list, safe=False)


def add_comment(request):
    if request.method == "POST":
        comment = request.POST['comment']
        profile = request.user.profile
        pk = request.POST["challenge_pk"]
        challenge = Challenge.objects.get(pk=pk)
        challenge.comments.create(text=comment, profile=profile)
    
    return JsonResponse("Success", safe=False)


def follow_user(request, pk):
    following_user_id = pk
    data = {}
    try:
        following_user = User.objects.get(id=following_user_id)
        current_user = request.user
        if not current_user.following.all().filter(following_user_id=following_user.id):
            UserFollowing.objects.create(user_id=current_user, following_user_id=following_user)
            data['success_message'] = 'successful'
        else:
            data['error_message'] = 'already followed'
    except Exception:
        data['error_message'] = 'error'
        return redirect('index')
    return redirect('user', following_user.username)

def unfollow_user(request, pk):
    following_user_id = pk
    data = {}
    try:
        following_user = User.objects.get(id=following_user_id)
        current_user = request.user
        if current_user.following.all().filter(following_user_id=following_user.id):
            UserFollowing.objects.filter(user_id=current_user.id, following_user_id=following_user.id).delete()
            data['success_message'] = 'successful'
        else:
            data['error_message'] = following_user.id
    except Exception:
        data['error_message'] = 'error'
        return redirect('index')
    return redirect('user', following_user.username)


def addUnsplashPicture(request):
    if request.method == "POST":
        url = request.POST["url"]
        url += ".jpg"
        response = requests.get(url, stream=True)
        # Get the filename from the url, used for saving later
        file_name = url.split('/')[-1]
        
        # Create a temporary file
        lf = tempfile.NamedTemporaryFile()

        # Read the streamed image in sections
        for block in response.iter_content(1024 * 8):
            
            # If no more file then stop
            if not block:
                break

            # Write image block to temporary file
            lf.write(block)

        request.user.profile.image.save(file_name, files.File(lf))

    return JsonResponse("Success", safe=False)

def upvote(request, obj_type, pk, challenge_id=null, project_id=null):
    obj = ""
    if obj_type == "challenge":
        obj = Challenge.objects.get(pk=pk)
    elif obj_type == "project":
        obj = Project.objects.get(pk=pk)
    elif obj_type == "comment":
        obj = comment.objects.get(pk=pk)
    user = request.user
    try:
        voted = ""
        if obj_type == "challenge":
            voted = UpvoteChallenge.objects.get(challenge=obj, user=user)
        elif obj_type == "project":
            voted = UpvoteProject.objects.get(project=obj, user=user)
        elif obj_type == "comment":
            voted = UpvoteComment.objects.get(comment=obj, user=user)
        voted.delete()
        obj.upvote -= 1
    except:
        objVote = ""
        if obj_type == "challenge":
            objVote = UpvoteChallenge()
        elif obj_type == "project":
            objVote = UpvoteProject()
        elif obj_type == "comment":
            objVote = UpvoteComment()
        objVote = UpvoteChallenge()
        objVote.obj = obj
        objVote.user = user
        objVote.save()
        obj.upvote += 1
        obj.save()
    if obj_type == "challenge":
        return redirect("challenge", obj.id)
    elif obj_type == "project":
        return redirect("project", obj.id)
    elif obj_type == "comment":
        if challenge_id:
            return redirect("challenge", obj.id)
        elif project_id:
            return redirect("project", obj.id)

def add_bookmark(request):
    #Inspired from https://evileg.com/en/post/244/
    if request.method == "POST":
        user = request.user
        pk = request.POST["challenge_pk"]
        bookmark, created = BookmarkChallenge.get_or_create(user=user, obj_id=pk)
        # If no new bookmark has been created, then the request is to delete the bookmark
        if not created:
            bookmark.delete()
