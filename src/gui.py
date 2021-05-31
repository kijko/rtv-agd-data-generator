import threading
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from matrix import SimulationProgressEventHandler


def prepare_gui(run_simulation):
    window = Tk()
    window.title("Big Data Gen")

    mainframe = ttk.Frame(window, padding="10 20 10 20")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    def on_config_load_button():
        config_path.set(filedialog.askopenfilename())

    def on_products_load_button():
        products_path.set(filedialog.askopenfilename())

    ttk.Button(mainframe, text="Wczytaj plik konfiguracyjny", command=on_config_load_button) \
        .grid(column=1, row=0, sticky=W)

    ttk.Button(mainframe, text="Wczytaj plik z produktami", command=on_products_load_button) \
        .grid(column=1, row=1, sticky=W)

    config_path = StringVar()
    config_path.set("Nie wybrano pliku")
    ttk.Label(mainframe, text="Plik konfiguracyjny: ").grid(column=0, row=2, sticky=W)
    ttk.Label(mainframe, textvariable=config_path).grid(column=1, row=2, sticky=W)

    products_path = StringVar()
    products_path.set("Nie wybrano pliku")
    ttk.Label(mainframe, text="Plik z produktami: ").grid(column=0, row=3, sticky=W)
    ttk.Label(mainframe, textvariable=products_path).grid(column=1, row=3, sticky=W)

    class GUISimulationProgressHandler(SimulationProgressEventHandler):
        def on_start(self):
            progress.set("0 / 0")
            status.set("Symulacja trwa...")
            generate_button.configure(state=DISABLED)

        def on_end(self):
            status.set("Symulacja zakończona")
            generate_button.configure(state=NORMAL)

        def on_progress_change(self, persons_done, all_people):
            progress.set(str(persons_done) + " / " + str(all_people))

    def run_simulation_on_as_new_thread():
        threading.Thread(target=run_simulation, args=(GUISimulationProgressHandler(),)).start()

    generate_button = ttk.Button(mainframe, text="Generuj bazę", command=run_simulation_on_as_new_thread)
    generate_button.grid(column=1, row=4, sticky=W)

    ttk.Label(mainframe).grid(column=2, row=0)

    status = StringVar()
    status.set("Nic nie robię")
    ttk.Label(mainframe, textvariable=status).grid(column=0, row=5, sticky=W)

    progress = StringVar()
    progress.set("0 / 0")
    ttk.Label(mainframe, textvariable=progress).grid(column=0, row=6, sticky=W)

    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)

    return window


def run_gui(run_simulation):
    gui = prepare_gui(run_simulation)
    gui.mainloop()
