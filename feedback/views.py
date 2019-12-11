from django.shortcuts import render, HttpResponse, get_object_or_404
from . import models
from django.utils import timezone
import datetime
from django.http import JsonResponse
import json
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.


def post_feedback_response(request):
    active_feedback = models.Feedback.objects.filter(is_active=True).first()

    if active_feedback != None:
        feedback_end_date = (active_feedback.end_date).replace(tzinfo=None)
        feedback_today_date = (datetime.datetime.utcnow()).replace(tzinfo=None)
        feedback_expired = (feedback_today_date > feedback_end_date)

        if feedback_expired == False:
            questions = models.Question.objects.filter(
                feedback_id=active_feedback.id).order_by('order').all()
            feedback = active_feedback

            # data to be sent to front-end onload event
            question_types = []
            question_list = []
            feedback_data = [feedback.title, feedback.note]

            for question in questions:
                question_types.append(question.response_type)
                question_list.append(
                    {"title": question.title, "id": question.id})

            if request.POST.get('action') == 'post':
                user_id = request.POST.get('user_id')
                responses = json.loads(request.POST.get('response'))
                response_date = datetime.datetime.utcnow()

                json_results = []

                for res in responses:
                    models.Response.objects.create(
                        question_id=models.Question.objects.get(
                            id=int(res['question_id'])),
                        response=res['response'],
                        user_id=User.objects.get(id=int(user_id)),
                        response_date=response_date
                    )

                    # send json response data to the front end
                    response_data = {}
                    response_data['question_id'] = int(res['question_id'])
                    response_data['response'] = res['response']
                    response_data['user_id'] = int(user_id)
                    response_data['response_date'] = str(response_date)
                    json_results.append(response_data)

                return JsonResponse(json_results, safe=False)

            elif request.GET.get('action') == 'get':
                response_data = {
                    'question': question_list,
                    'feeback': feedback_data
                }
                return JsonResponse(response_data)
