import time
from transitions import Machine
from machinekit import hal
from machinekit import rtapi as rt


class MiniMachine(object):
    states = ['init', 'move to cart', 'at cart', 'move to takeout', 'at takeout']
    transitions = [
        { 'trigger': 'start', 'source': 'init', 'dest': 'at takeout' },
        { 'trigger': 'go_cart', 'source': 'at takeout', 'dest': 'move to cart' },
        { 'trigger': 'finish_move_cart', 'source': 'move to cart', 'dest': 'at cart' },
        { 'trigger': 'go_takeout',  'source': 'at cart', 'dest': 'move to takeout' },
        { 'trigger': 'finish_move_takeout', 'source': 'move to takeout', 'dest': 'at takeout'}
]

    
    def __init__(self,name):
        self.name = name
        self.machine = Machine(model=self,
                               states=MiniMachine.states,
                               transitions=MiniMachine.transitions,
                               initial='init')
        self.rt = rt
        #self.rt.init_RTAPI()
        self.switch = hal.Signal('input_switch')
        self.go_jerry = hal.Signal('go_jerry')
        self.jplan_x_active = hal.Pin('jplan_x.0.active')
        self.jplan_y_active = hal.Pin('jplan_y.0.active')
        self.jplan_z_active = hal.Pin('jplan_z.0.active')

        
    def showpins(self):
        #print(self.switch)
        print("switch : %s has value %s" % (self.switch, self.switch.get()))
        print("jplan_x: %s has value %s" % (self.jplan_x_active, self.jplan_x_active.get()))
        print("jplan_y: %s has value %s" % (self.jplan_y_active, self.jplan_y_active.get()))
        print("jplan_z: %s has value %s" % (self.jplan_z_active, self.jplan_z_active.get()))


    def process(self):
        # this loop will run until the hal pin 'go_jerry' is set to False
        posXa=0
        posXb=-50
        posYa=0
        posYb=30
        posYc=62
        posZa=13
        posZb=33
        while self.go_jerry.get() == True:
            if (self.state == 'init'):
                print(self.state)
                while self.switch.get() == False:
                    pass
                # go to next state via transition
                hal.Pin('jplan_z.0.pos-cmd').set(posZa)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move is finished
                self.start()

                # when switch gets set to "cart" the machine will start to move
                # to the cart location
            if (self.state == 'at takeout'):
                # set LED to indicate ready to move
                hal.Signal('emcmot.00.enable').set(1)
                print(self.state)
                while self.switch.get() == False:
                    pass
                self.go_cart()

            if (self.state == 'move to cart'):
                print(self.state)
                # reset LED to indicate that we're moving
                hal.Signal('emcmot.00.enable').set(0)
                # go up a bit
                hal.Pin('jplan_z.0.pos-cmd').set(posZb)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move is finished, go to y a bit
                hal.Pin('jplan_y.0.pos-cmd').set(posYb)
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # move is finished, go to cart x pos (-x)
                hal.Pin('jplan_x.0.pos-cmd').set(posXb)
                time.sleep(0.1)
                while self.jplan_x_active.get() == True:
                    # wait
                    pass
                # move is finished, go to cart y pos (+y)
                hal.Pin('jplan_y.0.pos-cmd').set(posYc)
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # lower z to pick product
                hal.Pin('jplan_z.0.pos-cmd').set(posZa)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                self.finish_move_cart()

                # when switch gets set to "takeout" again the machine will start to move
                # to the takeout location
            if (self.state == 'at cart'):
                print(self.state)
                # set LED to indicate ready to move
                hal.Signal('emcmot.00.enable').set(1)
                while self.switch.get() == False:
                    pass
                self.go_takeout()

            if (self.state == 'move to takeout'):
                # reset LED to indicate we're moving
                hal.Signal('emcmot.00.enable').set(0)
                print(self.state)
                # go up a bit
                hal.Pin('jplan_z.0.pos-cmd').set(posZb)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move is finished, go to y a bit
                hal.Pin('jplan_y.0.pos-cmd').set(posYb)
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # move is finished, go to takeout x pos (x)
                hal.Pin('jplan_x.0.pos-cmd').set(posXa)
                time.sleep(0.1)
                while self.jplan_x_active.get() == True:
                    # wait
                    pass
                # move is finished, go to takout y pos (y)
                hal.Pin('jplan_y.0.pos-cmd').set(posYa)
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # lower z to pick product
                hal.Pin('jplan_z.0.pos-cmd').set(posZa)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                self.finish_move_takeout()



            
# commands to copy paste in python                
# from machineclass import MiniMachine
# m=MiniMachine(name='m')
