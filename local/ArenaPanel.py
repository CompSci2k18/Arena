from tkinter import *

"""/*
    Class: ArenaPanel
    An abstract super class for <LogPanel> and <GameServerPanel>, providing
    an interface that must be implemented, along with the <_popup> method
*/"""
class ArenaPanel(LabelFrame):
    # Group: Constructors

    """/*
        Constructor: __init__
        Create the <Panel> and initialise any instance variables it may have

        Parameters:
            obj master - The parent of this panel
            string title - The title to be displayed on the panel
            int width - The width of the panel in pixels
            int height - The height of the panel in pixels
            array *args - An array of extra arguments to be passed in
            dict **kwargs - A dict of extra keyword arguments to be passed in
    */"""
    def __init__(self, master, title, width, height, *args, **kwargs):
        super(ArenaPanel, self).__init__(master, text=title,
            width=width, height=height)
        # Group: Variables

        # obj: _master
        # The parent of the window
        self._master = master
        self._initialiseVariables(*args, **kwargs)
        self._initialiseChildren()

    # Group: Private Methods

    """/*
        Function: _initialiseVariables
        Initialise all instance variables to be used in this panel

        Parameters:
            array *args - An array of extra arguments needed
            dict **kwargs - A dict of extra keyword arguments needed
    */"""
    def _initialiseVariables(self, *args, **kwargs):
        raise NotImplemented("This method must be overrided")

    """/*
        Function: _initialiseChildren
        Create any children of this panel and add them into the panel
    */"""
    def _initialiseChildren(self):
        raise NotImplemented("This method must be overrided")

    """/*
        Function: _popup
        Allows any subclass to create a popup for displaying errors

        Parameters:
            string title - The title of the popup
            string message - The error message to be displayed
    */"""
    def _popup(self, title, message):
        popup = Toplevel(self._master)
        popup.title(title)

        Label(popup, text=message).pack(fill=BOTH, expand=1)

        Button(popup, command=popup.destroy, text="Close").pack(fill=BOTH,
            expand=1)

    # Group: Public Methods

    """/*
        Function: close
        Handled the closing of the panel, including checking if the panel can
        be closed, and closing any service the panel handles
    */"""
    def close(self):
        raise NotImplemented("This method must be overrided")

