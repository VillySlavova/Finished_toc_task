import re
import threading
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.utils import timezone
from django.db import transaction

from .models import Collector, Contact


EMAIL_REGEX = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
PHONE_REGEX = re.compile(r'\+?\d[\d\s\-\(\)]{6,}')

TIMEOUT = 5
MAX_PAGES = 50  # safety limit so we don't crawl forever


def _append_log(collector: Collector, message: str):
    """Append a timestamped message to the collector log."""
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    collector.log = (collector.log or "") + line
    collector.save(update_fields=["log"])


def start_scraper_for_domain(domain):
    collector = Collector.objects.create(
        domain=domain,
        type='scraper',
        status='pending',
        enabled=True,
        stop_requested=False,
    )
    _start_scraper_thread(collector.id)
    return collector


def start_scraper_for_existing_collector(collector: Collector):
    if not collector.enabled:
        return
    _start_scraper_thread(collector.id)


def _start_scraper_thread(collector_id: int):
    thread = threading.Thread(
        target=_scraper_worker,
        args=(collector_id,),
        daemon=True,
    )
    thread.start()


def _scraper_worker(collector_id: int):
    collector = Collector.objects.select_related("domain").get(id=collector_id)

    if not collector.enabled:
        return

    collector.status = 'running'
    collector.started_at = timezone.now()
    collector.finished_at = None
    collector.stop_requested = False
    collector.save(update_fields=[
        "status", "started_at", "finished_at", "stop_requested"
    ])

    domain_name = collector.domain.name.strip()
    _append_log(collector, f"Scraper started for {domain_name}")

    # BFS crawl
    visited = set()
    to_visit = []
    contacts_found = set()

    # try both http and https as starting points
    for scheme in ("http", "https"):
        to_visit.append(f"{scheme}://{domain_name}")

    try:
        while to_visit and len(visited) < MAX_PAGES:
            # reload collector to see stop flag
            collector = Collector.objects.get(id=collector_id)
            if collector.stop_requested:
                _append_log(collector, "Stop requested. Exiting scraper.")
                collector.status = 'stopped'
                collector.finished_at = timezone.now()
                collector.save(update_fields=["status", "finished_at"])
                return

            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            _append_log(collector, f"Fetching {url}")

            try:
                resp = requests.get(url, timeout=TIMEOUT)
            except Exception as e:
                _append_log(collector, f"Request failed: {e}")
                continue

            # stay inside the same domain
            parsed = urlparse(url)
            if domain_name not in parsed.netloc:
                continue

            html = resp.text

            # extract emails and phones
            emails = EMAIL_REGEX.findall(html)
            phones = PHONE_REGEX.findall(html)

            for email in emails:
                contacts_found.add(("email", email.strip()))
            for phone in phones:
                contacts_found.add(("phone", phone.strip()))

            # find links to crawl further
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a["href"])
                if next_url not in visited:
                    to_visit.append(next_url)

        _append_log(collector, f"Saving {len(contacts_found)} contacts to database.")

        with transaction.atomic():
            for ctype, value in contacts_found:
                if not value:
                    continue
                if ctype == "email":
                    Contact.objects.get_or_create(
                        domain=collector.domain,
                        email=value,
                        phone=None,
                        source_collector=collector,
                    )
                elif ctype == "phone":
                    Contact.objects.get_or_create(
                        domain=collector.domain,
                        email=None,
                        phone=value,
                        source_collector=collector,
                    )

        collector = Collector.objects.get(id=collector_id)
        collector.status = 'finished'
        collector.finished_at = timezone.now()
        collector.save(update_fields=["status", "finished_at"])
        _append_log(collector, "Scraper finished successfully.")

    except Exception as e:
        collector = Collector.objects.get(id=collector_id)
        collector.status = 'failed'
        collector.finished_at = timezone.now()
        collector.save(update_fields=["status", "finished_at"])
        _append_log(collector, f"Scraper failed with error: {e}")