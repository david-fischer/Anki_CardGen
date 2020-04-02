
from bs4 import BeautifulSoup
from collections import defaultdict
import argparse
from os.path import splitext
from more_itertools import unique_everseen






def main(file_name):
    
    
    mark_dict={"Gelb":"words","Blau":"phrases","Pink":"short_phrases"}
    infile=open(file_name)

    soup=BeautifulSoup(infile,"lxml")
    infile.close()
    file_name=splitext(file_name)[0]+"_"
    #print(file_name)

    headings=soup.find_all(class_="noteHeading")
    contents=soup.find_all(class_="noteText")

    colors=[heading.find("span").text for heading in headings]
    contents=[content.text.strip() for content in contents]

    two_d_list=[(colors[i],contents[i]) for i in range(len(headings))]

    d = defaultdict(list)
    for k, v in two_d_list:
        d[k].append(v)

    
    
    d["Gelb"]=[word.strip(",.;:-–—!?¿¡\"\'")for word in d["Gelb"]]

    for x in d:
        d[x]=list(unique_everseen(d[x]))
        d[x]=[word+"\n" for word in d[x]]



    for x in d:
        file=open(file_name+mark_dict[x]+".txt","w")
        file.writelines(d[x])
        file.close()

    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Extracts words from Kindle markings.")

    parser.add_argument('--file', type=str, help="/path/to/file.ext")
    #parser.add_argument('--dict', type="", help="the url of the api")
    

    args = parser.parse_args()
    file_name=args.file
    
    main(file_name)
