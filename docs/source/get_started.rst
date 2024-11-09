===========
Get Started
===========

.. _installation_section:

Installation
============

To install ``pysilpo`` use one of the following methods:

Using pip
-----------

You can install ``pysilpo`` with ``pip``:

.. code-block:: bash

   pip install pysilpo

Using Poetry
------------

If you're using Poetry to manage your dependencies, you can add ``pysilpo`` to your project with the following command:

.. code-block:: bash

   poetry add pysilpo

Example
========

Here is a simple example of how to fetch all cheques for a user by date range:

.. code-block:: python

    from pysilpo import Silpo
    from datetime import datetime

    silpo = Silpo(phone_number="+380123456789")

    cheques = silpo.cheque.all(
        date_from=datetime(2024, 7, 19), date_to=datetime(2024, 8, 19)
    )

    for cheque in cheques:
        print(cheque.sum_balance)
        print(cheque.detail.positions)

Get products

.. code-block:: python

    from pysilpo import Silpo

    silpo = Silpo()
    products = silpo.product.all()

    for product in products:
        print(product.title)
