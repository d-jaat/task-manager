import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import subprocess
import threading
import queue
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation


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
        # Create a notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create a frame for the Processes tab
        self.processes_frame = tk.Frame(self.notebook)
        self.notebook.add(self.processes_frame, text="Processes")

        # Create a frame for the Performance tab
        self.performance_frame = tk.Frame(self.notebook)
        self.notebook.add(self.performance_frame, text="Performance")

        # Add content to Processes tab
        self.create_processes_tab()

        # Add content to Performance tab
        self.create_performance_tab()

    def create_processes_tab(self):
        search_frame = tk.Frame(self.processes_frame)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(search_frame, text="Search", command=self.search_process)
        search_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(search_frame, text="Reset", command=self.reset_search)
        reset_button.pack(side=tk.LEFT, padx=5)

        columns = ("pid", "name", "cpu (%)", "memory (MB)")
        self.tree = ttk.Treeview(self.processes_frame, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col.capitalize(), command=lambda c=col: self.sort_by_column(c, False))
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.terminate_button = tk.Button(self.processes_frame, text="Terminate Process",
                                          command=self.terminate_process)
        self.terminate_button.pack(pady=10)

        self.create_button = tk.Button(self.processes_frame, text="Create Process", command=self.create_process)
        self.create_button.pack(pady=10)

    def create_performance_tab(self):
        self.fig, (self.ax_cpu, self.ax_memory) = plt.subplots(2, 1, figsize=(8, 6))
        self.fig.tight_layout(pad=3.0)

        self.cpu_data = []
        self.memory_data = []
        self.time_data = []
        self.start_time = time.time()

        self.ax_cpu.set_title('CPU Usage (%)')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel('Time (s)')
        self.ax_cpu.set_ylabel('CPU (%)')

        self.ax_memory.set_title('Memory Usage (MB)')
        self.ax_memory.set_ylim(0, psutil.virtual_memory().total / (1024 * 1024))
        self.ax_memory.set_xlabel('Time (s)')
        self.ax_memory.set_ylabel('Memory (MB)')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.performance_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.ani = animation.FuncAnimation(self.fig, self.update_performance_graphs, interval=1000)

    def update_performance_graphs(self, frame):
        current_time = time.time() - self.start_time
        self.time_data.append(current_time)
        self.cpu_data.append(psutil.cpu_percent())
        self.memory_data.append(psutil.virtual_memory().used / (1024 * 1024))

        if len(self.time_data) > 60:
            self.time_data = self.time_data[-60:]
            self.cpu_data = self.cpu_data[-60:]
            self.memory_data = self.memory_data[-60:]

        self.ax_cpu.clear()
        self.ax_memory.clear()

        self.ax_cpu.plot(self.time_data, self.cpu_data, label='CPU (%)')
        self.ax_cpu.set_title('CPU Usage (%)')
        self.ax_cpu.set_ylim(0, 100)
        self.ax_cpu.set_xlabel('Time (s)')
        self.ax_cpu.set_ylabel('CPU (%)')

        self.ax_memory.plot(self.time_data, self.memory_data, label='Memory (MB)')
        self.ax_memory.set_title('Memory Usage (MB)')
        self.ax_memory.set_ylim(0, psutil.virtual_memory().total / (1024 * 1024))
        self.ax_memory.set_xlabel('Time (s)')
        self.ax_memory.set_ylabel('Memory (MB)')

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def sort_by_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_by_column(col, not reverse))

    def update_process_list(self, search_term=None):
        self.stop_event.set()
        self.stop_event = threading.Event()
        thread = threading.Thread(target=self.fetch_process_list, args=(search_term,))
        thread.start()
        self.after(100, self.check_process_queue)

    def fetch_process_list(self, search_term):
        processes = []
        num_cpus = psutil.cpu_count()
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            if self.stop_event.is_set():
                return
            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent'] / num_cpus  # Normalize by number of CPUs
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

        self.update_treeview(processes)
        self.after(1000, self.update_process_list)

    def update_treeview(self, processes):
        current_items = {self.tree.item(child)['values'][0]: child for child in self.tree.get_children()}
        new_items = {proc[0]: proc for proc in processes}

        for pid in set(current_items) - set(new_items):
            self.tree.delete(current_items[pid])

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

