__author__ = 'brian'

from Tkinter import *
import ttk
from tkFileDialog import askopenfilename
from autoscrollbar import AutoScrollable
import glob
import os
import sys

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )
import utils
import custom_widgets
#import model_solvers


class InitialConditionsFrame(ttk.Frame):

    def __init__(self, parent, controller=None, order_index=0):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.order_index = order_index

    def prep(self):

        self.model = self.controller.get_model()

        reaction_summary_title = ttk.Label(self, text="Reaction summary", anchor=W)
        reaction_summary_title.grid(row=0, column=0, sticky=W)
        reaction_summary_frame = ttk.Frame(self)
        reaction_summary_frame.grid(column=0, row=1, padx=(10,100), sticky=(N,W))
        for i, reaction in enumerate(self.model.get_reactions()):
            label = ttk.Label(reaction_summary_frame, text=reaction, anchor=W)
            label.grid(column=0, row=i, pady=10, sticky=W)


        dl = ttk.Label(self, text="Initial conditions (Molar concentration)", anchor=W)
        dl.grid(row=0, column=1, sticky=W)
        ic_entry_frame = ttk.Frame(self)
        ic_entry_frame.grid(row=1, column=1, padx=(20, 50))
        initial_conditions = self.model.get_initial_conditions()
        all_symbols = self.model.get_all_elements()
        longest_symbol = max([len(x) for x in all_symbols])
        self.initial_condition_widgets = {}
        for i, s in enumerate(all_symbols):
            if s in initial_conditions:
                ic_entry_widget = custom_widgets.InitialConditionEntryPanel(ic_entry_frame, s, initial_conditions[s], length=longest_symbol)
            else:
                ic_entry_widget = custom_widgets.InitialConditionEntryPanel(ic_entry_frame, s, 0.0, length=longest_symbol)
            ic_entry_widget.grid(row=i, column=1)
            self.initial_condition_widgets[s] = ic_entry_widget

        time_label = ttk.Label(self, text='Simulation time (seconds)', anchor=E)
        time_label.grid(column=2, row=0, sticky=E, padx=10, pady=10)
        time_entry_frame = ttk.Frame(self)
        time_entry_frame.grid(row=1, column=2, sticky=(N,E), padx=(30,5))

        self.sim_time = DoubleVar()
        self.sim_time.set(self.model.get_simulation_time())
        time_entry = ttk.Entry(time_entry_frame, textvariable=self.sim_time, width=4)
        time_entry.grid(row=0, column=0, sticky=(N,E), padx=10, pady=10)

        self.next_button = Button(self, text='Simulate', anchor=E)
        self.next_button['command'] = lambda: self.store_model_and_advance()
        self.next_button.grid(column=2, row=3, sticky=(S,E), pady=10)

        self.previous_button = ttk.Button(self, text='Previous')
        self.previous_button['command'] = lambda: self.controller.show_frame(self.order_index - 1)
        self.previous_button.grid(column=0, row=3, sticky=(S,W), pady=10, padx=10)

        self.ic_error_msg_var = StringVar()
        self.ic_error_msg_label = ttk.Label(self, textvariable=self.ic_error_msg_var, anchor=E)
        self.ic_error_msg_label.grid(column=1, row=3, sticky=E, padx=10, pady=10)

        self.time_error_msg_var = StringVar()
        self.time_error_msg_label = ttk.Label(time_entry_frame, textvariable=self.time_error_msg_var, anchor=E)
        self.time_error_msg_label.grid(column=0, row=1, sticky=E, padx=10, pady=10)

    def store_model_and_advance(self):

        ic_dict = {}
        is_clean = True
        self.ic_error_msg_var.set('')
        self.time_error_msg_var.set('')
        for symbol, widget in self.initial_condition_widgets.items():
            try:
                ic_dict[symbol] = widget.ic.get()
            except ValueError as ex:
                is_clean = False
                self.ic_error_msg_var.set('Problem with initial condition for symbol %s:\n %s' % (symbol, ex.message))
                widget.ic_entry.focus()
        self.model.set_initial_conditions(ic_dict)
        try:
            self.model.set_simulation_time(self.sim_time.get())
        except Exception as ex:
            is_clean = False
            self.time_error_msg_var.set('Problem with simulation time: %s' % ex.message)

        if is_clean:
            self.controller.set_model(self.model)
            self.controller.show_frame(self.order_index + 1)


