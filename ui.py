import tkinter as tk
from tkinter import ttk
import sv_ttk

class SamAssistantUI(tk.Tk):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.title("SAM AI Assistant")
        self.geometry("400x250")
        self.resizable(False, False)  # Disable resizing
        self.overrideredirect(True)  # Remove window decorations
        self.attributes('-topmost', True)  # Keep window on top

        # Position the window at the bottom right of the screen
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - 400
        y = screen_height - 250
        self.geometry(f"400x250+{x}+{y}")

        sv_ttk.set_theme("dark")  # Apply theme
        self.configure(bg="#1e1e2e")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # Top bar
        top_frame = ttk.Frame(self, style="Custom.TFrame")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        top_frame.grid_columnconfigure(1, weight=1)

        # Left side of top bar
        left_frame = ttk.Frame(top_frame)
        left_frame.grid(row=0, column=0, sticky="nsw")

        self.mic_button = tk.Button(left_frame, text="၊၊||၊", command=self.backend.toggle_listening,
                                    bg="#1f2937", fg="white", font=("Segoe UI", 12), width=3, bd=0)
        self.mic_button.pack(side=tk.LEFT, padx=(0, 5))

        sam_label = ttk.Label(left_frame, text="SAM", font=("Segoe UI", 14, "bold"), foreground="#cba6f7")
        sam_label.pack(side=tk.LEFT)

        # Right side of top bar
        right_frame = ttk.Frame(top_frame)
        right_frame.grid(row=0, column=2, sticky="nse")

        self.type_button = ttk.Button(right_frame, text="💬", command=self.backend.toggle_input_bar,
                                      style="Accent.TButton", width=3)
        self.type_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Listening indicator (initially hidden)
        self.listening_frame = ttk.Frame(top_frame)
        self.listening_frame.grid(row=0, column=1, sticky="nse")

        self.wave_label = ttk.Label(self.listening_frame, text="🔊", font=("Segoe UI", 12), foreground="#89b4fa")
        self.wave_label.pack(side=tk.LEFT)

        self.listening_label = ttk.Label(self.listening_frame, text="Listening...", font=("Segoe UI", 10),
                                         foreground="#89b4fa")
        self.listening_label.pack(side=tk.LEFT)

        self.listening_frame.grid_remove()  # Initially hidden

        # Middle: Input and Output display
        self.middle_frame = ttk.Frame(self, style="Custom.TFrame")
        self.middle_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_rowconfigure(1, weight=1)

        self.input_frame = ttk.Frame(self.middle_frame)
        self.input_frame.grid(row=0, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(self.input_frame, textvariable=self.input_var, font=("Segoe UI", 10))
        self.input_entry.grid(row=0, column=0, sticky="ew", pady=(2, 0))
        self.input_entry.bind("<Return>", lambda event: self.backend.process_input())  # Send on Enter

        self.send_button = ttk.Button(self.input_frame, text="Send", command=self.backend.process_input,
                                      style="Accent.TButton")
        self.send_button.grid(row=0, column=1, padx=(2, 0), pady=(2, 0))

        self.input_frame.grid_remove()  # Initially hidden

        # Create a text area for output
        text_bg_frame = ttk.Frame(self.middle_frame, style="Custom.TFrame")
        text_bg_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        self.output_text = tk.Text(text_bg_frame, font=("Segoe UI", 10), bg="#181825", fg="#cdd6f4", 
                                   wrap=tk.WORD, height=8, borderwidth=0, highlightthickness=0)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.config(state=tk.DISABLED)

        self.output_text.tag_configure("user", foreground="#a6e3a1")
        self.output_text.tag_configure("assistant", foreground="#89b4fa")

    def add_to_output(self, message, tag):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, message + "\n\n", tag)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def hide_ui(self):
        """Hide the UI (sleep mode)."""
        self.withdraw()  # Hide the window

    def show_ui(self):
        """Show the UI (wake up)."""
        self.deiconify()  # Show the window

    def run(self):
        self.mainloop()
        