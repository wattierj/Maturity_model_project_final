from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup, name='signup'),
    path('enter-code/', views.enter_company_code, name='enter_code'),
    path('select-role/', views.select_role, name='select_role'),
    path('diagnostic/', views.diagnostic_form, name='diagnostic'),
    path('login/', auth_views.LoginView.as_view(template_name="maturity_site/login.html"), name='login'),
    path('logout/',auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path('signup/', views.signup, name='signup'),
    path('company_code/', views.company_code_view, name='company_code'),
    path('account/', views.account_view, name='account'),
    path('results/<int:result_id>/', views.result_view, name="result"),
    path('no_results/', views.result_view, name="no_results"),
    path('results/generate/', views.generate_result_view, name="generate_results"),
    path('results/history/', views.result_history_view, name="result_history"),
    path('end_survey/', views.end_survey, name='end_survey'),
    path('results/<int:result_id>/pdf/', views.generate_pdf_report, name='generate_pdf_report'),


]