class CalculatorResultFrame(ttk.Frame):

    def __init__(self, parent, controller=None, order_index=0):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.order_index = order_index
        dl = ttk.Label(self, text="results")
        dl.grid(row=0, column=0)

        self.previous_button = ttk.Button(self, text='Previous')
        self.previous_button['command'] = lambda: self.controller.show_frame(self.order_index - 1)
        self.previous_button.grid(column=0, row=1, sticky=(N,E), pady=10)

    def prep(self):
        #solver = model_solvers.ODESolver(self.controller.get_model())
        #solution = solver.equilibrium_solution()
        pass

class ModelSetupFrame(ttk.Frame):
    
    def __init__(self,parent, controller=None, order_index=0):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        self.order_index = order_index
        
        # add a paned window for building/loading and viewing current model:
        pf = ttk.Panedwindow(self, orient=HORIZONTAL)
        left_panel = ttk.Labelframe(pf, text='Model Specification', width=600, height=400)
        right_panel = ttk.Labelframe(pf, text='Current Model', width=400, height=200)   # second pane
        pf.add(left_panel)
        pf.add(right_panel)
        pf.grid(column=0,row=0, sticky=(N,W,E,S))

        # set this attribute to None- if pre-defined models are loaded, it will be reset.
        self.model = None

        ############################ left panel material begin #######################################################
        ############################ left tab material begin ########################################################
        # add some choice tabs to the left panel-
        tabs = ttk.Notebook(left_panel)
        tabs.grid(column=0, row=0, sticky=(N,W,E,S), pady=10)
        tabs.grid_columnconfigure(0, weight=1)
        tabs.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(0, weight=1)

        # add a frame for the existing model tab
        predefined_model_frame = ttk.Frame(tabs)
        header_label = ttk.Label(predefined_model_frame, text="Select a pre-defined model below")
        header_label.grid(column=0, row=0, sticky=(N,W), pady=10)

        # populate a listbox for selecting existing models, including a scrollbar
        self.predefined_model_map = self.get_predefined_models()
        self.model_names = tuple(self.predefined_model_map.keys())
        m_names = StringVar(value=self.model_names)
        self.predefined_model_listbox = Listbox(predefined_model_frame, listvariable=m_names, selectmode=SINGLE)
        self.predefined_model_listbox.grid(column=0, row=1, sticky=(N,S,E,W))
        scroller = ttk.Scrollbar(predefined_model_frame, orient=VERTICAL, command=self.predefined_model_listbox.yview)
        scroller.grid(column=1, row=1, sticky=(N,S))
        self.predefined_model_listbox['yscrollcommand'] = scroller.set
        self.predefined_model_listbox.bind('<<ListboxSelect>>', self.display_model_from_listbox)

        # only allow the listbox to expand/grow with its parent
        predefined_model_frame.grid_columnconfigure(0, weight=1)
        predefined_model_frame.grid_rowconfigure(1, weight=1)
        ############################ left tab material end ###########################################################

        ############################ right tab material begin #######################################################

        model_builder_frame = ttk.Frame(tabs)

        open_file_label = ttk.Label(model_builder_frame, text='Load model from file:')
        open_file_button = ttk.Button(model_builder_frame,
                                      text='Open',
                                      command=self.open_file_dialog)

        add_reaction_button = ttk.Button(model_builder_frame,
                                         text='Create new reaction',
                                         command=self.add_new_reaction)

        or_manual_label = ttk.Label(model_builder_frame, text='Or manually enter reactions:')
        open_file_label.grid(column=0, row=0, sticky=(N,W), pady=10)
        open_file_button.grid(column=0, row=1, sticky=(N,W), pady=(0,10))
        or_manual_label.grid(column=0, row=2, sticky=(N,W), pady=10)
        add_reaction_button.grid(column=0, row=3, sticky=(N,W), pady=(0,10))



        ############################ right tab material end #######################################################

        ############################ left panel material end #######################################################


        ############################ right panel material begin #######################################################

        # an auto-scrolling panel to contain the equations- this way they will not go off-screen on resizing
        self.reaction_summary_panel = AutoScrollable(right_panel)
        self.reaction_summary_panel.grid(column=0, row=0, sticky=(N,S,E,W))

        # a place to put error messages when submissions have errors:
        self.submission_error_text = StringVar()
        self.submission_error_label = ttk.Label(right_panel, textvariable=self.submission_error_text)
        self.submission_error_label.grid(column=0, row=1, sticky=(N,E), padx=(0,10))

        # a button for moving to the next step in the workflow.  Initially disabled, until the model is loaded
        self.next_button = ttk.Button(right_panel, text='Next')
        self.next_button['command'] = lambda: self.store_model_and_advance()
        self.next_button.grid(column=1, row=1, sticky=(N,E), pady=10)
        self.next_button.state(['disabled'])

        for child in right_panel.winfo_children():
            child.grid_configure(padx=5)

        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)

        ############################ right panel material end #########################################################

        # add the panels to the respective tabs:
        tabs.add(predefined_model_frame, text='Predefined Models')
        tabs.add(model_builder_frame, text='Create a model')

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_reaction_widget_dict = {}
        self.reaction_indexer = 0 # keeps track of maximum index for the dictionary above

    def open_file_dialog(self):
        filepath = askopenfilename()
        self.clear_reaction_panel()
        try:
            self.model = self.controller.load_model_from_file(filepath)
            reactions = self.model.get_reactions()
            self.load_reactions(reactions)
            self.submission_error_text.set('')
        except Exception as ex:
            print 'exception caught'
            error_msg = ttk.Label(self.reaction_summary_panel.frame, text=ex.message)
            error_msg.grid(column=0, row=0)

    def store_model_and_advance(self):
        # 'save' the model (by parsing the ReactionEntryPanel widgets) and push it up
        # to the 'main' app, so that other pages have access to the model
        reaction_strings_dict = {}
        for reaction_id, reaction_widget in self.current_reaction_widget_dict.items():

            reactant_str = reaction_widget.reactants.get()
            product_str = reaction_widget.products.get()
            ka = reaction_widget.ka.get()
            kd = reaction_widget.kd.get()
            direction_symbol = reaction_widget.direction_symbol.get()
            reaction_strings_dict[reaction_id] = '%s %s %s, %s, %s' % (reactant_str, direction_symbol, product_str, ka, kd)

        try:

            # even if the model was loaded from a file (with initial conditions, etc) the user could have edited it,
            # so we get the most recent state here.  However, in the case that the model was loaded from a file, a model
            # instance exists somewhere.  We *might* be able to get initial conditions and/or simulation time from that
            # We then insert those parameters into the 'new' Model instance below
            reaction_factory = utils.GUIReactionFactory(reaction_strings_dict)
            model = utils.Model(reaction_factory)

            # if we happened to load the data from a file, get any initial conditions from that
            if self.model:
                initial_conditions_from_file = self.model.get_initial_conditions()
                initial_conditions_from_file = {x:initial_conditions_from_file[x]
                                                for x in initial_conditions_from_file.keys()
                                                if x in model.get_all_elements()}
                model.set_initial_conditions(initial_conditions_from_file)
                simulation_time_from_file = self.model.get_simulation_time()
                model.set_simulation_time(simulation_time_from_file)

            self.controller.set_model(model)

            # move on to the next page
            self.controller.show_frame(self.order_index + 1)
            self.submission_error_text.set('')
        except Exception as ex:
            print ex.message
            self.submission_error_text.set(ex.detailed_message)
            self.current_reaction_widget_dict[ex.error_index].reactant_entry.focus()
            print ex.error_index
            print ex.detailed_message

    def add_new_reaction(self, reaction_obj = None):
        reaction_widget = custom_widgets.ReactionEntryPanel(self.reaction_summary_panel.frame, reaction_obj=reaction_obj)
        try:
            row_index = max(self.current_reaction_widget_dict.keys())+1
        except ValueError:
            row_index = 0
        eqn_index = self.reaction_indexer
        reaction_widget.grid(column=0, row=row_index, sticky=(N, S, E, W))
        rm_button = ttk.Button(self.reaction_summary_panel.frame, text='x', width=2)
        rm_button['command']= lambda btn=rm_button, idx= eqn_index, obj=reaction_widget: self.remove_eqn(btn, idx, obj)
        rm_button.grid(column=1, row=row_index)
        self.current_reaction_widget_dict[eqn_index] = reaction_widget
        self.reaction_indexer += 1
        self.next_button.state(['!disabled'])

    @staticmethod
    def get_predefined_models():
        suffix = '.model'
        model_files = glob.glob('%s/*%s' % (os.path.dirname(os.path.realpath(__file__)), suffix))
        print model_files
        model_file_map = {}
        for mf in model_files:
            model_name = os.path.basename(mf)[:-len(suffix)]
            model_file_map[model_name] = mf
        return model_file_map

    def remove_eqn(self, btn, index, obj):
        btn.destroy()
        obj.destroy()
        print 'remove equation with index: %s' % index
        self.current_reaction_widget_dict.pop(index)
        if len(self.current_reaction_widget_dict.keys()) == 0:
            self.next_button.state(['disabled'])

    def clear_reaction_panel(self):
        for child in self.reaction_summary_panel.frame.winfo_children():
            child.destroy()
        self.current_reaction_widget_dict ={}


    def load_reactions(self, reactions):
        # remove any existing reactions-- we're loading fresh!
        self.clear_reaction_panel()
        for rx in reactions:
            self.add_new_reaction(rx)

    def display_model_from_listbox(self, *args):

        # until we know for sure what's going on, disable the next button
        self.next_button.state(['disabled'])

        self.current_reaction_widget_dict = {}

        # the selected item is given by the integer index
        idxs = self.predefined_model_listbox.curselection()
        if len(idxs) == 1:
            for child in self.reaction_summary_panel.frame.winfo_children():
                child.destroy()
            idx = int(idxs[0])
            selected_model_name = self.model_names[idx]
            try:
                self.model = self.controller.load_model_from_file(self.predefined_model_map[selected_model_name])
                reactions = self.model.get_reactions()
                self.load_reactions(reactions)
                self.submission_error_text.set('')
            except Exception as ex:
                print 'exception caught'
                error_msg = ttk.Label(self.reaction_summary_panel.frame, text=ex.message)
                error_msg.grid(column=0, row=0)

    def prep(self):
        pass

class AppMain(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        main_container = ttk.Frame(self)
        main_container.grid(row=0, column=0, sticky=(N,S,E,W))
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        # now, we will add frames into the main_container
        self.frames = {}
        for i, F in enumerate([ModelSetupFrame, InitialConditionsFrame, CalculatorResultFrame]):
            frame = F(parent=main_container, controller=self, order_index=i)
            self.frames[i] =  frame
            frame.grid(row=0, column=0, sticky=(N,S,E,W))

        self.current_frame = 0
        self.show_frame(0)

    def show_frame(self, idx):
        frame = self.frames[idx]
        frame.prep()
        frame.tkraise()
        self.current_frame = idx

    def set_model(self, model):
        print 'pushing model to main app'
        print model
        self.model = model

    def get_model(self):
        return self.model

    @staticmethod
    def load_model_from_file(f):
        print 'load from %s' % f
        factory = utils.FileReactionFactory(f)
        model = utils.Model(factory)
        return model


def gui_main():

    #root = Tk()
    root = AppMain()
    root.title("True T")

    # if the window is resized, change the size to follow:
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("%dx%d+0+0" % (int(w/2.0), int(h/2.0)))
    return root

if __name__ == '__main__':
    gui_root = gui_main()
    gui_root.mainloop()