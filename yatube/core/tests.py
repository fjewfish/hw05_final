from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Проверка использование касмоного шаблопри при ошибке 404."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
