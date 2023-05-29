# importing module
import math
import matplotlib.pyplot as plt
import scipy.integrate
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from pandas import *
from scipy import signal
from scipy import integrate
import tkinter as tk
from tkmacosx import Button
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile
from PIL import Image, ImageTk
import os
import norm_lines
import ctypes


def check_file():
    global x_time
    global y_time
    global z_time
    global t
    temp_name = (tk.filedialog.askopenfile(mode='r', filetypes=[('CSV file', '*.csv')]))
    if temp_name is None:
        try_again = messagebox.askretrycancel("Error message", "No file selected")
        if try_again:
            check_file()
        else:
            quit()

    data = read_csv(str(temp_name.name))
    if list(data.columns) == ['Time', 'X', 'Y', 'Z']:
        x_time = data['X']
        y_time = data['Y']
        z_time = data['Z']
    elif list(data.columns) == ['Time', 'X', 'Y']:
        x_time = data['X']
        y_time = data['Y']
        z_time = [0] * len(y_time)
    elif list(data.columns) == ['Time', 'X']:
        x_time = data['X']
        y_time = [0] * len(x_time)
        z_time = [0] * len(x_time)
    else:
        try_again = messagebox.askretrycancel("Error message", "Selected file cannot be read")
        if try_again:
            check_file()
        else:
            quit()

    t = data['Time']
    sample_rate = 1 / (t[2] - t[1])
    if sample_rate > 0:
        success_lbl = tk.Label(
            start_top_frame,
            text="File " + str(temp_name.name) + " loaded successfully\nSample rate of the signal: "
                 + str(sample_rate) + " Hz", font='Lato 10 bold', fg='white', bg='#262c2b')
        success_lbl.pack(side=tk.TOP, pady=5, padx=5)
        sample_rate_label = tk.Label(start_top_frame, text="Choose vibration units: ",
                                     fg='white', bg='#262c2b', font='Lato 10 bold')
        sample_rate_label.pack(side=tk.LEFT, pady=5, padx=5)
    else:
        print("Error")
        quit()

    # vibration unit selection
    unit_var = tk.StringVar(start_window)
    unit_var.set("Select unit...")
    units = ["m/s", "m/s^2", "mm/s", "mm/s^2"]
    units_menu = tk.OptionMenu(start_top_frame, unit_var, *units)
    units_menu.pack(side=tk.LEFT, pady=5, padx=5)
    units_menu.configure(fg='white', bg='black', font='Lato 10 bold')

    Button(start_top_frame,
           text="Ok",
           width=50,
           command=lambda: define_plot(unit_var.get(), sample_rate),
           fg='white', bg='#1f2226',
           font='Lato 10 bold').pack(side=tk.RIGHT, pady=5, padx=5)


def define_plot(unit_var, sample_rate):
    global x_time
    global y_time
    global z_time
    global t
    if unit_var == "m/s" or unit_var == "m/s^2":
        pass
    elif unit_var == "mm/s":
        x_time = x_time / 1000
        y_time = y_time / 1000
        z_time = z_time / 1000
        unit_var = "m/s"
    elif unit_var == "mm/s^2":
        x_time = x_time / 1000
        y_time = y_time / 1000
        z_time = z_time / 1000
        unit_var = "m/s^2"
    else:
        quit()
        return 0
    band_rms_x, band_rms_y, band_rms_z, band_max_x, band_max_y, band_max_z, band_center, band_width = bars(sample_rate)

    plot_label = tk.Label(
        start_bottom_frame,
        text="Choose type of plot: \n",
        fg='white', bg='#262c2b',
        font='Lato 12 bold')
    plot_label.pack(side=tk.TOP, pady=5, padx=5)

    Button(
        start_bottom_frame,
        text="RMS",
        width=50,
        fg='white', bg='#1f2226', font='Lato 10 bold',
        command=lambda: plot_window_setup("RMS", band_rms_x, band_rms_y, band_rms_z,
                                          band_center, band_width, unit_var)). \
        pack(side=tk.RIGHT, pady=5, padx=5)
    Button(
        start_bottom_frame,
        text="MAX",
        width=50,
        fg='white', bg='#1f2226', font='Lato 10 bold',
        command=lambda: plot_window_setup("MAX", band_max_x, band_max_y, band_max_z,
                                          band_center, band_width, unit_var)). \
        pack(side=tk.LEFT, pady=5, padx=5)


