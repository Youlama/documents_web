"""
URL configuration for settings project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

from replacing_documents import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Document

    path('document', views.get_document_list, name='document_list'),
    path('document/<int:pk>', views.get_document, name='document'),
    path('document/post', views.post_document, name='document_post'),
    path('document/<int:pk>/delete', views.delete_document, name='document_delete'),
    path('document/<int:pk>/put', views.put_document, name='document_put'),
    path('document/<int:pk>/add', views.post_document_to_request, name='document_add'),
    path('document/<int:pk>/add_image', views.post_document_image, name='document_add_image'),

    # InstallDocumentRequest

    path('install_document_requests', views.get_install_document_requests, name='install_document_requests'),
    path('install_document_requests/<int:pk>', views.get_install_document_request, name='install_document_request'),
    path('install_document_requests/<int:pk>/put', views.put_install_document_request,
         name='install_document_request_put'),
    path('install_document_requests/<int:pk>/form', views.form_install_document_request,
         name='install_document_request_form'),
    path('install_document_requests/<int:pk>/resolve', views.resolve_install_document_request,
         name='install_document_request_resolve'),
    path('install_document_requests/<int:pk>/delete', views.delete_install_document_request,
         name='install_document_request_delete'),

    # DocumentInRequest

    path('document_in_request/<int:request_pk>/<int:document_pk>/put', views.put_document_in_request, name='document_in_request_put'),
    path('document_in_request/<int:request_pk>/<int:document_pk>/delete', views.delete_document_in_request, name='document_in_request_delete'),

    # User

    path('users/create', views.create_user, name='users_create'),
    path('users/login', views.login_user, name='users_login'),
    path('users/logout', views.logout_user, name='users_logout'),
    path('users/update', views.update_user, name='users_update'),
]