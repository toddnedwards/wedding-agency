from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.core.mail import EmailMessage
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
import logging
from .email_delivery import send_contact_notification
from .forms import ContactForm
from .models import BlogPost
from apps.vendors.models import Musician, Caricaturist, Photographer


logger = logging.getLogger(__name__)

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = BlogPost.objects.filter(is_published=True)[:3]
        context['featured_musicians'] = Musician.objects.filter(is_approved=True, is_active=True)[:6]
        context['featured_caricaturists'] = Caricaturist.objects.filter(is_approved=True, is_active=True)[:3]
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'

class ServicesView(TemplateView):
    template_name = 'core/services.html'


class FaqView(TemplateView):
    template_name = 'core/faq.html'


class VibeQuizView(TemplateView):
    template_name = 'core/vibe_quiz.html'

class ContactView(TemplateView):
    template_name = 'core/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', ContactForm())
        return context

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please check the form and try again.')
            return self.render_to_response(self.get_context_data(form=form), status=400)

        contact_message = form.save()

        # Send email
        try:
            send_contact_notification(contact_message)
        except Exception:
            logger.exception(
                'Could not send contact form notification for message %s using %s via %s:%s.',
                contact_message.pk,
                settings.EMAIL_BACKEND,
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
            )
            messages.warning(request, 'Your message was saved, but we could not send the email notification. Please try again or contact us directly.')

        else:
            messages.success(request, 'Your message has been sent successfully! We\'ll be in touch soon.')
        return redirect('contact')


def robots_txt(request):
    if not settings.INDEXING_ENABLED:
        return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')

    sitemap_url = request.build_absolute_uri('/sitemap.xml')
    return HttpResponse(f'User-agent: *\nAllow: /\n\nSitemap: {sitemap_url}\n', content_type='text/plain')

class BlogListView(ListView):
    model = BlogPost
    template_name = 'core/blog_list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        return BlogPost.objects.filter(is_published=True).order_by('-created_at')

class BlogDetailView(DetailView):
    model = BlogPost
    template_name = 'core/blog_detail.html'
    context_object_name = 'post'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_posts'] = BlogPost.objects.filter(
            is_published=True
        ).exclude(id=self.object.id)[:3]
        return context
