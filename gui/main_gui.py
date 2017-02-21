__author__ = 'brian'

from Tkinter import *
import ttk
from autoscrollbar import AutoScrollable
import glob
import os
import sys
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )
import utils
import custom_widgets


def load_model(f):
    print 'load from %s' % f
    factory = utils.FileReactionFactory(f)
    model = utils.Model(factory)
    reactions = model.get_reactions()
    return reactions



def gui_main(predefined_model_map):

    def remove_eqn(btn, index, obj):
        btn.destroy()
        obj.destroy()

    def display_model(*args):
        next_button.state(['disabled'])
        print args
        idxs = predefined_model_listbox.curselection()
        if len(idxs)==1:
            for child in eqn_edit_panel.frame.winfo_children():
                child.destroy()
            idx = int(idxs[0])
            selected_model_name = model_names[idx]
            try:
                reactions = load_model(predefined_model_map[selected_model_name])
                rm_buttons = []
                for i,rx in enumerate(reactions):
                    new_reaction = custom_widgets.ReactionEntryPanel(eqn_edit_panel.frame, reaction_obj=rx)
                    new_reaction.grid(column=0, row=i, sticky=(N,S,E,W))
                    rm_button = ttk.Button(eqn_edit_panel.frame, text='x', width=2)
                    rm_button['command']= lambda btn=rm_button, idx=i, obj=new_reaction: remove_eqn(btn, idx, obj)
                    rm_button.grid(column=1, row=i)
                    eqn_rows.append(new_reaction)
                next_button.state(['!disabled'])
            except Exception as ex:
                print 'exception caught'
                error_msg = ttk.Label(eqn_edit_panel.frame, text=ex.message)
                error_msg.grid(column=0, row=0)


    root = Tk()
    root.title("True T")

    # The 'main' frame to hold everything
    mainframe = ttk.Frame(root, padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    # if the window is resized, change the size to follow:
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    pf = ttk.Panedwindow(mainframe, orient=HORIZONTAL)
    #pf.configure(width=15)
    f1 = ttk.Labelframe(pf, text='Model Specification', width=600, height=400)
    f2 = ttk.Labelframe(pf, text='Current Model', width=400, height=400)   # second pane
    pf.add(f1)
    pf.add(f2)
    pf.grid(column=0,row=0, sticky=(N,W,E,S))

    # add some choice tabs
    tabs = ttk.Notebook(f1)
    tabs.grid(column=0, row=0, sticky=(N,W,E,S), pady=10)
    tabs.grid_columnconfigure(0, weight=1)
    tabs.grid_rowconfigure(0, weight=1)

    f1.grid_columnconfigure(0, weight=1)
    f1.grid_rowconfigure(0, weight=1)
    subframe = ttk.Frame(tabs)

    tabs.add(subframe, text='Predefined Models')


    subframe.grid_columnconfigure(0, weight=1)
    subframe.grid_rowconfigure(1, weight=1)
    header_label = ttk.Label(subframe, text="Select a pre-defined model below")
    header_label.grid(column=0,row=0, sticky=(N,W), pady=10)

    # some listbox stuff
    model_names = tuple(predefined_model_map.keys())
    mnames = StringVar(value=model_names)
    predefined_model_listbox = Listbox(subframe, listvariable=mnames, selectmode=SINGLE)
    predefined_model_listbox.grid(column=0, row=1, sticky=(N,S,E,W))
    scroller = ttk.Scrollbar(subframe, orient=VERTICAL, command=predefined_model_listbox.yview)
    scroller.grid(column=1, row=1, sticky=(N,S))
    predefined_model_listbox['yscrollcommand'] = scroller.set


    eqn_rows = []
    #eqn_edit_panel = ttk.Frame(f2)
    eqn_edit_panel = AutoScrollable(f2)
    eqn_edit_panel.grid(column=0, row=0, sticky=(N,S,E,W))

    next_button = ttk.Button(f2,text='Next')
    next_button.grid(column=0, row=1, sticky=(S,E), pady=10)
    next_button.state(['disabled'])

    predefined_model_listbox.bind('<<ListboxSelect>>', display_model)
    dummyframe = ttk.Frame(tabs)
    tabs.add(dummyframe, text='Create a model')

    f1.grid_columnconfigure(0, weight=1)
    f1.grid_rowconfigure(1, weight=1)
    f2.grid_columnconfigure(0, weight=1)
    f2.grid_rowconfigure(0, weight=1)
    mainframe.grid_columnconfigure(0, weight=1)
    mainframe.grid_rowconfigure(0, weight=1)
    for child in f2.winfo_children():
        child.grid_configure(padx=5)

    w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry("%dx%d+0+0" % (int(w/2.0), int(h/2.0)))
    return root


def get_predefined_models():
    suffix = '.model'
    model_files = glob.glob('%s/*%s' % (os.path.dirname(os.path.realpath(__file__)), suffix))
    print model_files
    model_file_map = {}
    for mf in model_files:
        model_name = os.path.basename(mf)[:-len(suffix)]
        model_file_map[model_name] = mf
    return model_file_map

if __name__ == '__main__':
    predefined_model_map = get_predefined_models()
    root = gui_main(predefined_model_map)
    root.mainloop()