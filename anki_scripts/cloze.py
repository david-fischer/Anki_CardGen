
import yad
import re
from add_card import add_cloze_card



#x=["^","val1","val2","val3"]

#phrase="Me di cuenta de inmediato que estaba preocupada y triste."
#words=["^"]+phrase.split()


yad=yad.YAD()
#?yad.Form

#x = (
#     ("LBL",""),
#     ("CBE","",words),
#     ("CBE","",words),
#     ("CBE","",words),
#     ("LBL",phrase),
#     ("","Hint:",""),
#     ("","Hint:",""),
#     ("","Hint:",""),
     #("H","Hidden label","Hidden text"),
     #("NUM","Numeric",(0,0,100,1,2)),
     #("CB","Combo box",("val1","^val2","val3")),
     #("CBE","Editable Combo box",("val1","^val2","val3")),
     #("FL","Select a file",""),
     #("DIR","Select Directory",""),
     #("CDIR","Create Directory",""),
     #("FN","Select Font",("Sans","Regular","12")),
     #("MFL","Select Multiple files",""),
     #("DT","Date",""),
     #("SCL","Scale",""),
     #("CLR","Color Palette",""),
     #"TXT","Multi-line text entry",""),
     #"CHK","Checkbox","true"),
     #"BTN",("gtk-ok","","OK"),"echo hi"),
#)

#user_input=yad.Form(fields=x,columns=2,title="Phrase")#,selectable_labels=1,focused=3)

#editor = "This is result of the match"
#new_editor = re.sub(r"\bresult\b","resultado",editor)
#print(new_editor)
#newest_editor = re.sub(r"\bresult\b","resultado",new_editor)
#print(newest_editor)


def add_cloze_del(phrase,word,hint,number):
    #word=user_input[i+1]
    if word!="":
        #print(word)
        #hint=user_input[i+5]
        replace_string="<font color=\"blue\"> <b> {{c%s::%s:: %s }} </b></font>"%(number,word,hint)
        reg_exp=r"\b%s\b"%word
        #print(reg_exp)
        phrase=re.sub(reg_exp,replace_string,phrase)
    return phrase

def get_cloze_phrase(phrase):
    words=["^"]+[word.strip(",;.?!\"\'") for word in phrase.split()]
    x = (
     ("LBL",""),
     ("CBE","",words),
     ("CBE","",words),
     ("CBE","",words),
     ("TXT","",phrase),
     ("","Hint:",""),
     ("","Hint:",""),
     ("","Hint:",""),
    )
    
    user_input=yad.Form(fields=x,columns=2,title="Phrase")
    phrase=user_input[4]
    #print(phrase)
    for i in range(1,4):
        word=user_input[i]
        hint=user_input[i+4]
        phrase=add_cloze_del(phrase,word,hint,i)

    return phrase
