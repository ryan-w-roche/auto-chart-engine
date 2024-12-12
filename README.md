# Auto-Chart Engine (ACE)

## Overview
Clone Hero is a rhythm game for the PC that uses scrolling sheets of colored notes to simulate the timing of musical notes being hit to a song track. It is the culmination of two communities, Guitar Hero and Rock Band, coming together to create a clone of the games, free for everyone and able to create charts (the scrolling sheets with colored notes) for any song they want. This project will tackle the process of charting songs to make it more accessible and effective so more songs can be included in the game. The plan is to use machine learning to train a model from audio files, cross-referenced with previously existing charts to output a chart file that can be used in the game. Initially, we will take a .mp3 file and separate the drums from the other instruments. Then that isolated drum track will be transformed into a format readable by models which the final custom-trained model can then read to create a chart in an acceptable file format. The final model will be a supervised LLM/SLM trained on a large data set of charts paired with their respective audio.

## Video Link
TODO

## Install Instructions
**Dependencies:**
1. In the terminal, enter in the following command:
```Python
pip install -r requirements.txt
```

**Software:**
- Moonscraper: https://github.com/FireFox2000000/Moonscraper-Chart-Editor
- Clone Hero: https://clonehero.net

## Future Code Drop Plans
**Code Drop 2:**
- Finish testing within Jupyter notebooks
- Begin implementation of the ace package CLI

**Code Drop 3:**
- Finish ace package CLI code
- Begin NFR tests
- Begin user error handling

**Code Drop 4:**
- Finish NFR tests
- Finish user error handling
- Final cleanup if necessary