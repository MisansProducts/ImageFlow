from collections import defaultdict
import itertools
import os
from pathlib import Path
import re
import shutil
import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional

import imagehash
import imageio
from PIL import Image, ImageOps
import rawpy

class InputPanel(tk.Frame):
    def __init__(self, master: Optional[tk.Widget]=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Housekeeping
        self._CTRL_CHARS_RE = re.compile(r"[\x00-\x1F]") # ASCII control chars 0x00–0x1F (NUL through Unit Separator)
        self._WINDOWS_RESERVED = {
            "CON", "PRN", "AUX", "NUL",
            *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))
        }

        # Configuration
        self.font = ('Arial', 12)
        self.font_small = ('Arial', 10)
        self.font_mono = ('Courier New', 12)

        # Variables
        self._init_variables()

        # UI Setup
        self._create_widgets()
        self._setup_binds()
        self._setup_layout()

        # Sets defaults
        self.sort_dims_combobox.current(0) # None
        self.exts_combobox.current(0) # .png
        self.name_entry.focus()
    
    def _init_variables(self):
        """Initializes Tkinter variables and traces."""
        self.name_var = tk.StringVar()
        self.name_var.trace_add("write", self.on_name_change)

        self.number_var = tk.StringVar()
        self.number_var.trace_add("write", self.on_number_change)

        self.space_var = tk.BooleanVar(value=True)

        self.rename_var = tk.BooleanVar(value=False)

        self.filter_dupes_var = tk.BooleanVar(value=False)

        self.tolerance_var = tk.DoubleVar(value=5.0)
    
    def _create_widgets(self):
        """Initializes all widgets."""
        # Validation variables
        name_vc = (self.register(self.validate_name), '%P')
        number_vc = (self.register(self.validate_number), '%P')
        
        # --- Row 0 ---
        self.name_label = tk.Label(self, text="Image name", font=self.font)
        self.row0_frame = tk.Frame(self)
        self.name_entry = ttk.Entry(self.row0_frame, textvariable=self.name_var, validate="key", validatecommand=name_vc, width=22, font=self.font)
        self.space_check = tk.Checkbutton(self.row0_frame, variable=self.space_var, text="Presume space?", command=self.on_name_change, font=self.font_small)
        self.rename_check = tk.Checkbutton(self.row0_frame, variable=self.rename_var, text="Rename only?", command=self.on_rename_change, font=self.font_small)

        # --- Row 1 ---
        self.number_label = tk.Label(self, text="Starting number", font=self.font)
        self.row1_frame = tk.Frame(self)
        self.number_entry = ttk.Entry(self.row1_frame, textvariable=self.number_var, validate="key", validatecommand=number_vc, width=4, font=self.font)
        self.sort_dims_label = tk.Label(self.row1_frame, text="Sort dimension", font=self.font_small)
        self.sort_dims_combobox = ttk.Combobox(self.row1_frame, values=["None", "Width", "Height"], width=6, font=self.font_small, state="readonly")
        self.filter_dupes_check = tk.Checkbutton(self.row1_frame, variable=self.filter_dupes_var, text="Filter duplicates?", command=self.on_filter_dupes_change, font=self.font_small)
        self.tolerance_label = tk.Label(self.row1_frame, text="Tolerance", font=self.font_small, state="disabled")
        self.tolerance_scale = ttk.Scale(self.row1_frame, variable=self.tolerance_var, from_=0, to=10, length=125, command=lambda _: self.on_tolerance_change(), state="disabled")
        self.tolerance_number_label = tk.Label(self.row1_frame, text="0.5", font=self.font_small, state="disabled")
        
        # --- Row 2 ---
        self.exts_label = tk.Label(self, text="Extension", font=self.font)
        self.exts_combobox = ttk.Combobox(self, values=[".png", ".jpeg"], width=4, font=self.font, state="readonly")

        # --- Row 3 ---
        self.preview_label = tk.Label(self, text="Preview", font=self.font)
        self.preview_frame = tk.Frame(self)
        self.result_name_label = tk.Label(self.preview_frame, text="Image ", font=self.font_mono, bd=0, padx=0)
        self.result_number_label = tk.Label(self.preview_frame, text="1", font=self.font_mono, bd=0, padx=0)
        self.result_extension_label = tk.Label(self.preview_frame, text=".png", font=self.font_mono, bd=0, padx=0)
    
    def _setup_binds(self):
        """Sets up bindings for widgets."""
        # Adds click-to-jump functionality for the tolerance scale
        def jump_to_mouse(event: tk.Event):
            self.tolerance_scale.event_generate('<Button-2>', x=event.x, y=event.y) # does exactly what right-click does
            return "break" # stops the default "step" behavior
        self.tolerance_scale.bind('<Button-1>', jump_to_mouse)

        # Allows selecting an option in the extensions combobox to trigger on_extension_change()
        self.exts_combobox.bind("<<ComboboxSelected>>", self.on_extension_change)

    def _setup_layout(self):
        """Places widgets using consistent grid layout for main rows, packs for sub-widgets."""
        pad_opts = {'padx': 10, 'pady': 5, 'sticky': 'w'}
        label_opts = {'sticky': 'e'}
        
        # --- Row 0 ---
        self.name_label.grid(row=0, column=0, **label_opts)
        self.row0_frame.grid(row=0, column=1, columnspan=3, **pad_opts)
        self.name_entry.pack(side="left")
        self.space_check.pack(side="left", padx=(10, 0))
        self.rename_check.pack(side="left", padx=(5, 0))

        # --- Row 1 ---
        self.number_label.grid(row=1, column=0, **label_opts)
        self.row1_frame.grid(row=1, column=1, columnspan=3, **pad_opts)
        self.number_entry.pack(side="left")
        self.sort_dims_label.pack(side="left", padx=(10, 0))
        self.sort_dims_combobox.pack(side="left", padx=(5, 0))
        self.filter_dupes_check.pack(side="left", padx=(10, 0))
        self.tolerance_label.pack(side="left", padx=(5, 0))
        self.tolerance_scale.pack(side="left")
        self.tolerance_number_label.pack(side="left")

        # --- Row 2 ---
        self.exts_label.grid(row=2, column=0, **label_opts)
        self.exts_combobox.grid(row=2, column=1, **pad_opts)
        
        # --- Row 3 ---
        self.preview_label.grid(row=3, column=0, **label_opts)
        self.preview_frame.grid(row=3, column=1, columnspan=3, **pad_opts)
        self.result_name_label.pack(side="left")
        self.result_number_label.pack(side="left")
        self.result_extension_label.pack(side="left")
    
    def validate_name(self, proposed: str) -> bool:
        # Allow clearing the field
        if proposed == "":
            return True

        # Disallow ASCII control characters (includes NUL)
        if self._CTRL_CHARS_RE.search(proposed):
            return False

        # Disallow Windows-forbidden characters: < > : " / \ | ? *
        if any(ch in proposed for ch in '<>:"/\\|?*'):
            return False

        # Disallow Windows reserved device names (case-insensitive), even with extension
        base = proposed.split(".", 1)[0].strip().upper()
        if base in self._WINDOWS_RESERVED:
            return False

        return True
    
    def validate_number(self, input: str) -> bool:
        if input.isdigit() or input == "":
            return True
        return False
    
    def on_name_change(self, *args):
        text = self.name_var.get()
        if self.space_var.get():
            display_text = f"{text} " if text else "Image "
        else:
            display_text = f"{text}" if text else "Image"
        self.result_name_label.config(text=display_text)
    
    def on_rename_change(self):
        if self.rename_var.get():
            self.exts_label.config(state="disabled")
            self.exts_combobox.config(state="disabled")
            self.result_extension_label.config(text=".*")
        else:
            self.exts_label.config(state="normal")
            self.exts_combobox.config(state="readonly")
            self.result_extension_label.config(text=self.exts_combobox.get())
    
    def on_number_change(self, *args):
        num = self.number_var.get()
        self.result_number_label.config(text=num if num else "1")
    
    def on_filter_dupes_change(self):
        if self.filter_dupes_var.get():
            self.tolerance_label.config(state="normal")
            self.tolerance_scale.config(state="enabled")
            self.tolerance_number_label.config(state="normal")
        else:
            self.tolerance_label.config(state="disabled")
            self.tolerance_scale.config(state="disabled")
            self.tolerance_number_label.config(state="disabled")

    def on_tolerance_change(self, _=None):
        value = round(self.tolerance_var.get(), 1) # rounds to nearest 0.1
        self.tolerance_var.set(value)
        self.tolerance_number_label.config(text=f"{value:.1f}")
    
    def on_extension_change(self, *args):
        self.result_extension_label.config(text=self.exts_combobox.get())
    
    def get_values(self) -> Dict[str, Any]:
        return {
            'name': self.name_entry.get(),
            'number': self.number_entry.get(),
            'extension': self.exts_combobox.get(),
            'presume_space': self.space_var.get(),
            'rename_only': self.rename_var.get(),
            'dimension': self.sort_dims_combobox.get(),
            'filter_dupes': self.filter_dupes_var.get(),
            'tolerance': self.tolerance_var.get()
        }
    
