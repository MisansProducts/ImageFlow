import os
from pathlib import Path
import re

from PIL import Image

def main():
    # Sorting algorithm for numbers (1 to 1, 2 to 2, etc... instead of 1 to 1, 10 to 2, etc)
    def natural_sort_key(s):
        pattern = re.compile('([0-9]+)')
        return [int(c) if c.isdigit() else c for c in pattern.split(s)]
    
    # Creates input directory
    input_path = Path('Input')
    if not input_path.exists():
        input_path.mkdir(parents=True)
        return print(f"Creating a folder named '{input_path.name}'.\nPlease move unsorted images into the '{input_path.name}' directory.")
    
    # Creates output directory
    output_path = Path('Output')
    if not output_path.exists():
        output_path.mkdir(parents=True)
        print(f"Creating a folder named '{output_path.name}'.")
    
    # Checks if there are any images in the input directory
    extensions = {'.png', '.jpg', '.jpeg'}
    if not any(file.suffix.lower() in extensions for file in input_path.iterdir() if file.is_file()):
        return print(f"There are no images to sort!\nPlease move unsorted images into the '{input_path.name}' directory.")
    
    # Gets a list of all the unsorted images
    unsorted_images = [file.name for file in input_path.iterdir() if file.is_file() and file.suffix.lower() in extensions]

    # Name input
    my_name = input("File name: ") + " "

    # Number input
    try:
        i = int(input("Starting number: "))
    except:
        i = 1
        print("Input error... setting starting number to 1.")
    
    # Converts the unsorted images into PNG
    for filename in sorted(unsorted_images, key = natural_sort_key):
        new_name = my_name + str(i) + ".png"
        src = os.path.join(input_path, filename)
        dst = os.path.join(output_path, new_name)
        img = Image.open(src)
        img.save(dst, 'PNG')
        print(f"Converted {filename} to {new_name}")
        i += 1
    print("All done!")

if __name__ == '__main__':
    main()
