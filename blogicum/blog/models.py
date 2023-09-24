from django.contrib.auth import get_user_model
from django.db import models as mdl
from django.urls import reverse
from django.utils import timezone as dt


User = get_user_model()


class BaseModel(mdl.Model):
    is_published = mdl.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.')
    created_at = mdl.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class Comment(mdl.Model):
    text = mdl.TextField('Текст')
    post = mdl.ForeignKey(
        'Post',
        on_delete=mdl.CASCADE,
        related_name='comment',
    )
    author = mdl.ForeignKey(User, on_delete=mdl.CASCADE)
    created_at = mdl.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at',)


class Category(BaseModel):
    title = mdl.CharField('Заголовок', max_length=256)
    description = mdl.TextField('Описание')
    slug = mdl.SlugField(
        'Идентификатор',
        unique=True,
        help_text=('Идентификатор страницы для URL; '
                   'разрешены символы латиницы, цифры, '
                   'дефис и подчёркивание.'))

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'


class Location(BaseModel):
    name = mdl.CharField('Название места', max_length=256)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(BaseModel):
    title = mdl.CharField('Заголовок', max_length=256)
    text = mdl.TextField('Текст')
    pub_date = mdl.DateTimeField(
        'Дата и время публикации',
        help_text=('Если установить дату и время в будущем — '
                   'можно делать отложенные публикации.'))
    author = mdl.ForeignKey(
        User,
        on_delete=mdl.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts'
    )
    image = mdl.ImageField('Фото', upload_to='media', blank=True)
    location = mdl.ForeignKey(
        Location,
        on_delete=mdl.SET_NULL,
        blank=True,
        null=True,
        verbose_name='Местоположение',
        related_name='posts'
    )
    category = mdl.ForeignKey(
        Category,
        on_delete=mdl.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='posts'
    )

    @classmethod
    def published_posts(cls):
        return cls.objects.filter(pub_date__lte=dt.now(),
                                  is_published=True,
                                  category__is_published=True,)

    def get_absolute_url(self):
        return reverse('blog:post_detail', {'username': self.author})

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date', 'category', 'title')
