import re
import os


selection = os.popen("xsel -o").read()
empty="_"*len(selection)

paste_string = "{{c1::%s::%s}}"%(selection,empty)

os.popen("echo \"%s\" | tr -d '\n' | xsel -bi" %paste_string)


os.popen('''xdotool key 'ctrl+v'
xdotool key 'Left'
xdotool key 'Left'
xdotool key 'ctrl+shift+Left' ''')




