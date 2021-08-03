Chess
=====

.. image:: https://img.shields.io/pypi/v/simplebot_chess.svg
   :target: https://pypi.org/project/simplebot_chess

.. image:: https://img.shields.io/pypi/pyversions/simplebot_chess.svg
   :target: https://pypi.org/project/simplebot_chess

.. image:: https://pepy.tech/badge/simplebot_chess
   :target: https://pepy.tech/project/simplebot_chess

.. image:: https://img.shields.io/pypi/l/simplebot_chess.svg
   :target: https://pypi.org/project/simplebot_chess

.. image:: https://github.com/simplebot-org/simplebot_chess/actions/workflows/python-ci.yml/badge.svg
   :target: https://github.com/simplebot-org/simplebot_chess/actions/workflows/python-ci.yml

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black

A chess game plugin for `SimpleBot`_.
To move use `Standard Algebraic Notation <https://en.wikipedia.org/wiki/Algebraic_notation_(chess)>`_, or `Long Algebraic Notation (without hyphens) <https://en.wikipedia.org/wiki/Universal_Chess_Interface>`_.

If this plugin has collisions with commands from other plugins in your bot, you can set a command prefix like ``/chess_`` for all commands::

  simplebot -a bot@example.com db simplebot_chess/command_prefix chess_

Install
-------

To install run::

  pip install simplebot-chess


.. _SimpleBot: https://github.com/simplebot-org/simplebot
