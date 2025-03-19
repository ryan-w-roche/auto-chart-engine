# Auto-Chart Engine (ACE)

## Overview
Clone Hero is a rhythm game for the PC that uses scrolling sheets of colored notes to simulate the timing of musical notes being hit to a song track. It is the culmination of two communities, Guitar Hero and Rock Band, coming together to create a clone of the games, free for everyone and able to create charts (the scrolling sheets with colored notes) for any song they want. This project will tackle the process of charting songs to make it more accessible and effective so more songs can be included in the game. The plan is to use machine learning to train a model from audio files, cross-referenced with previously existing charts to output a chart file that can be used in the game. Initially, we will take a .mp3 file and separate the drums from the other instruments. Then that isolated drum track will be transformed into a format readable by models which the final custom-trained model can then read to create a chart in an acceptable file format. The final model will be a supervised LLM/SLM trained on a large data set of charts paired with their respective audio.

## Links
- **Code Drop 3 Video:** 
- **Git Repo:** https://github.com/ryan-w-roche/auto-chart-engine

## Install Instructions
**Dependencies:**
1. In the terminal, enter in the following command:
```Python
pip install -r requirements.txt
```

**Software:**
- Moonscraper: https://github.com/FireFox2000000/Moonscraper-Chart-Editor
- Clone Hero: https://clonehero.net

## CLI Usage
The Auto-Chart Engine CLI allows you to extract drum tracks from MIDI files and convert them into `.chart` files compatible with Clone Hero.

### Basic Usage
```
python -m ace -i /path/to/your/midi/file.mid -o /optional/output/directory
```

#### Required Arguments:
- `-i, --input_dir`: Path to the MIDI file you want to convert

#### Optional Arguments:
- `-o, --output_dir`: Directory where output files will be saved (defaults to your Downloads folder)

### Example
```
python -m ace -i "C:/Users/username/Music/my_song.mid" -o "C:/Users/username/Documents/CloneHero"
```

### How It Works
1. The CLI extracts the drum tracks from your MIDI file
2. It generates a new MIDI file containing only the drum tracks (saved with suffix "_DRUMS")
3. It then converts this drum-only MIDI file into a Clone Hero compatible `.chart` file

### Generated Files
When you run the CLI, it produces two output files:
1. A MIDI file containing only the drum tracks (named `<original_filename>_DRUMS.mid`)
2. A `.chart` file compatible with Clone Hero (named `<original_filename>_DRUMS.chart`)

### Data Storage
The CLI uses AWS S3 for file storage and organization:
- Raw MIDI files are stored in the `raw-midi-files` bucket
- Extracted drum MIDI files are stored in the `split-midi-files` bucket
- Generated chart files are stored in the `chart-files` bucket

To use S3 storage, you need to set up AWS credentials:
1. Create a `.env` file in the project root directory
2. Add the following environment variables:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=your_region
   ```

If you don't configure AWS credentials, the CLI will still operate as intended with local files but won't store data in S3.

### Drum Mapping
The CLI maps standard drum notes to Clone Hero's drum notes:
- Kick → Line 
- Snare → Red note 
- Hi-Hat → Yellow cymbal
- 1st Tom → Yellow note
- 2nd Tom → Blue note
- 3rd Tom → Green note
- Crash → Green cymbal
- Ride → Blue cymbal

### Troubleshooting
- If you encounter errors related to AWS, check your `.env` file and ensure credentials are correct
- For best results, use standard MIDI files with proper drum channel mapping (channel 10/9)
- Output files are saved both locally and to S3 if credentials are provided

## Code Drop Plans
**Code Drop 1:**
- Set up coding environment
- Set up remote desktop for development
- Begin testing within Jupyter notebooks

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