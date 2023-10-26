import tkinter as tk
from tkinter import filedialog
from tkinter import *
from tkinter import ttk
from tkinter import StringVar
from tkinter import colorchooser
from tkinter import messagebox
import serial
import threading
import csv
import time
from serial.tools import list_ports
import os
import json

# Constanten voor de kleuren
COLORS = []

# Functie om beschikbare COM-poorten op te halen
def get_available_com_ports():
    com_ports = [port.device for port in list_ports.comports()]
    return com_ports

# Functie om een COM-poort te selecteren
def select_com_port():
    com_ports = get_available_com_ports()
    if com_ports:
        port_selection.set(com_ports[0])  # Stel standaard de eerste beschikbare COM-poort in
        com_port_dropdown['values'] = com_ports

# Functie om de lijst met COM-poorten dynamisch bij te werken
def update_com_ports():
    com_ports = get_available_com_ports()
    if com_ports:
        current_selection = port_selection.get()
        com_port_dropdown['values'] = com_ports
        if current_selection in com_ports:
            port_selection.set(current_selection)
        elif current_selection not in com_ports:
            # Als de huidige selectie niet langer beschikbaar is, selecteer een nieuwe COM-poort
            port_selection.set(com_ports[0])
    else:
        com_port_dropdown['values'] = []  # Geen beschikbare COM-poorten
        port_selection.set("")  # Wis de huidige selectie


# Voeg een functie toe om de COM-poort te wijzigen wanneer een nieuwe poort is geselecteerd in het dropdown-menu
def on_com_port_selection_change(event):
    global serial_port
    serial_port = port_selection.get()  # Bijwerken van de serial_port variabele

grid_columns = 25
group_size = 250  # Grootte van elke groep vierkantjes
modules = 120
grid_size = group_size*modules
grid_rows=int(grid_size/grid_columns)
square_size = 15  # Grootte van elk vierkantje


def save_parameters_to_json():
    parameters = {
        "grid_columns": grid_columns,
        "group_size": group_size,
        "modules": modules,
        "square_size": square_size,
        "COLORS": COLORS
    }

    try:
        with open("Project1\.vscode\settings.json", "w") as json_file:
            json.dump(parameters, json_file, indent=4)
        messagebox.showinfo("Settings are saved", "Settings are saved")
    except Exception as e:
        messagebox.showerror("Error while saving", f"An error occured when saving: {str(e)}")

def load_parameters_from_json():
    global grid_columns, group_size, modules, square_size, COLORS

    try:
        with open("Project1\.vscode\settings.json", "r") as json_file:
            parameters = json.load(json_file)
            grid_columns = parameters.get("grid_columns", grid_columns)
            group_size = parameters.get("group_size", group_size)
            modules = parameters.get("modules", modules)
            square_size = parameters.get("square_size", square_size)
            COLORS = parameters.get("COLORS", COLORS)
    except Exception as e:
        messagebox.showerror("Error while loading", f"An error occured while loading the settings: {str(e)}")

load_parameters_from_json()

# Bereken het aantal groepen
num_groups = grid_size // group_size

# Schakelstanden voor elk vierkantje
switch_states = [0] * (grid_size)


# Standaardkleur voor elk vierkant
default_color = 0  # Je kunt dit aanpassen aan je voorkeur

# Initialiseer de colourList met standaardkleuren voor alle vierkanten
colourList = []

# Lijst om bij te houden welke squares moeten worden geüpdatet en hun kleur
updateList = []

# Lijst om de huidige kleur van elk vierkant bij te houden
current_square_colors = [COLORS[0]] * grid_size

def resize_canvas_to_group():
    canvas_height = square_size*(group_size/grid_columns)
    canvas.configure(scrollregion=canvas.bbox("all"), height=canvas_height)

