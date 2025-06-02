from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Company


class CompanySignUpForms(UserCreationForm):
    company_name = forms.CharField(label='Company Name', max_length=100, required=True)
    sector = forms.ChoiceField(choices=Company.SECTOR_CHOICES, label="secteur d'activité", required=True)
    number_empl = forms.IntegerField(required=True)
    age = forms.IntegerField(required=True)
    sales_revenue = forms.DecimalField(max_digits=5, decimal_places=2, required=True)

    class Meta:
        model = Company
        fields = ('username', 'email','sector', 'number_empl', 'age', 'sales_revenue', 'password1', 'password2', 'company_name', )
