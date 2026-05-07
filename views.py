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

@login_required
def dashboard(request):
    template = "health_dashboard/dashboard.html"

    today = timezone.now()
    one_year = today - timedelta(days=365)
    editor_role_id = Role.objects.get(name="Editor").id

    results = []
    for j in Journal.objects.all():
        included = j.get_setting(
            group_name="plugin:health_dashboard",
            setting_name="dashboard_include",
        )
        if included:
            unassigned_threshold = int(j.get_setting(
                group_name="plugin:health_dashboard",
                setting_name="threshold_unassigned_days",
            ))
            d = today - timedelta(days=unassigned_threshold)
            unassigned_set = j.article_set.filter(stage="Unassigned",
                                                date_submitted__lte=d)\
                                        .order_by("date_submitted")
            oldest_date = unassigned_set.first().date_submitted if unassigned_set.exists() else today
            login_threshold = int(j.get_setting(
                group_name="plugin:health_dashboard",
                setting_name="threshold_login_days",
            ))


            editors = j.accountrole_set.filter(role=editor_role_id)\
                                        .exclude(user__last_login=None)\
                                        .order_by("-user__last_login")
            if editors.exists():
                last_editor = editors.first().user
                days_since_login = (today - last_editor.last_login).days
            else:
                last_editor = "No editors have logged in"
                days_since_login = None

            incomplete_articles = j.article_set.filter(stage__in=incomplete_stages)
            incomplete_articles = incomplete_articles.annotate(
                last_action=Max(
                    "workflowlog__timestamp"
                )
            )
            threshold = timedelta(days=int(j.get_setting(
                group_name="plugin:health_dashboard",
                setting_name="threshold_stalled_days",
            )))
            total_stalled = incomplete_articles.filter(last_action__lte=(today - threshold)).count()

            annual_peer_reviewed = j.article_set.filter(peer_reviewed=True,
                                                    stage="Published",
                                                    date_published__gte=one_year).count()

            cadence = j.issue_set.filter(date__lte=today, date__gte=one_year).count()
            publication_frequency = int(j.get_setting(
                group_name="plugin:health_dashboard",
                setting_name="publication_frequency",
            ))


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

