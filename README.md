# ImageFlow

ImageFlow is a Python program that automates the process of renaming and converting image files to PNG format. It helps organize large collections of images with consistent naming conventions.

## Features

- Renames images sequentially with a custom prefix
- Converts images to PNG format
- Handles natural sorting of numbers (1, 2, 3... instead of 1, 10, 11...)
- Creates necessary directories automatically
- Simple command-line interface

## Requirements

- Python 3.11.5 or later
- Pillow 10.4.0 or later

## Installation

1. Clone or download this repository
2. Install Python from [python.org](https://www.python.org/downloads/)

## Usage

1. Place your unsorted images in the `Input` folder (will be created automatically if it doesn't exist)
2. Run `run.bat` (double-click or run from a command-line interface)
3. Enter your desired file name prefix when prompted
4. Enter the starting number for the sequence
5. The program will process all images and save them as PNGs in the `Output` folder

Example:
```
File name: Vacation
Starting number: 1
```
This will create files named "Vacation 1.png", "Vacation 2.png", etc.

## Important Notes

- Only image files (.png, .jpg, .jpeg) should be placed in the Input folder
- Non-image files may become corrupted if processed
- The program is particularly useful for organizing photos of the same subject or event

## Credits

Alex Akoopie - Creator
