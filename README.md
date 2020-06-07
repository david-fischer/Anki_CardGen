

![GitHub Logo](assets/AnkiCardGen_small.png)

<h3 align="center">AnkiCardGen</h3>

<!--

<div align="center">
  [![Status](https://img.shields.io/badge/status-active-success.svg)]() 
  [![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/issues)
  [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/pulls)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

-->
---
[Kivy](https://kivy.org/) App (mobile/dektop) for quick generation of personalized flash cards for [Anki](https://apps.ankiweb.net/) with:

* Image
* Audio
* Example
* Synonym - Antonym
* Definition

Currently supported languages:
* Brazilian Portuguese


## ❓ About 
Anki is a powerful tool for reviewing flash cards, in particular for language learning.
While having flash cards with multiple cues (image, audio, example, ...) is beneficial, one does not want to spend a large amount of time in the creation. This project aims to provide the solution to this process
by automatically downloading and processing data for a given word in the target language. Then it offers the user a choice of various options for the content of the card.
This allows quick generation of high-quality, personalized cards.

## 🏗 Current State

* [x] Importing a list of words
    * [x] User interface to load
        * [x] from exported kindle-notes in html-format
        * [ ] from simple text file
    * [x] Pre-Processing
        * [x] Extracting the words
        * [x] Removal of punctuation
        * [x] Get dictionary form of word
    * [ ] Clicking on loaded words to start generation-process
* [ ] Processing single words
    * [x] Fetching necessary data to build card
    * [x] Provide user interface to select content of card
    * [x] Process the user input
    * [x] Downloading image and audio files
    * [x] Building the Anki card from html-templates

## 🔧 Installing 

### App
<!-- TODO: Add apk file-->
* [ ] A compiled .apk file for Android is provided in the apk folder

### Prerequisites

Install requirements
```
pip install -r requirements.txt
```

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

## :microscope: Troubleshooting

* python3.8 not working -> change to 3.7

## 🎈 Usage 
(add info)

## 🚀 Contribute
So far, the project only supports Brasilian Portuguese, as it is the language I am currently learning.
Feel free to contribute e.g. by implementing crawlers for the necessary information for words in other languages as well.

## ✍️ Authors 
- [David Fischer](https://github.com/david-fischer) - Author

<!--
See also the list of [contributors](https://github.com/kylelobo/The-Documentation-Compendium/contributors) who participated in this project.
-->

## 🎉 Acknowledgements 

* [ ] List info here
