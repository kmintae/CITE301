# Referenced from https://wayhome25.github.io/python/2017/02/26/py-14-list/
# Referenced from https://codechacha.com/ko/how-to-import-python-files/

# For Multi-Threading & Usage of Synchronization (Semaphore, Lock)
import threading
import yaml

# Configurations
config = yaml.load(open("./Config.yaml", 'r'), Loader=yaml.FullLoader)

# --- Import S_RoboticArmControl/RobotControl.py ---
import os
import sys
path_for_roboAC = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
path_for_roboAC = os.path.join(path_for_roboAC, 'S_RoboticArmControl')
sys.path.append(path_for_roboAC)

from RobotControl import Robot
# --- Import S_RoboticArmControl/RobotControl.py ---


# --- Import S_TaskManagement/TaskManager  ---
path_for_tm = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
path_for_tm = os.path.join(path_for_tm, 'S_TaskManagement')
sys.path.append(path_for_tm)

from TaskManager import TaskManager
# --- Import S_TaskManagement/TaskManager  ---


# --- Import S_CameraVision/ImageDetection.py ---
path_for_CV = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
path_for_CV = os.path.join(path_for_CV, 'S_CameraVision')
sys.path.append(path_for_CV)

from ImageDetection import updatePosition
# --- Import S_CameraVision/ImageDetection.py ---


class SharedRoboList :
    def __init__ (self) :
        self.armList_conn = []
        # Construction of roboInfoList
        self.roboInfoList = []
        self.roboTerminated = []

        for i in range(config["MAX_ROBOT_CONNECTED"]) :
            self.armList_conn.append(None)
            self.roboInfoList.append(None)
            self.roboTerminated.append(False)

        # Lock for Information List
        self.lock = threading.Lock()

        # Whole Process State Information
        self.running = False

        # Monitor for Running State
        self.monitor = threading.Condition()

    def action_conn_init(self, conn, robot_arm_num, robot_arm_color, robot_arm_init_pos, tm, im):
        self.lock.acquire()
        # Adding current connection to the list.
        self.armList_conn[robot_arm_num] = conn
        self.roboInfoList[robot_arm_num] = Robot()
        self.roboInfoList[robot_arm_num].setColorRGB(robot_arm_color)
        self.roboInfoList[robot_arm_num].setInitPos(robot_arm_init_pos)

        # Reset Current Position & Direction Information
        updatePosition(self.roboInfoList[robot_arm_num], im)

        # Push Initial Instructions based on Infos (Move to Initial Position)
        tm.pushInitialInstruction(self.roboInfoList[robot_arm_num])

        self.lock.release()

    def action_conn(self, robot_arm_num, tm, im):
        # For Iterating while loop, get the instructions from image
        while True:
            # WAIT until user starts
            # Checking Whole Process State (Run / Stop)
            self.monitor.acquire()
            while (self.running == False) :
                self.monitor.wait()
            self.monitor.release()

            # Calculate the next instructions by Task Manager
            ## For CITD III, We need an robo_arm_num infos to seperate two trajectories.
            ## In CITD IV, We will try to generalize for more than three trajectories.
            next_instruction = tm.fetchNextTask(self.roboInfoList[robot_arm_num])

            # If the robot is waiting for the other robot to finish their task,
            # then this robot would be waiting for a new block by a condition variable in BrickListManager.
            # That means if next_instruction is None, which means no instruction left in queue
            # infers that all tasks are done.
            if (next_instruction == "") :
                self.lock.acquire()
                self.roboTerminated[robot_arm_num] = True

                # Exit Condition - Reset infos
                self.armList_conn[robot_arm_num] = None
                self.roboInfoList[robot_arm_num] = None

                self.lock.release()

            self.armList_conn[robot_arm_num].sendall(next_instruction.encode())
            end_msg = self.armList_conn[robot_arm_num].recv(config["MAX_BUF_SIZE"]).decode()

            updatePosition(self.roboInfoList[robot_arm_num], im)

    def isRunning(self, robot_num_new):
        self.lock.acquire()
        isRun = (not (self.armList_conn[robot_num_new] == None))
        self.lock.release()
        return isRun

    def isTasksDone(self):
        self.lock.acquire()
        for i in range (config["MAX_ROBOT_CONNECTED"]) :
            if (self.roboTerminated[i] == False) :
                self.lock.release()
                return False
        self.lock.release()
        return True

    def isProcessRunning (self) :
        self.monitor.acquire()
        isRunning = self.running
        self.monitor.release()
        return isRunning

    def setProcessRunning (self, isRunning):
        self.monitor.acquire()
        if (isRunning == True and self.running == False): # False -> True
            self.running = isRunning
            self.monitor.notifyAll() # Child Threads ALL Wake Up!
        else :
            self.running = isRunning
        self.monitor.release()