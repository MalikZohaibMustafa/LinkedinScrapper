from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('scrape', views.scrape, name='scrape'),
    path('getQuestions', views.getQuestions, name='getQuestions'),
    path('getRecommendation', views.getRecommendation, name='getRecommendation'),
    path('manualUpload', views.manualUpload, name='manualUpload'),
    path("regenerate", views.regenerate, name="regenerate")
    
]