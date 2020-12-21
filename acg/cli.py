"""
This is the entry-point for pyinstaller.

It makes sure that the script is called from the right path,
such that the settings file ``ankicardgen.ini`` is placed in the folder of the main script as opposed to the folder
from which the script is called.
"""

from .main import main
from .paths import MAIN_DIR
from .utils import CD

with CD(MAIN_DIR):
    main()
