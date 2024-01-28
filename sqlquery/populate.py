# -*- coding: utf-8 -*-
"""
populates the product table with 200 product records

How to run code:
1) run as part of init files
2) import and run `PopulateProduct` function in django shell

"""

from .factory import ProductFactory
from .models import Product


def PopulateProduct():
    """insert 200 product records into product table"""

    ProductFactory.create_batch(200)
    records = Product.objects.all()

    print(f"Number of records inserted: {records.count()}")
