# -*- coding: utf-8 -*-

from django.http.response import Http404
from django.views.generic import TemplateView
from mptt_graph.models import GraphModel
from mptt_graph.utils import get_model_from_path
from django.contrib.auth.mixins import LoginRequiredMixin
from njangi.models import NjangiTree


class ModelListGraphsView(LoginRequiredMixin, TemplateView):
    template_name = 'mptt_graph/index.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise Http404
        return super(ModelListGraphsView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ModelListGraphsView, self).get_context_data(**kwargs)
        context['graphs'] = GraphModel.objects.all()
        return context


class ModelGraphView(LoginRequiredMixin, TemplateView):
    template_name = 'mptt_graph/tree.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_staff:
            raise Http404
        return super(ModelGraphView, self).dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ModelGraphView, self).get_context_data(**kwargs)
        model = get_model_from_path(self.kwargs['modpath'])
        root_node_pk = self.kwargs['pk']
        root_node = model.objects.get(pk=root_node_pk)
        nodes = root_node.get_descendants(include_self=True)
        context['nodes'] = nodes
        return context


class ModelGraphInlineView(ModelGraphView):
    template_name = 'mptt_graph/tree_inline.html'


class UserNetworkView(LoginRequiredMixin, TemplateView):
    template_name = 'mptt_graph/network_graph.html'

    def get_context_data(self, **kwargs):
        context = super(UserNetworkView, self).get_context_data(**kwargs)
        user_id = kwargs['user_id']
        request_user = self.request.user
        nodes = ""

        if int(user_id) and int(user_id) >= int(request_user.id):
            try:
                node = NjangiTree.objects.filter(user__id=user_id).get()
                nodes = node.get_descendants(include_self=True)
            except NjangiTree.DoesNotExist:
                nodes = ""
        context['nodes'] = nodes
        return context