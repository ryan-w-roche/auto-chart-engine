# Imports and Setup
from mido import MidiFile, MidiTrack, MetaMessage
from .data.file_data import S3FileManager
from dotenv import load_dotenv
from collections import defaultdict

import os
import io
import mido

class ChartTranslator:
    # TODO: Docstring
    def __init__(self):
        load_dotenv()

        # Initialize S3FileManager with bucket name and credentials
        self.raw_midi_bucket_name = "raw-midi-files"
        self.split_midi_bucket_name = "split-midi-files"
        self.chart_bucket_name = "chart-files"

        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION")

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

    # TODO: Docstring
    def split_midi(self, in_file_dir: str, out_dir: str):
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
            print(f".mid file successfully created at: {output_file_dir}")
        else:
            print("Error: Failed to create .mid file or file is empty")

        # Write split MIDI file to S3
        output_buffer = io.BytesIO()
        out_mid.save(file=output_buffer)
        output_buffer.seek(0)
        self.split_midi_bucket.write_file(key=out_file_key, data=output_buffer.getvalue())

        # Save and return
        return out_file_key
    
    def convert_to_chart(self, in_file_key: str, out_dir: str):
        output_file_dir = os.path.join(out_dir, f"{os.path.splitext(in_file_key)[0]}.chart")
        out_file_key = os.path.basename(output_file_dir)

        # Constants
        DRUM_MAPPING = {
            35: (0, 'K'),  # Acoustic Bass Drum mapped to note 0 with flag 'K' 
            36: (0, 'K'),  # Bass Drum (Kick) mapped to note 0 with flag 'K' 
            38: (1, 'R'),  # Acoustic Snare mapped to note 1 with flag 'R' 
            40: (1, 'R'),  # Electric Snare mapped to note 1 with flag 'R' 
            42: (2, 'Y'),  # Closed Hi-Hat mapped to note 2 with flag 'Y'   #cymbal
            44: (2, 'Y'),  # Pedal Hi-Hat mapped to note 2 with flag 'Y'    #cymbal
            46: (3, 'B'),  # Open Hi-Hat mapped to note 3 with flag 'B'     #cymbal
            49: (4, 'G'),  # Crash Cymbal 1 mapped to note 4 with flag 'G'  #cymbal
            51: (3, 'B'),  # Ride Cymbal mapped to note 3 with flag 'B'     #cymbal
            45: (4, 'G'),  # Low Tom mapped to note 4 with flag 'G' 
            47: (3, 'B'),  # Mid Tom mapped to note 3 with flag 'B' 
            48: (2, 'Y'),  # High Mid Tom mapped to note 2 with flag 'Y' 
            50: (2, 'Y'),  # High Tom mapped to note 2 with flag 'Y' 
            57: (4, 'G'),  # Crash Cymbal 2 mapped to note 2 with flag 'G'  #cymbal
        }
        CHART_RESOLUTION = 192
        
        song_metadata = {
            "Name": f"\"{out_file_key}\"",
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
            "Genre": "\"Rock\""
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
                    if msg.note == 42 or msg.note == 44: # Y
                        note_str = f"N 66 0{' ' + flag if flag else ''}"
                        chart_data["ExpertDrums"][chart_tick].append(note_str)
                    elif msg.note == 46 or msg.note == 51: # B
                        note_str = f"N 67 0{' ' + flag if flag else ''}"
                        chart_data["ExpertDrums"][chart_tick].append(note_str)
                    elif msg.note == 49 or msg.note == 57: # G
                        note_str = f"N 68 0{' ' + flag if flag else ''}"
                        chart_data["ExpertDrums"][chart_tick].append(note_str)
        
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
        with open(output_file_dir, 'w') as f:
            f.write(chart_text)

        if os.path.exists(output_file_dir):
            print(f".chart file successfully created at: {output_file_dir}")
        else:
            print("Error: Failed to create .chart file or file is empty")

        # Write chart file to S3
        with open(output_file_dir, 'rb') as f:
            self.chart_bucket.write_file(key=out_file_key, data=f)