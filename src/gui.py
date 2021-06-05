import threading
import sys
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from matrix import SimulationProgressEventHandler, YMLConfiguration
from products import CSVInMemoryProductRepository
from error import ValidationError


def prepare_gui(run_simulation):
    window = Tk()
    window.title("Big Data Gen")

    mainframe = ttk.Frame(window, padding="10 20 10 20")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    input = SimulatorInput()

    def on_config_load_button():
        config_file_path = filedialog.askopenfilename()
        config_path.set(config_file_path)

        input.yml_input_file_path = config_file_path
        refresh_configuration()

    def on_products_load_button():
        products_file_path = filedialog.askopenfilename()
        products_path.set(products_file_path)

        input.csv_input_file_path = products_file_path
        refresh_configuration()

    config_load_button = ttk.Button(mainframe, text="Wczytaj plik konfiguracyjny", command=on_config_load_button)
    config_load_button.grid(column=1, row=0, sticky=W)

    products_load_button = ttk.Button(mainframe, text="Wczytaj plik z produktami", command=on_products_load_button)
    products_load_button.grid(column=1, row=1, sticky=W)

    config_path = StringVar()
    config_path.set("Nie wybrano pliku")
    ttk.Label(mainframe, text="Plik konfiguracyjny: ").grid(column=0, row=2, sticky=W)
    ttk.Label(mainframe, textvariable=config_path).grid(column=1, row=2, sticky=W)

    products_path = StringVar()
    products_path.set("Nie wybrano pliku")
    ttk.Label(mainframe, text="Plik z produktami: ").grid(column=0, row=3, sticky=W)
    ttk.Label(mainframe, textvariable=products_path).grid(column=1, row=3, sticky=W)

    def freeze_buttons():
        config_load_button.configure(state=DISABLED)
        products_load_button.configure(state=DISABLED)
        generate_button.configure(state=DISABLED)

    def unfreeze_buttons():
        config_load_button.configure(state=NORMAL)
        products_load_button.configure(state=NORMAL)
        generate_button.configure(state=NORMAL)

    class GUISimulationProgressHandler(SimulationProgressEventHandler):
        def on_start(self):
            progress.set("0 / 0")
            status.set("Symulacja trwa...")
            freeze_buttons()

        def on_end(self):
            status.set("Symulacja zakończona")
            unfreeze_buttons()

        def on_progress_change(self, persons_done, all_people):
            progress.set(str(persons_done) + " / " + str(all_people))

    def refresh_configuration():
        if input.csv_input_file_path is not None and input.yml_input_file_path is not None:
            is_fine = True
            try:
                input.product_repository = CSVInMemoryProductRepository(input.csv_input_file_path)
            except ValidationError as err:
                is_fine = False
                products_path.set(repr(err))

            try:
                input.simulation_config = YMLConfiguration(input.yml_input_file_path, input.product_repository)
            except ValidationError as err:
                is_fine = False
                config_path.set(repr(err))

            if is_fine:
                generate_button.configure(state=NORMAL)
                progress.set("0 / " + str(input.simulation_config.global_settings.population))
            else:
                generate_button.configure(state=DISABLED)

        else:
            generate_button.configure(state=DISABLED)

    def run_simulation_on_as_new_thread():
        if input.product_repository is not None and input.simulation_config is not None:
            output_dir = "."

            if len(sys.argv) > 1:
                output_dir = str(sys.argv[1])

            threading.Thread(
                target=run_simulation,
                args=(GUISimulationProgressHandler(), input.simulation_config, output_dir)
            ).start()
        else:
            print("Plik z produktami oraz konfiguracją muszą być określone")

    generate_button = ttk.Button(mainframe, text="Generuj bazę", command=run_simulation_on_as_new_thread, state=DISABLED)
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

    def on_close():
        print("CLOSING")
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    return window


def run_gui(run_simulation):
    gui = prepare_gui(run_simulation)
    gui.mainloop()


class SimulatorInput:
    def __init__(self):
        self.yml_input_file_path = None
        self.csv_input_file_path = None
        self.simulation_config = None
        self.product_repository = None
