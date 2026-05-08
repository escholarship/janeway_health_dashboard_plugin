from django.db import models

from journal.models import Journal

class Category(models.Model):
    label = models.CharField(max_length=50)

    def __str__(self):
        return self.label

class JournalCategory(models.Model):
    journal = models.ForeignKey(Journal, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.journal}: {self.category}"
