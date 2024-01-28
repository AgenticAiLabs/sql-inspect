import random
import factory
from factory.faker import faker
from .models import Product

FAKE = faker.Faker()


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    product_name = factory.Faker("sentence", nb_words=5)
    slug = factory.Faker("slug")
    is_digital = random.choice([True, False])