# Functie om vierkantkleuren bij te werken
def update_square_colors():
    for i in range(grid_size):
        if i in updateList:
            canvas.itemconfig(square_widgets[i], fill=COLORS[colourList[updateList.index(i)]])
            current_square_colors[i] = COLORS[colourList[updateList.index(i)]]
        # Voeg anders de bestaande kleur toe
        else:
            canvas.itemconfig(square_widgets[i], fill=current_square_colors[i])

# Voeg tooltips toe aan het canvas
tooltips = []  # Lijst om tooltips bij te houden

# Functie om tooltips te vernietigen wanneer de muiscursor het canvas verlaat
def hide_square_tooltip(event):
    for tooltip in tooltips:
        tooltip.destroy()
    tooltips.clear()

# Functie om een tooltip voor een specifiek vierkant weer te geven
def show_square_tooltip_for_square(event, square):
    x, y = event.x_root, event.y_root  # Gebruik x_root en y_root voor absolute schermcoördinaten
    square_tooltip_text = f"Switch {square-1}"

    # Controleer eerst of er al een tooltip voor dit vierkant bestaat
    for tooltip in tooltips:
        if tooltip.square == square:
            return  # Tooltip bestaat al voor dit vierkant

    # Pas de positie aan om dichter bij de muis te zijn
    offset_x = 10
    offset_y = 10
    x += offset_x
    y += offset_y

    # Toon de tooltip in een Toplevel-venster
    tw = Toplevel(root)
    tw.wm_overrideredirect(1)
    tw.wm_geometry(f"+{x}+{y}")
    label = Label(tw, text=square_tooltip_text, justify=LEFT,
                  background="#ffffe0", relief=SOLID, borderwidth=1,
                  font=("tahoma", "8", "normal"))
    label.pack(ipadx=1)

    # Voeg de tooltip toe aan de lijst
    tooltips.append(tw)
    tw.square = square  # Voeg een attribuut 'square' toe aan het Toplevel-venster

# Functie om de tooltips voor het huidige vierkant te tonen en te verbergen voor anderen
def update_square_tooltips(event):
    x, y = event.x, event.y
    item = canvas.find_closest(x, y)
    current_square = item[0]

    # Toon de tooltip voor het huidige vierkant
    show_square_tooltip_for_square(event, current_square)

# Function to be called when the button is clicked
def button_click():
    threading.Thread(target=send_and_receive_data).start()

# Voeg een functie toe om een bestand te selecteren
def selectFile():
    global file_path
    file_path = filedialog.askopenfilename()
    if file_path and os.path.isfile(file_path) and file_path.lower().endswith(".csv"):
        file_label.config(text=f"Selected file: {os.path.basename(file_path)}")
        button.config(state=tk.NORMAL)  # Activeer de "Send" knop
    else:
        file_label.config(text="Selected file: Not yet selected")
        button.config(state=tk.DISABLED)  # Deactiveer de "Send" knop als er geen bestand is geselecteerd
        if file_path:
            messagebox.showerror("Error", "Select a valid CSV file")

def convert_to_binary(number):
    # Functie om een getal naar een binaire representatie om te zetten
    binary_str = bin(int(number))[2:]
    return binary_str

def convert_to_binary2(number):
    # Functie om een getal naar een binaire representatie om te zetten
    binary_str = format(int(number), '02b')  # Zorg voor een binaire reeks van 2 bits
    return binary_str

def swap_last_two_bits(binary_str):
    # Functie om de laatste twee bits van een binaire string om te wisselen
    if len(binary_str) >= 2:
        return binary_str[:-2] + binary_str[-1] + binary_str[-2]
    return binary_str

def convert_data(num1, num2):
    # Functie om de data achter elkaar te plakken in de juiste volgorde

    # Zet de getallen om naar binaire representaties
    binary_num1 = convert_to_binary(num1)
    binary_num2 = convert_to_binary2(num2)

    # Combineer de binaire getallen
    combined_binary = binary_num1 + swap_last_two_bits(binary_num2)  # Wissel de laatste twee bits van binary_num2

    myBytes = bytearray()
    
    for i in range(0, len(combined_binary), 8):
        chunk = combined_binary[i:i + 8]
        myBytes.append(int(chunk, 2))
    
    return myBytes