def bars(rate):
    band_center = [1, 1.25, 1.6, 2, 2.5, 3.15, 4, 5, 6.3, 8, 10, 12.5, 16, 20, 25, 31.5, 40, 50, 63, 80, 100]
    band_rms_x = [0] * len(band_center)
    band_max_x = [0] * len(band_center)
    band_rms_y = [0] * len(band_center)
    band_rms_z = [0] * len(band_center)
    band_max_y = [0] * len(band_center)
    band_max_z = [0] * len(band_center)
    for j in range(len(band_center)):
        band_low = band_center[j] * (2 ** (-1 / 6))
        band_high = band_center[j] * (2 ** (1 / 6))
        band_rms_x[j], band_rms_y[j], band_rms_z[j], band_max_x[j], band_max_y[j], band_max_z[j] = \
            butterworth_filter(band_low, band_high, rate)

    bar_width = [0] * len(band_center)
    bar_width[0] = 0.1
    for i in range(len(band_center)):
        if i != 0:
            bar_width[i] = bar_width[i - 1] * (2 ** (1 / 3))
    return band_rms_x, band_rms_y, band_rms_z, band_max_x, band_max_y, band_max_z, band_center, bar_width


def butterworth_filter(low, high, rate):
    global x_time
    global y_time
    global z_time
    rms_sum = 0.0
    sos = signal.butter(2, [low, high], btype='bandpass', output='sos', fs=rate)
    filtered_x = signal.sosfilt(sos, x_time)
    filtered_y = signal.sosfilt(sos, y_time)
    filtered_z = signal.sosfilt(sos, z_time)
    for m in range(len(filtered_x)):
        rms_sum = rms_sum + (filtered_x[m]) ** 2
    rms_x = math.sqrt(rms_sum / len(filtered_x))
    rms_sum = 0.0
    for n in range(len(filtered_y)):
        rms_sum = rms_sum + (filtered_y[n]) ** 2
    rms_y = math.sqrt(rms_sum / len(filtered_y))
    rms_sum = 0.0
    for k in range(len(filtered_z)):
        rms_sum = rms_sum + (filtered_z[k]) ** 2
    rms_z = math.sqrt(rms_sum / len(filtered_z))

    return rms_x, rms_y, rms_z, max(filtered_x), max(filtered_y), max(filtered_z)


