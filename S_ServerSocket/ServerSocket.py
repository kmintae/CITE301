# Referenced from https://soooprmx.com/archives/8737

# Assume that Server IPs are fixed
# Assume that Camera is connected to Server
# Assume that we can correspond the robot_arm in the images and the robot_arm sockets (Important)

# For Multi-Threading & Usage of Synchronization (Semaphore, Lock)
import threading
import socket
import yaml
import time

# Configurations
config = yaml.load(open("./Config.yaml", 'r'), Loader=yaml.FullLoader)

# Connection Handler
def connection_handler(conn, addr, tm, im, im_pos, robot_status):
    # Server Flow 1: First line is the Robot Arm Information info
    recv_info = conn.recv(config["MAX_BUF_SIZE"]).decode().split(' ')
    robot_arm_num = int(recv_info[0])
    robot_arm_color = [float(recv_info[1]), float(recv_info[2]), float(recv_info[3])]
    robot_arm_init_pos = [float(recv_info[4]), float(recv_info[5])]

    # Server Flow 2: Actions for Robo_arms
    robot_status.action_conn_init(conn, robot_arm_num, robot_arm_color, robot_arm_init_pos, tm, im, im_pos)
    robot_status.action_conn(robot_arm_num, tm, im, im_pos)

def run_server(tm, im, im_pos, gm, robot_status):
    serverSock = socket.socket()
    serverSock.bind((config["SERVER_IP_ADDR"], config["SERVER_PORT"]))

    # Setting Timeout as 5 seconds
    # serverSock.settimeout(5)
    serverSock.settimeout(None)

    # Server Routine
    while True:
        serverSock.listen(config["MAX_ROBOT_CONNECTED"])
        conn, addr = serverSock.accept()
        if (robot_status.isTasksDone() == False) :
            t = threading.Thread(target=connection_handler, args=(conn, addr, tm, im, im_pos, robot_status))
            t.start()

            # Adding Current Thread to grandchild thread list.
            gm.t_grandchild_list.append(t)
