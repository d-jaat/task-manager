import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import subprocess


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Self Made Task Manager")
        self.geometry("800x600")
        self.create_widgets()
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
        columns = ("pid", "name", "cpu", "memory")
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
        for i in self.tree.get_children():
            self.tree.delete(i)

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent']
            memory = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB

            if search_term:
                if str(pid) == search_term or search_term.lower() in name.lower():
                    self.tree.insert("", tk.END, values=(pid, name, cpu, memory))
            else:
                self.tree.insert("", tk.END, values=(pid, name, cpu, memory))

        self.after(1000, self.update_process_list)

    def search_process(self):
        search_term = self.search_var.get()
        self.update_process_list(search_term)

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
