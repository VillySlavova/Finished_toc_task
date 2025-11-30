import threading
from django.utils import timezone

import whois

from .models import Collector, Contact


def _append_log(collector: Collector, message: str):
    #Appends a timestamped message to the collector log.
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}\n"
    collector.log = (collector.log or "") + line
    collector.save(update_fields=["log"])


def start_whois_for_domain(domain):
    collector, created = Collector.objects.get_or_create(
        domain=domain,
        type='whois',
        defaults={
            "status": "pending",
            "enabled": True,
            "stop_requested": False,
        }
    )
    if not collector.enabled:
        return collector
    _start_whois_thread(collector.id)
    return collector


def start_whois_for_existing_collector(collector: Collector):
    #Starts an existing WHOIS collector from the Collectors page.
    if not collector.enabled:
        return
    _start_whois_thread(collector.id)


def _start_whois_thread(collector_id: int):
    thread = threading.Thread(
        target=_whois_worker,
        args=(collector_id,),
        daemon=True,
    )
    thread.start()


def _whois_worker(collector_id: int):
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
    _append_log(collector, f"WHOIS collector started for {domain_name}")

    try:
        data = whois.whois(domain_name)
    except Exception as e:
        _append_log(collector, f"WHOIS lookup failed: {e}")
        collector.status = 'failed'
        collector.finished_at = timezone.now()
        collector.save(update_fields=["status", "finished_at"])
        return

    try:
        emails = set()
        phones = set()

        raw_emails = getattr(data, "emails", None)
        if isinstance(raw_emails, str):
            emails.add(raw_emails.strip())
        elif isinstance(raw_emails, (list, tuple, set)):
            for e in raw_emails:
                if e:
                    emails.add(str(e).strip())

        raw_phone = getattr(data, "phone", None)
        if isinstance(raw_phone, str):
            phones.add(raw_phone.strip())
        elif isinstance(raw_phone, (list, tuple, set)):
            for p in raw_phone:
                if p:
                    phones.add(str(p).strip())

        _append_log(collector, f"WHOIS found {len(emails)} emails and {len(phones)} phones.")

        for email in emails:
            Contact.objects.get_or_create(
                domain=collector.domain,
                email=email,
                phone=None,
                source_collector=collector,
            )

        for phone in phones:
            Contact.objects.get_or_create(
                domain=collector.domain,
                email=None,
                phone=phone,
                source_collector=collector,
            )

        collector.status = 'finished'
        collector.finished_at = timezone.now()
        collector.save(update_fields=["status", "finished_at"])
        _append_log(collector, "WHOIS collector finished successfully.")

    except Exception as e:
        _append_log(collector, f"WHOIS processing failed: {e}")
        collector.status = 'failed'
        collector.finished_at = timezone.now()
        collector.save(update_fields=["status", "finished_at"])