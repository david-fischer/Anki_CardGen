![Logo](src/assets/AnkiCardGen_small.png)

<h1 align="center">AnkiCardGen</h1>



[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

#### Screenshots

<table>
  <tr>
      <td>Nav-Drawer</td>
      <td>Queue</td>
      <td>Single Word Text</td>
      <td>Single Word Image</td>
  </tr>
  <tr>
    <td><img src="screenshots/nav_drawer_open.png" width=270 height=480></td>
    <td><img src="screenshots/screen_queue.png" width=270 height=480></td>
    <td><img src="screenshots/example_word_text.png" width=270 height=480></td>
    <td><img src="screenshots/example_word_images.png" width=270 height=480></td>
  </tr>
 </table>
<details>
<summary>Example Cards</summary>
<table>
  <tr>
      <td>Word-Meaning Front</td>
      <td>Meaning-Word Front</td>
      <td>Back</td>
  </tr>
  <tr>
    <td><img src="screenshots/casa/pt-meaning_front.png" width=270 height=480></td>
    <td><img src="screenshots/casa/meaning-pt_front.png" width=270 height=480></td>
    <td><img src="screenshots/casa/pt-meaning_back.png" width=270 height=480></td>
  </tr>
  <tr>
    <td><img src="screenshots/convite/pt-meaning_front.png" width=270 height=480></td>
    <td><img src="screenshots/convite/meaning-pt_front.png" width=270 height=480></td>
    <td><img src="screenshots/convite/pt-meaning_back.png" width=270 height=480></td>
  </tr>
  <tr>
    <td><img src="screenshots/comecar/pt-meaning_front.png" width=270 height=480></td>
    <td><img src="screenshots/comecar/meaning-pt_front.png" width=270 height=480></td>
    <td><img src="screenshots/comecar/pt-meaning_back.png" width=270 height=480></td>
  </tr>
 </table>
</details>

[Kivy](https://kivy.org/) App (mobile/dektop) for quick generation of personalized language flash cards for [Anki](https://apps.ankiweb.net/) containing:

* Image
* Audio
* Example
* Synonym - Antonym
* Definition

Currently supported languages:
* **Brazilian Portuguese**

## ❓ About 

Anki is a powerful tool for reviewing flash cards, in particular for language learning.

Having flash cards with multiple cues (image, audio, example-sentence, ...) is beneficial, but one does not want to spend a large amount of time in the creation. This project aims to provide the solution to this process. The app automatically downloads and processes data for a given word in the target language and offers the user a choice of various options for the content of the card.

This allows quick generation of high-quality, personalized cards.

## 🏗 Current State

* [x] Importing a list of words
    * [x] User interface to load
        * [x] from exported kindle-notes in html-format
        * [x] from simple text file
    * [x] Pre-Processing
        * [x] Extracting the words
        * [x] Removal of punctuation
        * [x] Get dictionary form of word **(only desktop)**
    * [x] Clicking on loaded words to start generation-process
* [x] Processing single words
    * [x] Fetching necessary data to build card
    * [x] Provide user interface to select content of card
    * [x] Process the user input
    * [x] Downloading image and audio files
    * [x] Building the Anki card from html-templates

- [ ] Incremental saving of apkgs
- [ ] Error handling for incomplete selection
- [ ] Chaning of languages

## 🚧 Installing 

### Prerequisites

Download repository and install requirements:

```
git clone https://github.com/david-fischer/Anki_CardGen.git
cd Anki_CardGen
pip install -r requirements.txt
```

Install [spacy](https://github.com/explosion/spaCy) model, e.g. for portuguese: 

```
pythn -m spacy download pt_core_news_sm
```

**NOTE:** This model is used to find the dictionary form of words (e.g. casas -> casa). It is optional and does not yet work on the mobile version.

### Building the Android App

The apk is built using [Buildozer](https://buildozer.readthedocs.io/en/latest/)
```
buildozer android debug deploy
```

### Building the iOS App
(not yet tested)
```
buildozer ios debug deploy
```

## 🎯 Troubleshooting

* python3.8 not working -> change to 3.7

## 🔧 Usage 
(add info)

## 🚀 Contribute
* So far, the project only supports Brasilian Portuguese, as it is the language I am currently learning.
  Feel free to contribute e.g. by implementing crawlers for the necessary information for words in other languages as well.
* Unfortunately, I had problems building SpaCy (more precisely its dependency blis) on arm. I therefore removed it from the dependencies in buildozer.spec and built the code to work around it if the package is not present.make blis work on mobile

## ✍️ Authors 
- [David Fischer](https://github.com/david-fischer) - Author

<!--
See also the list of [contributors](https://link/to/contributers) who participated in this project.
-->

## 🎉 Acknowledgements 

* [ ] List info here
