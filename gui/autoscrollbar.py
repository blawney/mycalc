# Adapted from here: http://effbot.org/zone/tkinter-autoscrollbar.htm

from Tkinter import *

class AutoScrollbar(Scrollbar):
    '''
    A scrollbar that hides itself if it's not needed. 
    Only works if you use the grid geometry manager.
    '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)

    def pack(self, *args, **kwargs):
        raise TclError('Cannot use pack with this widget.')

    def place(self, *args, **kwargs):
        raise TclError('Cannot use pack with this widget.')


class AutoScrollable(Frame):
    def __init__(self, top, *args, **kwargs):
        Frame.__init__(self, top, *args, **kwargs)

        hscrollbar = AutoScrollbar(self, orient = HORIZONTAL)
        hscrollbar.grid(row = 1, column = 0, sticky = 'ew')

        vscrollbar = AutoScrollbar(self, orient = VERTICAL)
        vscrollbar.grid(row = 0, column = 1, sticky = 'ns')

        self.canvas = Canvas(self, xscrollcommand = hscrollbar.set,
                              yscrollcommand = vscrollbar.set)
        self.canvas.grid(row = 0, column = 0, sticky = 'nsew')

        hscrollbar.config(command = self.canvas.xview)
        vscrollbar.config(command = self.canvas.yview)

        # Make the canvas expandable
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        # Create the canvas contents
        self.frame = Frame(self.canvas)
        self.frame.rowconfigure(1, weight = 1)
        self.frame.columnconfigure(1, weight = 1)

        self.canvas.create_window(0, 0, window = self.frame, anchor = 'nw')
        self.canvas.config(scrollregion = self.canvas.bbox('all'))

        def frame_changed(event):
            self.frame.update_idletasks()
            self.canvas.config(scrollregion = self.canvas.bbox('all'))

        self.frame.bind('<Configure>', frame_changed)
        self.canvas.bind('<Enter>', self._bound_to_mousewheel)
        self.canvas.bind('<Leave>', self._unbound_to_mousewheel)

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)   
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)   
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)  
 
    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>") 
        self.canvas.unbind_all("<Button-5>")  

    def _on_mousewheel(self, event):
        direction =-1 
        if event.num ==5 or event.delta < 0:
            direction = 1
        self.canvas.yview_scroll(direction, "units")

