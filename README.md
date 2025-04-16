# Auto-Chart Engine (ACE)

## Overview
Clone Hero is a free rhythm game for PC, inspired by Guitar Hero and Rock Band, that allows players to create and play custom charts for any song. This project seeks to streamline and elevate the charting process by leveraging advanced extraction techniques to generate playable chart files directly from audio tracks. By isolating drum tracks from MIDI files and extracting precise note data, the engine produces highly accurate Clone Hero charts that accurately represent the original MIDI composition. This engine reduces the time required to chart a song, streamlining the creation of multiple songs in Clone Hero.


## Links
- **CLI Demonstration:** https://youtu.be/5lndr9maaSY?si=u9W6KzgyaVSeP5da
- **Git Repo:** https://github.com/ryan-w-roche/auto-chart-engine


## Install Instructions
**Dependencies:**
1. In the terminal, enter in the following command:
```Python
pip install -r requirements.txt
```
2. Install `fluidsynth` with `chocolatey (Windows)` or `homebrew (Mac)` or your Linux package manager:
```
choco install fluidsynth
```

3. Configure AWS S3 buckets and credentials:
      - Create or login to your AWS account
      - Go to `S3`
      - Create 4 new buckets named the following:
      ```
      > raw-song-files
      > raw-midi-files
      > split-midi-files
      > chart-files
      ```
      - Create an access key
      - In the root of the project, create a `.env` file and input the following:
      ```
      AWS_ACCESS_KEY_ID=<Your Key ID>
      AWS_SECRET_ACCESS_KEY=<Your Access Key>
      AWS_REGION=<Your Region>
      ```

**Software:**
- Moonscraper (testing/BPM editing): https://github.com/FireFox2000000/Moonscraper-Chart-Editor
- Clone Hero (song playability): https://clonehero.net


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
2. Generates a new MIDI file containing only the drum tracks (saved with suffix "_DRUMS")
3. Based on the MIDI with the extracted drums, a `.ogg` version of the midi is generated
4. Converts this drum-only MIDI file into a Clone Hero compatible `.chart` file

### Generated Files
When you run the CLI, it produces 3 outputs:
1. A MIDI file containing only the drum tracks (named `<original_filename>_DRUMS.mid`)
2. A `.chart` file (named `<original_filename>_DRUMS.chart`)
3. A folder named `artist - <song_name> (ACE)`
      - Contains `notes.chart` and `song.ogg` files for Clone Hero

### Data Storage
The CLI uses AWS S3 for file storage and organization:
- Raw MIDI files are stored in the `raw-midi-files` bucket
- Extracted drum MIDI files are stored in the `split-midi-files` bucket
- Generated chart files are stored in the `chart-files` bucket
- Generated song files are stored in the `raw-song-files` bucket

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

## Import to Clone Hero Instructions
1. Locate the generated folder titled `artist - <song> (ACE)`
2. Copy/cut and paste into your Clone Her songs path
3. In Clone Hero, go to `Settings` → `General` → `Scan Songs` → `Yes`
      - This should create a `song.ini` file in the folder that was copied into the Clone Hero songs path
4. In the `song.ini` file is more metadata you can edit, but the important one to edit is the `diff_drums` which categorizes the song based on drumming difficulty
5. Repeat the process in step `3` to see the drum difficulty change
6. You are now ready to play your newly imported song!


## Code Drops
**Code Drop 1:**</br>
Video: https://youtu.be/RRo5YtyhadQ
- Set up coding environment
- Set up remote desktop for development
- Begin testing within Jupyter notebooks

**Code Drop 2:**</br>
Video: https://youtu.be/zmEVN-mckbk
- Finish testing within Jupyter notebooks
- Begin implementation of the ace package CLI

**Code Drop 3:**</br>
Video: https://youtu.be/o2kNhwA7w-w
- Finish ace package CLI code
- Begin NFR tests
- Begin user error handling

**Code Drop 4:**</br>
- Finish NFR tests
- Finish user error handling
- Final cleanup if necessary