__author__ = 'brian'

from Tkinter import *
import ttk
from tkFileDialog   import askopenfilename
from autoscrollbar import AutoScrollable
import glob
import os
import sys

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )
import utils
import custom_widgets


def load_model_from_file(f):
    print 'load from %s' % f
    factory = utils.FileReactionFactory(f)
    model = utils.Model(factory)
    reactions = model.get_reactions()
    return reactions


class ModelSetupFrame(ttk.Frame):
    
    def __init__(self,parent, controller=None,):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        
        # add a paned window for building/loading and viewing current model:
        pf = ttk.Panedwindow(self, orient=HORIZONTAL)
        left_panel = ttk.Labelframe(pf, text='Model Specification', width=600, height=400)
        right_panel = ttk.Labelframe(pf, text='Current Model', width=400, height=200)   # second pane
        pf.add(left_panel)
        pf.add(right_panel)
        pf.grid(column=0,row=0, sticky=(N,W,E,S))

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

        # a button for moving to the next step in the workflow.  Initially disabled, until the model is loaded
        self.next_button = ttk.Button(right_panel, text='Next')
        self.next_button.grid(column=0, row=1, sticky=(N,E), pady=10)
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
            reactions = load_model_from_file(filepath)
            self.load_reactions(reactions)
        except Exception as ex:
            print 'exception caught'
            error_msg = ttk.Label(self.reaction_summary_panel.frame, text=ex.message)
            error_msg.grid(column=0, row=0)

    def add_new_reaction(self, reaction_obj = None):
        reaction_widget = custom_widgets.ReactionEntryPanel(self.reaction_summary_panel.frame, reaction_obj=reaction_obj)
        try:
            row_index = max(self.current_reaction_widget_dict.keys())+1
        except ValueError:
            row_index = 0
        eqn_index = self.reaction_indexer
        reaction_widget.grid(column=0, row=row_index, sticky=(N, S, E, W))
        rm_button = ttk.Button(self.reaction_summary_panel.frame, text='x', width=2)
        rm_button['command']= lambda btn=rm_button, idx= eqn_index, obj=reaction_widget : self.remove_eqn(btn, idx, obj)
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
                reactions = load_model_from_file(self.predefined_model_map[selected_model_name])
                self.load_reactions(reactions)
            except Exception as ex:
                print 'exception caught'
                error_msg = ttk.Label(self.reaction_summary_panel.frame, text=ex.message)
                error_msg.grid(column=0, row=0)


def gui_main():

    root = Tk()
    root.title("True T")

    model_setup_frame = ModelSetupFrame(root)
    model_setup_frame.grid(column=0, row=0, sticky=(N, W, E, S))

    # if the window is resized, change the size to follow:
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("%dx%d+0+0" % (int(w/2.0), int(h/2.0)))
    return root

if __name__ == '__main__':
    gui_root = gui_main()
    gui_root.mainloop()