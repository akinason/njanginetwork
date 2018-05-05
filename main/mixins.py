from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.urls import reverse


class ContributionRequiredMixin(LoginRequiredMixin):
    """
    Verify that the current user has done the first contribution.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_contributed:
            return HttpResponseRedirect(reverse('njangi:signup_contribution_required'))
        return super().dispatch(request, *args, **kwargs)