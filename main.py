import os
from pathlib import Path
import re
import shutil
import tkinter as tk
from tkinter import ttk

import imageio
from PIL import Image, ImageOps
import rawpy

class InputPanel(tk.Frame):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        # Housekeeping
        font=('Arial', 12)
        self.number_vc = self.register(self.validate_number)
        self.space_var = tk.BooleanVar(value=True)
        self.rname_var = tk.BooleanVar(value=False)

        # Creates widgets
        self.name_label = tk.Label(self, text="Image name", font=font)
        self.name_entry = ttk.Entry(self, width=22, font=font)
        self.number_label = tk.Label(self, text="Starting number", font=font)
        self.number_entry = ttk.Entry(self, validate="key", validatecommand=(self.number_vc, '%P'), width=4, font=font)
        self.space_checkbutton = tk.Checkbutton(self, text="Presume space?", variable=self.space_var, font=font)
        self.rname_checkbutton = tk.Checkbutton(self, text="Rename only?", variable=self.rname_var, font=font)

        # Packs widgets
        self.name_label.grid(row=0, column=0, sticky="e")
        self.name_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="w")
        self.number_label.grid(row=1, column=0, sticky="e")
        self.number_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.space_checkbutton.grid(row=1, column=2, padx=(0, 10), pady=5, sticky="w")
        self.rname_checkbutton.grid(row=1, column=3, padx=(0, 10), pady=5, sticky="w")
        
        # Configures grid columns
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Sets focus to name_entry
        self.name_entry.focus()
    
    def validate_number(self, input: str):
        if input.isdigit() or input == "":
            return True
        return False
    
    def get_values(self):
        return {
            'name': self.name_entry.get(),
            'number': self.number_entry.get(),
            'presume_space': self.space_var.get(),
            'rename_only': self.rname_var.get()
        }

class Main:
    def __init__(self, root: tk.Tk):
        # Housekeeping
        self.root = root
        self.root.title("ImageFlow")
        self.root.geometry("800x450")
        
        # Creates widgets
        top = tk.Frame(root, height=0) # Placeholder
        self.input_panel = InputPanel(root)
        self.convert_button = tk.Button(root, text="Convert", command=self.convert_command, width=40, font=('Arial', 12))
        bottom = tk.Frame(root, height=0) # Placeholder
        
        # Packs widgets
        top.pack(expand=True)
        self.input_panel.pack(anchor='w')
        self.convert_button.pack(anchor='center')
        bottom.pack(expand=True)

        # Variables
        self.default_name = "Image"
        self.default_start = 1
        self.default_space = True
        self.name = self.default_name
        self.start = self.default_start
        self.space = self.default_space
        self.my_name = f"{self.name} " if self.space else self.name
        self.i = self.start
        self.num_digits = 1

    def convert_command(self):
        self.toggle_elements("disabled")

        # Parses input values
        input_values = self.input_panel.get_values()
        self.name = str(input_values['name']) if input_values['name'] else self.default_name
        self.start = int(input_values['number']) if input_values['number'] else self.default_start
        self.space = bool(input_values['presume_space'])

        # Sets values
        self.my_name = f"{self.name} " if self.space else self.name
        self.i = self.start
        self.num_digits = len(input_values['number'])

        # Runs the command
        self.run(bool(input_values['rename_only']))
    
    def toggle_elements(self, state):
        self.input_panel.name_entry.config(state=state)
        self.input_panel.number_entry.config(state=state)
        self.input_panel.space_checkbutton.config(state=state)
        self.convert_button.config(state=state)
    
    def run(self, rename_only=False):
        # Creates input directory
        input_path = Path('Input')
        if not input_path.exists():
            input_path.mkdir(parents=True)
            self.root.update()
            self.toggle_elements("normal")
            return print(f"Creating a folder named '{input_path.name}'.\nPlease move unsorted images into the '{input_path.name}' directory.")
        
        if not rename_only:
            # Checks if there are any images in the input directory
            extensions = {'.png', '.jpg', '.jpeg', '.arw', '.nef', '.webp'}
            if not any(file.suffix.lower() in extensions for file in input_path.iterdir() if file.is_file()):
                self.root.update()
                self.toggle_elements("normal")
                return print(f"There are no images to sort!\nPlease move unsorted images into the '{input_path.name}' directory.")
            
            # Gets a list of all the unsorted images
            unsorted_images = [file.name for file in input_path.iterdir() if file.is_file() and file.suffix.lower() in extensions]
        else:
            if not any(item.is_file() for item in input_path.iterdir()):
                self.root.update()
                self.toggle_elements("normal")
                return print(f"There are no images to sort!\nPlease move unsorted images into the '{input_path.name}' directory.")
            
            # Technically can rename any file, not just images
            unsorted_images = [file.name for file in input_path.iterdir() if file.is_file()]
        
        # Creates output directory
        output_path = Path('Output')
        if not output_path.exists():
            output_path.mkdir(parents=True)
            print(f"Creating a folder named '{output_path.name}'.")
        
        # Converts the unsorted images into PNG
        for filename in sorted(unsorted_images, key = self.natural_sort_key):
            if not rename_only:
                new_name = f"{self.my_name}{self.i:0{self.num_digits}d}.png"
                src = os.path.join(input_path, filename)
                dst = os.path.join(output_path, new_name)
                if Path(src).suffix.lower() in {'.arw', '.nef'}: # Accounts for Sony RAW format
                    self.convert_raw_to_png(src, dst)
                else: # All other native image formats
                    img = Image.open(src)
                    img = ImageOps.exif_transpose(img) # Auto-rotates based on EXIF
                    img.save(dst, 'PNG')
                print(f"Converted {filename} to {new_name}")
            else:
                new_name = f"{self.my_name}{self.i:0{self.num_digits}d}{Path(filename).suffix}"
                src = os.path.join(input_path, filename)
                dst = os.path.join(output_path, new_name)
                shutil.copy2(src, dst)
                print(f"Renamed {filename} to {new_name}")
            self.i += 1
        print("All done!")
        self.root.update()
        self.toggle_elements("normal")
        
    def convert_raw_to_png(self, src, dst):
        with rawpy.imread(src) as raw:
            rgb = raw.postprocess() # Demosaics and converts to RGB
        imageio.imsave(dst, rgb)

    # Sorting algorithm for numbers (1 to 1, 2 to 2, etc... instead of 1 to 1, 10 to 2, etc)
    def natural_sort_key(self, s: str):
        pattern = re.compile('([0-9]+)')
        return [int(c) if c.isdigit() else c.lower() for c in pattern.split(s)]

if __name__ == "__main__":
    root = tk.Tk()
    app = Main(root)
    root.mainloop()
