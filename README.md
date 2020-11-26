# korean-english-interlinear
Command-line python script that, from supplied Korean text, generates Korean-English interlinear direct translation rendered in html with parts-of-speech tags and definitions.

Uses these Python libraries:
- [Konlpy](https://github.com/konlpy/konlpy) (using [Okt](https://github.com/open-korean-text/open-korean-text), and [Mecab-ko](http://eunjeon.blogspot.kr/)),
- [Soylemma](https://github.com/lovit/korean_lemmatizer), and

Requires the [KEngDic dictionary](https://github.com/garfieldnate/kengdic) to be loaded into a [PostgreSQL](https://www.postgresql.org/) database.

To run in (Linux) shell:
./korean-english-interlinear.py sample.txt

Outputs an HTML file with a similar name.
Credit for the interlinear css to [Pat on Stack Exchange](https://linguistics.stackexchange.com/questions/3/how-do-i-format-an-interlinear-gloss-for-html),
and for the colour scheme to [Solarized 8](https://github.com/lifepillar/vim-solarized8).

![Alt text](/screenshot.png?raw=true)
