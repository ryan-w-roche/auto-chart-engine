# Imports and Setup
from mido import MidiFile, MidiTrack, MetaMessage
from .data.file_data import S3FileManager
from dotenv import load_dotenv

import os
import io

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
        self.split_midi_bucket = S3FileManager(
            bucket_name=self.chart_bucket_name,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name
        )

    # TODO: Docstring
    def split_midi(self, in_file_dir: str):
        # Write raw MIDI file to S3
        in_file_key = os.path.basename(in_file_dir)         # Extract just the file name
        with open(in_file_dir, 'rb') as f:
            self.raw_midi_bucket.write_file(key=in_file_key, data=f)

        base, ext = os.path.splitext(in_file_key)           # Split into name and extension
        formatted_base = base.lower().replace(' ', '_')     # Convert the base name to lowercase and replace spaces with underscores
        out_file_key = f"{formatted_base}_DRUMS{ext}"       # Append "_DRUMS" and then the original extension

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

        # Write split MIDI file to S3
        output_buffer = io.BytesIO()
        out_mid.save(file=output_buffer)
        output_buffer.seek(0)
        self.split_midi_bucket.write_file(key=out_file_key, data=output_buffer.getvalue())

        # Save and return
        return out_file_key
    
    def convert_to_chart(self, in_file_key: str, out_dir: str):
        pass