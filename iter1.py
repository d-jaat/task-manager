import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import subprocess


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

        # Create a terminate button
        self.terminate_button = tk.Button(self, text="Terminate Process", command=self.terminate_process)
        self.terminate_button.pack(pady=10)


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



if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()
