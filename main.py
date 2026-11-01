import argparse
import logging
import sys
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.

    Returns:
        argparse.ArgumentParser: The argument parser object.
    """
    parser = argparse.ArgumentParser(description='Adds Laplacian noise to numerical data for differential privacy.')

    parser.add_argument('data_file', type=str, help='Path to the numerical data file (CSV).')
    parser.add_argument('epsilon', type=float, help='Privacy parameter epsilon (higher value means less privacy). Must be a positive number.')
    parser.add_argument('output_file', type=str, help='Path to the output file with noisy data.')
    parser.add_argument('--sensitivity', type=float, default=1.0, help='Sensitivity of the data (default: 1.0).')
    parser.add_argument('--column', type=int, default=0, help='Column index to apply noise to (default: 0).')
    parser.add_argument('--delimiter', type=str, default=',', help='Delimiter used in the data file (default: comma).')

    return parser

def laplace_noise(sensitivity, epsilon):
    """
    Generates Laplacian noise.

    Args:
        sensitivity (float): The sensitivity of the data.
        epsilon (float): The privacy parameter epsilon.

    Returns:
        float: A single Laplacian noise value.
    """
    try:
        if epsilon <= 0:
            raise ValueError("Epsilon must be a positive number.")
        
        # Each value draws its own noise at the full scale, sensitivity
        # divided by epsilon, and nothing in this tool splits epsilon
        # across the rows of a file or keeps a running total of what a
        # file has spent. The parameter describes one value at a time.
        # Anyone adding up the privacy cost of a whole release has to do
        # that accounting themselves, outside this tool. There is also no
        # seed anywhere in it: numpy draws from its global generator, so a
        # run cannot be reproduced or audited after the fact.
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return noise
    except Exception as e:
        logging.error(f"Error generating Laplacian noise: {e}")
        raise

def apply_differential_privacy(data_file, epsilon, output_file, sensitivity=1.0, column=0, delimiter=','):
    """
    Applies differential privacy by adding Laplacian noise to the specified column in the data file.

    Args:
        data_file (str): Path to the numerical data file (CSV).
        epsilon (float): Privacy parameter epsilon.
        output_file (str): Path to the output file with noisy data.
        sensitivity (float, optional): Sensitivity of the data. Defaults to 1.0.
        column (int, optional): Column index to apply noise to. Defaults to 0.
        delimiter (str, optional): Delimiter used in the data file. Defaults to ','.
    """
    # Validate before opening the output file. Checking epsilon inside
    # laplace_noise, as this code used to, meant an invalid epsilon was
    # only discovered after the output file had been created and its
    # first lines written, leaving a truncated file that looks usable.
    # A negative column was worse: it passed the range check below and
    # Python indexing quietly noised the last column instead.
    if epsilon <= 0:
        logging.error("Epsilon must be a positive number.")
        sys.exit(1)
    if sensitivity <= 0:
        logging.error("Sensitivity must be a positive number.")
        sys.exit(1)
    if column < 0:
        logging.error("Column index cannot be negative.")
        sys.exit(1)
    if Path(data_file).resolve() == Path(output_file).resolve():
        logging.error("Output file must not be the same as the input file.")
        sys.exit(1)
    try:
        with open(data_file, 'r') as infile:
            raw_lines = infile.readlines()
    except FileNotFoundError:
        logging.error(f"Data file not found: {data_file}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)
    output_lines = []
    noised_count = 0
    try:
        for i, raw_line in enumerate(raw_lines):
            line = raw_line.strip()
            values = line.split(delimiter)
            if len(values) <= column:
                logging.error(f"Column index {column} is out of range for line {i+1}.  Skipping this line.")
                output_lines.append(line + '\n')
                continue
            try:
                numerical_value = float(values[column])
            except ValueError:
                # A skipped line is written out exactly as it came in. That
                # is what saves a header row: it fails the float test and
                # passes through untouched. It is also what leaves a stray
                # text value sitting in the noised column in the clear, and
                # the run still succeeds as long as one other value noised.
                logging.error(f"Non-numerical value found in column {column} on line {i+1}. Skipping this line.")
                output_lines.append(line + '\n')
                continue
            noise = laplace_noise(sensitivity, epsilon)
            noisy_value = numerical_value + noise
            # Only the target cell is rewritten, as a full precision float
            # string; every other cell keeps its original text byte for
            # byte, including its formatting. A short input like 5 comes
            # out as a long decimal, and that shape change is visible in
            # every noised row. float() also accepts nan and inf here, and
            # noise added to either one changes nothing about them.
            noisy_values = values[:]
            noisy_values[column] = str(noisy_value)
            output_lines.append(delimiter.join(noisy_values) + '\n')
            noised_count += 1
        if noised_count == 0:
            logging.error("No values were noised.")
            sys.exit(1)
        with open(output_file, 'w') as outfile:
            outfile.writelines(output_lines)
        logging.info(f"Differential privacy applied successfully. Noisy data written to {output_file}")

    except FileNotFoundError:
        logging.error(f"Data file not found: {data_file}")
        sys.exit(1)
    except ValueError as ve:
         logging.error(f"Value Error: {ve}")
         sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    """
    Main function to parse arguments and apply differential privacy.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    try:
        apply_differential_privacy(args.data_file, args.epsilon, args.output_file, args.sensitivity, args.column, args.delimiter)
    except Exception as e:
        logging.error(f"Error during differential privacy application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """
    Usage Examples:

    1. Basic usage:
       python main.py data.csv 1.0 noisy_data.csv

    2. Specifying sensitivity and column index:
       python main.py data.csv 0.5 noisy_data.csv --sensitivity 0.5 --column 2

    3. Using a different delimiter:
       python main.py data.csv 2.0 noisy_data.csv --delimiter ';'
    """
    main()