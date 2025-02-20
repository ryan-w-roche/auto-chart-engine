from argparse import ArgumentParser
from split import Splitter

import os

def main():
    parser = ArgumentParser()

    # Input directory
    parser.add_argument(
        "-i", "--input_dir",
        type=str,
        required=True,
        help="The directory of the MIDI file to split."
    )

    # Output directory
    home_dir = os.path.expanduser("~")
    parser.add_argument(
        "-o", "--output_dir",
        type=str,
        default=os.path.join(home_dir, "Downloads"),
        help="The directory to save the split MIDI file."
    )
    args = parser.parse_args()

    # LOGIC
    # Split the MIDI file
    splitter = Splitter()
    out_file_key = splitter.split_midi(in_file_key=args.input_dir)

    # Convert to .chart file

if __name__ == "__main__":
    main()