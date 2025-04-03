from argparse import ArgumentParser
from ace.translate import ChartTranslator

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
    charter = ChartTranslator()
    split_midi_key = charter.split_midi(in_file_dir=args.input_dir, out_dir=args.output_dir)

    # Convert to .chart file
    charter.convert_to_chart(in_file_key=split_midi_key, out_dir=args.output_dir)

if __name__ == "__main__":
    main()