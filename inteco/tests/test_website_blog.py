
from datetime import date, timedelta

from odoo.tests.common import TransactionCase


class TestWebsiteBlog(TransactionCase):
    """Test cases for blog-related models"""

    def setUp(self):
        super(TestWebsiteBlog, self).setUp()
        self.blog_model = self.env['blog.blog']
        self.post_model = self.env['blog.post']
        self.blog = self.blog_model.create({
            'name': 'New Blog',
        })

    def test_001_onchange_post_date(self):
        """Validates that the post date's onchange method returns a warning
            when it's set to an earlier date than today; and the field is
            after that.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        blog_post = self.post_model.create({
            'name': 'New Post',
            'blog_id': self.blog.id,
            'post_date': tomorrow,
        })
        self.assertFalse(
            blog_post.onchange_post_date(),
            "The onchange shouldn't return any value.")
        blog_post.post_date = today
        self.assertFalse(
            blog_post.onchange_post_date(),
            "The onchange shouldn't return any value.")
        blog_post.post_date = yesterday
        result = blog_post.onchange_post_date()
        self.assertTrue(
            result, "The onchange should've returned a warning.")
        self.assertIn(
            'warning', result, "The onchange should've returned a warning.")
        self.assertDictEqual(
            result.get('value'), {'post_date': False},
            "Onchange method should've cleared the post date")
