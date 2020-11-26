#!/usr/bin/python

##setup
database_username = ""
database_password = ""


##initialization
testing = True

import sys
import os.path
import html
import urllib.parse
import psycopg2
import textwrap

from konlpy.tag import Mecab
mecab = Mecab()
from konlpy.tag import Okt
okt = Okt()

from soylemma import Lemmatizer
lemmatizer = Lemmatizer()

if(not testing):
    if(len(sys.argv) < 2):
        print("Error, no filename specified.")
        sys.exit(1)
    filename = sys.argv[1]
else:
    #filename = os.getcwd() + "/Documents/Korean Learning/korean-english-interlinear/sample.txt"
    filename = os.getcwd() + "/Documents/Korean Learning/shincheong.txt"

if not os.path.exists(filename):
    print("Error, file not found.")
    sys.exit(1)
with open(filename) as f:
    content = f.readlines()
content = [x.strip() for x in content] 


##connect to database and check tables are there
con = psycopg2.connect(database="kenddic", user=database_username, password=database_password, host="localhost")
print("Database opened successfully")
cur = con.cursor()

#sql code to create another table like the main one, this taken from KEngDic:
create_added_table = """CREATE TABLE korean_english_added (
    id SERIAL PRIMARY KEY,
    wordid integer,
    word character varying(130),
    syn character varying(190),
    def text,
    posn integer,
    pos character varying(13),
    submitter character varying(25),
    doe timestamp without time zone,
    wordsize smallint,
    hanja character varying,
    wordid2 integer,
    extradata character varying
);"""

cur.execute("select * from information_schema.tables where table_name=%s", ('korean_english',))
if not bool(cur.rowcount):
    print("Error, database dictionary table missing or not set up.")
    sys.exit(1)

cur.execute("select * from information_schema.tables where table_name=%s", ('korean_english_added',))
if not bool(cur.rowcount):
    cur.execute(create_added_table)
    cur.close()
    con.commit()
    cur = con.cursor()
    cur.execute("select * from information_schema.tables where table_name=%s", ('korean_english_added',))
    if not bool(cur.rowcount):
        print("Error, database added dictionary table missing or not set up.")
        sys.exit(1)


##mecab-ko used by konlpy seems to be using Sejong tagset as seen:
#http://semanticweb.kaist.ac.kr/nlp2rdf/resource/sejong.owl
#summary table here: https://www.aclweb.org/anthology/W12-5201.pdf
#doesn't look like Penn Korean Treebank: ftp://ftp.cis.upenn.edu/pub/ircs/tr/01-09/01-09.pdf
#, http://www.sfu.ca/~chunghye/papers/paclic-tb-paper2.pdf
#,https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
#following I derrived from .owl file from kiast above with additional superclasses (second entried in tuples) from summary table noted above:
SejongTagset = {
    'EC':   ('VerbalEnding',    'Particle'),
    'EF':   ('VerbalEnding',    'Particle'),
    'EP':   ('VerbalEnding',    'Particle'),
    'ETM':  ('VerbalEnding',    'Particle'),
    'ETN':  ('VerbalEnding',    'Particle'),
    'IC':   ('Interjection',    'Interjection'),
    'JC':   ('AuxiliaryPostposition',   'Particle'),
    'JKB':  ('CaseMarker',      'Particle'),
    'JKC':  ('CaseMarker',      'Particle'),
    'JKG':  ('CaseMarker',      'Particle'),
    'JKO':  ('CaseMarker',      'Particle'),
    'JKQ':  ('CaseMarker',      'Particle'),
    'JKS':  ('CaseMarker',      'Particle'),
    'JKV':  ('CaseMarker',      'Particle'),
    'JX':   ('AuxiliaryPostposition', 'Particle'),
    'MAG':  ('GeneralAdverb',   'Adverb'),
    'MAJ':  ('ConjunctiveAdverb', 'Adverb'),
    'MM':   ('Determiner',      'Determiner'),
    'NA':   ('LikelyNoun',      'Noun'),
    'NF':   ('LikelyNoun',      'Noun'),
    'NNB':  ('CommonNoun',      'Noun'),
    'NNG':  ('CommonNoun',      'Noun'),
    'NNP':  ('ProperNoun',      'Noun'),
    'NP':   ('Pronoun',         'Pronoun'),
    'NV':   ('Verb',            'Verb'),
    'SE':   ('Symbol',          'Symbol'),
    'SF':   ('Symbol',          'Symbol'),
    'SH':   ('ForeignWord',     'ForeignWord'),
    'SL':   ('ForeignWord',     'ForeignWord'),
    'SN':   ('CardinalNumber',  'CardinalNumber'),
    'SO':   ('Symbol',          'Symbol'),
    'SP':   ('Symbol',          'Symbol'),
    'SS':   ('Symbol',          'Symbol'),
    'VA':   ('Adjective',       'Verb'),
    'VC':   ('Copula',          'Verb'),
    'VCN':  ('Copula',          'Verb'),
    'VCP':  ('Copula',          'Verb'),
    'VV':   ('VerbalPredicate', 'Verb'),
    'VX':   ('AuxiliaryPredicate', 'Verb'),
    'XN':   ('CardinalNumber',  'CardinalNumber'),
    'XPN':  ('Prefix',          'Particle'),
    'XR':   ('Radical',         'Particle'),
    'XSA':  ('Suffix',          'Particle'),
    'XSN':  ('Suffix',          'Particle'),
    'XSV':  ('Suffix',          'Particle'),
    
    #just added following weird ones I ran into 
    #https://lucene.apache.org/core/7_4_0/analyzers-nori/org/apache/lucene/analysis/ko/POS.Tag.html
    'SC':   ('Separator',       'Symbol'), 
    'SSO':  ('OpeningBracket',  'Symbol'), 
    'SSC':  ('ClosingBracket',  'Symbol'), 
    'SY':   ('OtherSymbol',     'Symbol'), 
    'NR':   ('Numeral',         'Symbol'), 
    'NNBC': ('DependantNoun',   'Noun'), 
    'UNKNOWN': ('UNKNOWN',   'UNKNOWN'), 
}

