

def yad_args(path,search_term,translated,folder,gender,synonyms,examples):#,images):
    #front=""
    #print(gender)
    article_list=["el","la"," "]
    if gender=="m":
        pass
    elif gender=="f":
        #print("FEMININ")
        article_list[0],article_list[1]=article_list[1],article_list[0]
    else:
        article_list[0],article_list[2]=article_list[2],article_list[0]
        #article_list[2],article_list[0]=article_list[0],article_list[2]
        
    main_buttons=[
        ["TXT","Meaning",translated],
        ["CB","Article",article_list],
        ["","Word or Phrase:",search_term]]
        #["","Type:",word_type]]
        
    #for i in range(len(synonyms)):
    #    synonyms[i]=synonyms[i]+"  -  "+trans_syns[i]
    #print(main_buttons)
    syn_buttons = [["CHK","Synonym: "+syn,"false"] for syn in synonyms]
    
    example_buttons=[["CHK","Example: "+ex,"true"] for ex in examples]    
    #for i in im_buttons:
        #print(i)
    return main_buttons+syn_buttons+example_buttons#+im_buttons

def yad_img_args(path,folder,images):
    im_buttons=[["BTN",['',path+folder+"/"+im],
                 "bash -c \"cd %s; cp \"%s\" %s.jpg;timeout 1 xdotool key \"Escape\" \""%(path,folder+"/"+im,folder)]for im in images]
    return im_buttons



