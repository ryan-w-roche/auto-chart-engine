# Imports and Setup
from mido import MidiFile, MidiTrack, MetaMessage

import os

class Splitter:
    # TODO: Docstring
    def __init__(self):
        pass

    def split_midi(self, in_file_dir: str = None):
        file_name = os.path.basename(in_file_dir)           # Extract just the file name
        base, ext = os.path.splitext(file_name)             # Split into name and extension
        formatted_base = base.lower().replace(' ', '_')     # Convert the base name to lowercase and replace spaces with underscores
        out_file_name = f"{formatted_base}_DRUMS{ext}"      # Append "_DRUMS" and then the original extension
        out_file_dir = f"../songs/split_midi_songs/{out_file_name}"

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

        # Save and return
        out_mid.save(out_file_dir)