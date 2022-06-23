from django.db import models
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

from core.models import CreatedModel

from yatube.settings import MODEL_STR_METHOD_LENGHT

User = get_user_model()


class Group(CreatedModel):
    title = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название новой группы',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Слаг',
        help_text='Слаг для url',
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Описание новой группы',
    )

    def __str__(self):
        return self.title[:MODEL_STR_METHOD_LENGHT]

    def get_absolute_url(self):
        return reverse('posts:group_list', kwargs={'slug': self.slug})


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст нового поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:MODEL_STR_METHOD_LENGHT]

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'post_id': self.id})


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст комментария'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:MODEL_STR_METHOD_LENGHT]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        ordering = ['-user']
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_follower'
            )
        ]
