import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import subprocess
import threading
import queue
import time


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Manager")
        self.geometry("800x600")
        self.create_widgets()
        self.process_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.search_var.trace("w", self.debounce_search)
        self.update_process_list()

    def create_widgets(self):
        # Create a search bar
        search_frame = tk.Frame(self)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(search_frame, text="Search", command=self.search_process)
        search_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(search_frame, text="Reset", command=self.reset_search)
        reset_button.pack(side=tk.LEFT, padx=5)

        # Create a treeview widget
        columns = ("pid", "name", "cpu (%)", "memory (MB)")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_by_column(c, False))
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Create a terminate button
        self.terminate_button = tk.Button(self, text="Terminate Process", command=self.terminate_process)
        self.terminate_button.pack(pady=10)

        # Create a create process button
        self.create_button = tk.Button(self, text="Create Process", command=self.create_process)
        self.create_button.pack(pady=10)

    def sort_by_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def update_process_list(self, search_term=None):
        # Stop any existing thread before starting a new one
        self.stop_event.set()
        self.stop_event = threading.Event()
        thread = threading.Thread(target=self.fetch_process_list, args=(search_term,))
        thread.start()
        self.after(100, self.check_process_queue)

    def fetch_process_list(self, search_term):
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            if self.stop_event.is_set():
                return
            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent']
            memory = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB

            if search_term:
                if str(pid) == search_term or search_term.lower() in name.lower():
                    processes.append((pid, name, cpu, memory))
            else:
                processes.append((pid, name, cpu, memory))

        self.process_queue.put(processes)

    def check_process_queue(self):
        try:
            processes = self.process_queue.get_nowait()
        except queue.Empty:
            self.after(100, self.check_process_queue)
            return

        # Update the treeview with the new process list
        self.update_treeview(processes)

        # Schedule the next update
        self.after(1000, self.update_process_list)

    def update_treeview(self, processes):
        current_items = {self.tree.item(child)['values'][0]: child for child in self.tree.get_children()}
        new_items = {proc[0]: proc for proc in processes}

        # Delete items not in the new process list
        for pid in set(current_items) - set(new_items):
            self.tree.delete(current_items[pid])

        # Update existing items and add new ones
        for pid, proc in new_items.items():
            if pid in current_items:
                self.tree.item(current_items[pid], values=proc)
            else:
                self.tree.insert("", tk.END, values=proc)

    def search_process(self):
        search_term = self.search_var.get()
        self.update_process_list(search_term)

    def debounce_search(self, *args):
        self.after_cancel(self.after_id) if hasattr(self, 'after_id') else None
        self.after_id = self.after(300, self.search_process)

    def reset_search(self):
        self.search_var.set("")
        self.update_process_list()

    def terminate_process(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a process to terminate")
            return

        pid = self.tree.item(selected_item[0], 'values')[0]
        try:
            p = psutil.Process(int(pid))
            p.terminate()
            p.wait(timeout=3)
            messagebox.showinfo("Success", f"Process {pid} terminated successfully")
            self.update_process_list()
        except psutil.NoSuchProcess:
            messagebox.showerror("Error", "No such process found")
        except psutil.AccessDenied:
            messagebox.showerror("Error", "Access denied")
        except psutil.TimeoutExpired:
            messagebox.showerror("Error", "Timeout expired while terminating process")

    def create_process(self):
        file_path = filedialog.askopenfilename(title="Select Script or Executable")
        if file_path:
            try:
                subprocess.Popen([file_path])
                messagebox.showinfo("Success", f"Process {file_path} started successfully")
                self.update_process_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start process: {e}")


if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()