# Function to send and receive data in a separate thread
def send_and_receive_data():
    try:
        on_com_port_selection_change("<DummyEvent>")
        start_time = time.time()  # Start the timer
        with open(file_path, 'r', encoding='utf-8-sig') as csv_file:
            global ser
            global serial_port
            ser = serial.Serial(serial_port, baudrate=1843200)
            csv_reader = csv.reader(csv_file, delimiter=';')

            for row in csv_reader:
                if len(row) >= 2:  # Controleer of er minstens 2 kolommen in de rij zijn
                    num1 = int(row[0])
                    num2 = int(row[1])
                    if 0 <= num1 < grid_size and 0 <= num2 < len(COLORS):
                        updateList.append(num1)
                        colourList.append(num2)
                        ser.write(convert_data(num1, num2))
                    else:
                        messagebox.showerror("Fout", f"Ongeldige invoer in CSV-bestand op regel {csv_reader.line_num}")
                        ser.close()
                        return

            ser.close()
            end_time = time.time()  # Stop the timer
            elapsed_time = end_time - start_time
            label1.config(text=f"Time elapsed: {elapsed_time}")
        update_square_colors()
        updateList.clear()  # Wis de lijst met update-vierkanten
        colourList.clear()  # Wis de lijst met kleuren

    except FileNotFoundError:
        messagebox.showerror("Fout", "Het geselecteerde bestand bestaat niet.")
    except Exception as e:
        messagebox.showerror("Fout", f"Fout bij het verwerken van het bestand: {str(e)}")

# Function to send manually entered data
def send_manual_data():
    try:
        on_com_port_selection_change("<DummyEvent>")
        start_time = time.time()  # Start the timer
        ser = serial.Serial(serial_port, baudrate=1843200)

        num1 = entry_num1.get()
        num2 = entry_num2.get()

        if num1 and num2:
            switch_num = int(num1)
            signal_num = int(num2)

            if 0 <= switch_num < (grid_size-1) and 0 <= signal_num < len(COLORS):
                updateList.append(switch_num)
                colourList.append(signal_num)
                # Stuur de gecombineerde binaire gegevens naar de seriële poort
                ser.write(convert_data(switch_num, signal_num))

                update_square_colors()
                updateList.clear()  # Wis de lijst met update-vierkanten
                colourList.clear()  # Wis de lijst met kleuren
                ser.close()
                end_time = time.time()  # Stop the timer
                elapsed_time = end_time - start_time
                label1.config(text=f"Time elapsed: {elapsed_time}")
            else:
                messagebox.showerror(text="Invalid input: Switch number or signal out of range")
        else:
            messagebox.showerror(text="Invalid input: Both fields are required")
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")

# Create the main window
root = tk.Tk()
root.title("BE Precision Technology - Probe Card Tester")
root.iconbitmap("Project1\.vscode\BEPTLogo.ico")
root.geometry("790x660")  # Set the initial window size to 1920x1080 pixels
root.configure(bg="white")

# Create A Main frame
main_frame = Frame(root)
main_frame.pack(fill=BOTH, expand=1)
# Create Frame for X Scrollbar
sec = Frame(main_frame)
sec.pack(fill=X, side=BOTTOM)
# Create A Canvas
my_canvas = Canvas(main_frame)
my_canvas.pack(side=LEFT, fill=BOTH, expand=1)
# Add A Scrollbars to Canvas
x_scrollbar = ttk.Scrollbar(sec, orient=HORIZONTAL, command=my_canvas.xview)
x_scrollbar.pack(side=BOTTOM, fill=X)
y_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
y_scrollbar.pack(side=RIGHT, fill=Y)
# Configure the canvas
my_canvas.configure(xscrollcommand=x_scrollbar.set)
my_canvas.configure(yscrollcommand=y_scrollbar.set)
my_canvas.bind("<Configure>", lambda e: my_canvas.config(scrollregion=my_canvas.bbox(ALL)))
# Create Another Frame INSIDE the Canvas
big_frame = Frame(my_canvas, bg="white")

