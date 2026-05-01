from django.db import models


class Meeting(models.Model):
    title = models.CharField(max_length=180)
    date = models.DateField()
    time = models.CharField(max_length=16, blank=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return self.title