#https://praacticalaac.org/praactical/how-we-do-it-using-language-boards-to-support-aac-use-by-nerissa-hall-and-hillary-jellison/
#https://alltogether.wordpress.com/2007/09/17/goossens-crain-elder-communication-overlay-color-reminder/
#https://vimawesome.com/plugin/solarized-8
SuperClass_Colours = {
    'Adverb':       '#b78a00',
    'Noun':         'hsl(0, 0%, 20%)',
    'Pronoun':      '#25a399',
    'Verb':         '#cc4a0e',
    'CardinalNumber': 'hsl(0, 0%, 20%)',
    'Determiner':   '#729f01',
    'ForeignWord':  'hsl(0, 0%, 70%)',
    'Interjection': '#cc4a0e',
    'Symbol':       'hsl(0, 0, 20%)',
    'Particle':     '#657b85',
    'UNKNOWN':      'hsl(0, 0, 20%)'
}

def get_sejongtagset_name(tag):
    tag = tag.split("+")[0] #go with first tag if multiple
    if tag in SejongTagset:
        return SejongTagset[tag][0]
    else:
        return ""

def get_sejongtagset_superclass(tag):
    tag = tag.split("+")[0] #go with first tag if multiple
    if tag in SejongTagset:
        return SejongTagset[tag][1]
    else:
        print("Note: can't find " + tag + " in tagset!")
        return ""        

def get_sejongtagset_colour(tag):
    sejong_superclass = get_sejongtagset_superclass(tag)
    if sejong_superclass == "":
        return ""
    return SuperClass_Colours[sejong_superclass]
    
def print_tree(tree, prepend = ""):
    #print("call on: " + str(tree))
    print(prepend + "[")
    for branch in tree:
        #print("operating on branch: " + str(branch))
        if type(branch) == list:
            print_tree(branch, prepend + "\t")
        elif type(branch) == tuple:
            print(prepend + "\t" + " ".join(branch))
        else:
            print(prepend + "error, unexpected branch type" + str(type(branch)))
    print(prepend + "]")    

