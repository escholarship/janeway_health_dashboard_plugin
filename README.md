# Janeway Journal Health Dashboard
Janeway plugin that displays key journal health indicators

## Indicators

- Stale unassigned articles: Number of articles that have been in in the "Unassigned" stage for more than `threshold_unassigned_days`
- Last editor login: the name of the last editor to log in and how many days since they logged in (flagged more than `threshold_login_days`)
- Articles stalled after reviews: Number of articles that are still in status "Under Review" after all reviews have been complete for more than `threshold_review_days`
- Stalled articles: Number of articles in incomplete stages that have been there more than `threshold_stalled_days`
- Annual peer-reviewed articles: Count of peer-reviewed articles published in the last year (flagged less than 5)
- Issues in last year: Total issues published in the last year (flagged if less than `publication_frequency`)