def plot_window_setup(plot_type, band_x, band_y, band_z, band_center, band_width, unit_var):
    global x_time
    global y_time
    global z_time

    plot_window = tk.Toplevel(start_window)
    plot_window.title('PLOT')
    plot_window.geometry("1000x800")
    plot_window.configure(bg='#262c2b')
    plot_top_frame = tk.Frame(plot_window)
    plot_top_frame.pack(side=tk.TOP)
    plot_top_frame.configure(bg='#262c2b')
    plot_bottom_frame = tk.Frame(plot_window)
    plot_bottom_frame.pack(side=tk.BOTTOM)
    plot_bottom_frame.configure(bg='#262c2b')
    plot_right_frame = tk.Frame(plot_window)
    plot_right_frame.pack(side=tk.RIGHT)
    plot_right_frame.configure(bg='#262c2b')
    plot_left_frame = tk.Frame(plot_window)
    plot_left_frame.pack(side=tk.LEFT)
    plot_left_frame.configure(bg='#262c2b')

    plot_exit_button = Button(plot_bottom_frame,
                              command=lambda: plot_window.destroy(),
                              width=80, fg='white', bg='#1f2226',
                              text="EXIT", font='Lato 10 bold')
    plot_exit_button.pack(pady=5, padx=5)
    plot_save_button = Button(plot_right_frame,
                              command=lambda: print_csv(band_x, band_y, band_z, band_center, plot_type, unit_var),
                              width=100, fg='white', bg='#1f2226',
                              text="SAVE TO CSV", font='Lato 10 bold')
    plot_save_button.pack(pady=5, padx=5)
    filter_button = Button(
        plot_right_frame,
        text="Load custom filter...",
        # state="disabled",
        width=120,
        command=lambda: custom_filter(band_center),
        fg='white', bg='#1f2226',
        font='Lato 10 bold')
    filter_button.pack(pady=5, padx=5, )

    switch_variable = tk.StringVar(plot_window)
    switch_variable.set("None")
    plot_x_button = tk.Radiobutton(
        plot_top_frame,
        variable=switch_variable,
        value="X",
        indicatoron=False,
        height=2, width=8, fg='white', bg='#1f2226',
        text="X", font='Lato 10 bold')
    plot_x_button.pack(side=tk.LEFT, padx=5, pady=5)
    plot_y_button = tk.Radiobutton(
        plot_top_frame,
        variable=switch_variable,
        value="Y",
        indicatoron=False,
        height=2, width=8, fg='white', bg='#1f2226',
        text="Y", font='Lato 10 bold')
    plot_y_button.pack(side=tk.LEFT, padx=5, pady=5)
    if all(item == 0 for item in y_time):
        plot_y_button.configure(state="disabled")
    plot_z_button = tk.Radiobutton(
        plot_top_frame,
        variable=switch_variable,
        value="Z",
        indicatoron=False,
        height=2, width=8, fg='white', bg='#1f2226',
        text="Z", font='Lato 10 bold')
    plot_z_button.pack(side=tk.LEFT, padx=5, pady=5)
    if all(item == 0 for item in z_time):
        plot_z_button.configure(state="disabled")

    label_on_off = tk.IntVar(plot_window)
    plot_label_check = tk.Checkbutton(
        plot_left_frame,
        text="Show amplitudes", font='Lato 10',
        fg='white', bg='black',
        variable=label_on_off,
        onvalue=1,
        offvalue=0)
    plot_label_check.pack(side=tk.BOTTOM, padx=5, pady=5)

    # vdv calc
    if unit_var == "m/s^2":
        vdv_x, vdv_y, vdv_z = vdv(band_center)
        vdv_values_label = tk.Label(plot_right_frame,
                                    text="VDV X: " + str("{:.5f}".format(vdv_x)) + "\nVDV Y: "
                                         + str("{:.5f}".format(vdv_y)) + "\nVDV Z: " + str("{:.5f}".format(vdv_z)),
                                    fg='white', bg='#262c2b',
                                    font='Lato 12 bold')
        vdv_values_label.pack(side=tk.BOTTOM, pady=5, padx=5)
        vdv_time_label = tk.Label(plot_right_frame,
                                  text="VDV values",
                                  fg='white', bg='#262c2b',
                                  font='Lato 10 bold')
        vdv_time_label.pack(side=tk.BOTTOM, pady=5, padx=5)

    # norm comparison selection
    swd_var = tk.StringVar(plot_window)
    swd_var.set("Select SWD...")
    swds = ["SWD I", "SWD II"]
    swd_menu = tk.OptionMenu(plot_left_frame, swd_var, *swds)
    swd_menu.pack(side=tk.TOP, padx=5, pady=5)
    swd_menu.configure(fg='white', bg='#262c2b', font='Lato 10 bold')

    norm_line_var = tk.StringVar(plot_window)
    norm_line_var.set("Select norm line...")
    norm_lines_names = ["A", "B", "C", "D", "A\'", "B\'", "C\'", "D\'"]
    norm_line_menu = tk.OptionMenu(plot_left_frame, norm_line_var, *norm_lines_names)
    norm_line_menu.pack(side=tk.TOP, padx=5, pady=5)
    norm_line_menu.configure(fg='white', bg='#262c2b', font='Lato 10 bold')

    norm_apply_button = Button(
        plot_left_frame,
        text="Apply",
        width=50,
        command=lambda: choose_norm(swd_var.get(), norm_line_var.get(), unit_var),
        fg='white', bg='#1f2226',
        font='Lato 10 bold')
    norm_apply_button.pack(side=tk.TOP, padx=5, pady=5)

    plot_apply_button = Button(plot_top_frame,
                               text="Apply",
                               width=50, fg='white', bg='#1f2226',
                               command=lambda: plot_fin(
                                   plot_type, switch_variable.get(), band_x, band_y, band_z,
                                   band_center, band_width, unit_var, plot_window, label_on_off.get()),
                               font='Lato 10 bold')
    plot_apply_button.pack(side=tk.BOTTOM, padx=5, pady=25)


