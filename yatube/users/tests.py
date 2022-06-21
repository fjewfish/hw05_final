from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from .forms import CreationForm

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.signup_url = reverse('users:signup')
        cls.login_url = reverse('users:login')
        cls.password_change_url = reverse('users:password_change')
        cls.password_change_done_url = reverse('users:password_change_done')
        cls.password_reset_url = reverse('users:password_reset')
        cls.password_reset_done_url = reverse('users:password_reset_done')
        cls.reset_done_url = reverse('users:password_reset_complete')
        cls.logout_url = reverse('users:logout')
        cls.reset_token_url = reverse(
            'users:password_reset_confirm',
            kwargs={'uidb64': 'uidb64', 'token': 'token'}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test-username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_url_exists_at_desired_location(self):
        """Публичные страницы приложения users доступны пользователю."""
        public_urls = (
            self.signup_url,
            self.login_url,
        )
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url_exists_at_desired_location(self):
        """Приватные страницы приложения users доступны пользователю."""
        private_urls = (
            self.password_change_url,
            self.password_change_done_url,
            self.password_reset_url,
            self.password_reset_done_url,
            self.reset_token_url,
            self.reset_done_url,
            self.logout_url,
        )
        for url in private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_authorized_user(self):
        """Корректно работают перенаправления в приложении users."""
        redirect_urls = (
            self.password_change_url,
            self.password_change_done_url,
        )
        for url in redirect_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, '/auth/login/?next=' + url)

    def test_urls_uses_correct_template(self):
        """URL-адрес приложения users использует соответствующий шаблон."""
        templates_url_names = {
            self.signup_url: 'users/signup.html',
            self.login_url: 'users/login.html',
            self.password_change_url: 'users/password_change_form.html',
            self.password_change_done_url: 'users/password_change_done.html',
            self.password_reset_url: 'users/password_reset_form.html',
            self.password_reset_done_url: 'users/password_reset_done.html',
            self.reset_token_url: 'users/password_reset_confirm.html',
            self.reset_done_url: 'users/password_reset_complete.html',
            self.logout_url: 'users/logged_out.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_singup_url_show_correct_context(self):
        """Шаблон singup сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.signup_url)
        self.assertIsInstance(response.context.get('form'), CreationForm)

    def test_singup_form(self):
        """Отправка валидной формы создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'test_name',
            'last_name': 'test_surname',
            'username': 'test_username',
            'email': 'test@yandex.ru',
            'password1': 'test_password',
            'password2': 'test_password',
        }
        response = self.authorized_client.post(
            self.signup_url,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='test_name',
                last_name='test_surname',
                username='test_username',
                email='test@yandex.ru',
            ).exists()
        )
