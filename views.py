from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.utils import timezone
from django.db.models import Count
from django.db.models import Max
from django.db.models import Q

from journal.models import Journal
from core.models import Role, SettingValue
from review.models import ReviewRound

from .plugin_settings import PLUGIN_NAME

incomplete_stages = ["Assigned",
                     "Under Review",
                     "Under Revision",
                     "Accepted",
                     "Editor Copyediting",
                     "Author Copyediting",
                     "Final Copyediting",
                     "Typesetting",
                     "typesetting_plugin",
                     "Proofing",
                     "pre_publication"]

# journal_category

def get_setting(journal, name):
    return journal.get_setting(
            group_name="plugin:health_dashboard",
            setting_name=name,
        )

@login_required
def dashboard(request):
    template = "health_dashboard/dashboard.html"

    today = timezone.now()
    one_year = today - timedelta(days=365)
    editor_role_id = Role.objects.get(name="Editor").id

    results = []
    journals = Journal.objects.prefetch_related("article_set")
    for j in journals:
        if get_setting(j, "dashboard_include"):
            # Unassigned articles
            unassigned_threshold = int(get_setting(j, "threshold_unassigned_days"))
            d = today - timedelta(days=unassigned_threshold)
            unassigned_set = j.article_set.filter(stage="Unassigned",
                                                date_submitted__lte=d)\
                                          .order_by("date_submitted")
            oldest_date = unassigned_set.first().date_submitted if unassigned_set.exists() else today

            # Last editor login
            login_threshold = int(get_setting(j, "threshold_login_days"))
            editors = j.accountrole_set.filter(role=editor_role_id)\
                                       .exclude(user__last_login=None)\
                                       .order_by("-user__last_login")
            if editors.exists():
                last_editor = editors.first().user
                days_since_login = (today - last_editor.last_login).days
            else:
                last_editor = "No editors have logged in"
                days_since_login = None

            # Incomplete articles that have stalled in a pre-publication stage
            incomplete_articles = j.article_set.filter(stage__in=incomplete_stages)
            incomplete_articles = incomplete_articles.annotate(
                last_action=Max(
                    "workflowlog__timestamp"
                )
            )
            threshold = timedelta(days=int(get_setting(j, "threshold_stalled_days")))
            total_stalled = incomplete_articles.filter(last_action__lte=(today - threshold)).count()

            # Peer-reviewed articles published in the last year
            annual_peer_reviewed = j.article_set.filter(peer_reviewed=True,
                                                    stage="Published",
                                                    date_published__gte=one_year).count()


            # Issues published in the last year
            cadence = j.issue_set.filter(date__lte=today, date__gte=one_year).count()
            publication_frequency = int(get_setting(j, "publication_frequency"))


            values = {"journal": j,
                    "total_unassigned": unassigned_set.count(),
                    "days_unassigned": (today - oldest_date).days,
                    "last_editor": last_editor,
                    "days_since_login": days_since_login,
                    "login_threshold": login_threshold,
                    "total_stalled": total_stalled,
                    "annual_peer_reviewed": annual_peer_reviewed,
                    "cadence": cadence,
                    "publication_frequency": publication_frequency}
            
            results.append(values)

    context = {'plugin_name': PLUGIN_NAME,
               'results': results}
    return render(request, template, context)


    # count stalled articles and time since last review completed
    # threshold_post_review_days
    # stalled_articles = ReviewRound.objects\
    #     .filter(article__stage="Under Review")\
    #     .exclude(reviewassignment__is_complete=False)\
    #     .values_list("article", flat=True).distinct()
    # stalled_reviews = Journal.objects\
    #     .annotate(
    #         stalled_reviews=Count(
    #             "article",
    #             filter=Q(article__in=stalled_articles),
    #         )
    #     )

