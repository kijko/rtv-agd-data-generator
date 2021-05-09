from tkinter import *

window = Tk()

window.title("Big Data Gen")
window.geometry("640x480")


def run_gui(on_run_func):
    btn = Button(window, text="Run example simulation", command=on_run_func)
    btn.grid(column=1, row=0)
    window.mainloop()
