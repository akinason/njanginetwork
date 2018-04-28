from django.db.models import F
from django.shortcuts import reverse, render, redirect
from django.views import generic

from blog.models import Post, MainCategory, Category


class BlogIndexView(generic.TemplateView):
    template_name = 'blog/index.html'

    # def get_context_data(self, **kwargs):
    #     context = super(BlogIndexView, self).get_context_data(**kwargs)
    #     context['post_list'] = Post.objects.filter(
    #         is_published=True, category__is_published=True
    #     ).order_by(
    #         '-created_on'
    #     )
    #     context['category_list'] = MainCategory.objects.filter(
    #         is_published=True
    #     ).order_by(
    #         'name'
    #     )
    #     return context
    def get(self, request, *args, **kwargs):
        return redirect('blog:post_list', 0, permanent=True)


class CategoryList(generic.TemplateView):
    template_name = 'blog/category_list.html'

    def get_context_data(self, **kwargs):
        context = super(CategoryList, self).get_context_data(**kwargs)
        main_category_id = kwargs.get('pk', "")
        if main_category_id:
            context['category_list'] = Category.objects.filter(is_published=True, main_category__id=main_category_id)
            try:
                context['main_category'] = MainCategory.objects.get(pk=main_category_id)
            except MainCategory.DoesNotExist:
                context['main_category'] = ""
        else:
            context['category_list'] = ""
        return context


class PostListView(generic.ListView):
    paginate_by = 10
    template_name = 'post/post_list.html'
    context_object_name = 'post_list'
    model = Post
    pk = None

    def get_queryset(self):
        """
        :return: The list of post ordered in descending order of date created, which has been published and whose
                 category and main category have been published.
        """

        if 'pk' in self.kwargs:
            self.pk = self.kwargs['pk']
        if int(self.pk) > 0:
            queryset = super(PostListView, self).get_queryset()
            return queryset.objects.filter(
              category__id=self.pk, is_published=True,  category__is_published=True,
            ).order_by(
                '-created_on'
            )
        elif int(self.pk) == 0:
            return self.model.objects.filter(is_published=True, category__is_published=True).order_by('-created_on')
        return self.model.objects.filter(is_published=True, category__is_published=True).order_by('-created_on')


class PostDetailView(generic.DetailView):
    template_name = 'blog/post_detail.html'
    model = Post
    context_object_name = 'post'

    def get_object(self, queryset=None):
        obj = super(PostDetailView, self).get_object(queryset=queryset)
        obj.view_count += F(1)
        return obj
