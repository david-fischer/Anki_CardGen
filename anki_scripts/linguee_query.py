import warnings
warnings.filterwarnings('ignore')
import requests
import itertools

languages=itertools.cycle(("de","en","es","pt","it","fr","el"))
#languages=itertools.cycle(("en","el","es","de","pt","it"))
#itertools.cycle(("en", "el", "es","bg", "cs", "da","de", "et", "fi", "fr",
          #                     "hu", "it", "ja", "lt", "lv", "mt", "nl", "pl", "pt", "ro",
          #                     "ru", "sk", "sl", "sv", "zh"))

#linguee_api_url="https://linguee-api.herokuapp.com/api?q=%s&src=es&dst=%s"




def ask_once(qry_str,lang,try_no,linguee_api_url):
    print("querying ... (Language: %s)"%lang)
    data=requests.get(linguee_api_url%(qry_str,lang))
    print(data.status_code)
    #print(data.json())
    if data.status_code==200:
        #print(data.json())
        if data.json()["exact_matches"]==None:
            lang=next(languages)
            return ask_once(qry_str,lang,try_no+1,linguee_api_url)
        return data.json()
    if data.status_code==500:
        lang=next(languages)
        if try_no==20:
            return {"exact_matches":None}
        else:
            return ask_once(qry_str,lang,try_no+1,linguee_api_url)
        
        
def extract_info(response):
    if response["exact_matches"]!=None:
        examples=[]
        match=response["exact_matches"][0]
        audio_id=match["audio_links"][0]["url_part"]
        word_type=match["word_type"]["pos"]
        if word_type=="noun":
            gender=match["word_type"]["gender"][0]
        else:
            gender=""
        examples=[]
        real_ex=[x["src"] for x in response["real_examples"]]#.sort(key = lambda s: len(s))
        for key in match["translations"]:
            try:
                examples.append(key["examples"][0]["source"])
            except:
                pass
        examples=list(set(examples))
        i=len(examples)
        for x in real_ex:
            if(len(x)<150):
                examples.append(x)
                i+=1
            if i==3:
                break
        return audio_id,word_type,gender,examples
    
        
def ask(qry_str,linguee_api_url):
    languages=itertools.cycle(("de","en","es","pt","it","fr","el"))
    return ask_once(qry_str,"de",0,linguee_api_url)
        


