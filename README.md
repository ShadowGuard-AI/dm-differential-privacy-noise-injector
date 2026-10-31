![Banner](banner.png)

# dm-differential-privacy-noise-injector
Adds Laplacian noise to numerical data. This is a per value Laplace mechanism with an operator supplied sensitivity and epsilon. Sensitivity is asserted by the operator and is never checked against the data, and no epsilon budget is tracked across runs, so running the same data more than once adds up in a way this tool does not record or limit. - Focused on Tools designed to generate or mask sensitive data with realistic-looking but meaningless values

## Choosing parameters

Epsilon is the privacy parameter for a single run. A smaller epsilon adds more noise and gives stronger privacy for that run. A larger epsilon adds less noise and gives weaker privacy, so the output stays closer to the original values.
Sensitivity is the largest change one person or one record could make to a value in the named column, in the units of that column. Set it from what you know about the data before you run the tool. If a column can span hundreds, a sensitivity of 1 is too small for that column. The default sensitivity is 1.0.
The output file must not be the same file as the input file. A run that noises no values exits with an error and writes no output file.

## Install
`git clone https://github.com/ShadowStrikeHQ/dm-differential-privacy-noise-injector`

## Usage
`./dm-differential-privacy-noise-injector [params]`

## Parameters
- `-h`: Show help message and exit
- `--sensitivity`: No description provided
- `--column`: No description provided
- `--delimiter`: No description provided

## License
Copyright (c) ShadowStrikeHQ
