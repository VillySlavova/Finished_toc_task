from django.db import models


class Domain(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Collector(models.Model):
    TYPE_CHOICES = [
        ('scraper', 'Scraper'),
        ('whois', 'WHOIS'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('finished', 'Finished'),
        ('failed', 'Failed'),
        ('stopped', 'Stopped'),
    ]

    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name='collectors',
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    enabled = models.BooleanField(default=True)
    stop_requested = models.BooleanField(default=False)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    log = models.TextField(blank=True)

    def __str__(self):
        return f"{self.get_type_display()} for {self.domain.name}"
class Contact(models.Model):
    domain = models.ForeignKey(
        Domain,
        on_delete=models.CASCADE,
        related_name='contacts'
    )

    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    source_collector = models.ForeignKey(
        Collector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='found_contacts'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email or self.phone} for {self.domain.name}"
