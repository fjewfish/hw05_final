from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'test-username'
        cls.group_slug = 'test-slug'
        cls.index_url = reverse('posts:index')
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
        cls.another_user_post = reverse(
            'posts:post_detail', kwargs={'post_id': '2'}
        )
        cls.not_allowed_edit_url = reverse(
            'posts:edit', kwargs={'post_id': '2'}
        )
        cls.profile_follow_url = reverse(
            'posts:profile_follow', kwargs={'username': cls.username}
        )
        cls.profile_unfollow_url = reverse(
            'posts:profile_unfollow', kwargs={'username': cls.username}
        )
        cls.follow_index_url = reverse('posts:follow_index')
        cls.post_create_url = reverse('posts:post_create')
        cls.group_create_url = reverse('posts:group_create')
        cls.edit_redirect = '/auth/login/?next=/posts/1/edit/'
        cls.create_redirect = '/auth/login/?next=/create/'
        cls.create_group_redirect = '/auth/login/?next=/create_group/'
        cls.not_found_404_url = '/unexisting_page/'
        cls.user = User.objects.create_user(username=cls.username)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.group_slug,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
        )
        cls.another_user = User.objects.create_user(username='another_user')
        cls.post = Post.objects.create(
            author=cls.another_user,
            text='Тестовая пост 2',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_public_url_exists_at_desired_location(self):
        """Публичные страницы приложения posts доступны пользователю."""
        public_urls = {
            self.index_url: HTTPStatus.OK,
            self.group_list_url: HTTPStatus.OK,
            self.profile_url: HTTPStatus.OK,
            self.post_detail_url: HTTPStatus.OK,
            self.not_found_404_url: HTTPStatus.NOT_FOUND,
        }
        for url, status in public_urls.items():
            with self.subTest(url=url, status=status):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

    def test_private_url_exists_at_desired_location(self):
        """Приватные страницы приложения posts доступны пользователю."""
        private_url = (
            (self.post_edit_url, self.authorized_client, HTTPStatus.OK),
            (self.post_edit_url, self.guest_client, HTTPStatus.FOUND),
            (self.post_create_url, self.authorized_client, HTTPStatus.OK),
            (self.post_create_url, self.guest_client, HTTPStatus.FOUND),
            (self.group_create_url, self.authorized_client, HTTPStatus.OK),
            (self.group_create_url, self.guest_client, HTTPStatus.FOUND),
            (self.not_allowed_edit_url, self.authorized_client,
             HTTPStatus.FOUND),
            (self.follow_index_url, self.authorized_client, HTTPStatus.OK),
            (self.follow_index_url, self.guest_client, HTTPStatus.FOUND),
        )
        for url, client, status in private_url:
            with self.subTest(url=url, client=client, status=status):
                response = client.get(url)
                self.assertEqual(response.status_code, status)

    def test_urls_redirect(self):
        """Корректно работают перенаправления в приложении posts."""
        redirect_urls = (
            (self.post_edit_url, self.guest_client, self.edit_redirect),
            (self.post_create_url, self.guest_client, self.create_redirect),
            (self.group_create_url, self.guest_client,
             self.create_group_redirect),
            (self.not_allowed_edit_url, self.authorized_client,
             self.another_user_post),
            (self.profile_follow_url, self.authorized_client,
             self.profile_url),
            (self.profile_unfollow_url, self.authorized_client,
             self.profile_url),
        )
        for url, client, redirect in redirect_urls:
            with self.subTest(url=url, client=client, redirect=redirect):
                response = client.get(url)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
            self.post_edit_url: 'posts/create_post.html',
            self.post_create_url: 'posts/create_post.html',
            self.follow_index_url: 'posts/follow.html',
            self.group_create_url: 'posts/create_group.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)