def get_trans_new_fetch(word, original_word, addition = ""):
    if addition == "":
        comparator = "="
    else:
        comparator = "LIKE"
    cur.execute("SELECT word, TRIM(coalesce(def, '')) AS trans FROM korean_english WHERE word " + comparator + " %s UNION SELECT word, TRIM(coalesce(def, '')) AS trans FROM korean_english_added WHERE word " + comparator + " %s;", (word + addition, word + addition))
    rows = cur.fetchall()   
    if type(rows) is list and len(rows) > 0:
        if addition == "":
            oword_blank_defs = sum( 1 for row in rows if row[0] == original_word and row[1] == "" )
            oword_non_blank_defs = sum( 1 for row in rows if row[0] == original_word and row[1] != "" )
            if oword_non_blank_defs == 0 and oword_blank_defs > 0:
                #then we didn't find any non-blank defs and we did find a blank def
                print("Note, blank dictionary definition for word: " + original_word)
                blank_dictionary_definitions.append(original_word)
            
        return_rows = [
            (
                row[1] if word == original_word else
                " ".join([row[0],row[1]]) 
            )
            for row in rows if row is not None and row[1] != ""
            ]
        if len(return_rows) > 20:
            return "\n".join( return_rows[0:20] ) + "\n..."
        else:
            return "\n".join( return_rows )
    return ""
    
def get_trans_new_recursive(word, original_word):
    #print("Last ditch searching for translation for: " + word)
    if word == "":
        return ""
    translation = get_trans_new_fetch(word, original_word, "")
    if translation != "":
        return translation
    translation = get_trans_new_fetch(word, original_word, "_")
    if translation != "":
        return translation
    # translation = get_trans_new_fetch(word, original_word, "%")
    # if translation != "":
    #     return translation
    return get_trans_new_recursive(word[:-1], original_word)

def get_translation(plain_word):
    if plain_word == "":
        return ""

    #first look up the given word in dictionary
    translation = get_trans_new_fetch(plain_word, plain_word)

    #then try lemmatizing the word one way (returns one), see if in dic
    if translation == "":
        lemmatized_word = okt.pos(plain_word, norm=True, stem=True)
        if type(lemmatized_word) == list and len(lemmatized_word) == 0:
            print("warning, zero length list back from okt for: " + plain_word)
        elif type(lemmatized_word) == list and type(lemmatized_word[0]) == tuple:
            lemmatized_word = lemmatized_word[0][0]
            translation = get_trans_new_fetch(lemmatized_word, plain_word)

    #then try backup lemmatizing method (returns multiple), see if in dic
    if translation == "":
        lemmatized_words = lemmatizer.lemmatize(plain_word)
        for lemmatized_word in lemmatized_words:
            if type(lemmatized_word) == tuple:
                lemmatized_word = lemmatized_word[0]
                translation = get_trans_new_fetch(lemmatized_word, plain_word)
                if translation != "": 
                    break
                    
    #then try backup method of extending and truncating recursively
    if translation == "":
            translation = get_trans_new_recursive(plain_word, plain_word)
            if translation != "":
                translation = "(?)" + translation
                print("Note, no match for word: " + plain_word + ",\n using questionable match: " + translation.replace("<br>\n", "; ").replace("<br>"," ")[:20] + "...")
                missing_dictionary_entries.append(plain_word)

    if translation == "":
        print("Error, no non-empty dictionary entry for word: " + plain_word)
        missing_dictionary_entries.append(plain_word)

    return translation


## Main construction
structured_content = []

#to catch warnings to deal with
blank_dictionary_definitions = []
missing_dictionary_entries = []

for j in range(len(content)):
    line = content[j]
    if line != "":
        if line[0] == "#":
            structured_content.append(line[1:])
        else:
            #see for explanation, but not how I installed this (installed through konlpy):
            #https://pypi.org/project/python-mecab-ko/
            structured_content.append(mecab.pos(line, flatten = False))

