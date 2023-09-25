from blog.models import Comment, Post
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect


class CommentDispatchMixin:

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Comment, pk=kwargs['comment_pk'])
        if instance.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PostDispatchMixin:
    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Post,
            pk=kwargs['post_pk'])
        if instance.author != request.user:
            return redirect('blog:post_detail', self.kwargs['post_pk'])
        return super().dispatch(request, *args, **kwargs)
