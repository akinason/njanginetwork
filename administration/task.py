from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model as UserModel

from njanginetwork.celery import app as celery_app
from .models import Beneficiary, Remuneration, remuneration_status

# generating the beneficiary list on a backgroud task from a "remuneration create form"
@celery_app.task
def create_beneficiaries(remuneration_id):
    remuneration = get_object_or_404(Remuneration, pk=remuneration_id)
    levels_data = [remuneration.level_1, remuneration.level_2, remuneration.level_3,
                   remuneration.level_4, remuneration.level_5, remuneration.level_6]
    levels_involved_and_amount = []

    for index, level_data in enumerate(levels_data):
        if level_data > 0:
            amount = remuneration.allocated_amount * levels_data[index]
            levels_involved_and_amount.append([index + 1, amount])

    beneficiary_list = []

    for beneficiary_level in levels_involved_and_amount:
        beneficiary_count = UserModel().objects.filter(
            level=beneficiary_level[0]).count()
        share_per_person = round(beneficiary_level[1] / beneficiary_count, 0)
        beneficiary = UserModel().objects.filter(
            level=beneficiary_level[0])

        # arrangement... [beneficiary, level, share_per_person]
        beneficiary_list.append(
            [beneficiary, beneficiary_level[0], share_per_person])

    # Reodering the beneficiary list in the format... [beneficiary, level, amount]
    ordered_beneficiary_list = []

    for beneficiary in beneficiary_list:
        for beneficiaries in beneficiary[0]:
            ordered_beneficiary_list.append(
                [beneficiaries, beneficiary[1], beneficiary[-1]])

    print("CREATING THE LIST BENEFICIARIES")
    for beneficiary in ordered_beneficiary_list:
        new_beneficiairy = Beneficiary.objects.create(
            remuneration=remuneration, user=beneficiary[0], amount=beneficiary[-1], user_level=beneficiary[1])

    print("DONE CREATING THE BENEFICIARIES")

    # changing remuneration status to "GENERATED"
    remuneration.status = remuneration_status.generated()
    remuneration.save()

    return {"status": True}