def format_tree(branch, d = 0):
    #print("call on: " + str(tree))
    if type(branch) == list:
        if len(branch) > 0:
            if type(branch[0]) == list:
                #we have a list of lists, either further branching or sentence
                if len(branch[0]) > 0:
                    if d > 0:
                        xprint('    <li>')
                    xprint('<div class=wrapper>')
                    xprint('    <ol class=sentence>')
                    for twig in branch:
                        format_tree(twig, d + 1)
                    
                    #check if this was a list of lists of tuples (a sentence)
                    #and add sentence translate link if so
                    if type(branch[0][0]) == tuple:
                        link =  "https://papago.naver.com/?sk=ko&tk=en&st=" + urllib.parse.quote(
                                    " ".join(
                                        "".join(tup[0] for tup in twig)
                                        for twig in branch)
                                    )
                        xprint('    <li>')
                        xprint('      <ol class=comment>')
                        xprint(f'        <li lang=es><a title="Papago line translation" class=translink target="_blank" rel="noopener noreferrer" href="{link}">&#10093;</a></li>')
                        xprint('      </ol>')
                        xprint('    </li>')

                    xprint('    </ol>')
                    xprint('</div>')
                    if d > 0:
                        xprint('    </li>')
            elif type(branch[0]) == tuple:
                #we have a list of tuples comprising a word
                format_word(branch)
            else:
                print("error, unexpected branch type" + str(type(branch)))
    elif type(branch) is str:
        xprint('<div class=wrapper>')
        xprint('    <ol class=sentence>')
        xprint('    <li>')
        xprint('      <ol class=comment>')
        xprint('        <li lang=en_MORPH>')
        xprint(html.escape(branch))
        xprint('        </li>')
        xprint('      </ol>')
        xprint('    </li>')
        xprint('    </ol>')
        xprint('</div>')
    else: 
        print("error, expected list or str, got something else")


def format_word(branch):
    #example format:
    #branch = [('“', 'SSO'), ('톱질', 'NNG'), ('하', 'XSV'), ('세', 'EC')]

    plain_word = "".join([(x[0] if (x[1][0] != "S") else "") for x in branch])
    if plain_word == "":
        if sum([1 for x in branch if x[1][0] != "S"]) > 0:
            print("Warning, plain word is empty, printing branch: ")
            print(branch)

    for x in branch:
        if x[1] == "UNKNOWN":
            print("Note, unknown class for word: " + x[0])
    full_word = "".join([   (   "<span style='color:" + get_sejongtagset_colour(x[1]) + ";'>" + 
                                html.escape(x[0]) +
                                "</span>"
                            ) for x in branch   ])
    full_word_length = sum(len(x[0]) for x in branch)
                            
    link = "https://en.dict.naver.com/#/search?query=" + urllib.parse.quote(plain_word)
    
    non_symbol_pos = [ x[1] for x in branch if x[1][0] != "S" ]
    
    pos_info = "/".join(non_symbol_pos)
    pos_info_long = "\n".join([   (
                                        x[0] + " " + get_sejongtagset_name(x[1])
                                    ) for x in branch if x[1][0] != "S"  ])
                                    
    translation = get_translation(plain_word)
    
    wrapper.width = full_word_length*3 if full_word_length > 1 else 2*3
    wrapper.max_lines = 4
    translations = translation.split("\n")
    if len(translations) > 1:
        tshort = "\n".join([t[0:wrapper.width] for t in translations])
        tshort = html.escape(wrapper.fill(tshort)).replace("\n", "<BR>")
    else:
        tshort = html.escape(wrapper.fill(translation.replace("\n", "; "))).replace("\n", "<BR>")
    
    #tshort_split = translation.split("\n")    
    # if len(tshort_split) >= 2:
    #     tshort = "; ".join([tshort_split[0][:10],tshort_split[1][:8]])
    # else: 
    #     tshort = ("; ".join(tshort_split))[:10]
    
    description = ( html.escape(pos_info) + "\n" + 
                    tshort
                    ).replace("\n","<br>")
    
    tooltip = ( html.escape(pos_info_long) + "\n\n" +        
                html.escape(translation)
                ).replace("\n","<br>")

    xprint('    <li>')
    xprint('      <ol class=word>')
    xprint(f'        <li lang=es><a title="Naver word translation" class=diclink target="_blank" rel="noopener noreferrer" href="{link}">{full_word}</a></li>')
    xprint(f'        <li lang=en_MORPH class=tooltip>{description}<span class=tooltiptext>{tooltip}</span></li><br>')
    xprint('      </ol>')
    xprint('    </li>')
    
##main proceedures for generating output
output = ""

def xprint(message):
    global output
    output = output + message + "\n"

wrapper = textwrap.TextWrapper(placeholder = "]")

