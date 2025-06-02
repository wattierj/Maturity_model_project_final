from django.db import models
from django.contrib.auth.models import User, AbstractUser
import uuid
from django.core.exceptions import ValidationError

# Create your models here.
ROLE_CHOICES = [
    ('manager', 'Manager'),
    ('employee', 'Employee')
]


class Company (AbstractUser):
    SECTOR_CHOICES = [
        ("manufacturing", "Manufacturing"),
        ("construction", "Construction"),
        ("retail", "Retail and Wholesale Trade"),
        ("it", " Information and Communication Technology (ICT)"),
        ("proscitec", "Professional, Scientific, and Technical Services"),
        ("finance", "Finance and Insurance"),
        ("estate", "Real Estate and Rental Services"),
        ("healthcare", "Healthcare and Social Assistance"),
        ("accommodation", "Accommodation and Food Services"),
        ("education", "Education and Training"),
        ("transportation", "Transportation and Logistics"),
        ("agriculture", "Agriculture, Forestry, and Fishing"),
        ("arts", "Arts, Entertainment, and Recreation"),
        ("administrative", "Administrative and Support Services"),
        ("utilities", "Utilities and Energy"),
        ("mining", "Mining and Quarrying"),
        ("publicad", "Public Administration"),
        ("waste", "Waste Management and Remediation Services"),
        ("textiles", "Textiles and Apparel"),
        ("other", "Personal and Other Services")]

    name = models.CharField(max_length=100,)
    code = models.CharField(max_length=100, unique=True, default=0)
    number_of_employee = models.IntegerField(null=True, blank=True)
    sector = models.CharField(max_length=100, choices=SECTOR_CHOICES)
    age = models.IntegerField(null=True, blank=True)
    sales_revenue = models.IntegerField(null=True)
    username=models.CharField(max_length=100, null=True, blank=True, unique=True)
    password = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)


class Survey (models.Model):
    title = models.CharField(max_length=100)
    version = models.DecimalField(max_digits=5, decimal_places=2)
    type = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.title} {self.version} {self.type}"


class Axis (models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class Results (models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    global_average = models.FloatField(null=True, blank=True)
    average_axe_x = models.FloatField(null=True, blank=True)
    average_axe_y = models.FloatField(null=True, blank=True)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"Result {self.id} - {self.company}"


class Diagnostic (models.Model):
    result = models.ForeignKey(Results, on_delete=models.CASCADE,null=True, blank=True)
    axe = models.ForeignKey(Axis, on_delete=models.CASCADE, null=True, blank=True)
    score_global = models.FloatField(null=True, blank=True)
    score_axe_x = models.FloatField(null=True, blank=True)
    score_axe_y = models.FloatField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=100, choices=ROLE_CHOICES, null=True, blank=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE,null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    already_results = models.BooleanField(default=False)

    def __str__(self):
        return f"Diagnostic {self.result} - {self.axe}"


class Dimension (models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    axe = models.ForeignKey(Axis, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.axe.name})"


class Question (models.Model):
    content = models.TextField()
    axe = models.ForeignKey(Axis, on_delete=models.CASCADE, null=True, blank=True)
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, null=True, blank=True)
    section = models.IntegerField(default=1, help_text="Numéro de la page/Section")
    is_identification = models.BooleanField(default=False, null=True, blank=True, help_text="Not usable question in the sum of maturity level")

    def __str__(self):
        return self.content


class Recommendation (models.Model):
    RECO_TYPE_CHOICES =[
        ('axe', 'Based on axis/dimensions'),
        ('ecart', 'Based on a difference btw Manager/Employé'),
        ("question", 'Based on a low value answer')
    ]

    type = models.CharField(max_length=100, choices=RECO_TYPE_CHOICES, null=True, blank=True)
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE, related_name='recommendations', null=True, blank=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    axe = models.ForeignKey(Axis, on_delete=models.CASCADE, null=True, blank=True)
    dimension = models.ForeignKey(Dimension, on_delete=models.CASCADE, null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    threshold = models.FloatField(null=True, blank=True)
    min_difference = models.FloatField(null=True, blank=True)
    result = models.ForeignKey('Results', on_delete=models.CASCADE, null=True, blank=True)
    template_text = models.TextField(null=True, blank=True)

    def clean(self):
        if self.type=='axis' and not self.axe:
            raise ValidationError("Un axe est requis pour les recommendations de type 'axis'. ")
        if self.type=='question' and not self.question:
            raise ValidationError("Une question est requise pour les recommendations de type 'questions' ")
        if self.type=='ecart' and not self.question:
            raise ValidationError("Une question est requise pour les recommendations de type 'ecart'")


    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reco ({self.type}) - {self.description[:30]}"


class PossibleAnswer (models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="possible_answers")
    label = models.CharField(max_length=100)
    value = models.IntegerField()

    def __str__(self):
        return f"{self.label} {self.value}"


class Answer (models.Model):
    diagnostic = models.ForeignKey(Diagnostic, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.IntegerField()
    date_answered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer {self.id} - {self.diagnostic}"