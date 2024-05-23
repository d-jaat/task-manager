import tkinter as tk
from tkinter import ttk, messagebox
import psutil


class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Task Manager")
        self.geometry("800x600")
        self.create_widgets()
        self.update_process_list()

    def create_widgets(self):
        # Create a treeview widget
        columns = ("pid", "name", "cpu", "memory")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_by_column(c, False))
        self.tree.pack(fill=tk.BOTH, expand=True)



    def sort_by_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def update_process_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent']
            memory = proc.info['memory_info'].rss / (1024 * 1024)  # Convert to MB

            self.tree.insert("", tk.END, values=(pid, name, cpu, memory))

        self.after(1000, self.update_process_list)



if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()
