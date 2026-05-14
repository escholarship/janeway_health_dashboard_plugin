from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from django.db.models import Count
from django.db.models import Max
from django.db.models import Q

from journal.models import Journal
from core.models import Role, SettingValue
from submission.models import Article

from .plugin_settings import PLUGIN_NAME
from .models import JournalCategory
from .forms import CategorySelectForm

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

def get_setting(journal_settings, default_settings, name):
    if name in journal_settings:
        return journal_settings[name]
    return default_settings[name]

@login_required
def dashboard(request):
    template = "health_dashboard/dashboard.html"

    today = timezone.now()
    one_year = today - timedelta(days=365)
    editor_role_id = Role.objects.get(name="Editor").id

    # categories = request.GET.get("categories", [])
    # if len(categories):
    #     form = CategorySelectForm(request.GET)
    #     journal_ids = JournalCategory.objects.filter(category__in=categories)\
    #                                          .values_list("journal__pk", flat=True)\
    #                                          .distinct()
    #     journals = Journal.objects.filter(pk__in=journal_ids)
    # else:
    #     form = CategorySelectForm()

    default_settings = {
        x: y for x, y in SettingValue.objects.filter(
                            journal=None,
                            setting__group__name="plugin:health_dashboard")\
            .values_list("setting__name", "value")
    }

    results = []
    for j in Journal.objects.all():
        journal_settings = {
            x: y for x, y in SettingValue.objects.filter(
                                journal=j,
                                setting__group__name="plugin:health_dashboard")\
                .values_list("setting__name", "value")
        }
        if get_setting(journal_settings, default_settings, "dashboard_include"):
            # Unassigned articles
            unassigned_threshold = int(get_setting(journal_settings,
                                                   default_settings,
                                                   "threshold_unassigned_days"))
            d = today - timedelta(days=unassigned_threshold)
            unassigned_set = j.article_set.filter(stage="Unassigned",
                                                date_submitted__lte=d)\
                                          .order_by("date_submitted")
            oldest = unassigned_set.first()
            oldest_date = oldest.date_submitted if oldest else today

            # Last editor login
            login_threshold = int(get_setting(journal_settings,
                                              default_settings,
                                              "threshold_login_days"))
            j.accountrole_set.select_related("user")
            editors = j.accountrole_set.filter(role=editor_role_id)\
                                       .exclude(user__last_login=None)\
                                       .order_by("-user__last_login")
            last_editor_role = editors.first()
            if last_editor_role:
                last_editor = last_editor_role.user
                days_since_login = (today - last_editor.last_login).days
            else:
                last_editor = "No editors have logged in"
                days_since_login = None

            reviews_threshold = today - timedelta(days=int(get_setting(journal_settings,
                                                                       default_settings,
                                                                       "threshold_review_days")))
            stalled_after_reviews = Article.objects.filter(
                journal=j,
                stage="Under Review",
            ).annotate(
                incomplete_reviews=Count(
                    "reviewassignment",
                    filter=Q(reviewassignment__is_complete=False)
                ),
                last_complete=Max("reviewassignment__date_complete"),
            ).filter(
                incomplete_reviews=0,
                last_complete__lte=reviews_threshold,
            ).count()

            # Incomplete articles that have stalled in a pre-publication stage
            incomplete_articles = j.article_set.filter(stage__in=incomplete_stages)
            incomplete_articles = incomplete_articles.annotate(
                last_action=Max(
                    "workflowlog__timestamp"
                )
            )
            threshold = timedelta(days=int(get_setting(journal_settings,
                                                       default_settings,
                                                       "threshold_stalled_days")))
            total_stalled = incomplete_articles.filter(last_action__lte=(today - threshold)).count()

            # Peer-reviewed articles published in the last year
            annual_peer_reviewed = j.article_set.filter(peer_reviewed=True,
                                                        stage="Published",
                                                        date_published__gte=one_year).count()


            # Issues published in the last year
            cadence = j.issue_set.filter(date__lte=today, date__gte=one_year).count()
            publication_frequency = int(get_setting(journal_settings,
                                                    default_settings,
                                                    "publication_frequency"))


            values = {
                "journal": j,
                "total_unassigned": unassigned_set.count(),
                "days_unassigned": (today - oldest_date).days,
                "last_editor": last_editor,
                "days_since_login": days_since_login,
                "login_threshold": login_threshold,
                "total_reviews_stalled": stalled_after_reviews,
                "total_stalled": total_stalled,
                "annual_peer_reviewed": annual_peer_reviewed,
                "cadence": cadence,
                "publication_frequency": publication_frequency,
                "categories": ", ".join(j.journalcategory_set.values_list('category__label', flat=True))
            }
            
            results.append(values)

    context = {'plugin_name': PLUGIN_NAME,
               #'form': form,
               'results': results}
    return render(request, template, context)
