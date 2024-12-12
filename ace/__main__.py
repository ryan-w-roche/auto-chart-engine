from argparse import ArgumentParser
from ace.charter import Charter

import os

def main():
    parser = ArgumentParser()

    # Input directory
    parser.add_argument(
        "-i", "--input_dir",
        type=str,
        required=True,
        help="The directory of the MIDI file to process"
    )

    # Output directory
    home_dir = os.path.expanduser("~")
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=os.path.join(home_dir, "Downloads"),
        help="The directory to save all output files"
    )
    args = parser.parse_args()

    # LOGIC
    # Split the MIDI file
    charter = Charter()
    split_midi_key = charter.split_midi(in_file_dir=args.input_dir, out_dir=args.output_dir)

    # Create Clone Hero folder
    song_name = os.path.basename(args.input_dir).replace('.mid', '').replace('_', ' ').title()
    ch_out_dir = f"artist - {song_name} (ACE)"
    os.makedirs(os.path.join(args.output_dir, ch_out_dir), exist_ok=True)
    
    # Convert to .chart file
    charter.generate_chart_file(
        in_file_key=split_midi_key,
        out_dir=args.output_dir,
        ch_out_dir=ch_out_dir
    )

    # Generate .ogg file
    charter.generate_ogg_file(
        in_file_key=split_midi_key,
        out_dir=args.output_dir,
        ch_out_dir=ch_out_dir
    )

if __name__ == "__main__":
    main()