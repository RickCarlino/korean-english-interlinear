# korean-english-interlinear
Command-line python script that, from supplied Korean text, generates Korean-English interlinear direct translation rendered in html with parts-of-speech tags and definitions.

Uses these Python libraries:
- [Konlpy (using Okt, and Mecab-ko)](https://github.com/konlpy/konlpy),
- [Soylemma](https://github.com/lovit/korean_lemmatizer), and

Requires the [KEngDic dictionary](https://github.com/garfieldnate/kengdic) to be loaded into a [PostgreSQL](https://www.postgresql.org/) database.

To run in (Linux) shell:
./korean-english-interlinear.py sample.txt

Outputs an HTML file with a similar name.

![Alt text](/screenshot.png?raw=true)
