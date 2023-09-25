from blog.models import Category, Comment, Post
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone as tz
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .mixins import CommentDispatchMixin, PostDispatchMixin

User = get_user_model()


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        self.post_object = get_object_or_404(Post, pk=kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_object
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_pk': self.post_object.pk}
        )


class IndexListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = 10

    def get_queryset(self):
        return self.model.published_posts().select_related(
            'author'
        ).annotate(
            comment_count=Count('comment')
        ).order_by('-pub_date', 'category', 'title')


class CommentUpdateView(LoginRequiredMixin, CommentDispatchMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={
                'post_pk': self.kwargs.get('post_pk')
            }
        )


class CommentDeleteView(LoginRequiredMixin, CommentDispatchMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_pk'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={
                'post_pk': self.kwargs.get('post_pk')
            }
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_pk'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Post,
            pk=kwargs['post_pk'])
        if not instance.is_published or instance.pub_date > tz.now():
            if instance.author != request.user:
                raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comment.select_related('author')
        )
        return context


class PostUpdateView(LoginRequiredMixin, PostDispatchMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_pk'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={
                'post_pk': self.kwargs.get('post_pk')
            }
        )


class PostDeleteView(LoginRequiredMixin, PostDispatchMixin, DeleteView):
    model = Post
    fields = '__all__'
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_pk'

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.request.user})


class CategoryPosts(ListView):
    model = Post
    template_name = "blog/category.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        if not category_slug:
            return Post.objects.none()
        category = get_object_or_404(Category, slug=category_slug)
        return Post.objects.filter(
            is_published=True,
            pub_date__lt=tz.now(),
            category=category).annotate(
                comment_count=Count('comment')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['category'] = get_object_or_404(
                Category,
                slug=category_slug,
                is_published=True
            )
        return context


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        data = get_object_or_404(User, username=username)
        return data

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            author=self.get_object()
        )
        if self.request.user.id != self.get_object().id:
            queryset = queryset.filter(
                is_published=True, pub_date__lt=tz.now(),
            )
        return queryset.order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comment')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_object()
        if context['profile']:
            return context
        return Http404


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:index')