# Voeg een zwarte balk toe aan de bovenkant van big_frame
black_frame = tk.Frame(big_frame, bg="grey20")
black_frame.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
custom_font = ("Microsoft JhengHei UI", 20, "bold")
text_label = tk.Label(black_frame, text="Probe Card Tester", fg="white", bg="grey20", font=custom_font)
text_label.pack(side="right", padx=10)

# Voeg een frame toe voor de linkerkant
left_frame = Frame(big_frame, bg="white")
left_frame.pack(side=LEFT, fill=BOTH, expand=1)

# Voeg een frame toe voor de rechterkant
right_frame = Frame(big_frame, bg="white")
right_frame.pack(side=RIGHT, fill=BOTH, expand=1)

# Voeg een blauwe balk toe aan de bovenkant van right_frame
top_right_frame = tk.Frame(right_frame, bg="RoyalBlue4")
top_right_frame.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg een blauwe balk toe aan de bovenkant van left_frame
top_left_frame = tk.Frame(left_frame, bg="RoyalBlue4")
top_left_frame.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
custom_font = ("Microsoft JhengHei UI", 20, "bold")
text_label = tk.Label(top_right_frame, text="Current Switch Signals", fg="white", bg="RoyalBlue4", font=custom_font)
text_label.pack(side="left", padx=10)

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
custom_font = ("Microsoft JhengHei UI", 20, "bold")
text_label = tk.Label(top_left_frame, text="Send Data", fg="white", bg="RoyalBlue4", font=custom_font)
text_label.pack(side="left", padx=10, pady=(5,5))

# Add that New Frame a Window In The Canvas
my_canvas.create_window((0, 0), window=big_frame, anchor="nw")

# Bereken de totale breedte en hoogte van het canvas
canvas_width = grid_columns * square_size
canvas_height = grid_rows * square_size

squares_frame = tk.Frame(right_frame, bg="white")
squares_frame.pack()

# Create a canvas for the grid of squares
canvas = tk.Canvas(squares_frame, width=canvas_width, height=square_size*(group_size/grid_columns), bg="white")

# Create square objects
square_ids = []
square_widgets = []  # Houd een lijst bij van de werkelijke widgetobjecten
for i in range(grid_rows):
    for j in range(grid_columns):
        x0 = j * square_size
        y0 = i * square_size
        x1 = x0 + square_size
        y1 = y0 + square_size
        square = canvas.create_rectangle(x0, y0, x1, y1, fill=COLORS[0], state="hidden")

        # Voeg de widget toe aan de lijst
        square_widgets.append(square)

        # Voeg tooltip toe met het nummer van het vakje als tekst
        square_tooltip_text = f"{i * grid_columns + j}"
        square_ids.append(square)  # Voeg het ID van het vierkant toe aan de lijst

        # Bind de tooltipfunctie aan het canvas om tooltips weer te geven wanneer de muiscursor zich boven de vierkanten bevindt
        canvas.tag_bind(square, "<Enter>", lambda e, square_id=square: show_square_tooltip_for_square(e, square_id))
        canvas.tag_bind(square, "<Leave>", hide_square_tooltip)
        canvas.tag_bind(square, "<Motion>", update_square_tooltips)

canvas.pack(side="left", pady=2, padx=2)

color_boxes = []
color_frame = tk.Frame(squares_frame, bg="white")
color_frame.pack(side="right")

color_labels = ["Signaal 1", "Signaal 2", "Signaal 3", "Signaal 4"]