def plot_fin(plot_type, axis, band_x, band_y, band_z,
             band_center, band_width, unit_var, plot_window, label_on_off):
    bands = [0] * len(band_center)
    global multiplication_filter
    global x_axis
    global y_axis
    global canvas
    global toolbar
    global norm_plot

    fig = plt.Figure(figsize=(8, 8), dpi=100)

    if axis == "X":
        for i in range(len(band_center)):
            bands[i] = band_x[i]
    elif axis == "Y":
        for i in range(len(band_center)):
            bands[i] = band_y[i]
    elif axis == "Z":
        for i in range(len(band_center)):
            bands[i] = band_z[i]
    if not all(item == 1 for item in multiplication_filter):
        for i in range(len(bands)):
            bands[i] = bands[i] * multiplication_filter[i]

    if canvas and toolbar:
        canvas.get_tk_widget().pack_forget()
        toolbar.pack_forget()
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    toolbar = NavigationToolbar2Tk(canvas, plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    if norm_plot:
        del norm_plot
    plot_bar = fig.add_subplot(111)
    plot_bar.bar(band_center, bands, width=band_width, label=str(band_center))
    norm_plot = plot_bar.plot(x_axis, y_axis, 'r')

    fig.supxlabel('Frequency [Hz]')
    plot_bar.set_xscale('log', base=2)
    plot_bar.plot()
    plot_bar.grid(True)
    plot_bar.set_xticks(band_center)
    plot_bar.set_xticklabels(band_center)

    if label_on_off == 1:
        for x, y in zip(band_center, bands):
            label = "{:.3f}".format(y)
            plot_bar.annotate(label, (x, y),
                              textcoords="offset points",
                              xytext=(0, 10),
                              ha='center')

    if unit_var == "m/s":
        fig.supylabel('Velocity [m/s]')
    else:
        fig.supylabel('Acceleration [m/s^2]')
    if plot_type == "MAX":
        fig.suptitle('Third octave analysis - MAX')
    elif plot_type == "RMS":
        fig.suptitle('Third octave analysis - RMS')


def print_csv(band_x, band_y, band_z, band_center, plot_type, unit):
    directory = tk.filedialog.askdirectory()
    for i in range(len(band_center)):
        band_x[i] = "{:.5f}".format(band_x[i])
        band_y[i] = "{:.5f}".format(band_y[i])
        band_z[i] = "{:.5f}".format(band_z[i])
    bands = DataFrame()
    if plot_type == "MAX":
        bands = DataFrame(list(zip(band_center, band_x, band_y, band_z)),
                          columns=['Frequency [Hz]', 'X_MAX [' + unit + ']',
                                   'Y_MAX [' + unit + ']', 'Z_MAX [' + unit + ']'])
    elif plot_type == "RMS":
        bands = DataFrame(list(zip(band_center, band_x, band_y, band_z)),
                          columns=['Frequency [Hz]', 'X_RMS [' + unit + ']',
                                   'Y_RMS [' + unit + ']', 'Z_RMS [' + unit + ']'])
    bands.to_csv(os.path.join(directory, r'plot.csv'), sep=';', index=False)


def choose_norm(swd, norm_line, unit_var):
    global x_axis
    global y_axis

    if unit_var == "m/s^2":
        if swd == "SWD I":
            if norm_line == "A":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis
                y_axis = norm_lines.buildings_SWD_I_acc_A
            elif norm_line == "B":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis
                y_axis = norm_lines.buildings_SWD_I_acc_B
            elif norm_line == "C":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis
                y_axis = norm_lines.buildings_SWD_I_acc_C
            elif norm_line == "D":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis_D
                y_axis = norm_lines.buildings_SWD_I_acc_D
            elif norm_line == "A\'":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis_Aa
                y_axis = norm_lines.buildings_SWD_I_acc_Aa
            elif norm_line == "B\'":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis_Aa
                y_axis = norm_lines.buildings_SWD_I_acc_Bb
            elif norm_line == "C\'":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis_Cc
                y_axis = norm_lines.buildings_SWD_I_acc_Cc
            elif norm_line == "D\'":
                x_axis = norm_lines.buildings_SWD_I_acc_X_axis_Dd
                y_axis = norm_lines.buildings_SWD_I_acc_Dd
        elif swd == "SWD II":
            if norm_line == "A":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_A_C
                y_axis = norm_lines.buildings_SWD_II_acc_A
            elif norm_line == "B":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_B
                y_axis = norm_lines.buildings_SWD_II_acc_B
            elif norm_line == "C":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_A_C
                y_axis = norm_lines.buildings_SWD_II_acc_C
            elif norm_line == "D":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_D
                y_axis = norm_lines.buildings_SWD_II_acc_D
            elif norm_line == "A\'":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_A_C
                y_axis = norm_lines.buildings_SWD_II_acc_Aa
            elif norm_line == "B\'":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_B
                y_axis = norm_lines.buildings_SWD_II_acc_Bb
            elif norm_line == "C\'":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_A_C
                y_axis = norm_lines.buildings_SWD_II_acc_Cc
            elif norm_line == "D\'":
                x_axis = norm_lines.buildings_SWD_II_acc_X_axis_Dd
                y_axis = norm_lines.buildings_SWD_II_acc_Dd
    elif unit_var == "m/s":
        if swd == "SWD I":
            if norm_line == "A":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_I_vel_A
            elif norm_line == "B":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_I_vel_B
            elif norm_line == "C":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_I_vel_C
            elif norm_line == "D":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_I_vel_D
            elif norm_line == "A\'":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_Aa
                y_axis = norm_lines.buildings_SWD_I_vel_Aa
            elif norm_line == "B\'":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_Bb
                y_axis = norm_lines.buildings_SWD_I_vel_Bb
            elif norm_line == "C\'":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_Cc
                y_axis = norm_lines.buildings_SWD_I_vel_Cc
            elif norm_line == "D\'":
                x_axis = norm_lines.buildings_SWD_I_vel_X_axis_Dd
                y_axis = norm_lines.buildings_SWD_I_vel_Dd
        elif swd == "SWD II":
            if norm_line == "A":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_A
            elif norm_line == "B":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_B
            elif norm_line == "C":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_C
            elif norm_line == "D":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_D
            elif norm_line == "A\'":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_Aa
            elif norm_line == "B\'":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_Bb
            elif norm_line == "C\'":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_Cc
            elif norm_line == "D\'":
                x_axis = norm_lines.buildings_SWD_II_vel_X_axis_A
                y_axis = norm_lines.buildings_SWD_II_vel_Dd


def custom_filter(band_center):
    global multiplication_filter

    filter_window = tk.Toplevel(start_window)
    filter_window.title('Filter')
    filter_window.geometry("400x600")
    filter_window.configure(bg='#262c2b')
    filter_top_frame = tk.Frame(filter_window)
    filter_top_frame.pack(side=tk.TOP)
    filter_top_frame.configure(bg='#262c2b')
    filter_bottom_frame = tk.Frame(filter_window)
    filter_bottom_frame.pack(side=tk.BOTTOM)
    filter_bottom_frame.configure(bg='#262c2b')

    if len(multiplication_filter) == 0:
        multiplication_filter = [1] * len(band_center)

    def load_filter_csv():
        temp_filter = []
        global multiplication_filter
        temp_filter_name = (tk.filedialog.askopenfile(mode='r', filetypes=[('CSV file', '*.csv')]))

        if temp_filter_name is None:
            try_again = messagebox.askretrycancel("Error message", "No file selected")
            if try_again:
                load_filter_csv()
            else:
                pass

        filter_data = read_csv(str(temp_filter_name.name))
        if list(filter_data.columns) == ['Fi']:
            temp_filter = filter_data['Fi']
            for j in range(len(multiplication_filter)):
                multiplication_filter[j] = temp_filter[j]
                octave_values.item(j, text="", values=(band_center[j], multiplication_filter[j]))
        else:
            try_again = messagebox.askretrycancel("Error message", "Selected file cannot be read")
            if try_again:
                load_filter_csv()
            else:
                pass

    filter_csv_button = Button(
        filter_top_frame,
        text="Load CSV",
        width=80,
        fg='white', bg='#1f2226',
        command=lambda: load_filter_csv(),
        font='Lato 10 bold')
    filter_csv_button.pack(side=tk.TOP, pady=5, padx=5)

    octave_frame = tk.Frame(filter_top_frame)
    octave_frame.pack(side=tk.TOP, pady=5, padx=5)
    octave_scroll = tk.Scrollbar(octave_frame, orient='vertical')
    octave_scroll.pack(side='right', fill='y')

    octave_values = ttk.Treeview(octave_frame, yscrollcommand=octave_scroll.set)
    octave_values.pack()

    octave_scroll.config(command=octave_values.yview)

    # column definition
    octave_values['columns'] = ('center_band', 'filter_value')

    octave_values.column("#0", width=0, stretch=False)
    octave_values.column("center_band", anchor='center', width=120)
    octave_values.column("filter_value", anchor='center', width=120)

    # headings
    octave_values.heading("#0", text="", anchor='center')
    octave_values.heading("center_band", text="Band Frequency [Hz]", anchor='center')
    octave_values.heading("filter_value", text="Filter value", anchor='center')

    for i in range(len(multiplication_filter)):
        octave_values.insert(parent='', index='end', iid=(str(i)), text='',
                             values=(band_center[i], multiplication_filter[i]))

    # select record

    def select_record():
        # clear entry boxes
        center_band_entry.delete(0, 'end')
        filter_value_entry.delete(0, 'end')

        # grab record
        selected = octave_values.focus()
        # grab record values
        record_values = octave_values.item(selected, 'values')
        # temp_label.config(text=selected)

        # output to entry boxes
        center_band_entry.insert(0, record_values[0])
        filter_value_entry.insert(0, record_values[1])

    # save record
    def update_record():
        selected = octave_values.focus()
        # save new data
        octave_values.item(selected, text="", values=(center_band_entry.get(), filter_value_entry.get()))

        # clear entry boxes
        center_band_entry.delete(0, 'end')
        filter_value_entry.delete(0, 'end')

    def reset_filter():
        for k in range(len(multiplication_filter)):
            multiplication_filter[k] = 1
            octave_values.item(k, text="", values=(band_center[k], multiplication_filter[k]))

    select_button = tk.Button(filter_top_frame, text="Select Record", command=select_record)
    select_button.pack(side=tk.TOP, padx=5, pady=5)

    # labels
    center_band = tk.Label(filter_top_frame, text="Center band", width=10)
    center_band.pack(side=tk.LEFT, padx=5, pady=5, anchor=tk.N)

    center_band_entry = tk.Entry(filter_top_frame, width=10)
    center_band_entry.pack(side=tk.LEFT, padx=5, pady=5, anchor=tk.S)

    filter_value = tk.Label(filter_top_frame, text="Filter value: ", width=10)
    filter_value.pack(side=tk.LEFT, padx=5, pady=5, anchor=tk.N)

    filter_value_entry = tk.Entry(filter_top_frame, width=10)
    filter_value_entry.pack(side=tk.LEFT, padx=5, pady=5, anchor=tk.S)

    edit_button = tk.Button(filter_window, text="Edit ", command=update_record)
    edit_button.pack(pady=10)

    filter_info_label = tk.Label(filter_bottom_frame,
                                 text="Filter applied",
                                 fg='white', bg='#262c2b',
                                 font='Lato 8')
    filter_info_label.pack(side=tk.BOTTOM, anchor=tk.S, pady=5, padx=5)

    # print(filter_list)
    filter_reset_button = Button(
        filter_bottom_frame,
        text="Reset to default",
        width=80,
        fg='white', bg='#1f2226',
        command=lambda: reset_filter(),
        font='Lato 10 bold')
    filter_reset_button.pack(side=tk.BOTTOM, pady=5, padx=5)

    filter_ok_button = Button(
        filter_bottom_frame,
        text="OK",
        width=20,
        fg='white', bg='#1f2226',
        command=lambda: get_filter_values(),
        font='Lato 10 bold')
    filter_ok_button.pack(side=tk.BOTTOM, pady=5, padx=5)

    def get_filter_values():
        for j in range(len(band_center)):
            temp_dict = octave_values.item(str(j))
            octave_values_list = list(temp_dict.values())
            multiplication_filter[j] = octave_values_list[2][1]
        filter_window.destroy()

    filter_window.mainloop()


def vdv(band_center):
    global x_time
    global y_time
    global z_time
    global t
    weight_x_y = [1.011, 1.008, 0.968, 0.890, 0.776, 0.642, 0.512, 0.409, 0.323, 0.253, 0.212, 0.161, 0.125, 0.100,
                  0.080, 0.0632, 0.0494, 0.0388, 0.0295, 0.0211, 0]
    weight_z = [0.482, 0.484, 0.494, 0.531, 0.631, 0.804, 0.967, 1.039, 1.054, 1.036, 0.988, 0.902, 0.768, 0.636,
                0.513, 0.405, 0.314, 0.246, 0.186, 0.132, 0]
    # integration limits
    '''i = 0
    for i in range(len(t)):
        if t[i] < vibration_time:
            pass
        else:
            if i >= len(t):
                break
            else:
                del t[i:]
                del x_time[i:]
                del y_time[i:]
                del z_time[i:]
            break'''

    rate = 1 / (t[2] - t[1])
    x_weighted = []
    y_weighted = []
    z_weighted = []
    for i in range(len(band_center)):
        band_low = band_center[i] * (2 ** (-1 / 6))
        band_high = band_center[i] * (2 ** (1 / 6))

        sos = signal.butter(2, [band_low, band_high], btype='bandpass', output='sos', fs=rate)
        filtered_x = signal.sosfilt(sos, x_time)
        filtered_y = signal.sosfilt(sos, y_time)
        filtered_z = signal.sosfilt(sos, z_time)
        for m in range(len(filtered_x)):
            filtered_x[m] = filtered_x[m] * weight_x_y[i]
            x_weighted.append(filtered_x[m])
        for m in range(len(filtered_y)):
            filtered_y[m] = filtered_y[m] * weight_x_y[i]
            y_weighted.append(filtered_y[m])
        for m in range(len(filtered_z)):
            filtered_z[m] = filtered_z[m] * weight_z[i]
            z_weighted.append(filtered_z[m])

    for i in range(len(z_weighted)):
        x_weighted[i] = x_weighted[i] ** 4
        y_weighted[i] = y_weighted[i] ** 4
        z_weighted[i] = z_weighted[i] ** 4
    vdv_x = (scipy.integrate.trapezoid(x_weighted)) ** 0.25
    vdv_y = (scipy.integrate.trapezoid(y_weighted)) ** 0.25
    vdv_z = (scipy.integrate.trapezoid(z_weighted)) ** 0.25

    return vdv_x, vdv_y, vdv_z


# starting window


# ctypes.windll.shcore.SetProcessDpiAwareness(1)
x_time = []
y_time = []
z_time = []
t = []
load_csv = 0
multiplication_filter = []
x_axis = []
y_axis = []
canvas = None
toolbar = None
norm_plot = None

# exec(open("norm_lines.py").read())
start_window = tk.Tk()
# ico = Image.open("kawka.png")
# photo = ImageTk.PhotoImage(ico)
# start_window.wm_iconphoto(True, photo)
start_window.title("KAWKA - Noise impact third octave analysis ")
start_window.geometry("600x400")
start_window.configure(bg='#262c2b')

start_bottom_frame = tk.Frame(start_window)
start_bottom_frame.pack(side=tk.BOTTOM)
start_bottom_frame.configure(bg='#262c2b')

start_top_frame = tk.Frame(start_window)
start_top_frame.pack(side=tk.TOP)
start_top_frame.configure(bg='#262c2b')

info_label = tk.Label(start_bottom_frame,
                      text="Kawka by bianek 2023",
                      fg='white', bg='#262c2b',
                      font='Lato 8')
info_label.pack(side=tk.BOTTOM, anchor=tk.S, pady=5, padx=5)

choose_file_lbl = tk.Label(start_top_frame,
                           text="Choose file to import:\n",
                           fg='white', bg='#262c2b',
                           font='Lato 12 bold')
choose_file_lbl.pack(side=tk.TOP, pady=5, padx=5)
browse_button = Button(start_top_frame,
                       text="Browse",
                       width=100,
                       fg='#ffffff', bg='#1f2226',
                       command=lambda: check_file(),
                       font='Lato 12 bold',
                       borderless=1)
browse_button.pack(side=tk.TOP, pady=5, padx=5)

start_window.mainloop()
