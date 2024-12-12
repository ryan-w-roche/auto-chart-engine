"""
Module for converting and processing MIDI files into Clone Hero chart files.
Handles drum track extraction, .chart file generation, and audio conversion.
"""
# Imports and Setup
from mido import MidiFile, MidiTrack, MetaMessage
from .data.file_data import S3FileManager
from dotenv import load_dotenv
from collections import defaultdict
from rich import print

import os
import io
import mido
import logging
import sys

logger = logging.getLogger(__name__)

class Charter:
    """
    Processes MIDI files to create Clone Hero compatible chart files.
    
    Extracts drum tracks from MIDI files, generates .chart format files,
    and converts MIDI to audio for use in Clone Hero.
    
    Manages AWS S3 connections for storing and retrieving files.
    """
    def __init__(self):
        """
        Initialize the Charter class with AWS S3 bucket connections.
        
        Sets up S3 bucket connections for raw songs, raw MIDIs, split MIDIs, and chart files.
        Validates that the .env file with AWS credentials exists and is properly configured.
        
        Raises:
            SystemExit: If the .env file doesn't exist or is empty.
        """
        # Determine the project root and find the .env file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)  # Go up one level from 'ace' directory
        dotenv_fp = os.path.join(project_root, ".env")

        # Check if the .env exist and is configured
        if not os.path.exists(dotenv_fp) or os.path.getsize(dotenv_fp) == 0:
            print("[bold red]The .env does not exist or is empty. Please configure with your AWS Credentials[/bold red]")
            print("[cyan]> Instructions for configuration are in the README[/cyan]")
            sys.exit(1)

        load_dotenv()

        # Initialize S3FileManager with bucket name and credentials
        self.raw_song_bucket_name = "raw-song-files"
        self.raw_midi_bucket_name = "raw-midi-files"
        self.split_midi_bucket_name = "split-midi-files"
        self.chart_bucket_name = "chart-files"

        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")

        # raw-song-files
        self.raw_song_bucket = S3FileManager(
            bucket_name=self.raw_song_bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        # raw-midi-files
        self.raw_midi_bucket = S3FileManager(
            bucket_name=self.raw_midi_bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        # split-midi-files
        self.split_midi_bucket = S3FileManager(
            bucket_name=self.split_midi_bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

        # chart-files
        self.chart_bucket = S3FileManager(
            bucket_name=self.chart_bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    def split_midi(self, in_file_dir: str, out_dir: str):
        """
        Extract drum tracks from a MIDI file and save to a new MIDI file.
        
        Splits the input MIDI file by extracting only the drum channel (channel 9)
        and saves it as a new file with "_DRUMS" appended to the filename.
        Uploads both the original and split MIDI files to S3.
        
        Args:
            in_file_dir (str): Path to the input MIDI file
            out_dir (str): Directory where the split MIDI file will be saved
            
        Returns:
            str: The key (filename) of the created split MIDI file
            
        Raises:
            SystemExit: If the input file or output directory doesn't exist
        """
        # Check if the input file exists
        if not os.path.exists(in_file_dir):
            logger.error(f"Error: Input file does not exist: {in_file_dir}")
            print(f"[bold red]Error:[/bold red] Input file does not exist: [cyan]{in_file_dir}[/cyan]")
            sys.exit(1)
        
        # Check if the output directory exists
        if not os.path.exists(out_dir):
            logger.error(f"Error: Output directory does not exist: {out_dir}")
            print(f"[bold red]Error:[/bold red] Output directory does not exist: [cyan]{out_dir}[/cyan]")
            sys.exit(1)

        # Write raw MIDI file to S3
        in_file_key = os.path.basename(in_file_dir)         # Extract just the file name
        with open(in_file_dir, 'rb') as f:
            self.raw_midi_bucket.write_file(key=in_file_key, data=f)

        base, ext = os.path.splitext(in_file_key)           # Split into name and extension
        formatted_base = base.lower().replace(' ', '_')     # Convert the base name to lowercase and replace spaces with underscores
        out_file_key = f"{formatted_base}_DRUMS{ext}"       # Append "_DRUMS" and then the original extension
        output_file_dir = os.path.join(out_dir, out_file_key)

        # Initialize MIDI files
        in_mid = MidiFile(in_file_dir)
        out_mid = MidiFile(ticks_per_beat=in_mid.ticks_per_beat)

        # Create drum track
        drum_track = MidiTrack()
        out_mid.tracks.append(drum_track)

        # Collect messages with absolute times
        all_messages = []
        current_time = 0

        # Process each track
        for track in in_mid.tracks:
            current_time = 0
            for msg in track:
                current_time += msg.time
                # Check if the note is in the drum channel and append it to the new midi if it is
                if (isinstance(msg, MetaMessage) and msg.type in ('set_tempo', 'time_signature')) or \
                    (msg.type in ('note_on', 'note_off') and msg.channel == 9) or \
                    (msg.type not in ('note_on', 'note_off')):
                    all_messages.append((current_time, msg))

        # Sort and convert to delta times
        all_messages.sort(key=lambda x: x[0])
        last_time = 0

        for abs_time, msg in all_messages:
            delta = abs_time - last_time
            new_msg = msg.copy(time=delta)
            drum_track.append(new_msg)
            last_time = abs_time

        # Write chart file to local directory
        out_mid.save(output_file_dir)

        if os.path.exists(output_file_dir):
            logger.info(f"Successfully created MIDI file at: {output_file_dir}")
            print(f"[bold green]✔ Successfully created MIDI file at:[/bold green] [cyan]{output_file_dir}[/cyan]")
        else:
            logger.error("Error: Failed to create MIDI file")
            print("[bold red]Error: Failed to create MIDI file[/bold red]")

        # Write split MIDI file to S3
        output_buffer = io.BytesIO()
        out_mid.save(file=output_buffer)
        output_buffer.seek(0)
        self.split_midi_bucket.write_file(key=out_file_key, data=output_buffer.getvalue())

        # Save and return
        return out_file_key
    
    def generate_chart_file(self, in_file_key: str, out_dir: str, ch_out_dir: str):
        """
        Generate a Clone Hero compatible .chart file from a MIDI file.
        
        Creates a .chart file from the input MIDI file with drum mappings for Clone Hero.
        Saves the chart file both in the output directory and in a Clone Hero specific
        directory structure with 'notes.chart' filename.
        
        Args:
            in_file_key (str): Key (filename) of the split MIDI file in S3
            out_dir (str): Directory where the chart file will be saved
            ch_out_dir (str): Clone Hero specific directory name for the chart
            
        Returns:
            None
        """
        chart_out_fp = os.path.join(out_dir, f"{os.path.splitext(in_file_key)[0]}.chart")
        out_file_key = os.path.basename(chart_out_fp)

        # Extract the song name from the file key
        song_name = out_file_key.replace('_DRUMS.chart', '') if out_file_key.endswith('_DRUMS.chart') else out_file_key
        song_name = song_name.replace('_', ' ').title()

        # Constants
        DRUM_MAPPING = {
            35: (0, 'K'),  # Acoustic Bass Drum
            36: (0, 'K'),  # Bass Drum (Kick)
            37: (1, 'R'),  # Side Stick
            38: (1, 'R'),  # Acoustic Snare
            39: (1, 'R'),  # Hand Clap
            40: (1, 'R'),  # Electric Snare
            41: (4, 'G'),  # Low Floor Tom
            42: (2, 'Y'),  # Closed Hi-Hat
            43: (4, 'G'),  # High Floor Tom
            44: (2, 'Y'),  # Pedal Hi-Hat
            45: (4, 'G'),  # Low Tom
            46: (3, 'B'),  # Open Hi-Hat
            47: (3, 'B'),  # Mid Tom
            48: (2, 'Y'),  # High Mid Tom
            49: (4, 'G'),  # Crash Cymbal 1
            50: (2, 'Y'),  # High Tom
            51: (3, 'B'),  # Ride Cymbal    
            52: (4, 'G'),  # Chinese Cymbal
            53: (3, 'B'),  # Ride Bell
            55: (2, 'Y'),  # Splash Cymbal
            57: (4, 'G'),  # Crash Cymbal 2
            59: (3, 'B'),  # Ride Cymbal 2
        }
        CHART_RESOLUTION = 192
        
        song_metadata = {
            "Name": f"\"{song_name}\"",
            "Artist": "\"Unknown\"",
            "Charter": "\"ACE\"",
            "Album": "\"Generated Charts\"",
            "Year": "\"2024\"",
            "Offset": 0,
            "Resolution": CHART_RESOLUTION,
            "Player2": "\"bass\"",
            "Difficulty": 0,
            "PreviewStart": 0,
            "PreviewEnd": 0,
            "Genre": "\"Rock\"",
            "MediaType": "\"cd\"",
            "MusicStream": "\"song.ogg\""
        }

        chart_data = {
            "Song": song_metadata,
            "SyncTrack": defaultdict(list),
            "Events": {},
            "ExpertDrums": defaultdict(list)
        }

        # Read split MIDI file from S3
        in_file_data = self.split_midi_bucket.read_file(key=in_file_key)
        in_file_buffer = io.BytesIO(in_file_data)
        midi = MidiFile(file=in_file_buffer)

        # Merge tracks to get length
        merged_track = mido.merge_tracks(midi.tracks)

        # Initialize chart file
        chart_data["SyncTrack"][0].append("TS 4")

        current_tick = 0
        for msg in merged_track:
            current_tick += msg.time
            chart_tick = int(current_tick * CHART_RESOLUTION / midi.ticks_per_beat)

            if msg.type == 'set_tempo':
                midi_tempo = msg.tempo
                bpm = int(mido.tempo2bpm(midi_tempo))
                ch_tempo = bpm * 1000
                chart_data["SyncTrack"][chart_tick].append(f"B {ch_tempo}")

            if msg.type == 'note_on' and msg.velocity > 0:
                if hasattr(msg, 'channel') and msg.channel == 9 and msg.note in DRUM_MAPPING:
                    note_num, flag = DRUM_MAPPING[msg.note]
                    note_str = f"N {note_num} 0{' ' + flag if flag else ''}"
                    chart_data["ExpertDrums"][chart_tick].append(note_str)

                    # Apply cymbals to expert notes
                    if msg.note in [42, 44, 55]:  # Yellow cymbal
                        chart_data["ExpertDrums"][chart_tick].append(f"N 66 0{' ' + flag if flag else ''}")
                    elif msg.note in [46, 51, 53, 59]:  # Blue cymbal
                        chart_data["ExpertDrums"][chart_tick].append(f"N 67 0{' ' + flag if flag else ''}")
                    elif msg.note in [49, 57, 52]:  # Green cymbal
                        chart_data["ExpertDrums"][chart_tick].append(f"N 68 0{' ' + flag if flag else ''}")
        
        # Build the .chart file text
        chart_text = "[Song]\n{\n"
        for key, value in chart_data["Song"].items():
            chart_text += f"  {key} = {value if isinstance(value, (int, float)) else f'{value}'}\n"
        chart_text += "}\n"

        chart_text += "[SyncTrack]\n{\n"
        for tick in sorted(chart_data["SyncTrack"].keys()):
            for event in chart_data["SyncTrack"][tick]:
                chart_text += f"  {tick} = {event}\n"
        chart_text += "}\n"

        chart_text += "[Events]\n{\n}\n"

        chart_text += "[ExpertDrums]\n{\n"
        for tick in sorted(chart_data["ExpertDrums"].keys()):
            for note in chart_data["ExpertDrums"][tick]:
                chart_text += f"  {tick} = {note[:-2]}\n"
        chart_text += "}"

        # Write chart file to local directory
        with open(chart_out_fp, 'w') as f:
            f.write(chart_text)

        if os.path.exists(chart_out_fp):
            logger.info(f"Successfully created chart file at: {chart_out_fp}")
            print(f"[bold green]✔ Successfully created chart file at:[/bold green] [cyan]{chart_out_fp}[/cyan]")
        else:
            logger.error("Error: Failed to create .chart file")
            print("[bold red]Error: Failed to create .chart file[/bold red]")

        # Write `notes.chart` version to a new folder for Clone Hero importing
        ch_out_fp = os.path.join(out_dir, ch_out_dir, "notes.chart")
        with open(ch_out_fp, 'w') as f:
            f.write(chart_text)

        if os.path.exists(ch_out_fp):
            logger.info(f"Successfully created chart file at: {ch_out_fp}")
            print(f"[bold green]✔ Successfully created chart file at:[/bold green] [cyan]{ch_out_fp}[/cyan]")
        else:
            logger.error("Error: Failed to create \"notes.chart\" file")
            print("[bold red]Error: Failed to create folder \"notes.chart\" file[/bold red]")

        # Write chart file to S3
        with open(chart_out_fp, 'rb') as f:
            self.chart_bucket.write_file(key=out_file_key, data=f)
    
    def generate_ogg_file(self, in_file_key: str, out_dir: str, ch_out_dir: str):
        """
        Convert a MIDI file to OGG audio format for Clone Hero.
        
        Uses FluidSynth to synthesize audio from the MIDI file and saves it as song.ogg
        in the Clone Hero directory structure for audio playback during gameplay.
        
        Args:
            in_file_key (str): Key (filename) of the split MIDI file
            out_dir (str): Directory where the original MIDI file is located
            ch_out_dir (str): Clone Hero specific directory where the OGG file will be saved
            
        Returns:
            None
        """
        from midi2audio import FluidSynth

        split_midi_fp = os.path.join(out_dir, in_file_key)
        ogg_out_fp = os.path.join(out_dir, ch_out_dir, "song.ogg")

        # Convert MIDI to OGG
        fs = FluidSynth(sound_font="ace/soundfonts/FluidR3_GM.sf2")
        fs.midi_to_audio(midi_file=split_midi_fp, audio_file=ogg_out_fp)

        if os.path.exists(ogg_out_fp):
            logger.info(f"Successfully created ogg file at: {ogg_out_fp}")
            print(f"[bold green]✔ Successfully created ogg file at:[/bold green] [cyan]{ogg_out_fp}[/cyan]")
        else:
            logger.error("Error: Failed to create \"song.ogg\" file")
            print("[bold red]Error: Failed to create \"song.ogg\" file[/bold red]")

        # Write ogg file to S3
        out_file_key = f"{os.path.splitext(in_file_key)[0]}.ogg"

        with open(ogg_out_fp, 'rb') as f:
            self.raw_song_bucket.write_file(key=out_file_key, data=f)