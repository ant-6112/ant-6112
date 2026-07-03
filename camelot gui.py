import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser

from camelot_core import (
    FLAVORS, BACKENDS, TABLE_STYLE_PRESETS, default_config, run_pipeline,
)


class CamelotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Camelot PDF Table Extractor")
        self.geometry("880x720")
        self.minsize(800, 640)

        self.cfg_defaults = default_config()
        self.vars = {}
        self.log_queue = queue.Queue()
        self.worker_thread = None

        self._build_widgets()
        self._poll_log_queue()

    def _build_widgets(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill="both", expand=True)

        notebook = ttk.Notebook(container)
        notebook.pack(fill="both", expand=True)

        self._build_io_tab(notebook)
        self._build_extraction_tab(notebook)
        self._build_filters_tab(notebook)
        self._build_advanced_tab(notebook)
        self._build_style_tab(notebook)

        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(8, 0))

        self.run_button = ttk.Button(bottom, text="Run Extraction", command=self.start_run)
        self.run_button.pack(side="left")

        self.open_output_button = ttk.Button(bottom, text="Open Output Folder", command=self.open_output_folder)
        self.open_output_button.pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(bottom, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        log_frame = ttk.LabelFrame(container, text="Log")
        log_frame.pack(fill="both", expand=False, pady=(8, 0))
        self.log_text = tk.Text(log_frame, height=10, wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def _var(self, key, kind="str"):
        val = self.cfg_defaults[key]
        if kind == "bool":
            v = tk.BooleanVar(value=bool(val))
        elif kind == "int":
            v = tk.IntVar(value=int(val) if val is not None else 0)
        elif kind == "double":
            v = tk.DoubleVar(value=float(val) if val is not None else 0.0)
        else:
            v = tk.StringVar(value=val if val is not None else "")
        self.vars[key] = v
        return v

    def _build_io_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Input / Output")

        self.input_mode = tk.StringVar(value="file")
        mode_frame = ttk.Frame(tab)
        mode_frame.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Radiobutton(mode_frame, text="Single PDF file", variable=self.input_mode, value="file").pack(side="left")
        ttk.Radiobutton(mode_frame, text="Folder of PDFs", variable=self.input_mode, value="folder").pack(side="left", padx=(12, 0))

        ttk.Label(tab, text="Input path:").grid(row=1, column=0, sticky="w")
        input_var = self._var("input_path")
        ttk.Entry(tab, textvariable=input_var, width=70).grid(row=1, column=1, sticky="we", padx=6)
        ttk.Button(tab, text="Browse...", command=self.browse_input).grid(row=1, column=2)

        recursive_var = self._var("recursive", "bool")
        ttk.Checkbutton(tab, text="Scan subfolders recursively", variable=recursive_var).grid(
            row=2, column=1, sticky="w", pady=(2, 10)
        )

        ttk.Label(tab, text="Output Excel file:").grid(row=3, column=0, sticky="w")
        output_var = self._var("output_path")
        ttk.Entry(tab, textvariable=output_var, width=70).grid(row=3, column=1, sticky="we", padx=6)
        ttk.Button(tab, text="Browse...", command=self.browse_output).grid(row=3, column=2)

        ttk.Label(tab, text="Pages:").grid(row=4, column=0, sticky="w", pady=(10, 0))
        pages_var = self._var("pages")
        ttk.Entry(tab, textvariable=pages_var, width=30).grid(row=4, column=1, sticky="w", pady=(10, 0))
        ttk.Label(tab, text="e.g. 'all', '1,3,4' or '1-3'. Ignored if page-text filter is enabled.", foreground="grey").grid(
            row=5, column=1, sticky="w"
        )

        tab.columnconfigure(1, weight=1)

    def _build_extraction_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Extraction")

        ttk.Label(tab, text="Flavor:").grid(row=0, column=0, sticky="w")
        flavor_var = self._var("flavor")
        flavor_box = ttk.Combobox(tab, textvariable=flavor_var, values=FLAVORS, state="readonly", width=20)
        flavor_box.grid(row=0, column=1, sticky="w")

        try_all_var = self._var("try_all_flavors", "bool")
        ttk.Checkbutton(
            tab, text="Try all flavors (adds a separate sheet per flavor for comparison)",
            variable=try_all_var,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 10))

        ttk.Label(tab, text="Backend:").grid(row=2, column=0, sticky="w")
        backend_var = self._var("backend")
        ttk.Combobox(tab, textvariable=backend_var, values=BACKENDS, state="readonly", width=20).grid(
            row=2, column=1, sticky="w"
        )
        ttk.Label(tab, text="Used by lattice / hybrid / ml flavors for PDF-to-image conversion.", foreground="grey").grid(
            row=3, column=1, sticky="w", pady=(0, 10)
        )

        stitch_var = self._var("stitch_enabled", "bool")
        ttk.Checkbutton(tab, text="Stitch multi-page tables", variable=stitch_var).grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(tab, text="Match rule:").grid(row=5, column=0, sticky="w")
        stitch_match_var = self._var("stitch_match")
        ttk.Combobox(
            tab, textvariable=stitch_match_var, values=["column_count", "first_row"], state="readonly", width=20,
        ).grid(row=5, column=1, sticky="w")
        keep_header_var = self._var("stitch_keep_first_header", "bool")
        ttk.Checkbutton(
            tab, text="Keep header row from every page (only applies to 'first_row' match)",
            variable=keep_header_var,
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(tab, text="Strip characters from cells:").grid(row=7, column=0, sticky="w")
        strip_var = self._var("strip_text")
        ttk.Entry(tab, textvariable=strip_var, width=30).grid(row=7, column=1, sticky="w")
        ttk.Label(
            tab, text="Characters to remove wherever found, e.g. spaces/newlines. Use \\n \\t for newline/tab.",
            foreground="grey",
        ).grid(row=8, column=1, sticky="w")

    def _build_filters_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Page Filters & Regions")

        section1 = ttk.LabelFrame(tab, text="Keep only pages with particular text", padding=10)
        section1.pack(fill="x", pady=(0, 10))

        filter_enabled_var = self._var("filter_pages_enabled", "bool")
        ttk.Checkbutton(section1, text="Enable page-text filter", variable=filter_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(section1, text="Text to search for:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        filter_text_var = self._var("filter_text")
        ttk.Entry(section1, textvariable=filter_text_var, width=40).grid(row=1, column=1, sticky="w", pady=(6, 0))
        filter_case_var = self._var("filter_case_sensitive", "bool")
        ttk.Checkbutton(section1, text="Case sensitive", variable=filter_case_var).grid(
            row=2, column=1, sticky="w"
        )
        ttk.Label(
            section1, text="Only pages whose text contains this string are parsed; overrides the Pages field.",
            foreground="grey",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        section2 = ttk.LabelFrame(tab, text="Derive table region from header / footer text", padding=10)
        section2.pack(fill="x")

        derive_enabled_var = self._var("derive_region_enabled", "bool")
        ttk.Checkbutton(section2, text="Enable header/footer-derived region", variable=derive_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(section2, text="Header text (table starts below this):").grid(row=1, column=0, sticky="w", pady=(6, 0))
        header_text_var = self._var("header_text")
        ttk.Entry(section2, textvariable=header_text_var, width=40).grid(row=1, column=1, sticky="w", pady=(6, 0))
        ttk.Label(section2, text="Footer text (table ends above this):").grid(row=2, column=0, sticky="w")
        footer_text_var = self._var("footer_text")
        ttk.Entry(section2, textvariable=footer_text_var, width=40).grid(row=2, column=1, sticky="w")
        derive_case_var = self._var("derive_case_sensitive", "bool")
        ttk.Checkbutton(section2, text="Case sensitive", variable=derive_case_var).grid(row=3, column=1, sticky="w")
        ttk.Label(
            section2,
            text="Locates the header/footer text on each page and builds a table_areas region between them,\n"
                 "so only the table between the two labels is extracted. Leave either field blank to only\n"
                 "bound one side. Overridden by a manual Table Areas entry in the Advanced tab.",
            foreground="grey", justify="left",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _build_advanced_tab(self, notebook):
        outer = ttk.Frame(notebook)
        notebook.add(outer, text="Advanced")

        canvas = tk.Canvas(outer, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=12)
        tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tab, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row = 0

        def label(text, r, c=0, **kw):
            ttk.Label(tab, text=text).grid(row=r, column=c, sticky="w", **kw)

        section = ttk.LabelFrame(tab, text="Regions & columns (manual, overrides derived regions)", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        ttk.Label(section, text="Table Areas (one x1,y1,x2,y2 per line):").grid(row=0, column=0, sticky="nw")
        self.table_areas_text = tk.Text(section, height=3, width=40)
        self.table_areas_text.grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(section, text="Table Regions (one x1,y1,x2,y2 per line):").grid(row=1, column=0, sticky="nw")
        self.table_regions_text = tk.Text(section, height=3, width=40)
        self.table_regions_text.grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(section, text="Columns (one comma-separated list per area, per line):").grid(row=2, column=0, sticky="nw")
        self.columns_text = tk.Text(section, height=3, width=40)
        self.columns_text.grid(row=2, column=1, sticky="w", padx=6)
        row += 1

        section = ttk.LabelFrame(tab, text="Text handling", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        split_var = self._var("split_text", "bool")
        ttk.Checkbutton(section, text="split_text (split text spanning multiple cells)", variable=split_var).grid(
            row=0, column=0, sticky="w"
        )
        flag_var = self._var("flag_size", "bool")
        ttk.Checkbutton(section, text="flag_size (flag sub/superscript text with <s></s>)", variable=flag_var).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Label(section, text="Replace text (one 'old=>new' per line):").grid(row=2, column=0, sticky="nw", pady=(6, 0))
        self.replace_text_text = tk.Text(section, height=3, width=40)
        self.replace_text_text.grid(row=2, column=1, sticky="w", padx=6, pady=(6, 0))
        row += 1

        section = ttk.LabelFrame(tab, text="Stream / Network / Hybrid tolerances", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        label("row_tol:", 0)
        ttk.Entry(section, textvariable=self._var("row_tol", "int"), width=10).grid(row=0, column=1, sticky="w")
        label("column_tol:", 0, c=2)
        ttk.Entry(section, textvariable=self._var("column_tol", "int"), width=10).grid(row=0, column=3, sticky="w")
        label("edge_tol (blank = library default):", 1)
        self.edge_tol_var = tk.StringVar(value="")
        ttk.Entry(section, textvariable=self.edge_tol_var, width=10).grid(row=1, column=1, sticky="w")
        row += 1

        section = ttk.LabelFrame(tab, text="Lattice / Hybrid line detection", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        label("engine:", 0)
        ttk.Combobox(
            section, textvariable=self._var("engine"), values=["combined", "raster", "vector"],
            state="readonly", width=12,
        ).grid(row=0, column=1, sticky="w")
        use_fallback_var = self._var("use_fallback", "bool")
        ttk.Checkbutton(section, text="use_fallback (try another backend if this one fails)", variable=use_fallback_var).grid(
            row=0, column=2, columnspan=2, sticky="w"
        )
        label("line_scale:", 1)
        ttk.Entry(section, textvariable=self._var("line_scale", "int"), width=10).grid(row=1, column=1, sticky="w")
        process_bg_var = self._var("process_background", "bool")
        ttk.Checkbutton(section, text="process_background", variable=process_bg_var).grid(row=1, column=2, sticky="w")
        label("line_tol:", 2)
        ttk.Entry(section, textvariable=self._var("line_tol", "int"), width=10).grid(row=2, column=1, sticky="w")
        label("joint_tol:", 2, c=2)
        ttk.Entry(section, textvariable=self._var("joint_tol", "int"), width=10).grid(row=2, column=3, sticky="w")
        label("threshold_blocksize:", 3)
        ttk.Entry(section, textvariable=self._var("threshold_blocksize", "int"), width=10).grid(row=3, column=1, sticky="w")
        label("threshold_constant:", 3, c=2)
        ttk.Entry(section, textvariable=self._var("threshold_constant", "int"), width=10).grid(row=3, column=3, sticky="w")
        label("iterations:", 4)
        ttk.Entry(section, textvariable=self._var("iterations", "int"), width=10).grid(row=4, column=1, sticky="w")
        label("erode_iterations:", 4, c=2)
        ttk.Entry(section, textvariable=self._var("erode_iterations", "int"), width=10).grid(row=4, column=3, sticky="w")
        label("resolution:", 5)
        ttk.Entry(section, textvariable=self._var("resolution", "int"), width=10).grid(row=5, column=1, sticky="w")
        row += 1

        section = ttk.LabelFrame(tab, text="ML flavor (neural, requires 'pip install camelot-py[ml]')", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        label("structure_model:", 0)
        ttk.Entry(section, textvariable=self._var("structure_model"), width=45).grid(row=0, column=1, columnspan=3, sticky="w")
        label("detection_model:", 1)
        ttk.Entry(section, textvariable=self._var("detection_model"), width=45).grid(row=1, column=1, columnspan=3, sticky="w")
        label("device:", 2)
        ttk.Combobox(section, textvariable=self._var("device"), values=["cpu", "cuda"], state="readonly", width=10).grid(
            row=2, column=1, sticky="w"
        )
        label("ocr:", 2, c=2)
        ttk.Combobox(section, textvariable=self._var("ocr"), values=["auto", "on", "off"], state="readonly", width=10).grid(
            row=2, column=3, sticky="w"
        )
        label("detection_threshold:", 3)
        ttk.Entry(section, textvariable=self._var("detection_threshold", "double"), width=10).grid(row=3, column=1, sticky="w")
        label("structure_threshold:", 3, c=2)
        ttk.Entry(section, textvariable=self._var("structure_threshold", "double"), width=10).grid(row=3, column=3, sticky="w")
        label("crop_padding:", 4)
        ttk.Entry(section, textvariable=self._var("crop_padding", "int"), width=10).grid(row=4, column=1, sticky="w")
        row += 1

        section = ttk.LabelFrame(tab, text="Misc", padding=8)
        section.grid(row=row, column=0, columnspan=4, sticky="we", pady=6)
        label("PDF password (blank = none):", 0)
        ttk.Entry(section, textvariable=self._var("password"), show="*", width=25).grid(row=0, column=1, sticky="w")
        parallel_var = self._var("parallel", "bool")
        ttk.Checkbutton(section, text="parallel (use all CPU cores)", variable=parallel_var).grid(
            row=1, column=0, sticky="w"
        )
        label("cpu_count (blank = all):", 1, c=2)
        self.cpu_count_var = tk.StringVar(value="")
        ttk.Entry(section, textvariable=self.cpu_count_var, width=10).grid(row=1, column=3, sticky="w")

    def _build_style_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=12)
        notebook.add(tab, text="Excel Style")

        ttk.Label(tab, text="Font name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(tab, textvariable=self._var("font_name"), width=25).grid(row=0, column=1, sticky="w")

        ttk.Label(tab, text="Font size:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(tab, textvariable=self._var("font_size", "int"), width=10).grid(row=1, column=1, sticky="w", pady=(6, 0))

        ttk.Label(tab, text="Header fill color:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        color_frame = ttk.Frame(tab)
        color_frame.grid(row=2, column=1, sticky="w", pady=(6, 0))
        self.color_var = self._var("header_color")
        color_entry = ttk.Entry(color_frame, textvariable=self.color_var, width=10)
        color_entry.pack(side="left")
        ttk.Button(color_frame, text="Choose...", command=self.pick_color).pack(side="left", padx=(6, 0))

        ttk.Label(tab, text="Row banding style:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(
            tab, textvariable=self._var("style_preset"), values=list(TABLE_STYLE_PRESETS.keys()),
            state="readonly", width=20,
        ).grid(row=3, column=1, sticky="w", pady=(6, 0))

        autofit_var = self._var("autofit", "bool")
        ttk.Checkbutton(tab, text="Auto-fit column widths", variable=autofit_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

    def pick_color(self):
        color = colorchooser.askcolor(color="#" + self.color_var.get())[1]
        if color:
            self.color_var.set(color.lstrip("#").upper())

    def browse_input(self):
        if self.input_mode.get() == "file":
            path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        else:
            path = filedialog.askdirectory()
        if path:
            self.vars["input_path"].set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if path:
            self.vars["output_path"].set(path)

    def open_output_folder(self):
        out = self.vars["output_path"].get()
        folder = os.path.dirname(os.path.abspath(out)) if out else os.getcwd()
        if os.path.isdir(folder):
            if os.name == "nt":
                os.startfile(folder)
            elif os.uname().sysname == "Darwin":
                os.system(f"open '{folder}'")
            else:
                os.system(f"xdg-open '{folder}'")

    def collect_config(self):
        cfg = {}
        for key, var in self.vars.items():
            cfg[key] = var.get()

        cfg["table_areas"] = self.table_areas_text.get("1.0", "end").strip()
        cfg["table_regions"] = self.table_regions_text.get("1.0", "end").strip()
        cfg["columns"] = self.columns_text.get("1.0", "end").strip()
        cfg["replace_text"] = self.replace_text_text.get("1.0", "end").strip()

        edge_tol_raw = self.edge_tol_var.get().strip()
        cfg["edge_tol"] = int(edge_tol_raw) if edge_tol_raw else None

        cpu_count_raw = self.cpu_count_var.get().strip()
        cfg["cpu_count"] = int(cpu_count_raw) if cpu_count_raw else None

        return cfg

    def start_run(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("Busy", "Extraction is already running.")
            return

        cfg = self.collect_config()
        if not cfg["input_path"]:
            messagebox.showerror("Missing input", "Please choose a PDF file or folder.")
            return
        if not cfg["output_path"]:
            messagebox.showerror("Missing output", "Please choose an output Excel file.")
            return

        self.log_text.delete("1.0", "end")
        self.run_button.configure(state="disabled")
        self.progress.start(10)

        self.worker_thread = threading.Thread(target=self._run_worker, args=(cfg,), daemon=True)
        self.worker_thread.start()

    def _run_worker(self, cfg):
        def log(msg):
            self.log_queue.put(msg)

        try:
            out_path = run_pipeline(cfg, log)
            self.log_queue.put(("__done__", out_path))
        except Exception as e:
            self.log_queue.put(("__error__", str(e)))

    def _poll_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__done__":
                    self.progress.stop()
                    self.run_button.configure(state="normal")
                    out_path = item[1]
                    if out_path:
                        messagebox.showinfo("Done", f"Extraction complete.\nSaved to:\n{out_path}")
                    else:
                        messagebox.showwarning("No tables", "No tables were extracted. Check the log for details.")
                elif isinstance(item, tuple) and item[0] == "__error__":
                    self.progress.stop()
                    self.run_button.configure(state="normal")
                    messagebox.showerror("Error", item[1])
                else:
                    self.log_text.insert("end", str(item) + "\n")
                    self.log_text.see("end")
        except queue.Empty:
            pass
        self.after(100, self._poll_log_queue)


if __name__ == "__main__":
    app = CamelotApp()
    app.mainloop()
