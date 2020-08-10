User Interface
========================================

The user interface is based on :mod:`kivy` and :mod:`kivymd`.

.. image:: ../screenshots/nav_drawer_open.png
   :width: 200
.. image:: ../screenshots/word_1.png
   :width: 200
.. image:: ../screenshots/word_2.png
   :width: 200
.. image:: ../screenshots/import.png
   :width: 200


The project is organized as follows:
Each screen of the app is defined by a screens/<screen_name>.kv file. The root widget of the screen is named
<ScreenNameRoot> and implemented in the file screens/<screen_name>.py.

.. toctree::
   :maxdepth: 1
   :glob:

   screens/*
