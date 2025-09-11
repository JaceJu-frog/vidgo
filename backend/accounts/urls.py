from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('hidden-categories/', views.update_hidden_categories, name='update_hidden_categories'),
    path('user-hidden-categories/', views.user_defined_hidden_categories, name='user_defined_hidden_categories'),
    path('check-root/', views.check_root_exists, name='check_root_exists'),
    path('register-root/', views.register_root, name='register_root'),
    path('create-user/', views.create_user, name='create_user'),
    path('list-users/', views.list_users, name='list_users'),
    path('update-user/<int:user_id>/', views.update_user, name='update_user'),
]