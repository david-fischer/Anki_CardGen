<div>
<img align="left" height=200 src="acg/assets/AnkiCardGen.png">
</br>
</br>
</br>
</br>
</br>
<h1>AnkiCardGen</h1>
</div>

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![LICENSE: MIT](https://img.shields.io/github/license/david-fischer/Anki_CardGen)](https://github.com/david-fischer/Anki_CardGen/blob/master/LICENSE) [![Version](https://img.shields.io/github/v/tag/david-fischer/Anki_CardGen?label=version)]() [![android apk](https://github.com/david-fischer/Anki_CardGen/workflows/build%20android%20apk/badge.svg?branch=v1.0.9)]() [![windows](https://github.com/david-fischer/Anki_CardGen/workflows/build%20windows/badge.svg?branch=v1.0.9)]() [![linux](https://github.com/david-fischer/Anki_CardGen/workflows/build%20linux/badge.svg?branch=v1.0.9)]() [![Documentation Status](https://readthedocs.org/projects/anki-cardgen/badge/?version=latest)](https://anki-cardgen.readthedocs.io/en/latest/?badge=latest)

Python [Kivy](https://kivy.org/) App for mobile and desktop for quick generation of personalized language flash cards for [Anki](https://apps.ankiweb.net/) containing: Image, audio, example, synonym - antonym, definition and more! The interface is built with the material-design-inspired [KivyMD](https://github.com/kivymd/KivyMD). The project is not affiliated with Anki.

> **:warning: This project is still under development, see [current state](https://github.com/david-fischer/Anki_CardGen#-current-state). If you would like to contribute have a look at the [documentation](https://anki-cardgen.readthedocs.io) and the [contribute](https://github.com/david-fischer/Anki_CardGen#-contribute) section.**

Currently supported languages:

* **Brazilian Portuguese**

### Screenshots
<!-- jinja-block screenshots
$ for file in img_files
$ if loop.index ==4
{{ comment_tag }}

<details>
<summary>More screenshots</summary>
$ endif
<img src="{{ file }}" width=270>&nbsp;{#- this comment removes whitespace (because of the - sign) #}
$ if loop.last and loop.length >=4
</details>
$ endif
$ endfor

<details>
<summary>Example Cards</summary>
$for word in words
<h3>{{ word.name }}</h3>
$for side in word.sides
    <img src="{{ side }}" width=270>
$ endfor
$ endfor
</details>
jinja-block screenshots-->
<!-- jinja-out screenshots start-->
<img src="screenshots/0-nav-drawer-open.png" width=270>&nbsp;<img src="screenshots/1-word.png" width=270>&nbsp;<img src="screenshots/2-word.png" width=270>&nbsp;<!-- -->

<details>
<summary>More screenshots</summary>
<img src="screenshots/3-word-images.png" width=270>&nbsp;<img src="screenshots/4-import.png" width=270>&nbsp;<img src="screenshots/5-export.png" width=270>&nbsp;</details>
<details>
<summary>Example Cards</summary>
<h3>casa</h3>
    <img src="screenshots/casa/meaning-pt_back.png" width=270>
    <img src="screenshots/casa/meaning-pt_front.png" width=270>
    <img src="screenshots/casa/pt-meaning_front.png" width=270>
<h3>comecar</h3>
    <img src="screenshots/comecar/meaning-pt_back.png" width=270>
    <img src="screenshots/comecar/meaning-pt_front.png" width=270>
    <img src="screenshots/comecar/pt-meaning_front.png" width=270>
<h3>convite</h3>
    <img src="screenshots/convite/meaning-pt_back.png" width=270>
    <img src="screenshots/convite/meaning-pt_front.png" width=270>
    <img src="screenshots/convite/pt-meaning_front.png" width=270>
</details>
<!-- jinja-out screenshots end-->

## ❓ About

Anki is a powerful tool for reviewing flash cards, in particular for learning languages.

Having flash cards with multiple cues (image, audio, example sentence, ...) is beneficial for memorization but one does not want to spend a large amount of time on the creation of the cards. This project aims to provide a solution to this process. The app automatically downloads and processes data for a given word in the target language and offers the user a choice of various options for the content of the card.

This allows quick generation of high-quality, personalized cards.

## ⚡ Quick Start

You can install the current version of the [Android-apk](https://github.com/david-fischer/Anki_CardGen/tree/data/android) and try it out. So far it is only tested on an S5 Neo.

Furthermore you can find the packaged application as zip-files for [linux](https://github.com/david-fischer/Anki_CardGen/raw/data/linux/AnkiCardGen.zip) and [windows](https://github.com/david-fischer/Anki_CardGen/raw/data/windows/AnkiCardGen.zip).

> **⚠️  The windows build has not been tested at all.**

## 🏗 Current State

* [x] Processing of single words
* [x] Batch-import from .txt and **from kindle-notes**
* [x] Queue-system for words that have not been processed
* [x] Overview over processed words and option to export as .apkg
* [ ] change of languages
* [ ] spacy on mobile

## 🚧 Installation

* Setup new virtual environment with python 3.7, e.g. with conda

```
conda create -n "<environment_name>" python==3.7
conda activate <environment_name>
```

* install application

```
pip install git+https://github.com/david-fischer/Anki_CardGen.git
```

* Install [spacy](https://github.com/explosion/spaCy) model, e.g. for portuguese:

```
python -m spacy download pt_core_news_sm
```

**NOTE:** This model is used to find the dictionary form of words (e.g. casas -> casa). It is optional and does not yet work on the mobile version.


## 🎯 Troubleshooting

* python==3.7

## 🔧 Usage

After installation you should be able to start the app from the command line:
```
acg
```


## 🚀 Contribute
* So far, the project only supports Brasilian Portuguese, as it is the language I am currently learning.
  Feel free to contribute e.g. by implementing crawlers for the necessary information for words in other languages as well.
* Unfortunately, I had problems building SpaCy (more precisely its dependency blis) on arm. I therefore removed it from the dependencies in buildozer.spec and built the code to work around it if the package is not present.

## ✍️ Authors
- [David Fischer](https://github.com/david-fischer) - Author

## 🎉 Acknowledgements

`acg/google-images-download` is basically https://github.com/Joeclinton1/google-images-download with minor fixes
