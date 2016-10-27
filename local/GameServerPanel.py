from ._addons import PanelException
from .ArenaPanel import ArenaPanel
from socket import gethostname, gethostbyname
from threading import Thread
from tkinter import *

class GameServerPanel(ArenaPanel):

    def _initialiseVariables(self, *args, **kwargs):
        self._host = gethostbyname(gethostname())

        default_port = 44444
        self._port = IntVar()
        self._port.set(default_port)

        self._status = StringVar()
        self._status.set("Server Stopped")

        self._buttonLabel = StringVar()
        self._buttonLabel.set("Start")

        self._broadcastStatus = StringVar()
        self._broadcastStatus.set("Not Broadcasting")

        self._broadcastButtonLabel = StringVar()
        self._broadcastButtonLabel.set("Start Broadcasting")

        self._running = False

        self._server = None

        self._thread = None

        self._logMethod = kwargs.get('logMethod', print)
        # Have an external handler for the running of this Panel, to handle
        # exceptions
        self._runHandler = kwargs.get('runHandler', self.toggle)

        self._broadcastHandler = kwargs.get('broadcastHandler', self.broadcast)

    def _initialiseChildren(self):
        # Host Panel - Label and a DISABLED Entry
        hostPanel = Frame(self)
        Label(hostPanel, text="Host Address").pack(side=LEFT, fill=X, expand=1)
        hostEntry = Entry(hostPanel)
        hostEntry.insert(0, self._host)
        hostEntry.config(state=DISABLED)
        hostEntry.pack(side=LEFT, fill=X, expand=1)
        hostPanel.pack(fill=BOTH, expand=1)

        # Port Panel - Label and an ENABLED Entry
        portPanel = Frame(self)
        Label(portPanel, text="Port Number").pack(side=LEFT, fill=X, expand=1)
        portEntry = Entry(portPanel, textvariable=self._port)
        portEntry.pack(side=LEFT, fill=X, expand=1)
        portPanel.pack(fill=BOTH, expand=1)

        # Status Panel - Label and a Button to run this server
        runPanel = Frame(self)
        self._statusLabel = Label(runPanel, textvariable=self._status,
            foreground="red")
        self._statusLabel.pack(side=LEFT, fill=BOTH, expand=1)
        runButton = Button(runPanel, textvariable=self._buttonLabel,
            command=self._runHandler)
        runButton.pack(side=LEFT, fill=X, expand=1)
        runPanel.pack(fill=BOTH, expand=1)

        # Broadcast Panel - Second status panel for control over broadcasting
        broadcastPanel = Frame(self)
        self._broadcastStatusLabel = Label(broadcastPanel,
            textvariable=self._broadcastStatus, foreground="red")
        self._broadcastStatusLabel.pack(side=LEFT, fill=BOTH, expand=1)
        broadcastButton = Button(broadcastPanel,
            textvariable=self._broadcastButtonLabel,
            command=self._broadcastHandler)

    def toggle(self):
        if not self._running:
            # Run the server
            port_num = self._port.get()
            try:
                self._server = ArenaServer(self._host, port_num,
                    self._logMethod)
            except Exception as e:
                raise PanelException("Error", str(e))
            else:
                # No exceptions
                # Create the thread
                self._thread = Thread(target=self._server.listen)
                self._thread.start()
                # Update the labels
                self._status.set("Server Running")
                self._buttonLabel.set("Stop")
                self._statusLabel.config(foreground="green")
                # Update the switch
                self._running = True
        else:
            # Try and close the server
            if self.canClose():
                # Close the server
                Thread(target=self._server.close).start()
                self._server = None
                self._thread = None
                # Update the labels
                self._status.set("Server Stopped")
                self._buttonLabel.set("Start")
                self._statusLabel.config(foreground="red")
                # Update the switch
                self._running = False
            else:
                raise PanelException("Cannot Close Server",
                    "The game has started, so the server cannot be closed")

    def canClose(self):
        return self._server == None or not self._server.inGame()
