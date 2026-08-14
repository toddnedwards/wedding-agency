from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.vendors.models import Vendor

from .models import BlogPost


class StaticPageSitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return ('home', 'vibe_quiz', 'about', 'services', 'faq', 'contact', 'blog_list')

    def location(self, item):
        return reverse(item)


class VendorSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    vendor_types = {
        'musician': 'musicians',
        'caricaturist': 'caricaturists',
        'photographer': 'photographers',
    }

    def items(self):
        return Vendor.objects.filter(is_active=True, is_approved=True).exclude(slug__isnull=True).exclude(slug='')

    def lastmod(self, vendor):
        return vendor.updated_at

    def location(self, vendor):
        return reverse(
            'bookings:vendor_detail',
            kwargs={
                'vendor_type': self.vendor_types[vendor.vendor_type],
                'slug': vendor.slug,
            },
        )


class BlogSitemap(Sitemap):
    priority = 0.7
    changefreq = 'monthly'

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, post):
        return post.updated_at

    def location(self, post):
        return reverse('blog_detail', kwargs={'slug': post.slug})