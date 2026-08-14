# wedding-agency
A Django-based platform for booking musicians, caricaturists, photographers, and other wedding vendors

## Built-In Analytics (Simple, No Extra Tools)

The project now captures lightweight funnel analytics without requiring external services.

### Where to view analytics

- Django Admin dashboard top cards (includes 7-day funnel summary, 24h trend, and vendor-type split).
- `Bookings > Funnel events` in Django admin for raw event logs.

### Events captured

- `vendor_card_click`
- `check_availability_click`
- `multi_enquiry_click`
- `enquiry_submit`

### Recommended weekly checks (10 minutes)

1. Review `Avail -> enquiry rate` on the admin dashboard.
2. Compare `Last 24h submits` vs `Prev 24h` for momentum.
3. Check vendor-type split to spot weaker categories.

### Keep it lean

- Do not add extra analytics scripts until this data is being reviewed consistently.
- If conversion drops, start with copy/CTA/date-filter improvements before major feature work.

### Weekly operating checklist

- See [docs/weekly-growth-checklist.md](docs/weekly-growth-checklist.md) for a simple 10-15 minute weekly routine.

## Daily Review Request Scheduler

Set up a daily scheduler entry to send post-event review request emails:

```bash
python3 manage.py send_review_requests
```

Example cron entry (runs every day at 09:00 server time):

```cron
0 9 * * * cd /workspaces/wedding-agency && /usr/bin/python3 manage.py send_review_requests
```
