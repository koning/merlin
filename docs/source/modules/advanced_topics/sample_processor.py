import argparse
import sys

import pandas as pd

def load_samples(sample_file_paths):
    """Read in processed sample files, returning flat list."""
    samples = []
    for sample_file_path in sample_file_paths:
        with open(sample_file_path, "r") as sample_file:
            for sample in sample_file:
                sample = sample.strip()
                samples.append(sample)

    return samples
                
def setup_argparse():
    parser = argparse.ArgumentParser(
        description="Read in and analyze samples from plain text file"
    )

    parser.add_argument(
        "sample_file_paths", help="paths to sample files", default="",
        nargs='+'
    )

    parser.add_argument("--results",
                        help="Name of output json file",
                        default="samples.json")
    
    return parser


def main():
    parser = setup_argparse()
    args = parser.parse_args()

    # Collect the samples
    samples = load_samples(args.sample_file_paths)

    # Count up the occurences
    namesdf = pd.DataFrame({"Name":samples})

    names = namesdf["Name"].value_counts()

    # Serialize processed samples
    names.to_json(args.results)
    
if __name__ == "__main__":
    sys.exit(main())
