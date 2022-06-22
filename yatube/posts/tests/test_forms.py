import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'test-username'
        cls.post_create_url = reverse('posts:post_create')
        cls.profile_url = reverse(
            'posts:profile', kwargs={'username': cls.username}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail', kwargs={'post_id': '1'}
        )
        cls.post_edit_url = reverse(
            'posts:edit', kwargs={'post_id': '1'}
        )
        cls.post_add_comment_url = reverse(
            'posts:add_comment', kwargs={'post_id': '1'}
        )
        cls.user = User.objects.create_user(username=cls.username)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый пост',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в БД."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост c картинкой',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.post_create_url,
            data=form_data,
            follow=True,
        )
        post = Post.objects.latest('pub_date')
        self.assertRedirects(response, self.profile_url)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.id, Post.objects.first().id)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post(self):
        """Валидная форма редактирует запись в в БД."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small_edit.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Измененный пост c картинкой',
            'group': self.group.pk,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse(
                'posts:edit',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(response, self.post_detail_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.image, 'posts/small_edit.gif')

    def test_authorized_user_can_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            self.post_add_comment_url,
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.first()
        self.assertRedirects(response, self.post_detail_url)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)

    def test_guest_user_can_not_comment(self):
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        self.guest_client.post(
            self.post_add_comment_url,
            data=form_data,
            follow=True,
        )
        self.assertEqual(comments_count, self.post.comments.count())
