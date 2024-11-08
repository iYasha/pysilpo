===========
Get Started
===========

.. _installation:

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

   from pysilpo import User, Cheque
    from datetime import datetime

    user = (
        User(
            phone_number="+380123456789",
        )
        .request_otp()
        .login()
    )

    cheques = Cheque(user).get_all(
        date_from=datetime(2024, 7, 19), date_to=datetime(2024, 8, 19)
    )

    for cheque in cheques:
        print(cheque.sum_balance)
        print(cheque.detail.positions)
