from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from .forms import AddSiteForm
from .models import Domain, Collector, Contact
from .scraper_collector import (
    start_scraper_for_domain,
    start_scraper_for_existing_collector,
)
from .whois_collector import (
    start_whois_for_domain,
    start_whois_for_existing_collector,
)


@login_required
def home_redirect(request):
    return redirect("add_site")


def is_collector_type_enabled(collector_type: str) -> bool:
    qs = Collector.objects.filter(type=collector_type)
    if not qs.exists():
        return True
    return qs.filter(enabled=True).exists()


@login_required
def add_site(request):
    message = None

    if request.method == "POST":
        form = AddSiteForm(request.POST)
        if form.is_valid():
            domain_name = form.cleaned_data["domain"]
            domain, created = Domain.objects.get_or_create(name=domain_name)

            if created:
                # start scraper only if scraper collectors are enabled
                if is_collector_type_enabled("scraper"):
                    start_scraper_for_domain(domain)

                # start whois only if whois collectors are enabled
                if is_collector_type_enabled("whois"):
                    start_whois_for_domain(domain)

                message = f"Domain {domain_name} was added and collectors were started."
            else:
                message = f"Domain {domain_name} already exists."

            # reset form after submit
            form = AddSiteForm()
    else:
        form = AddSiteForm()

    return render(
        request,
        "core/add_site.html",
        {
            "form": form,
            "message": message,
        },
    )


@login_required
def all_contacts(request):
    contacts = Contact.objects.all().order_by("-created_at")

    return render(
        request,
        "core/all_contacts.html",
        {
            "contacts": contacts,
        },
    )


@login_required
def collectors_list(request):
    if request.method == "POST":
        collector_id = request.POST.get("collector_id")
        action = request.POST.get("action")

        try:
            collector = Collector.objects.get(id=collector_id)
        except Collector.DoesNotExist:
            collector = None

        if collector:
            if action == "toggle_enabled":
                collector.enabled = not collector.enabled
                collector.save()

            elif action == "start":
                # real start: spawn a worker thread
                if collector.type == "scraper":
                    start_scraper_for_existing_collector(collector)
                elif collector.type == "whois":
                    start_whois_for_existing_collector(collector)

            elif action == "stop":
                # mark as stop requested; workers check this flag
                collector.stop_requested = True
                collector.status = "stopped"
                collector.save(update_fields=["stop_requested", "status"])

        return redirect("collectors")

    collectors = (
        Collector.objects.select_related("domain")
        .order_by("-started_at", "-id")
    )

    return render(
        request,
        "core/collectors.html",
        {
            "collectors": collectors,
        },
    )