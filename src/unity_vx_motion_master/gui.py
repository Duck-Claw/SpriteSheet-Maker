from __future__ import annotations

import queue
import threading
from pathlib import Path
from tkinter import BooleanVar, IntVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk

from PIL import Image, ImageTk

from .config import ProcessSettings
from .frame_source import load_frames, select_frame_range
from .processor import (
    add_canvas_margin,
    compose_sheet,
    find_union_alpha_bbox,
    place_on_canvas,
    preview_composite,
    process_to_sheet,
    remove_black_background,
    resolve_canvas_size,
)


class MotionMasterApp(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SpriteSheet Maker")
        self.geometry("1180x760")
        self.minsize(1020, 680)
        self.configure(bg="#15171b")

        self.input_path = StringVar()
        self.output_path = StringVar(value=str(Path("assets/output/sprite_sheet.png")))
        self.fps = StringVar(value="")
        self.start_frame = StringVar(value="")
        self.end_frame = StringVar(value="")
        self.remove_black = BooleanVar(value=True)
        self.black_threshold = IntVar(value=20)
        self.soft_edge = IntVar(value=8)
        self.alpha_strength = StringVar(value="1.0")
        self.auto_size = BooleanVar(value=True)
        self.frame_width = StringVar(value="256")
        self.frame_height = StringVar(value="256")
        self.anchor = StringVar(value="center")
        self.columns = StringVar(value="")
        self.padding = IntVar(value=0)
        self.max_texture_size = StringVar(value="4096")
        self.export_frames = BooleanVar(value=False)
        self.background = StringVar(value="checker")
        self.status = StringVar(value="Drop/select a GIF or video to begin.")

        self.preview_photo: ImageTk.PhotoImage | None = None
        self.frames: list[Image.Image] = []
        self.preview_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self._configure_style()
        self._build_layout()
        self.after(120, self._drain_queue)

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#15171b")
        style.configure("Panel.TFrame", background="#1d2026")
        style.configure("TLabel", background="#15171b", foreground="#eceff4", font=("Avenir Next", 12))
        style.configure("Muted.TLabel", background="#15171b", foreground="#8e96a6", font=("Avenir Next", 11))
        style.configure("Panel.TLabel", background="#1d2026", foreground="#eceff4", font=("Avenir Next", 12))
        style.configure("Header.TLabel", background="#15171b", foreground="#f4d06f", font=("Avenir Next", 20, "bold"))
        style.configure("Section.TLabel", background="#1d2026", foreground="#f4d06f", font=("Avenir Next", 13, "bold"))
        style.configure("TButton", font=("Avenir Next", 11), padding=(10, 6), background="#2f3540", foreground="#f6f7fb")
        style.map("TButton", background=[("active", "#3d4655")])
        style.configure("Accent.TButton", background="#f4d06f", foreground="#14161a", font=("Avenir Next", 12, "bold"), padding=(16, 8))
        style.map("Accent.TButton", background=[("active", "#ffe08a")])
        style.configure("TCheckbutton", background="#1d2026", foreground="#eceff4", font=("Avenir Next", 11))
        style.configure("TRadiobutton", background="#1d2026", foreground="#eceff4", font=("Avenir Next", 11))
        style.configure("TEntry", fieldbackground="#101217", foreground="#f6f7fb", bordercolor="#3b414c", insertcolor="#f6f7fb")
        style.configure("TCombobox", fieldbackground="#101217", foreground="#f6f7fb", background="#2f3540")

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)

        title = ttk.Label(root, text="SpriteSheet Maker", style="Header.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 14))

        controls = ttk.Frame(root, style="Panel.TFrame", padding=16)
        controls.grid(row=1, column=0, sticky="nsw", padx=(0, 16))
        controls.columnconfigure(1, weight=1)

        preview_panel = ttk.Frame(root, style="Panel.TFrame", padding=16)
        preview_panel.grid(row=1, column=1, sticky="nsew")
        preview_panel.rowconfigure(1, weight=1)
        preview_panel.columnconfigure(0, weight=1)

        self._build_controls(controls)
        self._build_preview(preview_panel)

        footer = ttk.Frame(root)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Export Sprite Sheet", style="Accent.TButton", command=self.export).grid(row=0, column=1, sticky="e")

    def _build_controls(self, parent: ttk.Frame) -> None:
        row = 0
        row = self._section(parent, row, "Input")
        ttk.Entry(parent, textvariable=self.input_path, width=34).grid(row=row, column=0, columnspan=2, sticky="ew", pady=4)
        row += 1
        ttk.Button(parent, text="Select Video / GIF", command=self.pick_input).grid(row=row, column=0, sticky="ew", pady=(0, 10))
        ttk.Button(parent, text="Preview", command=self.preview).grid(row=row, column=1, sticky="ew", pady=(0, 10), padx=(8, 0))
        row += 1

        row = self._section(parent, row, "Frame Range")
        row = self._field(parent, row, "FPS", self.fps, "Original")
        row = self._field(parent, row, "Start Frame", self.start_frame, "0")
        row = self._field(parent, row, "End Frame", self.end_frame, "All")

        row = self._section(parent, row, "Transparency")
        ttk.Checkbutton(parent, text="Remove Black Background", variable=self.remove_black).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)
        row += 1
        row = self._slider(parent, row, "Black Threshold", self.black_threshold, 0, 100)
        row = self._slider(parent, row, "Soft Edge", self.soft_edge, 0, 48)
        row = self._field(parent, row, "Alpha Strength", self.alpha_strength, "1.0")

        row = self._section(parent, row, "Frame Canvas")
        ttk.Checkbutton(parent, text="Auto Size", variable=self.auto_size).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)
        row += 1
        row = self._field(parent, row, "Width", self.frame_width, "256")
        row = self._field(parent, row, "Height", self.frame_height, "256")
        ttk.Label(parent, text="Anchor", style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Combobox(parent, textvariable=self.anchor, values=("center", "top", "bottom"), state="readonly", width=12).grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        row = self._section(parent, row, "Sprite Sheet")
        row = self._field(parent, row, "Columns", self.columns, "Auto")
        row = self._slider(parent, row, "Frame Margin", self.padding, 0, 64)
        row = self._field(parent, row, "Max Texture", self.max_texture_size, "4096")
        ttk.Checkbutton(parent, text="Export Individual Frames", variable=self.export_frames).grid(row=row, column=0, columnspan=2, sticky="w", pady=3)
        row += 1
        ttk.Entry(parent, textvariable=self.output_path).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 4))
        row += 1
        ttk.Button(parent, text="Choose Output PNG", command=self.pick_output).grid(row=row, column=0, columnspan=2, sticky="ew")

    def _build_preview(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent, style="Panel.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Preview", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Combobox(top, textvariable=self.background, values=("checker", "black", "white", "gray", "transparent"), state="readonly", width=14).grid(row=0, column=1, sticky="e")

        self.preview_label = ttk.Label(parent, text="No preview yet", anchor="center", style="Panel.TLabel")
        self.preview_label.grid(row=1, column=0, sticky="nsew")

    def _section(self, parent: ttk.Frame, row: int, text: str) -> int:
        ttk.Label(parent, text=text, style="Section.TLabel").grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))
        return row + 1

    def _field(self, parent: ttk.Frame, row: int, label: str, variable: StringVar, placeholder: str) -> int:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        entry = ttk.Entry(parent, textvariable=variable, width=14)
        entry.grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        if not variable.get():
            entry.insert(0, "")
        return row + 1

    def _slider(self, parent: ttk.Frame, row: int, label: str, variable: IntVar, start: int, end: int) -> int:
        ttk.Label(parent, text=label, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
        wrap = ttk.Frame(parent, style="Panel.TFrame")
        wrap.grid(row=row, column=1, sticky="ew", pady=4, padx=(8, 0))
        wrap.columnconfigure(0, weight=1)
        ttk.Scale(wrap, variable=variable, from_=start, to=end, orient="horizontal").grid(row=0, column=0, sticky="ew")
        ttk.Label(wrap, textvariable=variable, style="Panel.TLabel", width=3).grid(row=0, column=1, padx=(8, 0))
        return row + 1

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Media", "*.mp4 *.mov *.gif *.webm *.avi *.png *.jpg *.jpeg"), ("All files", "*.*")])
        if path:
            self.input_path.set(path)
            default_output = Path("assets/output") / f"{Path(path).stem}_sheet.png"
            self.output_path.set(str(default_output))
            self.preview()

    def pick_output(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.output_path.set(path)

    def preview(self) -> None:
        settings = self._read_settings(for_preview=True)
        if not settings:
            return
        self.status.set("Building preview...")
        threading.Thread(target=self._preview_worker, args=(settings,), daemon=True).start()

    def export(self) -> None:
        settings = self._read_settings(for_preview=False)
        if not settings:
            return
        self.status.set("Exporting sprite sheet...")
        threading.Thread(target=self._export_worker, args=(settings,), daemon=True).start()

    def _preview_worker(self, settings: ProcessSettings) -> None:
        try:
            frames = load_frames(settings.input_path, fps=settings.fps)
            frames = select_frame_range(frames, settings.start_frame, settings.end_frame)
            if len(frames) > 64:
                stride = max(1, len(frames) // 64)
                frames = frames[::stride]
            processed = [
                remove_black_background(frame, settings.black_threshold, settings.soft_edge, settings.alpha_strength)
                if settings.remove_black
                else frame.convert("RGBA")
                for frame in frames
            ]
            crop_box = find_union_alpha_bbox(processed)
            canvas_size = resolve_canvas_size(crop_box, settings)
            normalized = [add_canvas_margin(place_on_canvas(frame.crop(crop_box), canvas_size, settings.anchor), settings.padding) for frame in processed]
            sheet, _, _ = compose_sheet(normalized, settings.columns)
            preview = preview_composite(sheet, self.background.get())
            preview.thumbnail((760, 560), Image.Resampling.LANCZOS)
            self.preview_queue.put(("preview", preview))
            self.preview_queue.put(("status", f"Preview ready: {len(normalized)} sampled frames, frame {normalized[0].width}x{normalized[0].height}"))
        except Exception as exc:
            self.preview_queue.put(("error", str(exc)))

    def _export_worker(self, settings: ProcessSettings) -> None:
        try:
            metadata = process_to_sheet(settings)
            self.preview_queue.put(("status", f"Exported {metadata.frame_count} frames to {settings.output_path}"))
            image = Image.open(settings.output_path)
            preview = preview_composite(image, self.background.get())
            preview.thumbnail((760, 560), Image.Resampling.LANCZOS)
            self.preview_queue.put(("preview", preview))
        except Exception as exc:
            self.preview_queue.put(("error", str(exc)))

    def _drain_queue(self) -> None:
        while True:
            try:
                kind, payload = self.preview_queue.get_nowait()
            except queue.Empty:
                break
            if kind == "preview":
                self.preview_photo = ImageTk.PhotoImage(payload)
                self.preview_label.configure(image=self.preview_photo, text="")
            elif kind == "status":
                self.status.set(str(payload))
            elif kind == "error":
                self.status.set("Error")
                messagebox.showerror("SpriteSheet Maker", str(payload))
        self.after(120, self._drain_queue)

    def _read_settings(self, for_preview: bool) -> ProcessSettings | None:
        try:
            input_path = Path(self.input_path.get())
            if not input_path.exists():
                messagebox.showwarning("SpriteSheet Maker", "Select an input file first.")
                return None
            output_path = Path(self.output_path.get())
            fps = _optional_float(self.fps.get())
            start_frame = _optional_int(self.start_frame.get())
            end_frame = _optional_int(self.end_frame.get())
            frame_size = None
            if not self.auto_size.get():
                frame_size = (_required_int(self.frame_width.get(), "Width"), _required_int(self.frame_height.get(), "Height"))
            max_texture_size = _optional_int(self.max_texture_size.get())
            return ProcessSettings(
                input_path=input_path,
                output_path=output_path,
                fps=fps,
                start_frame=start_frame,
                end_frame=end_frame,
                remove_black=self.remove_black.get(),
                black_threshold=int(self.black_threshold.get()),
                soft_edge=int(self.soft_edge.get()),
                alpha_strength=float(self.alpha_strength.get() or 1.0),
                auto_size=self.auto_size.get(),
                frame_size=frame_size,
                anchor=self.anchor.get(),
                columns=_optional_int(self.columns.get()),
                padding=int(self.padding.get()),
                max_texture_size=max_texture_size,
                export_frames=self.export_frames.get() and not for_preview,
            )
        except Exception as exc:
            messagebox.showerror("SpriteSheet Maker", str(exc))
            return None


def _optional_int(value: str) -> int | None:
    value = value.strip()
    return None if not value else int(value)


def _required_int(value: str, label: str) -> int:
    value = value.strip()
    if not value:
        raise ValueError(f"{label} is required.")
    return int(value)


def _optional_float(value: str) -> float | None:
    value = value.strip()
    return None if not value else float(value)


def main() -> None:
    app = MotionMasterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
