import yad
import sys
import subprocess
from add_card import add_image_card
from linguee_query import ask,extract_info
import argparse

yad=yad.YAD()
path="/home/david/gen_ank/"





def yad_args(path,search_term,folder,word_type,gender,synonyms,examples,images):
    front=""
    article_list=["el","la","-"]
    if word_type=="noun":
        if gender=="m":
            front="el "
            article_list[0]="^"+article_list[0]
        elif gender=="f":
            front="la "
            article_list[1]="^"+article_list[1]
        else:
            article_list[2]="^"+article_list[2]
    article_list=["el","la","-"]
    main_buttons=[
        ["CB","Article",article_list],
        ["","Word or Phrase:",search_term],
        ["","Type:",word_type]]
        
    syn_buttons = [["CHK","Synonym: "+syn,"false"] for syn in synonyms]
    
    example_buttons=[["CHK","Example: "+ex,"true"] for ex in examples]
    
    im_buttons=[["BTN",['',path+folder+"/"+im],
                 "bash -c \"cd %s; cp \"%s\" %s.jpg \""%(path,folder+"/"+im,folder)]for im in images]
    
    #for i in im_buttons:
        #print(i)
    return main_buttons+syn_buttons+example_buttons+im_buttons



import sys, re, goslate
import requests
from bs4 import BeautifulSoup


def get_soup_object(url):
	return BeautifulSoup(requests.get(url).text)


def synonyms(word):
    url="http://www.wordreference.com/sinonimos/%s"%(word)
    soup=get_soup_object(url)
    results=soup.find_all(class_="trans clickable")[0].find_all("li")[0]
    return results.text

def html_list(str_list):
    start="<ul>\n"
    end="</ul>\n"
    middle=["<li type=\"square\">"+item+"</li>\n" for item in str_list]
    ret_str=start+"".join(middle)+end
    return ret_str



class Query:

    def __init__(self, search_term="gato negro",
                 Type="noun",
                 gender="m",
                 response=["Miau!"],
                 audio_link="ES_ES/70/70b783251225354e883a5bef3c011843-106",
                 audio_file_name="gato.mp3",
                 audio_base_url="http://www.linguee.de/mp3/%s.mp3",
                 examples=["Mi gato es negro.","Mi gato es verde."],
                 linguee_query_url="https://linguee-api.herokuapp.com/api?q=%s&src=es&dst=%s",
                 synonyms=[]
                ):
        self.search_term = search_term.strip()
        self.folder=self.search_term.replace(" ","_")
        self.type = Type
        self.gender=gender
        self.response = response
        self.audio_link=audio_link
        self.audio_file_name=audio_file_name
        self.examples=examples
        self.audio_base_url=audio_base_url
        self.linguee_query_url=linguee_query_url
        self.synonyms=synonyms
        self.front=self.search_term


    def linguee_query(self):
        self.word_or_phrase()
        qry_str=self.search_term.replace(" ","+")
        #print(qry_str)
        self.response=ask(qry_str)
        print(extract_info(self.response))
        #print(ask(qry_str))
        if self.type=="phrase":
            #print("phrase",qry_str)
            self.audio_link,b,c,self.examples=extract_info(self.response)
        else:
            self.audio_link,self.word_type,self.gender,self.examples=extract_info(self.response)
        #response=html_response
        #change languages
        #yad: Let user know if not possible to connect
        #yad: Let user know if no matches
    
    def word_or_phrase(self):
        #single word or phrase?
        if " " in self.search_term:
            #print("SPACE")
            self.type="phrase"

    def print_all(self):
        print("-----------------------------------------------")
        print("Search term: %s"%self.search_term)
        print("Folder: %s"%self.folder)
        print("Type : %s"%self.type)
        print("Synonyms: %s"%self.synonyms)
        #print("Response: %s"%self.response[0])
        print("Audio Link: %s"%self.audio_link)
        print("Audio File Name:%s"%self.audio_file_name)
        print("Example:%s"%self.examples)
        print("-----------------------------------------------")


    def download_images(self):
        print("Downloading images...")
        subprocess.call(["~/Schreibtisch/my_image_download %s"%self.search_term],shell=True)
        print("Downloading finished.")

    def set_synonyms(self):
        self.synonyms=synonyms(self.search_term).split(",")
    
    def download_audio(self):
        audio_url=self.audio_base_url%self.audio_link
        print("Downloading sound...")
        subprocess.call(["~/Schreibtisch/my_audio_download %s %s"%(self.folder,audio_url)],shell=True)
        print("Download finished.")
    
    def check_attributes(self,path):
        #starts yad to let user check stuff
        user_input=yad.Form(center=1,on_top=1,scroll=1,fullscreen=1,
                fields=yad_args(path=path,
                                search_term=self.search_term,
                                folder=self.folder,
                                word_type=self.type,
                                gender=self.gender,
                                synonyms=self.synonyms,
                                images=["1.jpg","2.jpg","3.jpg"],
                                examples=self.examples
                               )
                           )
        if user_input==None:
            return False
            print("Abbruch")
            #exit()
        elif user_input["rc"]==0:
            user_input.pop("rc")
            print(user_input)
        else:
            print("Abbruch")
            return False
            #exit()

        #change mistakes
        if user_input[0]!="":
            self.front=user_input[0]+" "+user_input[1]
        sl=len(self.synonyms)
        el=len(self.examples)
        for i in reversed(range(sl)):
            #print(i+3)
            if user_input[i+3]=="FALSE":
                del self.synonyms[i]
        for i in reversed(range(el)):
            if user_input[i+3+sl]=="FALSE":
                del self.examples[i]
            #print(i+3+sl)

        #{0: 'el', 1: 'gato negro', 2: 'noun', 3: 'FALSE', 4: 'FALSE',
        # 5: 'FALSE', 6: 'FALSE', 7: 'FALSE', 8: 'FALSE', 9: 'FALSE', 10: '', 11: '', 12: ''}
    
    def mark_examples(self):
        for word in self.search_term.split(" "):
            self.examples=[ex.replace(word,"<font color=red><b>"+word+"</font></b>") for ex in self.examples]
    
    def generate_card(self):
        syn_str=", ".join(self.synonyms)
        ex_str=html_list(self.examples)
        add_image_card(word=self.front,
                       file=self.folder,
                       synonyms=syn_str,
                       examples=ex_str)
                           
    
    def get_all_data(self,path):
        self.linguee_query()
        self.set_synonyms()
        self.mark_examples()
        self.download_audio()
        self.download_images()
        self.print_all()
        self.check_attributes(path)
        self.print_all()
        
    def import_card_to_deck(self):
        print("Importing Card to Deck")
        subprocess.call(["bash -c \"anki -p new /home/david/gen_ank/output.apkg \" "],shell=True)
        print("Download finished.")
    
        
        
def main(search_term):
    cat=Query(search_term)
    cat.get_all_data(path)
    cat.generate_card()
    cat.import_card_to_deck()
#cat.generate_card()

#cat.set_synonyms()

#cat.print_all()
#cat.download_images()
#cat.download_audio()
#cat.check_attributes(path)
#cat.check_attributes(path)
#cat.check_attributes(path)

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Adds Anki card to test_deck")

    parser.add_argument('--word', type=str, help="the search word")


    args = parser.parse_args()
    search_term=args.word

   # stuff only to run when not called via 'import' here
    main(search_term)