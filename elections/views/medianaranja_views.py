from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.forms import formsets
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.context import RequestContext
from django.utils import simplejson as json
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, UpdateView

from elections.models import Election, Candidate, Answer, Category, Question

# MediaNaranja Views
@login_required
@require_http_methods(['GET', 'POST'])
def associate_answer_to_candidate(request, candidate_slug, election_slug):
    election = get_object_or_404(Election, slug=election_slug, owner=request.user)
    candidate = get_object_or_404(Candidate, slug=candidate_slug, election=election)
    if request.POST:
        answer_id = request.POST.get('answer', None)
        answer = get_object_or_404(Answer, pk=answer_id, question__category__election=election)
        candidate.associate_answer(answer)
        return HttpResponse(json.dumps({'answer': answer.pk}),
                            content_type='application/json')
    return render_to_response(\
            'elections/associate_answer.html', {'candidate': candidate, 'categories': election.category_set},
            context_instance=RequestContext(request))

def post_medianaranja1(request, username, election_slug):
    user_list = User.objects.filter(username=username)
    if len(user_list) == 0:
        raise Http404

    election = Election.objects.get(slug=election_slug, owner=User.objects.get(username=user_list[0]))

    candidates = election.candidate_set.all()
    categories = election.category_set.all()

    number_of_questions = 0
    for c in categories:
        number_of_questions += len(c.get_questions())

    importances = []
    answers = []

    for i in range(number_of_questions):
        ans_id = int(request.POST['question-'+str(i)])
        answers.append(Answer.objects.filter(id=ans_id))
        importances.append(int(request.POST['importance-'+str(i)]))

    return medianaranja2(request, answers, importances, candidates, categories)

def get_medianaranja1(request, username, election_slug):
    u = User.objects.filter(username=username)
    if len(u) == 0:
        raise Http404
    e = Election.objects.filter(owner=u[0],slug=election_slug)
    if len(e) == 0:
        raise Http404

    send_to_template = []
    counter = 0
    for x in e[0].category_set.all():
        empty_questions = []
        list_questions = x.get_questions()
        for i in range(len(list_questions)):
            y = list_questions[i]
            empty_questions.append((counter,y,y.answer_set.all()))
            counter += 1
        send_to_template.append((x,empty_questions))

    return render_to_response('medianaranja1.html', {'stt':send_to_template,'election': e[0], 'categories': e[0].category_set}, context_instance = RequestContext(request))

def medianaranja1(request, username, election_slug):

    if request.method == "POST":
        return post_medianaranja1(request, username, election_slug)

    else:
        return get_medianaranja1(request, username, election_slug)

def medianaranja2(request, my_answers, importances, candidates, categories):

    scores_and_candidates = []

    for candidate in candidates:
        score = candidate.get_score(my_answers, importances)
        global_score = score[0]
        category_scores = score[1]
        scores_and_candidates.append([global_score,category_scores,candidate])
    scores_and_candidates.sort()
    scores_and_candidates.reverse()

    winner = scores_and_candidates[0]
    other_candidates = scores_and_candidates[1:]
    return render_to_response('medianaranja2.html', {'categories':categories,'winner':winner,'others':other_candidates}, context_instance = RequestContext(request))