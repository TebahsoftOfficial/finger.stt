from django.urls import path, include
from . import views

urlpatterns = [
    path('detail/<str:mode>/<str:pk>/', views.InterviewsUpdate.as_view()),
    path('create/<str:msg>/', views.InterviewsCreate.as_view()),
    path('', views.start_interviews),
    path('list/<str:msg>/', views.clientlist),
    path('sentimental/<str:pk>/', views.sentimental),
    path('wordcloud/<str:pk>/', views.wordcloud),
    path('document/<str:pk>/', views.document),
    path('search/<str:q>/', views.InterviewsSearch.as_view()),
    path('delete/<str:interview_pk>/', views.delete, name='interview_delete'),
    #path('report/<str:pk>/<str:label>', views.report),
    path('client/<str:pk>/', views.client_page, name='client_page'),
    path('client/delete/<str:pk>/', views.client_delete, name='client_delete'),
    path('client/modify/<str:pk>/', views.client_modify, name='client_modify'),
    path('client/pwcheck/<str:pk>/', views.client_pwcheck, name='client_pwcheck'),
    path('add/client/<str:redir>/', views.ClientCreate.as_view()),
    path('dbupdate/<str:msg>/', views.dbupdate),
    path('sentenceupdate/<str:pk>/', views.sentenceUpdate),
    path('addspeaker/<str:pk>/', views.addspeaker),
    path('inaction/', views.inaction),
    path('realtime/',views.RealtimeInterviews)

]