#!/usr/bin/env python3
"""
NeuralForge Studio — AirLLM-powered AI coding assistant
Entry point
"""
import sys
import os

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        import tkinter as tk
    except ImportError:
        print("ERROR: tkinter is not installed.")
        print("  Ubuntu/Debian: sudo apt install python3-tk")
        print("  Windows: Reinstall Python with tk/tcl option checked.")
        sys.exit(1)

    from ui.app import NeuralForgeApp
    root = tk.Tk()
    app = NeuralForgeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
