from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.utils import timezone
from django.db.models import Count
from django.db.models import Max
from django.db.models import Q

from journal.models import Journal
from core.models import Role
from review.models import ReviewRound

from .plugin_settings import PLUGIN_NAME

# dashboard_include
# journal_category

@login_required
def dashboard(request):
    template = "health_dashboard/dashboard.html"

    today = timezone.now()
    five_days = today - timedelta(days=5)
    one_year = today - timedelta(days=365)

    editor_role_id = Role.objects.get(name="Editor").id

    # threshold_unassigned_days
    # count and oldest unassigned article
    unassigned = Journal.objects\
        .annotate(
            unassigned=Count(
                "article",
                filter=Q(article__stage="Unassigned",
                         article__date_submitted__lte=five_days),
                distinct=True
            )                
        )
    result = { i.name: {"unassigned": i.unassigned, "url": i.site_url()} for i in unassigned }

    # threshold_login_days
    # last editor and days since last login
    last_login = Journal.objects\
        .annotate(
            last_login=Max("accountrole__user__last_login",
                           filter=Q(accountrole__role=editor_role_id))
        )
    for r in last_login:
        result[r.name].update({"last_login": r.last_login})

    # count stalled articles and time since last review completed
    # threshold_post_review_days
    stalled_articles = ReviewRound.objects\
        .filter(article__stage="Under Review")\
        .exclude(reviewassignment__is_complete=False)\
        .values_list("article", flat=True).distinct()
    stalled_reviews = Journal.objects\
        .annotate(
            stalled_reviews=Count(
                "article",
                filter=Q(article__in=stalled_articles),
            )
        )
    for r in stalled_reviews:
        result[r.name].update({"stalled_reviews": r.stalled_reviews})    

    # count peer-reviewed articles published in the last year
    peer_reviewed = Journal.objects\
        .annotate(
            peer_reviewed=Count(
                "article",
                filter=Q(article__peer_reviewed=True,
                         article__stage="Published",
                         article__date_published__gte=one_year),
                distinct=True
            )
        )
    for r in peer_reviewed:
        result[r.name].update({"peer_reviewed": r.peer_reviewed})

    # issues published in the last year
    # publication_frequency
    cadence = Journal.objects\
        .annotate(
            cadence=Count(
                "issue",
                filter=Q(issue__date__lte=today,
                         issue__date__gte=one_year),
                distinct=True
            )
        )
    for r in cadence:
        result[r.name].update({"cadence": r.cadence})

    context = {'plugin_name': PLUGIN_NAME,
               'result': result}
    return render(request, template, context)
