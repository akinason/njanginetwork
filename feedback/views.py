import datetime
import json

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import HttpResponse, get_object_or_404, render
from django.utils import timezone

from . import models

User = get_user_model()

# Create your views here.


def post_feedback_response(request):
    active_feedback = models.Feedback.objects.filter(is_active=True).first()

    user = request.user
    active_feebacks = models.Feedback.objects.filter(
        is_active=True).values('id')

    active_feedback_questions = models.Question.objects.filter(
        feedback_id__in=active_feebacks
    ).values('id', 'feedback_id__id')

    active_feedback_questions_only = [
        l['id'] for l in active_feedback_questions]

    responses = models.Response.objects.filter(
        question_id__id__in=active_feedback_questions_only, user_id=user
    ).values('id', 'question_id__id')
    answered_questions = [l['question_id__id'] for l in responses]
    active_feedback_questions_only = set(
        active_feedback_questions_only)
    answered_questions = set(answered_questions)
    unanswered_questions = active_feedback_questions_only.difference(
        answered_questions)
    unanswered_questions = list(unanswered_questions)

    unanswered_feedbacks = [
        l['feedback_id__id'] for l in active_feedback_questions if l['id'] in unanswered_questions]
    # Extract unique feedback ids
    unanswered_feedbacks = list(set(unanswered_feedbacks))

    active_feedback = models.Feedback.objects.filter(
        id__in=unanswered_feedbacks)  # Extract the feedbacks as objects.

    active_feedback = active_feedback.first()

    if active_feedback != None:
        feedback_end_date = (active_feedback.end_date).replace(tzinfo=None)
        feedback_today_date = (datetime.datetime.utcnow()).replace(tzinfo=None)
        feedback_expired = (feedback_today_date > feedback_end_date)

        if feedback_expired == False:
            questions = models.Question.objects.filter(
                feedback_id=active_feedback.id).order_by('order').all()
            feedback = active_feedback

            if request.method == "POST":
                user_id = request.POST.get('user_id')
                responses = json.loads(request.POST.get('response'))
                response_date = datetime.datetime.utcnow()

                json_results = []

                print(responses)
                for res in responses:
                    if res['multiple'] == True:
                        response = []
                        for data in res['response']:
                            response.append(data)

                        models.Response.objects.create(
                            question_id=models.Question.objects.get(
                                id=int(res['question_id'])),
                            response=str(response),
                            user_id=User.objects.get(id=int(user_id)),
                            response_date=response_date
                        )
                    else:
                        models.Response.objects.create(
                            question_id=models.Question.objects.get(
                                id=int(res['question_id'])),
                            response=res['response'],
                            user_id=User.objects.get(id=int(user_id)),
                            response_date=response_date
                        )

                return JsonResponse({'message': 'successful'})

            elif request.method == "GET":

                has_submitted = models.Response.objects.filter(
                    user_id=request.user.id, question_id__feedback_id=active_feedback).exists()
                # print(submitted_users)
                if has_submitted:
                    print("Already submitted")
                    response_data = {
                        'status': True
                    }
                else:
                    print('Not yet submitted')

                    # data to be sent to front-end onload event
                    question_list = []
                    feedback_data = [feedback.title, feedback.note]

                    # looping through all questions for that feedback
                    for question in questions:
                        # Getting all options from questions with data_type='OPTION'
                        option_list = []
                        for option in question.option_list.values():
                            option_list.append(option['value'])

                        question_list.append(
                            {"title": question.title,
                             "id": question.id,
                             'data_type': question.data_type,
                             'option_list': option_list,
                             'multiple': question.multiple
                             })
                    response_data = {
                        'question': question_list,
                        'feeback': feedback_data,
                        'status': False
                    }

                return JsonResponse(response_data)

    elif(active_feedback == None):
        return JsonResponse({'status': True})
