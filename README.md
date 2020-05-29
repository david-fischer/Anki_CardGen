![GitHub Logo](assets/AnkiCardGen.png)

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


## 🧐 About 
Anki is a powerful tool for reviewing flash cards, in particular for language learning.
While having flash cards with multiple cues (image, audio, example, ...) is beneficial, one does not want to spend a
large amount of time in the creation. This project aims to provide the solution to this process
by offering the user a choice of options for a given word, that is automatically downloaded and processed.

This allows quick generation of high-quality, personalized cards.

## Current State

-[x] Importing a list of words from exported kindle-notes (html)
    -[x] Extracting the words
    -[x] Removal of punctuation
    -[x] Get dictionary form of word
    -[ ] User interface to load notes
-[x] Fetching necessary data to build card
-[x] Provide user interface to select content of card
-[ ] Process the user input
-[ ] Downloading image and audio files
-[x] Building the Anki card from 

## 🏁 Getting Started 

### App
<!-- TODO: Add apk file-->
-[ ] A compiled .apk file for Android is provided in the apk folder

### Prerequisites

Install requirements
```
pip install -r requirements.txt
```



### 🔧 Building the Android App
The apk is built using [Buildozer](https://buildozer.readthedocs.io/en/latest/)
```
buildozer android debug deploy
```

### Building the iOS App
(not yet tested)
```
buildozer android debug deploy
```


### Break down into end to end tests
Explain what these tests test and why

```
Give an example
```

### And coding style tests
Explain what these tests test and why

```
Give an example
```

## 🎈 Usage <a name="usage"></a>
Add notes about how to use the system.

## 🚀 Contribute
So far, the project only supports Brasilian Portuguese, as it is the language I am currently learning.
Feel free to contribute e.g. by implementing crawlers for the necessary information for words in other languages as well.

## ✍️ Authors 
- [David Fischer](https://github.com/david-fischer) - Author

<!--
See also the list of [contributors](https://github.com/kylelobo/The-Documentation-Compendium/contributors) who participated in this project.
-->

## 🎉 Acknowledgements 

-[ ] List info here
