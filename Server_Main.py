# Referenced by ...
# https://docs.python.org/3/library/signal.html
# https://python.bakyeono.net/chapter-3-4.html
# https://docs.python.org/3/library/socket.html#socket.timeout
# https://docs.python.org/ko/3.8/library/os.html#os.WNOHANG
import threading
import signal
import os
import sys
from PyQt5.QtWidgets import QApplication

import S_ServerSocket.ServerSocket as ServerSocket
from S_CameraVision.ImageManager import ImageManager
from S_CameraVision.ImageDetection import saveImages
from S_ServerSocket.SharedRoboList import SharedRoboList
from S_TaskManagement.TaskManager import TaskManager
from S_GUI.GUIManager import MainWindow

# Task Manager
tm = None
# Image Manager
im = None
# GUI Manager
gm = None
# Shared Robot Information List
robot_status = None

# Thread t
t_child_saveImages = None
t_child_runServer = None
# Child Thread Lists
t_grandchild_list = None

## According to the python docs,
## Python signal handlers are always executed in the main Python thread,
## even if the signal was received in another thread.
def sigchld_handler(sig, frame):
    global t_child_saveImages, t_child_runServer, t_grandchild_list
    dead_thread_pid = os.waitpid(-1, 0)

    # Comparison of PIDs
    for t_grandchild in t_grandchild_list :
        if (t_grandchild.ident == dead_thread_pid) :
            t_grandchild_list.remove(t_grandchild)
            return

    # Comparison of PIDs
    if (t_child_saveImages.ident == dead_thread_pid) :
        t_child_saveImages = None
    elif (t_child_runServer.ident == dead_thread_pid) :
        t_child_runServer = None

if __name__ == "__main__" :
    signal.signal(signal.SIGCHLD, sigchld_handler)

    # Initiation of ImageManager, TaskManager, and SharedRoboList
    im = ImageManager()

    tm = TaskManager()
    robot_status = SharedRoboList()

    # Initiation of GUI & GUI Manager
    app = QApplication(sys.argv)

    gm = MainWindow()
    gm.show()

    gm.gui_extra_initiation(robot_status)

    # Initiation of t_grandchild
    t_grandchild_list = []

    # Execution of saveImages() by Multi-threading
    t = threading.Thread(target=saveImages, args=(im, ))
    t.start()
    t_child_saveImages = t

    # Execution of Server Loop by Multi-threading
    t = threading.Thread(target=ServerSocket.run_server, args=(tm, im, gm, robot_status, t_grandchild_list))
    t.start()
    t_child_runServer = t

    # Execution of GUIs
    app.exec_()

    # Afterwards Process
    signal.pthread_kill(t_child_saveImages.ident, signal.SIGKILL)
    for (t_grandchild, thread_type) in t_grandchild_list:
        signal.pthread_kill(t_grandchild.ident, signal.SIGKILL)
    signal.pthread_kill(t_child_runServer.ident, signal.SIGKILL)
    sys.exit(0)