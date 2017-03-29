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
        self.switch_takeout = hal.Signal('input_switch_takeout')
        self.switch_cart = hal.Signal('input_switch_cart')
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
        # create signals for locations
        hal.newsig('posXa', hal.HAL_FLOAT)
        hal.Signal('posXa').set(0)
        hal.newsig('posXb', hal.HAL_FLOAT)
        hal.Signal('posXb').set(-59)
        hal.newsig('posYa', hal.HAL_FLOAT)
        hal.Signal('posYa').set(0)
        hal.newsig('posYb', hal.HAL_FLOAT)
        hal.Signal('posYb').set(40)
        hal.newsig('posYc', hal.HAL_FLOAT)
        hal.Signal('posYc').set(63.5)
        hal.newsig('posZa', hal.HAL_FLOAT)
        hal.Signal('posZa').set(14)
        hal.newsig('posZb', hal.HAL_FLOAT)
        hal.Signal('posZb').set(33)

        while self.go_jerry.get() == True:
            if (self.state == 'init'):
                print(self.state)
                while self.switch_takeout.get() == False:
                    pass
                # go to next state via transition
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZa').get())
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
                time.sleep(0.1)
                print(self.state)
                # wait for led to be on
                while hal.Signal('emcmot.00.enable').get() == 0:
                    pass
                while self.switch_takeout.get() == True:
                    pass
                self.go_cart()

            if (self.state == 'move to cart'):
                print(self.state)
                # reset LED to indicate that we're moving
                hal.Signal('emcmot.00.enable').set(0)
                # go up a bit
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZb').get())
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move is finished, go to y a bit
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYb').get())
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # move is finished, go to cart x pos (-x)
                hal.Pin('jplan_x.0.pos-cmd').set(hal.Signal('posXb').get())
                time.sleep(0.1)
                while self.jplan_x_active.get() == True:
                    # wait
                    pass
                # move is finished, go to cart y pos (+y)
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYc').get())
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # lower z to pick product
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZa').get())
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
                time.sleep(0.1)
                # wait for led to be on
                while hal.Signal('emcmot.00.enable').get() == 0:
                    pass
                while self.switch_takeout.get() == False:
                    pass
                self.go_takeout()

            if (self.state == 'move to takeout'):
                # reset LED to indicate we're moving
                hal.Signal('emcmot.00.enable').set(0)
                print(self.state)
                # go up a bit
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZb').get())
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move is finished, go to y a bit
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYb').get())
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # move is finished, go to takeout x pos (x)
                hal.Pin('jplan_x.0.pos-cmd').set(hal.Signal('posXa').get())
                time.sleep(0.1)
                while self.jplan_x_active.get() == True:
                    # wait
                    pass
                # move is finished, go to takout y pos (y)
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYa').get())
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                # lower z to release product
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZa').get())
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                # move backward to scrape off product on back
                jointspeed_old = hal.Signal('joint_speed').get()
                hal.Signal('joint_speed').set(50)
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYa').get() + 20)
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass
                hal.Signal('joint_speed').set(jointspeed_old)
                hal.Pin('jplan_z.0.pos-cmd').set(hal.Signal('posZa').get() - 8)
                time.sleep(0.1)
                while self.jplan_z_active.get() == True:
                    # wait
                    pass
                hal.Pin('jplan_y.0.pos-cmd').set(hal.Signal('posYa').get())
                time.sleep(0.1)
                while self.jplan_y_active.get() == True:
                    # wait
                    pass

                self.finish_move_takeout()



            
# commands to copy paste in python                
# from machineclass import MiniMachine
# m=MiniMachine(name='m')
