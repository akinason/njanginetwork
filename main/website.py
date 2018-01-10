from django.utils.translation import ugettext_lazy as _


def the_problem():
    response = _(
        "Many people have joined what is locally known as “njangi” where people contribute a fixed amount of "
        "money at regular intervals and hand it to one member in the group. This usually occurs in a cycle of people "
        "who know themselves."
        "<p>If there are 10 people contributing 10000CFA every month (a total of 100, 000 CFA) and handing it over to"
        " the one person, it will take 10 months for the cycle to complete and everyone will go home at the end of "
        "the day with a total of 100000 CFA which is the equivalence of the total contribution made within the period "
        "of 10 months. (i.e. 10,000 x 10 = 100, 000 CFAF). </p>"
        "Usually, people don’t want to involve those people they know nothing about them because they are not sure as "
        "to whether the person will complete the cycle. Sometimes, it’s lack of an administrator to administer all "
        "these people in such a way that people do not have to fear others."
    )
    return response


def njangi_network():
    response = _(
        "Njangi network is a web based application which aims to solve this problem. It comes to provide an "
        "administrative system where people can join the network and contribute without knowing each other. "
        "<p>The system manages all the administration of the contributions but does not manage the funds. "
        "Funds are transferred from the contributor to the recipient directly using mobile money services such "
        "as MTN Mobile Money, Orange Money. </p>"
        "It provides a system where contributions are done to the same person every 30 days. The system checks in "
        "the network and gets the mobile account to which contributions are to be done and after the amount is "
        "transferred, the recipient receives it instantly."
    )
    return response


def the_model():
    response = _(
        "The system  positions network members in levels. At sign-up, everyone is at level zero (0), after "
        "contributing 2000 XOF to your level 1 upline member, you move to level 1 and there you are required to "
        "get just 2 people to join the network. "

        "<p>These two people sign-up and do their first contributions of 2000 XOF to you in other to move to level "
        "1. The model is explained in the table below:</p>"

        "<a href='https://docs.google.com/spreadsheets/d/1NzG6jpBapoFxcAGupP814yOffwAPmg7hcUQn1nqvn0M/edit?usp=sharing' "
        "target='_blank'>"
        "Njangi Network Analysis</a><br>"


        "NB: It should be noted that the only amount one ever starts contribution with is 2000 XOF and he/she "
        "never has to increase the amount again but rather contributes from the contributions he/she receives. "

        "<p>This is based on everyone getting 2 persons to join the network (if you have more than 2 the system will "
        "place them under your  downline network members)</p>"
    )
    return response