for branch in structured_content:
    format_tree(branch)        


##Enter missing words to database
missing_words = list(set(blank_dictionary_definitions + missing_dictionary_entries))
if len(missing_words) > 0 and not testing:
    if(input("\nWould you like to insert " + str(len(missing_words)) + " missing word definitions into database for next run? (y/n):") == "y"):
        submitter = input("Enter your name: ")
        import time    
        for word in missing_words:
            translation = input("For word " + word + " enter translation, f to finish, or leave blank for unkown:")
            if translation == "f": 
                break
            if translation != "":
                doe = time.strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("INSERT INTO korean_english_added (word, def, submitter, doe) VALUES (%s, %s, %s, %s);", (word, translation, submitter, doe))                
                con.commit()
                print(cur.rowcount, "record inserted successfully.")
cur.close()
con.close()



##print and format output

header = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
/* 
Credit for interlinear css to:
https://linguistics.stackexchange.com/questions/3/how-do-i-format-an-interlinear-gloss-for-html
http://jsfiddle.net/snifty/Ty8Vp/2/
*/

ol,ul{
    list-style:none;
}

body,div,li,ol,p,pre,ul{
    margin:0;
    padding:0;
}

body {
    background-color: white; 
    font-size: 16px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Fira Sans","Droid Sans","Helvetica Neue",Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";
    padding:0;
    margin:0;
    background-color: #fdf6e4; 
    font-size: 16px;
}

a{
    color:black;
    text-decoration:none;
}

a:hover{
    text-decoration:underline;
}

div.wrapper { 
    padding: 5px;
  overflow:visible;   
  margin: 1em 0;
  clear:both;
   font-size: 16px;
}

ol.sentence { 
  display:inline;    
}

ol.sentence li[lang=es]{
   font-weight:bold;  
    font-size: 20px; 
}

ol.sentence li[lang=en_MORPH]{
   font-family: monospace;  
   padding-top: 5px;
    font-size: 10px;
    color:#aaa;
}

ol.word { 
 padding: .5em;
 margin-bottom: .5em;
 background: white;
 float:left;
 border: 1px dotted #ddd;
 display: inline-block;   
 height: 6em;
}

ol.comment { 
 padding: .5em;
 margin-bottom: .5em;
 background: white;
 float:left;
 border: 1px dotted #ccc;
 display: inline-block;   
}

/* Credit for tooltip css to: https://www.w3schools.com/css/css_tooltip.asp */
/* Tooltip container */
.tooltip {
  position: relative;
  display: inline-block;
  /*border-bottom: 1px dotted black; If you want dots under the hoverable text */
}

/* Tooltip text */
.tooltip .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: white; /*#fdf6e4;*/
  color: #333;
  text-align: left;
  font-size: 10px;
  padding: 5px 5px;
  border-radius: 6px;
border: 1px dotted #ccc; 
  /* Position the tooltip text - see examples below! */
  position: absolute;
  z-index: 1;
}

.tooltip .tooltiptext {
  top: -5px;
  left: 105%;
}

.tooltip .tooltiptext::after {
  content: " ";
  position: absolute;
  top: 12px;
  right: 100%; /* To the left of the tooltip */
  margin-top: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: transparent hsla(0, 0%, 80%, 50) transparent transparent;
}

/* Show the tooltip text when you mouse over the tooltip container */
.tooltip:hover .tooltiptext {
  visibility: visible;
}

a.diclink {
    text-decoration: none;
}

a.translink {
    text-decoration: none;
    font-weight: normal;
    color: grey;
}

</style>
</head>
<body>
"""

footer = """
</body>
</html>
"""

##find a free filename and write output
if len(filename.split(".")) <= 1:
    outfilename = filename
else:
    outfilename = ".".join(filename.split(".")[0:-1])
if(not testing):
    i = 2
    if os.path.exists(outfilename + "-interlinear.html"):
        while os.path.exists(outfilename + "-" + str(i) + "-interlinear.html"):
            i = i + 1
        outfilename = outfilename + "-" + str(i)
outfilename = outfilename + "-interlinear.html"

print("\nWriting output to: " + outfilename)
outF = open(outfilename, "w")
outF.write(header)
outF.writelines(output)
outF.write(footer)
outF.close()
