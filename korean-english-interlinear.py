#!/usr/bin/python

# import sys
# filename = sys.argv[1]

filename = "/home/ddog/Documents/Korean Learning/korean-english-interlinear/sample-input.txt"

with open(filename) as f:
    content = f.readlines()

content = [x.strip() for x in content] 

import re
word_regex = r'\b\w+\b'

structured_content = []

import html

from konlpy.tag import Hannanum
hannanum = Hannanum()
from konlpy.tag import Mecab
mecab = Mecab()
from konlpy.tag import Okt
okt = Okt()

from soylemma import Lemmatizer
lemmatizer = Lemmatizer()


import psycopg2
con = psycopg2.connect(database="kenddic", user="ddog", password="", host="127.0.0.1", port="5432")
print("Database opened successfully")
cur = con.cursor()

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

    #for double coded ones using first coded tag as above
    # 'VCP+ETM':  ('Copula',          'Verb'), 
    # 'VCP+EP':   ('Copula',          'Verb'), 
    # 'VV+EC':    ('VerbalPredicate', 'Verb'), 
    # 'VA+EP':    ('Adjective',       'Verb'),
    # 'VV+EP':    ('Adjective',       'Verb') 
    
}

#https://praacticalaac.org/praactical/how-we-do-it-using-language-boards-to-support-aac-use-by-nerissa-hall-and-hillary-jellison/
#https://alltogether.wordpress.com/2007/09/17/goossens-crain-elder-communication-overlay-color-reminder/
#https://vimawesome.com/plugin/solarized-8
SuperClass_Colours = {
    'Adverb': '#b78a00',
    'Noun': 'hsl(0, 0%, 20%)',
    'Pronoun': '#25a399',
    'Verb': '#cc4a0e',
    'CardinalNumber': 'hsl(0, 0%, 20%)',
    'Determiner': '#729f01',
    'ForeignWord': 'hsl(0, 0%, 70%)',
    'Interjection': '#cc4a0e',
    'Symbol': 'hsl(0, 0, 20%)',
    'Particle': '#657b85'
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
        print("***Error: can't find " + tag + " in tagset!")
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

def get_trans_new_fetch(word, addition = ""):
    cur.execute("SELECT word, TRIM(coalesce(def, '')) AS trans FROM korean_english WHERE word like %s;", (word + addition,))        
    rows = cur.fetchall()
    if type(rows) is list and len(rows) > 0:
        return "<br>\n".join(["<br>".join([row[0],row[1]]) for row in rows if row is not None])
    return ""
    
def get_trans_new(word):
    print("Getting translation: " + word)
    if word == "":
        return ""
    translation = get_trans_new_fetch(word, "")
    if translation != "":
        return translation
    translation = get_trans_new_fetch(word, "_")
    if translation != "":
        return translation
    translation = get_trans_new_fetch(word, "%")
    if translation != "":
        return translation
    return get_trans_new(word[:-1])

## Main construction
for j in range(len(content)):
    line = content[j]
    if line != "":
        if line[0] == "#":
            structured_content.append(line[1:])
        else:
            #see for explan but not how I installed (installed through konlpy) https://pypi.org/project/python-mecab-ko/
            #another possible avenue: https://lovit.github.io/nlp/2018/06/07/lemmatizer/
            structured_content.append(mecab.pos(line, flatten = False))

#print("structured_content:")
#print(structured_content)

def format_tree(branch, d = 0):
    #print("call on: " + str(tree))
    if type(branch) == list:
        if type(branch[0]) == list:
            #we have a list of lists
            if d > 0:
                xprint('    <li>')
            xprint('<div class=wrapper>')
            xprint('    <ol class=sentence>')
            for twig in branch:
                format_tree(twig, d + 1)
            xprint('    </ol>')
            xprint('</div>')
            if d > 0:
                xprint('    </li>')
        elif type(branch[0]) == tuple:
            #we have a list of tuples comprising a word
            #branch = [('“', 'SSO'), ('톱질', 'NNG'), ('하', 'XSV'), ('세', 'EC')]

            plain_word = "".join([(x[0] if (x[1][0] != "S") else "") for x in branch])
            
            if plain_word == "":
                print("warning, plain word is empty, printing branch: ")
                print(branch)
            
            #print("working on plain word: " + plain_word)

            full_word = "".join([
                                    (
                                        "<span style='color:" + get_sejongtagset_colour(x[1]) + ";'>" + 
                                        html.escape(x[0]) +
                                        "</span>"
                                        
                                    ) for x in branch
                                ])
            
            link = "https://en.dict.naver.com/#/search?query=" + urllib.parse.quote(plain_word)
            
            non_symbol_pos = [
                                (x[0] + " " + x[1]) for x in branch if x[1][0] != "S"
                            ]
            pos_info = "<br>".join(non_symbol_pos)
            pos_info_long = "<br>".join([
                                            (
                                                x[0] + " " + get_sejongtagset_name(x[1])
                                            ) for x in branch if x[1][0] != "S"
                                        ])
            
            #first look up the given word in dictionary
            translation = get_trans_new_fetch(plain_word)
            #if translation != "":
            #    print("plain lookup in dic found match for: " + plain_word)

            #then try lemmatizing the word one way (returns one), see if in dic
            if translation == "":
                lemmatized_word = okt.pos(plain_word, norm=True, stem=True)
                if type(lemmatized_word) == list and len(lemmatized_word) == 0:
                    print("warning, zero length list back from okt for: " + plain_word)
                elif type(lemmatized_word) == list and type(lemmatized_word[0]) == tuple:
                    lemmatized_word = lemmatized_word[0][0]
                    translation = get_trans_new_fetch(lemmatized_word)
                    #if translation != "":
                    #    print("used main okt lemmatizer and found a match in dic for: " + lemmatized_word)

            #then try backup lemmatizing method (returns multiple), see if in dic
            if translation == "":
                lemmatized_words = lemmatizer.lemmatize(plain_word)
                for lemmatized_word in lemmatized_words:
                    if type(lemmatized_word) == tuple:
                        lemmatized_word = lemmatized_word[0]
                        translation = get_trans_new_fetch(lemmatized_word)
                        if translation != "": 
                            print("used backup soylemma lemmatizer and found a match in dic for: " + lemmatized_word)
                            break

            descriptiontop = html.escape(pos_info).replace("&lt;br&gt;","<br>")
            tooltiptop = html.escape(pos_info_long).replace("&lt;br&gt;","<br>")

            tshort_split = translation.split("<br>")
            if len(tshort_split) >= 2:
                tshort = "<br>".join([tshort_split[0][:10],tshort_split[1][:8]])
            else: 
                tshort = ("<br>".join(tshort_split))[:10]
            
            descriptionbot = html.escape(tshort).replace("&lt;br&gt;","<br>")
            tooltipbot = html.escape(translation).replace("&lt;br&gt;","<br>")


            xprint('    <li>')
            xprint('      <ol class=word>')
            xprint(f'        <li lang=es><a class=diclink target="_blank" rel="noopener noreferrer" href="{link}">{full_word}</a></li>')
            xprint(f'        <li lang=en_MORPH class=tooltip>{descriptiontop}<span class=tooltiptext>{tooltiptop}</span></li><br>')
            xprint(f'        <li lang=en_MORPH class=tooltip>{descriptionbot}<span class=tooltiptext>{tooltipbot}</span></li>')

            xprint('      </ol>')
            xprint('    </li>')
            
        else:
            print("error, unexpected branch type" + str(type(branch)))
    else: 
        print("error, expected list got something else")


            
output = ""

def xprint(message):
    global output
    output = output + message + "\n"

import urllib.parse

for j in range(len(structured_content)):
    line = structured_content[j]

    if type(line) is str:
        xprint('<div class=wrapper>')
        xprint('    <ol class=sentence>')
        xprint('    <li>')
        xprint('      <ol class=comment>')
        xprint('        <li lang=en_MORPH>')
        xprint(html.escape(line))
        xprint('        </li>')
        xprint('      </ol>')
        xprint('    </li>')
        xprint('    </ol>')
        xprint('</div>')
    elif type(line) is list:
        format_tree(line)        


con.close()

header = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

	<!--  http://jsfiddle.net/snifty/Ty8Vp/2/-->
	<!-- https://linguistics.stackexchange.com/questions/3/how-do-i-format-an-interlinear-gloss-for-html -->
	<!-- https://stackabuse.com/text-translation-with-google-translate-api-in-python/ -->
	<!-- http://lostintranslationland.blogspot.com/2011/05/heungbu-and-nolbu.html?m=1 -->
    <!-- https://www.w3schools.com/css/css_tooltip.asp -->

<style>

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
}

body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Oxygen,Ubuntu,Cantarell,"Fira Sans","Droid Sans","Helvetica Neue",Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji","Segoe UI Symbol";
    padding:0;
    margin:0;
}

a{
    color:black;
    text-decoration:none;
}

a:hover{
    text-decoration:underline;
}

body {
    background-color: #fdf6e4; font-size: 16px;
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
  background-color: #fdf6e4;
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
  top: 50%;
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



</style>
</head>
<body>
"""

footer = """
</body>
</html>
"""

outF = open(filename + ".html", "w")
outF.write(header)
outF.writelines(output)
outF.write(footer)
outF.close()
