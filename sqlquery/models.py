from django.db import models


class Product(models.Model):
    # id = models.BigIntegerField(primary_key=True, unique=True)
    product_name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    is_digital = models.BooleanField(default=False)

    def __str__(self):
        return self.product_name
