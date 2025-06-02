from django.conf import settings
from django.contrib import messages
from django.db.models import Avg, Max, Subquery, OuterRef, Subquery
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CompanySignUpForms
from .models import Question, Answer, Results, Company, Diagnostic, Axis, Recommendation
from django.utils import timezone
from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import random, string
from django.template import Template, Context
from django.template.loader import get_template
from xhtml2pdf import pisa
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
import os

# Create your views here.


def home(request):
    return render(request, 'maturity_site/home.html')


def about(request):
    return render(request, 'maturity_site/about.html')


def enter_company_code(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        print("Session:", request.session.session_key)
        print("CSRF token:", get_token(request))
        try:
            company = Company.objects.get(code=code)
            request.session['company_code'] = company.code
            print("Session:", request.session.session_key)
            print("CSRF token:", get_token(request))
            return redirect('select_role')
        except Company.DoesNotExist:
            return render(request, 'maturity_site/enter_code.html', {'error': "Invalid company code"})
    return render(request,'maturity_site/enter_code.html')


def select_role(request):
    if 'company_code' not in request.session:
        return redirect('enter_code')

    if request.method == 'POST':
        role = request.POST.get('role')
        return redirect(f'/diagnostic/?company_code={request.session['company_code']}&role={role}')
    return render(request, 'maturity_site/select_role.html')


def diagnostic_form(request):
    company_code = request.GET.get('company_code')
    role = request.GET.get('role')
    section = int(request.GET.get('section', 1))

    if not company_code or not role:
        return redirect('enter_code')

    try:
        company = Company.objects.get(code=company_code)
    except Company.DoesNotExist:
        return redirect('enter_code')

    question = Question.objects.filter(section=section)

    if request.method == 'POST':
        diagnostic_id = request.session.get('diagnostic_id')
        if not diagnostic_id:
            diagnostic = Diagnostic.objects.create(
                company=company,
                role=role,
                already_results=False
            )
            request.session['diagnostic_id'] = diagnostic.id
        else:
            diagnostic = get_object_or_404(Diagnostic, id=diagnostic_id)

        for key, value in request.POST.items():
            if key.startswith ('question_'):
                question_id = key.split('_')[1]
                question = Question.objects.get(id=question_id)
                Answer.objects.create(
                    diagnostic=diagnostic,
                    question=question,
                    value=int(value),
                    date_answered=timezone.now()
                )

        next_section = section + 1
        if Question.objects.filter(section=next_section).exists():
            return redirect(f'/diagnostic/?company_code={company_code}&role={role}&section={next_section}')
        else:
            del request.session['diagnostic_id']
            return redirect("end_survey")
    total_sections = Question.objects.values_list('section', flat=True).distinct().count()
    progress = int((section / total_sections)*100)

    return render(request, 'maturity_site/diagnostic_form.html', {
        'questions': question,
        'company': company,
        'role': role,
        'section': section,
        'total_sections': total_sections,
        'progress': progress
    })


def generate_company_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def signup(request):
    if request.method == 'POST':
        form = CompanySignUpForms(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if not user.code:
                user.code = generate_company_code()
            user.save()
            login(request, user)
            return redirect('company_code')#Dans le futur, mettre une vue direct sur la page compte de l'entreprise avec un dashboard
    else:
        form = CompanySignUpForms()
    return render(request, 'maturity_site/signup.html', {'form': form})


@login_required
def dashboard(request):
    company = Company.objects.get(owner=request.user)
    results = Results.objects.filter(company=company)
    return render(request, 'maturity_site/result.html', {
        'company': company,
        'results': results
    })


@login_required
def account_view(request):
    company = request.user
    pending_diagnostics = Diagnostic.objects.filter(company=company, already_results=False).count()
    return render(request, 'maturity_site/account.html', {'company':company,
                                                          'pending_diagnostics': pending_diagnostics})


@login_required
def company_code_view(request):
    company = request.user
    return render(request, 'maturity_site/company_code.html', {'company': company})


@login_required
def result_view(request, result_id):
    result = get_object_or_404(Results, id=result_id)
    company = result.company
    #company = request.user
    diagnostics = Diagnostic.objects.filter(company=company)
    recommendation = Recommendation.objects.filter(result=result)
    sector = result.company.sector

    axe_scores = {}
    total_score = 0
    total_count = 0

    for diagnostic in diagnostics:
        answers = Answer.objects.filter(diagnostic=diagnostic)
        for answer in answers:
            axe = answer.question.axe
            if axe.id not in axe_scores:
                axe_scores[axe.id] = [0, 0]
            axe_scores[axe.id][0] += answer.value
            axe_scores[axe.id][1] += 1
            total_score += answer.value
            total_count += 1

    global_average = round(total_score / total_count * 2, 2) if total_count else 0

    axe_x = Axis.objects.get(name="Technology Infrastructure")
    axe_y = Axis.objects.get(name="Digital Mindset")

    avg_x = round(axe_scores.get(axe_x.id, [0, 1])[0] / axe_scores.get(axe_x.id, [0, 1])[1] * 2, 2)
    avg_y = round(axe_scores.get(axe_y.id, [0, 1])[0] / axe_scores.get(axe_y.id, [0, 1])[1] * 2, 2)

    # Assign scores to the result object (si déjà existant)
    result.global_average = global_average
    result.average_axe_x = avg_x
    result.average_axe_y = avg_y
    result.save()

    #Competitors comparison :
    latest_results = Results.objects.filter(company__sector=sector).exclude(company=result.company).order_by('company', 'date_created')
    current_score = result.global_average
    other_scores = list(latest_results.values_list('global_average', flat=True))
    all_scores = sorted(other_scores +[current_score])

    rank = all_scores.index(current_score) + 1
    percentile = round((rank / len(all_scores)) *100, 2)

    #Recommendations Generations
    active_recommendations = []
    diagnostics = Diagnostic.objects.filter(company=result.company)
    answers = Answer.objects.filter(diagnostic__in=diagnostics).select_related('question__dimension', 'question__axe')
    axe_scores={}
    question_scores = {}
    dimension_scores = {}
    for answer in answers:
        question = answer.question
        dimension = answer.question.dimension
        axe = answer.question.axe

        if axe.id not in axe_scores:
            axe_scores[axe.id] = []
        axe_scores[axe.id].append(answer.value)

        if question.id not in question_scores:
            question_scores[question.id] = []
        question_scores[question.id].append(answer.value)

        if dimension.id not in dimension_scores:
            dimension_scores[dimension.id] = []
        dimension_scores[dimension.id].append(answer.value)

    def get_avg(queryset):
        values = list(queryset.values_list('value', flat=True))
        return sum(values) / len(values) if values else 0

    for rec in Recommendation.objects.all():
        if rec.type == "axe" and rec.axe:
            avg = sum(axe_scores.get(rec.axe.id, [])) / len(axe_scores.get(rec.axe.id, [1]))
            if avg < (rec.threshold or 5):
                text = render_recommendation_template(rec.template_text, {
                    "axe": rec.axe.name,
                    "score": round(avg, 2),
                    "threshold": rec.threshold,
                    "axe_score" : axe_scores
                })
                active_recommendations.append(text)

        elif rec.type == "question" and rec.dimension:
            avg = sum(dimension_scores.get(rec.dimension.id, [])) / len(dimension_scores.get(rec.dimension.id, [1]))
            if avg < (rec.threshold or 5):
                text = render_recommendation_template(rec.template_text, {
                    "dimension": rec.dimension.name,
                    "score":round(avg, 2),
                    "threshold":rec.threshold
                })
                active_recommendations.append(text)
        elif rec.type == 'ecart' and rec.question:
            manager_question = Answer.objects.filter(diagnostic__in=diagnostics.filter(role='manager'),
                                                     question=rec.question)
            employee_question = Answer.objects.filter(diagnostic__in=diagnostics.filter(role='employee'),
                                                      question=rec.question)
            avg_m = get_avg(manager_question)
            avg_e = get_avg(employee_question)
            diff = abs(avg_m - avg_e)

            if diff>= (rec.min_difference or 3):
                text =render_recommendation_template(rec.template_text, {
                    "dimension": rec.question.content,
                    "diff": round(diff, 2),
                    "manager_score":round(avg_m, 2),
                    "employee_score":round(avg_e, 2),
                })
                active_recommendations.append(text)
    left_px = round(avg_x * 40-10)
    bottom_px = round(avg_y * 40-10)
    return render(request, 'maturity_site/result.html',
              {'result': result, 'avg_x': avg_x, 'avg_y': avg_y, 'global_average': global_average,
                 'left_px': left_px, 'bottom_px': bottom_px, 'recommendations':active_recommendations, 'percentile':percentile})

@login_required()
def generate_result_view(request):
    company = request.user

    diagnostics = Diagnostic.objects.filter(company=company, already_results=False)
    if request.method == "POST":

        if diagnostics.exists():
            print("Button OK)")
            result = Results.objects.create(company=company)

            score_global = diagnostics.aggregate(Avg("score_global"))["score_global__avg"] or 0
            score_x = diagnostics.aggregate(Avg("score_axe_x"))["score_axe_x__avg"] or 0
            score_y = diagnostics.aggregate(Avg("score_axe_y"))["score_axe_y__avg"] or 0

            result.score_global = round(score_global, 2)
            result.score_axe_x = round(score_x, 2)
            result.score_axe_y = round(score_y, 2)
            result.save()

            diagnostics.update(already_results=True)

            return redirect('result', result_id=result.id)
    return render(request, 'maturity_site/generate_result.html', {
        'diagnostics': diagnostics,
    })


def result_history_view(request):
    company = request.user
    past_results = Results.objects.filter(company=company).order_by('-date_created')

    return render(request, "maturity_site/result_history.html",{
        "results": past_results
    })


def render_recommendation_template(template_string, context_data):
    template = Template(template_string)
    context = Context(context_data)
    return template.render(context)


def end_survey(request):
    return render(request, 'maturity_site/end_survey.html')


def generate_pdf_report(request, result_id):
    result = get_object_or_404(Results, id=result_id)
    company = request.user

    diagnostics = Diagnostic.objects.filter(company=company)
    answers = Answer.objects.filter(diagnostic__in=diagnostics). select_related('question')

    #Generate Matrix :
    def generate_matrix_with_position(result):
        width, height = 400,400
        img_path = os.path.join(settings.MEDIA_ROOT, f"matrix/matrix_{result.id}.png")
        os.makedirs(os.path.dirname(img_path), exist_ok=True)

        background = Image.open(os.path.join(settings.BASE_DIR, 'maturity_site\static\images\matrix.png'))

        left_px = round(result.average_axe_x * 40-10)
        bottom_px = round(result.average_axe_y * 40-10)

        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        ax.imshow(background, extent=[0, width, 0, height])
        ax.scatter(left_px, bottom_px, color='red', s=80, edgecolors='black', zorder=5)


        ax.axis('off')
        plt.tight_layout()
        fig.savefig(img_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return img_path
    #Question groups
    question_stats = {}
    for answer in answers:
        qid = answer.question.id
        if qid not in question_stats:
            question_stats[qid] = {
                'question':answer.question,
                'total':0,
                'distribution':{}
            }
        q_stat = question_stats[qid]
        q_stat['total'] +=1
        q_stat['distribution'][answer.value] = q_stat['distribution'].get(answer.value, 0) + 1

    #Dimension Average :
    dimension_scores = {}
    for answer in answers :
        dim = answer.question.dimension
        dimension_scores.setdefault(dim.id, {'dimension' : dim, 'values':[]})
        dimension_scores[dim.id]['values'].append(answer.value)

    for dim_data in dimension_scores.values():
        values = dim_data['values']
        dim_data['average'] = round(sum(values)/len(values), 2)
    matrix_img_url = generate_matrix_with_position(result)

    context={
        'result' : result,
        'company' : company,
        'question_stats' : question_stats,
        'dimension_scores' : dimension_scores.values(),
        'recommendations' : request.GET.get('reco_html',''),
        'matrix_img_url' : matrix_img_url,
    }


    template_path = 'maturity_site/pdf_report.html'
    template = get_template(template_path)
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_{result.company}_{result.date_created}.pdf'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse ("Error while generating PDF, try again later ! ")
    return response