Word Processing
========================================

The main object for the card generation is the :class:`templates.Template`, which contains a number of
:class:`parsers.Parser`\ s and :class:`fields.Field`\ s.
Each parser fetches data in some form.
Each field uses a part of this data to do one or more of the following:

    * process the data
    * display the data to the user
    * let the user make a choice or edit the data

If the :meth:`templates.Template.get_results` is called, each field returns a dict that is then merged into one.

This one dict should contain values for each field of the anki card that should be generated.

Feel free to define your own :class:`template.Template`\ s by the following steps:

    * inherit from :class:`templates.Template`
    * define parsers and fields
    * (customize further if you like)
    * add template to database to make it available in the app

.. toctree::
   :maxdepth: 2
   :glob:

   word_processing/*
