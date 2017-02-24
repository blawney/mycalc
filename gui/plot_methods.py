__author__ = 'brian'

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg
import seaborn as sns
sns.set_style('darkgrid')


def plot_evolution(t,y, current_h, current_w, title='', species=None):
    dpi = 100 # a reasonable value

    # want to make the width half of the total
    plot_height = 0.7*(current_h/float(dpi))
    plot_width = 0.5*(current_w/float(dpi))
    fig = Figure(figsize=(plot_width, plot_height), dpi=dpi)
    ax = fig.add_subplot(111)
    ax.plot(t, y)
    ax.set_title(title)
    ax.set_ylabel('[%s] (nM)' % species if species else 'Concentration (nM)')
    ax.set_xlabel('Time (s)')
    fig.tight_layout()
    return fig


class CustomToolbar(NavigationToolbar2TkAgg):
    def __init__(self,canvas_,parent_):
        self.toolitems = (
            ('Home', 'Return to original view', 'home', 'home'),
            #('Back', 'consectetuer adipiscing elit', 'back', 'back'),
            #('Forward', 'sed diam nonummy nibh euismod', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan the plot', 'move', 'pan'),
            ('Zoom', 'Zoom in', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            #('Subplots', 'putamus parum claram', 'subplots', 'configure_subplots'),
            ('Save', 'Save figure', 'filesave', 'save_figure'),
            )
        NavigationToolbar2TkAgg.__init__(self,canvas_,parent_)

