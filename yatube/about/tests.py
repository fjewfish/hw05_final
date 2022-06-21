from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus


class AboutURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_url = reverse('about:author')
        cls.tech_url = reverse('about:tech')

    def setUp(self):
        self.guest_client = Client()

    def test_public_url_exists_at_desired_location(self):
        """Публичные страницы приложения about доступны пользователю."""
        public_urls = (
            self.author_url,
            self.tech_url,
        )
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """URL-адрес приложения about использует соответствующий шаблон."""
        templates_url_names = {
            self.author_url: 'about/author.html',
            self.tech_url: 'about/tech.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
