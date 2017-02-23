__author__ = 'brian'

from Tkinter import *
import ttk

class ReactionEntryPanel(ttk.Frame):
    def __init__(self, parent, controller=None, reaction_obj = None):
        ttk.Frame.__init__(self, parent)
        self.controller = controller

        self.reactants = StringVar()
        self.products = StringVar()
        self.ka = DoubleVar()
        self.kd = DoubleVar()
        self.direction_symbol = StringVar()
        self.is_bidirectional = True

        if reaction_obj:
            self.reactants.set(reaction_obj.reactant_str())
            self.products.set(reaction_obj.product_str())
            self.ka.set(reaction_obj.get_fwd_k())
            self.kd.set(reaction_obj.get_rev_k())
            self.is_bidirectional = reaction_obj.is_bidirectional_reaction()

        self.reactant_entry = ttk.Entry(self, textvariable=self.reactants)
        self.product_entry = ttk.Entry(self, textvariable=self.products)
        self.direction_symbol_entry = ttk.Combobox(self, state='readonly', width=4, textvariable=self.direction_symbol)
        self.direction_symbol_entry['values'] = ('-->','<-->')
        if self.is_bidirectional:
            self.direction_symbol_entry.current(1)
        else:
            self.direction_symbol_entry.current(0)
        self.ka_entry = ttk.Entry(self, width=6, textvariable=self.ka)
        self.kd_entry = ttk.Entry(self, width=6, textvariable=self.kd)

        self.reactant_entry.grid(row=0, column=0)
        self.product_entry.grid(row=0,column=2)
        self.direction_symbol_entry.grid(row=0,column=1)
        self.ka_entry.grid(row=0,column=3, padx=10)
        self.kd_entry.grid(row=0, column=4, padx=10)
        self.grid_rowconfigure(0, weight=1)


        self.direction_symbol_entry.bind("<<ComboboxSelected>>", self.on_direction_change)

        for child in self.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def on_direction_change(self, *args):
        print 'event fired!'
        if self.direction_symbol.get().startswith('<'):
            self.is_bidirectional = True
            self.kd.set(0.0)
            self.kd_entry.state(['!disabled'])
        else:
            self.is_bidirectional = False
            self.kd.set(0.0)
            self.kd_entry.state(['disabled'])


class InitialConditionEntryPanel(ttk.Frame):

    def __init__(self, parent, species, ic, length=25):
        ttk.Frame.__init__(self, parent)

        label = ttk.Label(self, text=species, anchor=W, width=length)
        label.grid(column=0, row=0, sticky=W, padx=10, pady=10)

        self.ic = DoubleVar()
        self.ic.set(ic)
        self.ic_entry = ttk.Entry(self, textvariable=self.ic)
        self.ic_entry.grid(row=0, column=1, sticky=W, padx=10, pady=10)