for i, (color, label) in enumerate(zip(COLORS, color_labels)):
    signal_frame = tk.Frame(color_frame, bg="white")
    signal_frame.pack(side="top")  # Plaats de frame voor elk signaal boven elkaar

    color_box = tk.Canvas(signal_frame, width=30, height=30, bg=color)
    color_box.pack(side="left")  # Plaats het kleurvak links in het frame
    color_box.bind("<Button-1>", lambda event, signal=i: change_signal_color(signal))
    color_boxes.append(color_box)

    color_label = tk.Label(signal_frame, text=label, bg="white")
    color_label.pack(side="left", padx=(0,10))  # Plaats het label links in het frame

def update_all_square_colors():
    for i in range(len(square_widgets)):
        square_id = square_widgets[i]
        canvas.itemconfig(square_id, fill=COLORS[colourList[i]])

# Functie om de kleur van een signaal te wijzigen
def change_signal_color(signal):
    # Use the colorchooser module to pick a color
    color = colorchooser.askcolor()[1]

    # Check if a color was selected (user didn't cancel the dialog)
    if color:
        old_color = COLORS[signal]
        COLORS[signal] = color
        color_boxes[signal].configure(bg=color)  # Update the color of the box

        # Werk de kleur van de vierkanten bij voor alle vierkanten met de oude kleur
        for i in range(len(current_square_colors)):
            if current_square_colors[i] == old_color:
                canvas.itemconfig(square_widgets[i], fill=color)
                current_square_colors[i] = color

# Voeg een dropdown-menu toe om een COM-poort te selecteren
com_frame = tk.Frame(left_frame, bg="white")
com_frame.pack(pady=(10,0))
label_com_port = tk.Label(com_frame, text="Select COM Port:", bg="white")
label_com_port.pack(side="left")
port_selection = StringVar(root)
com_port_dropdown = ttk.Combobox(com_frame, textvariable=port_selection)
select_com_port()  # Haal beschikbare COM-poorten op en selecteer de eerste
com_port_dropdown.bind("<<ComboboxSelected>>", on_com_port_selection_change)
com_port_dropdown.pack(side="left")

# Functie om periodiek de COM-poorten bij te werken
def update_com_ports_periodically():
    update_com_ports()
    root.after(1000, update_com_ports_periodically)  # Herhaal elke 5 seconden

update_com_ports_periodically()


file_frame = tk.Frame(left_frame, bg="white")
file_frame.pack(pady=(10,0))

# Create file selection button
button = tk.Button(file_frame, text="Select File", command=selectFile)
button.pack(side="left", padx=(10,0))

# Voeg een label toe om de bestandsnaam weer te geven
file_label = tk.Label(file_frame, text="Selected file: Not yet selected", bg="white")
file_label.pack(side="left")

# Create a button
button = tk.Button(left_frame, text="Send!", command=button_click)
if file_label.cget("text") == "Geselecteerd bestand: Nog niet geselecteerd":
    button.config(state=tk.DISABLED)  # Deactiveer de knop
button.pack()

# Create a label
label1 = tk.Label(left_frame, text="Time elapsed: 0", bg="white")
label1.pack(pady=20)

# Voeg een blauwe balk toe aan de bovenkant van left_frame
top_left_frame2 = tk.Frame(left_frame, bg="RoyalBlue4")
top_left_frame2.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
text_label = tk.Label(top_left_frame2, text="Manual Data", fg="white", bg="RoyalBlue4", font=custom_font)
text_label.pack(side="left", padx=10, pady=5)

# Create labels and entry fields for manual data entry
switch_frame = tk.Frame(left_frame, bg="white")
switch_frame.pack(pady=(10,5))
label_num1 = tk.Label(switch_frame, text=f"Enter switch number (0-{group_size*modules-1}):", bg="white", width=40)
label_num1.pack(side="left")
entry_num1 = tk.Entry(switch_frame)
entry_num1.pack(side="left")

