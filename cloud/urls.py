from django.conf.urls import url

from . import views

app_name = 'cloud'

urlpatterns = [
    # /cloud/
    url(r'^$', views.index, name='index'),

    # /cloud/login
    url(r'^login$', views.login, name='login'),

    # /cloud/userPage
    url(r'^userPage$', views.userPage, name='userPage'),

    # /cloud/logout
    url(r'^logout$', views.logout, name='logout'),

    # /cloud/dirs/files
    url(r'^dirs/files$', views.filesInDir, name='filesInDir'),

    # /cloud/dirs/add
    url(r'^dirs/add$', views.createNewDirectory, name='createNewDirectory'),

    # /cloud/dirs/delete
    url(r'^dirs/delete$', views.deleteDirectory, name='deleteDirectory'),

    # /cloud/files/set
    url(r'^files/set$', views.setFile, name='setFile'),

    # /cloud/files/download
    url(r'^files/download$', views.getFile, name='getFile'),

    # /cloud/files/upload
    url(r'^files/upload$', views.uploadFile, name='uploadFile'),

    # /cloud/files/delete
    url(r'^files/delete$', views.deleteFile, name='deleteFile'),

    # /cloud/:number/
    url(r'^(?P<number>[0-9]+)/$', views.stam, name='stam'),
]
