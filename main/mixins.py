from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.urls import reverse

from main.utils import add_promoter_id_to_session, add_sponsor_id_to_session


class ContributionRequiredMixin(LoginRequiredMixin):
    """
    Verify that the current user has done the first contribution.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_contributed:
            return HttpResponseRedirect(reverse('njangi:signup_contribution_required'))
        return super().dispatch(request, *args, **kwargs)


class AdminPermissionRequiredMixin(LoginRequiredMixin):
    """
    Verify that the current user is an admin.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseRedirect(reverse('njangi:dashboard'))
        return super().dispatch(request, *args, **kwargs)


class AddReferralIDsToSession:
    """
    Adds the promoter_id and sponsor_id to session if they exist on the url.
    """
    def dispatch(self, request, *args, **kwargs):
        add_sponsor_id_to_session(request)
        add_promoter_id_to_session(request)
        return super().dispatch(request, *args, **kwargs)