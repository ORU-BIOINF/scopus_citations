#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function
import pandas as pd
import re
import sys
# matches . , : - ; ' @ and (.*?) 
r = re.compile("[.,:\-;'@]|\(.*?\)")

if len(sys.argv) != 3:
	print("""Usage:
		python scopus_citations.py scopus_file.csv publication_list.txt 
		  """)
	sys.exit(-1)
scopus_file = sys.argv[1]
publication_file = sys.argv[2]
# Read the file exported from Scopus and fix the column names
willem = pd.read_csv(scopus_file,skiprows=range(7))
willem_top = pd.read_csv(scopus_file,skiprows=list(range(6))+list(range(8,10000)))
willem.columns = pd.Index(list(willem.columns[:7]) + list(willem_top.columns[7:]))

# Read the publication list from dirk, titlest start with @ and entries seperated by new line
with open(publication_file,encoding= "ISO-8859-1") as fh:
    lines = list(map(str.strip,fh.readlines()))

# Create a dictionary from Scopus. The key is a tuple of the words in the title, and the value is the total citations for that paper (can be multiple values if multiple titles are the same)
scopus_dict = dict(map(lambda x: (tuple((r.sub(" ",x).lower().split())),willem[willem["Document Title"] == x].total.values),willem["Document Title"]))

# Create a dictionary from publication list where titles start with @. Key is a tuple of the words in the title, value is the line number in the file
titles_dict = {tuple(r.sub(" ",t).lower().split()):i for i,t in enumerate(lines) if t.startswith("@")}

# same_key contains the titles that are in both scopus_dict and titles_dict
same_key = set(scopus_dict.keys()).intersection(set(titles_dict.keys()))

titles = {}
for key in same_key:
    tot = scopus_dict[key]
    if len(tot)!=1: # If multiple entries in scopus have the same tiltle, then tot can be > 1 and we have a problem (ignore now)
        print("{} titles, that will be ignored, found in scopus that match: \"{}\"".format(len(tot)," ".join(key)))
        continue
    tot = tot[0]
    # Remove from scopus and titles dictionaries so thouse dictionaries contain what is not in common.
    scopus = scopus_dict.pop(key)
    title_ind = titles_dict.pop(key)

    # Key is the line number in the publication list, value is the citation count
    titles[title_ind] = str(tot)

# Print titles that did not match
print("\n".join(sorted(map(lambda x: " ".join(x[0]) + " "+str(x[1]),scopus_dict.items()))),file=open("no_match_scopus.txt","w"),sep="\n")
print("\n".join(sorted(map(lambda x: " ".join(x),titles_dict.keys()))),file=open("no_match_publication.txt","w"),sep="\n")

# Print the publication list with citation counts for those entries that were found in Scopus.
p = publication_file.split(".")
base = p[:-1]
f_type = p[-1]
with open(".".join(base +["with_citations",f_type]),"w") as fh:
    should_insert_next_empty = False
    next_cite = ""
    for i,l in enumerate(lines):
        if l.startswith("@"):
            should_insert_next_empty = True
            next_cite = titles.get(i,"")
            if next_cite:
                l = l[1:]
        elif should_insert_next_empty and not l.strip():
            print("Number of citations: {}.".format(next_cite),file=fh)
            should_insert_next_empty = False
        print(l,file=fh)

print("#####SUMMARY#####")
print("# entries in both files: {}".format(len(same_key)))
print("# entries in scopus not found in publication list: {}".format(len(scopus_dict)))
print("# entries in publication list not found in scopus: {}".format(len(titles_dict)))
