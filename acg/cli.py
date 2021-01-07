"""
This is the entry-point for pyinstaller.

It makes sure that the script is called from the right path,
such that the settings file ``ankicardgen.ini`` is placed in the folder of the main script as opposed to the folder
from which the script is called.
"""

from . import BASE_PATH
from .main import main
from .utils import CD

with CD(BASE_PATH):
    main()
