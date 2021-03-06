import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from py4j.java_gateway import (JavaGateway, GatewayParameters)

import random
from py4j.tests.java_gateway_test import gateway



# logging
logger = logging.getLogger(__name__)

def refer(val):
    temp = oct(val)[2:].zfill(4)
    result = [0] * 4
    for i, c in enumerate(temp):
        result[i] = int(c)
    return result




def transfer2JavaDblAry(gateway, pyArray, size):
    dblAry = gateway.new_array(gateway.jvm.double, size)
    i = 0
    for x in pyArray:
        dblAry[i] = float(x)
        i = i + 1
    return dblAry


#
# function to transfer data from Java_Collections array to python Numpy array
#

def transfer1DJavaArray2NumpyArray(ary) :
    size = len(ary)
    np_ary = np.zeros(size)
    for i in range(size):
        np_ary[i] = ary[i]
    return np_ary

def transfer2DJavaArray2NumpyArray(ary) :
    size1 = len(ary)
    size2 = len(ary[0])
    np_ary = np.zeros((size1,size2))
    for i in range(size1):
        for j in range(size2):
            np_ary[i,j] = ary[i][j]

    return np_ary

# A power system dynamic simulation environment implementation by extending the Gym Env class defined in core.py, which is available in
# https://github.com/openai/gym/blob/master/gym/core.py

class PowerDynSimEnv(gym.Env):
    metadata = {

    }

    _case_files =""
    _dyn_sim_config_file =""
    _rl_config_file =""
    step_time = 0.1
    action_type = 'discrete'

    # define InterPSS dynamic simulation service
    #ipss_app = None


    def __init__(self,case_files, dyn_sim_config_file,rl_config_file , server_port_num = 25333):

        global gateway
        gateway = JavaGateway(gateway_parameters=GatewayParameters(port = server_port_num,auto_convert=True))
        global ipss_app
        ipss_app = gateway.entry_point

        from gym import spaces

        _case_files = case_files
        _dyn_sim_config_file = dyn_sim_config_file
        _rl_config_file = rl_config_file

        #initialize the power system simulation service

        #  {observation_history_length,observation_space_dim, action_location_num, action_level_num};
        dim_ary= ipss_app.initStudyCase(case_files,dyn_sim_config_file,rl_config_file)

        print (dim_ary[0], dim_ary[1],dim_ary[2], dim_ary[3])

        observation_history_length = dim_ary[0]
        observation_space_dim =  dim_ary[1]

        action_location_num =  dim_ary[2]
        action_level_num = dim_ary[3]
        num = action_level_num ** action_location_num
        self.action_space = spaces.Discrete(num)


        #define action and observation spaces
        """
        if(action_location_num == 1):
            self.action_space      = spaces.Discrete(action_level_num) # Discrete, 1-D dimension
        else:
            #print('N-D dimension Discrete Action space is not supported it yet...TODO')
            # the following is based on the latest  gym dev version
            # action_def_vector   = np.ones(action_location_num, dtype=np.int32)*action_level_num

            # for gym version 0.10.4, it is parametrized by passing an array of arrays containing [min, max] for each discrete action space
            # for exmaple,  MultiDiscrete([ [0,4], [0,1], [0,1] ])

            action_def_vector = np.ones((action_location_num,2),dtype=np.int32)
            action_def_vector[:,1] = action_level_num -1
            aa = np.asarray(action_def_vector, dtype=np.int32)

            self.action_space   = spaces.MultiDiscrete(action_def_vector) # Discrete, N-D dimension
        """


        self.observation_space = spaces.Box(-999,999,shape=(observation_history_length * observation_space_dim,)) # Continuous

        self._seed()

        #TOOD get the initial states
        self.state = None

        self.steps_beyond_done = None
        self.restart_simulation = True

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _step(self, action):

        assert self.action_space.contains(action), "%r (%s) invalid"%(action, type(action))

        # print(action)
#         actionMapped = refer(action)
#         print(actionMapped)
        #actionPyAry = np.asarray(actionMapped,dtype = np.float64)
        actionPyAry = np.asarray(action,dtype = np.float64)

        # print(actionPyAry, 'len = ', actionPyAry.size)

        # np array size = number of elements in the array
        actionJavaAry = gateway.new_array(gateway.jvm.double, actionPyAry.size)

        if(actionPyAry.size ==1):
            actionJavaAry[0] = float(action)
        else:
            i = 0
            for x in actionPyAry:
                actionJavaAry[i] = x
                i = i + 1

        ipss_app.nextStepDynSim(self.step_time,actionJavaAry, self.action_type)

        # retrieve the state from InterPSS simulation service

        # observations is a Java_Collections array
        observations = ipss_app.getEnvironmentObversations();

        # convert it from Java_collections array to native Python array
        self.state = transfer2DJavaArray2NumpyArray(observations)

        #check the states to see whether it go beyond the limits
        done = ipss_app.isSimulationDone();


        if not done:
            reward = ipss_app.getReward()

        elif self.steps_beyond_done is None:
            self.steps_beyond_done = 0
            reward = ipss_app.getReward() # even it is done, ipss_app would calculate and return a corresponding reward
        else:
            if self.steps_beyond_done == 0:
                logger.warning("You are calling 'step()' even though this environment has already returned done = True. You should always call 'reset()' once you receive 'done = True' -- any further steps are undefined behavior.")
            self.steps_beyond_done += 1

            reward = 0.0

        return np.array(self.state).ravel(), reward, done, {}

    def _reset(self):

        total_bus_num = ipss_app.getTotalBusNum()

        # reset need to randomize the operation state and fault location, and fault time


        case_Idx = np.random.randint(0,10) # an integer, in the range of [0, 9]
        #fault_bus_idx = np.random.randint(0, total_bus_num) # an integer, in the range of [0, total_bus_num-1]
        #fault_bus_idx = np.random.randint(8, 9) # an integer, in the range of [0, total_bus_num-1]
        fault_bus_idx = 8 # an integer, in the range of [0, total_bus_num-1]
        #fault_start_time =random.uniform(0.99, 1.01) # a double number, in the range of [0.2, 1]
        fault_start_time = 1.0 # a double number, in the range of [0.2, 1]
        #0.8 1.0
        fault_duation_time = random.uniform(0.581, 0.585)  # a double number, in the range of [0.08, 0.4]
        #fault_duation_time = 0.585  # a double number, in the range of [0.08, 0.4]
        # 0.4-0.588

        # self.np_random


        # reset initial state to states of time = 0, non-fault

        ipss_app.Reset(case_Idx,fault_bus_idx,fault_start_time,fault_duation_time)

        #self.state = None

        # observations is a Java_Collections array
        observations = ipss_app.getEnvironmentObversations();

        # convert it from Java_collections array to native Python array
        self.state = transfer2DJavaArray2NumpyArray(observations)

        #print(self.state)

        self.steps_beyond_done = None
        self.restart_simulation = True

        return np.array(self.state).ravel(),fault_start_time,fault_duation_time

    # init the system with a specific state and fault
    def _validate(self, case_Idx, fault_bus_idx, fault_start_time, fault_duation_time):

        total_bus_num = ipss_app.getTotalBusNum()

        ipss_app.Reset(case_Idx,fault_bus_idx,fault_start_time,fault_duation_time)

        # observations is a Java_Collections array
        observations = ipss_app.getEnvironmentObversations();

        # convert it from Java_collections array to native Python array
        self.state = transfer2DJavaArray2NumpyArray(observations)

        self.steps_beyond_done = None
        self.restart_simulation = True

        return np.array(self.state).ravel()

    # def _render(self, mode='human', close=False):
