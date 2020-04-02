import re


search_term = "casa"

with open(f"{search_term}/source.txt") as file:
    # thumbnails = [line.split()[-2] for line in file]
    thumbnails = [line.split("\t")[0] for line in file]
    print(thumbnails)