signal_frame = tk.Frame(left_frame, bg="white")
signal_frame.pack(pady=5)
label_num2 = tk.Label(signal_frame, text="Enter signal (0-3):", bg="white", width=40)
label_num2.pack(side="left")
entry_num2 = tk.Entry(signal_frame)
entry_num2.pack(side="left")

# Create a button to send manual data
button_send_manual = tk.Button(left_frame, text="Send Manual Data", command=send_manual_data)
button_send_manual.pack(pady=(5,20))

# Voeg een blauwe balk toe aan de bovenkant van left_frame
top_left_frame3 = tk.Frame(left_frame, bg="RoyalBlue4")
top_left_frame3.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
text_label = tk.Label(top_left_frame3, text="Settings", fg="white", bg="RoyalBlue4", font=custom_font)
text_label.pack(side="left", padx=10, pady=5)

# Aantal groepen en groepsgrootte
current_group = 0

# Functie om de huidige groep weer te geven
def show_current_group():
    start = current_group * group_size
    end = (current_group + 1) * group_size

    for i, square_id in enumerate(square_ids):
        if start <= i < end:
            canvas.itemconfig(square_id, state="normal")
        else:
            canvas.itemconfig(square_id, state="hidden")

# Voeg een functie toe om de huidige groep te wijzigen wanneer een nieuwe groep is geselecteerd in het dropdown-menu
def on_group_selection_change(event):
    global current_group
    current_group = group_selection.get()
    current_group = int(current_group)  # Zet de geselecteerde waarde om in een integer
    show_current_group()  # Toon de bijgewerkte groep
    resize_canvas_to_group()

# Maak een StringVar voor de dropdown selectie
group_selection = StringVar(root)
group_selection.set(str(current_group))  # Stel de standaard selectie in op de huidige groep

# Voeg een functie toe om de waarden in de uitklapbare lijst dynamisch te genereren
def generate_group_dropdown_values():
    values = [str(i) for i in range(num_groups)]
    group_selection.set(str(current_group))  # Stel de geselecteerde waarde in op de huidige groep
    group_dropdown['values'] = values  # Update de waarden in de uitklapbare lijst

# Creëer de uitklapbare lijst met module nummers
number_frame = tk.Frame(right_frame, bg="white")
number_frame.pack(pady=(0,20))
label7 = tk.Label(number_frame, text="Module number:", bg="white")
label7.pack(side="left", anchor="nw")
group_dropdown = ttk.Combobox(number_frame, textvariable=group_selection)
generate_group_dropdown_values()  # Genereer de waarden voor de uitklapbare lijst
group_dropdown.bind("<<ComboboxSelected>>", on_group_selection_change)  # Voer de functie uit wanneer een nieuwe groep is geselecteerd
group_dropdown.pack(side="left", anchor="nw")

# Standaard weergave van de huidige groep
show_current_group()

# Voeg nieuwe labels en entry widgets toe om de parameters in te stellen
columns_frame = tk.Frame(left_frame, bg="white")
columns_frame.pack(pady=(10,5))
label_grid_columns = tk.Label(columns_frame, text="Grid Columns:", bg="white")
label_grid_columns.pack(side="left")
entry_grid_columns = tk.Entry(columns_frame)
entry_grid_columns.insert(0, grid_columns)  # Stel de standaardwaarde in
entry_grid_columns.pack(side="left")

group_frame = tk.Frame(left_frame, bg="white")
group_frame.pack(pady=(5))
label_group_size = tk.Label(group_frame, text="Group Size:      ", bg="white")
label_group_size.pack(side="left")
entry_group_size = tk.Entry(group_frame)
entry_group_size.insert(0, group_size)  # Stel de standaardwaarde in
entry_group_size.pack(side="left")

