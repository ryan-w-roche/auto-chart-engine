# Referencing: https://github.com/Fureniku/Drum-MIDI-To-Clone-Hero-Converter/tree/main/src/com/fureniku/miditochdrums

import os
import mido
from collections import defaultdict

def midi_to_chart_format(midi_file_path):

    # Create accessor variable for mido library
        # The mido library is used to interact with midi files
    mid = mido.MidiFile(midi_file_path)
    
    # Enhanced drum mapping with combinations
        # x: = midi mapping number representing drum note
        # (x, = .chart mapping number representing note color
        # 'x') = text based identifier for manual analysis of .chart file
    DRUM_MAPPING = {
        35: (0, 'K'),  # Acoustic Bass Drum
        36: (0, 'K'),  # Bass Drum (Kick)
        38: (1, 'R'),   # Acoustic Snare
        40: (1, 'R'),   # Electric Snare
        42: (2, 'Y'),   # Closed Hi-Hat
        44: (2, 'Y'),   # Pedal Hi-Hat
        46: (3, 'B'),   # Open Hi-Hat
        49: (4, 'G'),   # Crash 1
        51: (4, 'G'),   # Ride Cymbal
        45: (2, 'Y'),   # Low Tom
        47: (2, 'Y'),   # Mid Tom
        48: (2, 'Y'),   # High Tom
        50: (4, 'G'),   # High Tom
        57: (4, 'G'),   # Crash 2
    }
    
    # Meta data for the songs .chart file
        # Included metadata:
            # "Name", "Charter", "Resolution"
        # All other meta data fields need to be manually inputted
    song_metadata = {
        "Name": os.path.splitext(os.path.basename(midi_file_path))[0],
        "Artist": "Unknown",
        "Charter": "AI Generated",
        "Album": "Generated Charts",
        "Year": "2024",
        "Offset": 0,
        "Resolution": 192,
        "Player2": "bass",
        "Difficulty": 0,
        "PreviewStart": 0,
        "PreviewEnd": 0,
        "Genre": "rock"
    }
    
    # Calculate song length and get tempo
    total_ticks = 0 # Default ticks
    tempo = 120000  # Default tempo (120 BPM)
    time_sig = (4, 4)  # Default time signature
    
    # Get initial tempo
    initial_tempo = None
    for track in mid.tracks: # For each track inside of the file path
        for msg in track: 
            if msg.type == 'set_tempo':
                # DELETE
                print(msg)
                initial_tempo = msg.tempo
                break
        if initial_tempo:
            break
    
    initial_tempo = initial_tempo or tempo
    
    for track in mid.tracks:
        track_ticks = 0
        for msg in track:
            track_ticks += msg.time
            if msg.type == 'set_tempo':
                tempo = msg.tempo
            elif msg.type == 'time_signature':
                time_sig = (msg.numerator, msg.denominator)
        total_ticks = max(total_ticks, track_ticks)
    
    print('Total Ticks:', track_ticks)
    # Calculate song length in milliseconds
    song_length = (total_ticks * tempo) / (mid.ticks_per_beat * 1000000)
    print('Song Length in Seconds:',song_length)
    song_metadata["Length"] = int(song_length * 1000)
    
    chart_data = {
        "Song": song_metadata,
        "SyncTrack": defaultdict(list),
        "Events": {},
        "ExpertDrums": defaultdict(list)
    }
    
    # Add initial sync track events
    chart_data["SyncTrack"][0].append(f"B {initial_tempo}")
    chart_data["SyncTrack"][0].append(f"TS {time_sig[0]}")
    
    # Calculate initial ticks multiplier based on tempo
    ticks_multiplier = (mid.ticks_per_beat * 192) / (initial_tempo / 1000000 * 60)
    print(ticks_multiplier)
    
    # Process MIDI messages with corrected tick calculation
    current_tick = 0
    for track in mid.tracks:
        for msg in track:
            current_tick += msg.time
            # Convert MIDI ticks to chart ticks using the tempo-based multiplier
            chart_tick = int(current_tick * ticks_multiplier / mid.ticks_per_beat)
            
            if msg.type == 'note_on' and msg.velocity > 0:
                if hasattr(msg, 'channel') and msg.channel == 9 and msg.note in DRUM_MAPPING:
                    note_num, flag = DRUM_MAPPING[msg.note]
                    note_str = f"N {note_num} 0{' ' + flag if flag else ''}"
                    chart_data["ExpertDrums"][chart_tick].append(note_str)
            elif msg.type == 'set_tempo':
                # Update tempo in the sync track
                chart_data["SyncTrack"][chart_tick].append(f"B {msg.tempo}")
                # Recalculate ticks multiplier for new tempo
                ticks_multiplier = (mid.ticks_per_beat * 192) / (1000000 * 240 / msg.tempo)
            elif msg.type == 'time_signature':
                chart_data["SyncTrack"][chart_tick].append(f"TS {msg.numerator}")
    
    # Format the chart file
    chart_text = "[Song]\n{\n"
    for key, value in chart_data["Song"].items():
        chart_text += f"  {key} = {value if isinstance(value, (int, float)) else f'{value}'}\n"
    chart_text += "}\n\n"
    
    chart_text += "[SyncTrack]\n{\n"
    for tick in sorted(chart_data["SyncTrack"].keys()):
        for event in chart_data["SyncTrack"][tick]:
            chart_text += f"  {tick} = {event}\n"
    chart_text += "}\n\n"
    
    chart_text += "[Events]\n{\n}\n\n"
    
    chart_text += "[ExpertDrums]\n{\n"
    for tick in sorted(chart_data["ExpertDrums"].keys()):
        for note in chart_data["ExpertDrums"][tick]:
            chart_text += f"  {tick} = {note}\n"
    chart_text += "}\n"
    
    return chart_text

def generate_chart(midi_file_path, output_path):
    chart_content = midi_to_chart_format(midi_file_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(chart_content)

if __name__ == '__main__':
    midi_file_path = './songs/midi_songs/test-split.mid'
    track_name = os.path.splitext(os.path.basename(midi_file_path))[0]
    chart_path = f'./songs/chart_files/{track_name}.chart'
    generate_chart(midi_file_path=midi_file_path, output_path=chart_path)
