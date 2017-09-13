import time
from collections import deque
from transitions import Machine


class Segment(object):

    def __init__(self, start, end, velocity):
        self.startp = start
        self.endp = end
        self.vel = velocity

        
class Point(object):

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        

class MiniMachine(object):
    states = []
    transitions = []
    
    def __init__(self, name, rt, hal):
        self.name = name
        self.queue = deque()
        self.machine = Machine(model=self,
                               states=MiniMachine.states,
                               transitions=MiniMachine.transitions,
                               initial='init',
                               ignore_invalid_triggers=True)
        self.segments = []
        self.setup_segments()
        self.current_segment_index = 0
        self.setup_machine()
        self.rt = rt
        self.hal = hal
        self.x_pos_cmd = None
        self.y_pos_cmd = None
        self.z_pos_cmd = None

        
    def setup_segments(self):
        self.segments.append(Segment(Point(0,0,0), Point(50,50,50), 0.8))
        self.segments.append(Segment(Point(50,50,50), Point(150,150,50), 0.8))
        self.segments.append(Segment(Point(150,150,50), Point(200,0,0), 0.8))
        self.segments.append(Segment(Point(200,0,0), Point(0,0,0), 0.8))
        
        
    def setup_machine(self):
        m = self.machine
        m.add_states(['init', 'calculating', 'moving', 'target_reached', 'set_next_target', 'stopped'])
        m.add_transition('t_start', ['init', 'stopped', 'set_next_target'], 'calculating')
        m.add_transition('t_start_move', 'calculating', 'moving')
        m.add_transition('t_move_complete', 'moving', 'target_reached')
        m.add_transition('t_next_target', 'target_reached', 'set_next_target')
        m.add_transition('t_stop', ['moving', 'target_reached', 'set_next_target', 'calculating'], 'stopped')
        m.on_enter_calculating(self.calculate_move)
        m.on_enter_moving(self.wait_for_motion_finished)
        m.on_enter_set_next_target(self.next_target)
        m.on_enter_target_reached(self.t_next_target)
        m.on_enter_stopped(self.machine_stopped)
        m.on_exit_stopped(self.machine_started)

        
    def clear_queue(self):
        while (len(self.queue) > 0):
            q = self.queue.popleft()

            
    def machine_started(self):
        self.hal.Signal('s_start').set(0)

        
    def machine_stopped(self):
        # reset stop signal
        self.clear_queue()
        self.hal.Signal('s_stop').set(0)


    def set_jplan_pos_cmd(self):
        self.hal.Signal('s_move_acc').set(10.0)
        self.hal.Signal('s_move_vel').set(10.0)

        self.hal.Signal('s_ratio_x').set(self.ratio_x)
        self.hal.Signal('s_ratio_y').set(self.ratio_y)
        self.hal.Signal('s_ratio_z').set(self.ratio_z)
        
        self.hal.Pin('jplan_x.0.pos-cmd').set(self.x_pos_cmd)       
        self.hal.Pin('jplan_y.0.pos-cmd').set(self.y_pos_cmd)
        self.hal.Pin('jplan_z.0.pos-cmd').set(self.z_pos_cmd)

        
    def show_jplan_pos_cmd(self):
        val =  self.hal.Pin('jplan_x.0.pos-cmd').get()
        print('hal value x = %s' % val)
        val =  self.hal.Pin('jplan_y.0.pos-cmd').get()
        print('hal value y = %s' % val)
        val =  self.hal.Pin('jplan_z.0.pos-cmd').get()
        print('hal value z = %s' % val)


    def calculate_move(self):
        print("calculate move")
        print("current_segment_index = %s" % self.current_segment_index)
        self.current_segment = self.segments[self.current_segment_index]
        p_begin = self.current_segment.startp
        p_end = self.current_segment.endp

        # calculate relative distances
        d_x = p_end.x - p_begin.x
        d_y = p_end.y - p_begin.y
        d_z = p_end.z - p_begin.z
        d_tot = (d_x**2 + d_y**2 + d_z**2)**0.5
        print('d_tot = %s' % d_tot)

        # calculate ratio w.r.t. combined move
        self.ratio_x = ((d_x / d_tot)**2)**0.5
        self.ratio_y = ((d_y / d_tot)**2)**0.5
        self.ratio_z = ((d_z / d_tot)**2)**0.5

        self.x_pos_cmd = p_end.x
        self.y_pos_cmd = p_end.y
        self.z_pos_cmd = p_end.z
        
        self.queue.append(self.set_jplan_pos_cmd)
        self.queue.append(self.t_start_move)


    def determine_longest_coord(self, x, y, z):
        d_x = x
        d_y = y
        d_z = z

        # determine dominant coordinate
        if (d_x**2 > d_y**2):
            # x is greater than y
            if (d_x**2 > d_z**2):
                # x is also greater then Z
                current_dominant_axis = 'x'
            else:
                # Z can be equal to x, in that case have z dominant
                current_dominant_axis = 'z'
        else:
            # y is greater than x
            if (d_y**2 > d_z**2):
                # y is also greater than z
                current_dominant_axis = 'y'
            else:
                # Z can be equal to y, in that case have z dominant
                current_dominant_axis = 'z'
        return current_dominant_axis

    
    def next_target(self):
        # decide if we have reached the end of the list and start from the beginning
        if (self.current_segment_index == (len(self.segments)-1)):
            self.current_segment_index = 0
        else:
            self.current_segment_index += 1
        self.queue.append(self.t_start)


    def wait_for_motion_finished(self):
        # we need to determine when motion is finished
        # for this we look at the ratio and jplan being
        # in motion.
        #
        # when ratio is 0, this axis does not move, but because
        # of tiny_dp being < or > than 0, the planner still
        # thinks it is in motion.
        #
        # so we need to have a small workaround
        
        xmotionfinished = ymotionfinished = zmotionfinished = False
        
        if (self.hal.Signal('s_ratio_x').get() == 0):
            xmotionfinished = True
        else:
            if (self.hal.Signal('s_motion_x').get() == 0):
                xmotionfinished = True

        if (self.hal.Signal('s_ratio_y').get() == 0):
            ymotionfinished = True
        else:
            if (self.hal.Signal('s_motion_y').get() == 0):
                ymotionfinished = True   

        if (self.hal.Signal('s_ratio_z').get() == 0):
            zmotionfinished = True
        else:
            if (self.hal.Signal('s_motion_z').get() == 0):
                zmotionfinished = True   
        
        if (xmotionfinished and ymotionfinished and zmotionfinished):
            self.queue.append(self.t_move_complete)
        else:
            self.queue.append(self.wait_for_motion_finished)


    def read_inputs(self):
        if (self.hal.Signal('s_stop').get() == 1):
            self.queue.append(self.t_stop)
        if (self.hal.Signal('s_start').get() == 1):
            self.queue.append(self.t_start)
                            
        
    def process_queue(self):
        print(self.state)
        self.read_inputs()
        if (len(self.queue) > 0):
            q = self.queue.popleft()
            q()
            # autostart   
        if (self.state == 'init'):
            self.hal.Signal('s_jplan_enable').set(1)
            self.t_start()
