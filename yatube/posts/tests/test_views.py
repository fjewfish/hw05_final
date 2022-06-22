import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Follow, User
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'test-username'
        cls.group_slug = 'test-slug'
        cls.another_username = 'another-username'
        cls.another_group_slug = 'another-slug'
        cls.posts_num_test_user = settings.POSTS_PER_PAGE + 3
        cls.posts_quantity = cls.posts_num_test_user + 1
        cls.index_url = reverse('posts:index')
        cls.post_create_url = reverse('posts:post_create')
        cls.follow_index = reverse('posts:follow_index')
        cls.group_list_url = reverse(
            'posts:group_list', kwargs={'slug': cls.group_slug}
        )
        cls.profile_url = reverse(
            'posts:profile', kwargs={'username': cls.username}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        )
        cls.post_edit_url = reverse(
            'posts:edit', kwargs={'post_id': '1'}
        )
        cls.another_group_list_url = reverse(
            'posts:group_list', kwargs={'slug': cls.another_group_slug}
        )
        cls.another_profile_url = reverse(
            'posts:profile', kwargs={'username': cls.another_username}
        )
        cls.user = User.objects.create_user(username=cls.username)
        cls.another_user = User.objects.create_user(
            username=cls.another_username)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.group_slug,
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост 1',
            image=uploaded,
        )
        cls.posts_list = Post.objects.bulk_create(
            [
                Post(author=cls.user,
                     group=cls.group,
                     text=f'Тестовый пост {post_num}')
                for post_num in range(2, cls.posts_num_test_user + 1)
            ]
        )
        cls.another_group = Group.objects.create(
            title='Другая группа',
            slug=cls.another_group_slug,
            description='Другое описание',
        )
        cls.another_post = Post.objects.create(
            author=cls.another_user,
            group=cls.another_group,
            text='Другой пост',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)
        cache.clear()

    def _first_created_post_check(self, response) -> None:
        """Метод для проверки первого поста на страницах."""
        first_object = response.context['page_obj'][-1]
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.author, self.user)
        self.assertEqual(first_object.group, self.group)
        self.assertEqual(first_object.pub_date, self.post.pub_date)
        self.assertEqual(first_object.image, self.post.image)

    def test_pages_show_correct_context(self):
        """Шаблоны index, group_list, profile с правильным контекстом."""
        urls = (
            self.index_url,
            self.group_list_url,
            self.profile_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url, {'page': 2})
                self._first_created_post_check(response)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.post_detail_url)
        post = response.context['post']
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, self.post.image)

    def _postform_context_check(self, url: str) -> None:
        """Метод для проверки контекста postform."""
        response = self.authorized_client.get(url)
        self.assertIsInstance(response.context.get('form'), PostForm)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_edit_post_show_correct_context(self):
        """Шаблон create_post,edit_post сформирован с правильным контекстом."""
        urls = (
            self.post_create_url,
            self.post_edit_url,
        )
        for url in urls:
            with self.subTest(url=url):
                self._postform_context_check(url)

    def test_post_displayed_correctly(self):
        """Пост не попал в группу, для которой не был предназначен."""
        urls = (
            self.index_url,
            self.another_profile_url,
            self.another_group_list_url,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.another_authorized_client.get(url)
                self.assertIn(self.another_post, response.context['page_obj'])
        response = self.another_authorized_client.get(self.group_list_url)
        self.assertNotIn(self.another_post, response.context['page_obj'])

    def _page_paginator(self, url: str, posts_count: int) -> None:
        """Метод для проверки паджинатора на первой и второй странице."""
        posts_at_page = {
            1: settings.POSTS_PER_PAGE,
            2: posts_count - settings.POSTS_PER_PAGE
        }
        for page, posts in posts_at_page.items():
            with self.subTest(url=url, page=page, posts=posts):
                response = self.authorized_client.get(url, {'page': page})
                self.assertEqual(len(response.context['page_obj']), posts)

    def test_page_paginator(self):
        """Работа паджинатора в приложении posts."""
        urls = {
            self.index_url: self.posts_quantity,
            self.group_list_url: self.posts_num_test_user,
            self.profile_url: self.posts_num_test_user,
        }
        for url, posts_count in urls.items():
            self._page_paginator(url, posts_count)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index_url."""
        response = self.authorized_client.get(self.index_url)
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.user,
        )
        response_old = self.authorized_client.get(self.index_url)
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(self.index_url)
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_follow(self):
        """Тестирование подписки на автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='new author')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, new_author)
        self.assertEqual(follow.user, self.user)

    def test_unfollow(self):
        """Тестирование отписки от автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='new author')
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        new_user = User.objects.create(username='new author')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            )
        )
        response = authorized_client.get(self.follow_index, {'page': 2})
        self._first_created_post_check(response)

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        new_user = User.objects.create(username='new author')
        authorized_client = Client()
        authorized_client.force_login(new_user)
        response_unfollow = authorized_client.get(self.follow_index)
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)