class Main:
    def __init__(self, root: tk.Tk):
        # Housekeeping
        self.root = root
        self.root.title("ImageFlow")
        self.root.geometry("800x450")
        self.input_path = Path('Input')
        self.output_path = Path('Output')
        self.dupes_path = Path('Duplicates')
        self.unsorted_images = []
        
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

        # Default variables
        self.default_name = "Image"
        self.default_number = 1
        self.default_extension = 'PNG'
        self.default_presume_space = True
        self.default_rename_only = False
        self.default_dimension = 'None'
        self.default_filter_dupes = False
        self.default_tolerance = 5.0

        self.default_num_digits = 1

        # Variables
        self.name = self.default_name
        self.number = self.default_number
        self.extension = self.default_extension
        self.presume_space = self.default_presume_space
        self.rename_only = self.default_rename_only
        self.dimension = self.default_dimension
        self.filter_dupes = self.default_filter_dupes
        self.tolerance = self.default_tolerance

        self.num_digits = self.default_num_digits

    def debug_values(self):
        """Prints the values used in the image conversion along with their types."""
        print("--- Defaults ---")
        defaults = [
            ('default_name', self.default_name),
            ('default_number', self.default_number),
            ('default_extension', self.default_extension),
            ('default_presume_space', self.default_presume_space),
            ('default_rename_only', self.default_rename_only),
            ('default_dimension', self.default_dimension),
            ('default_filter_dupes', self.default_filter_dupes),
            ('default_tolerance', self.default_tolerance),
            ('default_num_digits', self.default_num_digits)
        ]
        for var_name, value in defaults:
            print(f"{var_name}: {value} ({type(value).__name__})")
        
        print("\n--- Current ---")
        values = [
            ('name', self.name),
            ('number', self.number),
            ('extension', self.extension),
            ('presume_space', self.presume_space),
            ('rename_only', self.rename_only),
            ('dimension', self.dimension),
            ('filter_dupes', self.filter_dupes),
            ('tolerance', self.tolerance),
            ('num_digits', self.num_digits)
        ]
        for var_name, value in values:
            print(f"{var_name}: {value} ({type(value).__name__})")

    def _iter_togglables(self) -> list[tk.Misc]:
        """Helper function that returns all widgets in InputPanel."""
        return [
            self.input_panel.name_label,
            self.input_panel.name_entry,
            self.input_panel.space_check,
            self.input_panel.rename_check,
            self.input_panel.number_label,
            self.input_panel.number_entry,
            self.input_panel.sort_dims_label,
            self.input_panel.sort_dims_combobox,
            self.input_panel.filter_dupes_check,
            self.input_panel.tolerance_label,
            self.input_panel.tolerance_scale,
            self.input_panel.tolerance_number_label,
            self.input_panel.exts_label,
            self.input_panel.exts_combobox,
            self.input_panel.preview_label,
            self.input_panel.result_name_label,
            self.input_panel.result_number_label,
            self.input_panel.result_extension_label,
            self.convert_button,
        ]

    def disable_elements(self):
        # Snapshots current states for each widget, then disables
        self._prev_states = {w: w.cget("state") for w in self._iter_togglables()}
        for w in self._iter_togglables():
            w.config(state="disabled")

    def restore_elements(self):
        # Restores each widget's previous state
        for w, st in getattr(self, "_prev_states", {}).items():
            w.config(state=st)
            
    def convert_command(self):
        # Parses input values
        input_values = self.input_panel.get_values()

        self.name = str(input_values['name']) if input_values['name'] else self.default_name
        self.number = int(input_values['number']) if input_values['number'] else self.default_number
        self.extension = str(input_values['extension']).upper()[1:] if input_values['extension'] else self.default_extension
        self.presume_space = bool(input_values['presume_space']) if input_values.get('presume_space') is not None else self.default_presume_space
        self.rename_only = bool(input_values['rename_only']) if input_values.get('rename_only') is not None  else self.default_rename_only
        self.dimension = str(input_values['dimension']).lower() if input_values['dimension'] else self.default_dimension
        self.filter_dupes = bool(input_values['filter_dupes']) if input_values.get('filter_dupes') is not None else self.default_filter_dupes
        self.tolerance = float(input_values['tolerance']) if input_values.get('tolerance') is not None else self.default_tolerance
        
        self.num_digits = len(input_values['number']) if input_values['number'] else self.default_num_digits

        # Runs the command
        self.disable_elements()
        threading.Thread(target=self.run, daemon=True).start()
    
    def ensure_dirs(self):
        """Verifies that the input, output, and dupes directories exist or creates them if necessary."""
        # Creates input directory
        if not self.input_path.exists():
            self.input_path.mkdir(parents=True)
            return print(f"Creating a folder named '{self.input_path.name}'.\nPlease move unsorted images into the '{self.input_path.name}' directory.")
        
        # Ensures that images exist in the input directory
        # TO DO: Replace extensions with a try-except to open the image to prevent errors further down the pipeline
        extensions = {'.png', '.jpg', '.jpeg', '.arw', '.nef', '.webp', '.txt'}
        if not any(file.suffix.lower() in extensions for file in self.input_path.iterdir() if file.is_file()):
            return print(f"There are no images to sort!\nPlease move unsorted images into the '{self.input_path.name}' directory.")
        
        # Gets a list of all the unsorted images
        self.unsorted_images = [file.name for file in self.input_path.iterdir() if file.is_file() and file.suffix.lower() in extensions]
            
        # Creates output directory
        if not self.output_path.exists():
            self.output_path.mkdir(parents=True)
            print(f"Creating a folder named '{self.output_path.name}'.")
        
        # Creates dupes directory
        if not self.dupes_path.exists():
            self.dupes_path.mkdir(parents=True)
            print(f"Creating a folder named '{self.dupes_path.name}'. Duplicate images will be moved here, if filtering out duplicates is selected.")
    
    def _convert(self, source_filename: str, target_filename: str):
        """Helper function to convert one image file format to another."""
        target_filename = f"{target_filename}{self.number:0{self.num_digits}d}.{self.extension.lower()}"
        src = Path(os.path.join(self.input_path, source_filename))
        dst = Path(os.path.join(self.output_path, target_filename))
        if src.suffix.lower() in {'.arw', '.nef'}: # Accounts for Sony RAW format
            with rawpy.imread(src) as raw:
                rgb = raw.postprocess() # Demosaics and converts to RGB
            imageio.imsave(dst, rgb)
        else: # All other native image formats
            img = Image.open(src)
            img = ImageOps.exif_transpose(img) # Auto-rotates based on EXIF
            img = img.convert("RGB")
            img.save(dst, self.extension)
        print(f"Converted {source_filename} to {target_filename}")
    
    def _rename(self, source_filename: str, target_filename: str):
        """Helper function to rename an image."""
        target_filename = f"{target_filename}{self.number:0{self.num_digits}d}{Path(source_filename).suffix}"
        src = Path(os.path.join(self.input_path, source_filename))
        dst = Path(os.path.join(self.output_path, target_filename))
        shutil.copy2(src, dst)
        print(f"Renamed {source_filename} to {target_filename}")

    def _filter_dupes(self):
        if not self.filter_dupes:
            return
        
        # Step 1: hash all images
        print("Computing image hashes...")
        hashes = []
        for filename in self.unsorted_images:
            src = Path(os.path.join(self.input_path, filename))
            try:
                with Image.open(src) as img:
                    hashes.append((filename, imagehash.dhash(img)))
            except Exception as e:
                print(f"\tError hashing {filename}: {e}")
        print(f"Processed {len(hashes)} images.")

        # Step 2: Union-find setup
        # Initially, each filename is is a parent of itself and has a rank/height of 0; disjoint sets
        parent = {filename: filename for filename, _ in hashes}
        rank = {filename: 0 for filename, _ in hashes}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]] # path compression
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            
            # union by rank
            if rank[ra] < rank[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            if rank[ra] == rank[rb]:
                rank[ra] += 1
        
        # Step 3: Build edges by tolerance, union into components
        for (filename1, hash1), (filename2, hash2) in itertools.combinations(hashes, 2):
            if hash1 - hash2 <= self.tolerance:
                union(filename1, filename2)
        
        # Step 4: Collect components
        groups = defaultdict(list)
        for filename, _, in hashes:
            groups[find(filename)].append(filename)
        
        # Step 5: Choose the best candidate to keep
        def score(filename):
            src = Path(os.path.join(self.input_path, filename))
            try:
                with Image.open(src) as img:
                    width, height = img.size
            except Exception:
                width, height = 0, 0
            return (src.stat().st_size, width * height)
        
        print("Moving duplicate images...")
        kept = []
        for _, files, in groups.items():
            # A disjoint set by itself; no similar images to this image
            if len(files) == 1:
                kept.append(files[0])
                continue
            
            keep = max(files, key=score)
            kept.append(keep)

            for filename in files:
                if filename == keep:
                    continue
                self.unsorted_images.remove(filename)
                src = Path(os.path.join(self.input_path, filename))
                dst = Path(os.path.join(self.dupes_path, filename))
                shutil.move(src, dst)
                print(f"\tMoved {src} to {dst}")
        print(f"Kept {len(kept)} images.")
        
    def run(self):
        self.ensure_dirs()
        self._filter_dupes()

        my_name = f"{self.name} " if self.presume_space else self.name
        sorted_images = sorted(self.unsorted_images, key=self.dimension_sort_key if self.dimension != 'none' else self.natural_sort_key)

        for filename in sorted_images:
            process_fn = self._rename if self.rename_only else self._convert
            process_fn(filename, my_name)
            self.number += 1

        print("All done!\n")

        self.root.after(0, self.restore_elements)

    # Sorting algorithm for numbers (1 to 1, 2 to 2, etc... instead of 1 to 1, 10 to 2, etc)
    def natural_sort_key(self, s: str):
        pattern = re.compile('([0-9]+)')
        return [int(c) if c.isdigit() else c.lower() for c in pattern.split(s)]
    
    # Sorting algorithm for dimensions (prioritizes width or height)
    def dimension_sort_key(self, filename: str):
        src = Path(os.path.join(self.input_path, filename))
        with Image.open(src) as img:
            width, height = img.size
            if self.dimension == 'height':
                return (-height, -width, self.natural_sort_key(filename))
            return (-width, -height, self.natural_sort_key(filename))

if __name__ == "__main__":
    root = tk.Tk()
    app = Main(root)
    root.mainloop()