modules_frame = tk.Frame(left_frame, bg="white")
modules_frame.pack(pady=(5))
label_modules = tk.Label(modules_frame, text="Modules:         ", bg="white")
label_modules.pack(side="left")
entry_modules = tk.Entry(modules_frame)
entry_modules.insert(0, modules)  # Stel de standaardwaarde in
entry_modules.pack(side="left")

size_frame = tk.Frame(left_frame, bg="white")
size_frame.pack(pady=(5))
label_square_size = tk.Label(size_frame, text="Square Size:    ", bg="white")
label_square_size.pack(side="left")
entry_square_size = tk.Entry(size_frame)
entry_square_size.insert(0, square_size)  # Stel de standaardwaarde in
entry_square_size.pack(side="left")

def rearrange_squares():
    # Herverdeel de vierkanten op het nieuwe raster
    for i in range(grid_rows):
        for j in range(grid_columns):
            x0 = j * square_size
            y0 = i * square_size
            x1 = x0 + square_size
            y1 = y0 + square_size
            canvas.coords(square_widgets[i * grid_columns + j], x0, y0, x1, y1)

# Voeg een functie toe om de parameters bij te werken met de ingevoerde waarden
def update_parameters():
    global grid_columns, group_size, modules, square_size

    # Haal de oude waarden op voor het geval dat validatie mislukt
    old_grid_columns = grid_columns
    old_group_size = group_size

    # Haal de ingevoerde waarden op uit de entry widgets
    grid_columns = int(entry_grid_columns.get())
    group_size = int(entry_group_size.get())

    if group_size % grid_columns != 0:
        messagebox.showerror("Ongeldige invoer", "group_size / grid_columns moet een geheel getal zijn.")
        # Herstel de vorige waarden
        entry_grid_columns.delete(0, END)
        entry_group_size.delete(0, END)
        entry_grid_columns.insert(0, old_grid_columns)
        entry_group_size.insert(0, old_group_size)
        grid_columns = old_grid_columns
        group_size = old_group_size
        return

    modules = int(entry_modules.get())
    square_size = int(entry_square_size.get())

    # Bereken het aantal groepen en de grid-rijen opnieuw
    global grid_size, num_groups, grid_rows
    grid_size = group_size * modules
    num_groups = grid_size // group_size
    grid_rows = grid_size // grid_columns
    
    label_num1.config(text=f"Enter switch number (0-{group_size*modules-1}):")
    
    # Pas de grootte van het canvas aan
    canvas_width = grid_columns * square_size
    canvas_height = grid_rows * square_size
    canvas.config(width=canvas_width, height=canvas_height)
    show_current_group()
    resize_canvas_to_group()
    rearrange_squares()

    # Controleer of de geselecteerde module groter is dan het nieuwe aantal modules
    global current_group
    if current_group >= modules:
        current_group = 0  # Zet de geselecteerde module terug naar 0 als deze groter is dan het nieuwe aantal modules

    # Roep de functie aan om de waarden in de uitklapbare lijst bij te werken
    generate_group_dropdown_values()
    on_group_selection_change("<DummyEvent>")

# Voeg een updateknop toe om de parameters bij te werken
buttons_frame = tk.Frame(left_frame, bg="white")
buttons_frame.pack(pady=(10,5))
update_button = tk.Button(buttons_frame, text="Update Settings", command=update_parameters)
update_button.pack(side="left", padx=(0,20))

save_button = tk.Button(buttons_frame, text="Save", command=save_parameters_to_json)
save_button.pack(side="left")

# Voeg een blauwe balk toe aan de bovenkant van left_frame
top_right_frame2 = tk.Frame(right_frame, bg="RoyalBlue4")
top_right_frame2.pack(side="top", fill="x")  # Stel in dat het de hele breedte beslaat

# Voeg witte tekst toe aan de zwarte balk aan de rechterkant
text_label = tk.Label(top_right_frame2, text="Log", fg="white", bg="RoyalBlue4", font=custom_font)
text_label.pack(side="left", padx=10, pady=0)

# Start the main loop
root.mainloop()