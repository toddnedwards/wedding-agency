from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('vibe-finder/', views.VibeQuizView.as_view(), name='vibe_quiz'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('services/', views.ServicesView.as_view(), name='services'),
    path('faq/', views.FaqView.as_view(), name='faq'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('blog/', views.BlogListView.as_view(), name='blog_list'),
    path('blog/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
]
