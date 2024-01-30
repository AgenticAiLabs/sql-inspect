from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=50)
    is_digital = models.BooleanField(default=False)

    def __str__(self):
        return self.name
