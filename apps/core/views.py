from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.generic import ListView, DetailView, TemplateView
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from .models import BlogPost, ContactMessage
from apps.vendors.models import Musician, Caricaturist, Photographer

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

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('contact')

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )

        # Send email
        try:
            send_mail(
                subject=f'New Contact Form Submission: {subject}',
                message=f'From: {name} ({email})\nPhone: {phone}\n\n{message}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
        except:
            pass

        messages.success(request, 'Your message has been sent successfully! We\'ll be in touch soon.')
        return redirect('contact')


def robots_txt(request):
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
