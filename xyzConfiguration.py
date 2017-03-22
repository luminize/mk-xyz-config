#!/usr/bin/env python

import os
import sys
from machinekit import hal
from machinekit import rtapi as rt
from machinekit import config as c


hardwarelist = {
	'none' : ['setup without hardware', 'none'],
	'mesa-5i20' : ['mesanet 5i20 anything IO FPGA card','hm2_5i20.0'],
	'mesa-5i25-7i76' : ['mesanet 5i25 anything IO FPGA card with 7i76 daughter card','hm2_5i25.0'],
	'bbb-cramps' : ['BeagleBone Black (PRU) with CRAMPS cape', 'hpg'],
	'bbb-bebopr++' : ['BeagleBone Black (PRU) with BeBoPr++ cape', 'hpg'],
}

def check_hardware(hardwarename):
        if hardwarename in hardwarelist:
                hardware = hardwarename
        else:
                hardware = 'none'

        print("Hardware used : %s" % hardware)
        if not hardware in hardwarelist:
                print("USAGE: %s <hardware>" % sys.argv[0])
                print("Argument \"%s\" is not in hardware list") % hardware
                print("")
                print "{:<15} {:<20}".format('Argument','Description')
                print("----------------------------------------------")
                for argument, description in hardwarelist.iteritems():
                        print "{:<15} {:<20}".format(argument, description[0])
                exit(1)
        else:
                print("card description  : %s, %s") % (hardware, hardwarelist[hardware][0])
                print("hal component name: %s") % (hardwarelist[hardware][1])
        
def setup_hardware(hardware):
        rt.init_RTAPI()
        card = hardwarelist[hardware][1]

        if hardware == 'mesa-5i20':
                print("Loading mesa 5i20")
                rt.loadrt('hostmot2')
                rt.loadrt('hm2_pci', config="firmware=hm2/5i20/SVST8_4.BIT \
								num_pwmgens=3 \
								num_stepgens=4")

        if hardware == 'mesa-5i25-7i76':
                print("Loading mesa 5i25")
                rt.loadrt('hostmot2')
                rt.loadrt('hm2_pci', config="num_pwmgens=0 \
								 num_stepgens=5 \
								 sserial_port_0=00xxxxxx")

        if hardware == 'bbb-cramps':
                print("Loading mesa bbb-cramps")
                os.system('./setup.cramps.sh')
                rt.loadrt('hal_bb_gpio',
			  output_pins='816,822,823,824,825,826,914,923,925',
			  input_pins='807,808,809,810,817,911,913')
                prubin = '%s/%s' % (c.Config().EMC2_RTLIB_DIR, 'xenomai/pru_generic.bin')
                rt.loadrt('hal_pru_generic',
			  pru=0, num_stepgens=5,
			  num_pwmgens=0,
			  prucode=prubin,
			  halname=card)

        if hardware == 'bbb-bebopr++':
                print("Loading mesa bbb-bebopr++")
                os.system('./setup.bridge.sh')
                rt.loadrt('hal_bb_gpio',
			  output_pins='807,924,926',
			  input_pins='808,809,810,814,817,818')
                prubin = '%s/%s' % (c.Config().EMC2_RTLIB_DIR, 'xenomai/pru_generic.bin')
                rt.loadrt('hal_pru_generic',
			  pru=0, num_stepgens=5,
			  num_pwmgens=0,
			  prucode=prubin,
			  halname=card)

def setup_config(hardware):
        # load 1 siggen component to verify workings
        rt.loadrt('siggen')
        card = hardwarelist[hardware][1] 
        # give name to servothread and create thread
        servothread = "st"
        rt.newthread('%s' % servothread, 1000000, fp=True)

        if (hardware == 'none'):
                # add functions in between
                hal.addf('siggen.0.update', servothread)
                setup_planners(servothread)
                # and here        
                pass

        if ((hardware == 'mesa-5i20') or (hardware == 'mesa-5i25-7i76')):
                hal.addf('%s.read' % card, servothread)
                hal.addf('%s.write' % card, servothread)
                # add functions in between here
                hal.addf('siggen.0.update', servothread)
                setup_planners(servothread)
                # and here
                hal.addf('%s.pet_watchdog' % card, servothread)

        if ((hardware == 'bbb-cramps') or (hardware == 'bbb-bebopr++')) :
                hal.addf('%s.capture-position' % card, servothread)
                hal.addf('bb_gpio.read', servothread)
                # add functions in between
                hal.addf('siggen.0.update',  servothread)
                setup_planners(servothread)
		setup_stepper_pid(servothread)
                # and here
                hal.addf('%s.update' % card, servothread)
                hal.addf('bb_gpio.write', servothread)

        if hardware == 'bbb-cramps':
                hal.Pin('%s.stepgen.00.steppin' % card).set(813)
                hal.Pin('%s.stepgen.00.dirpin' % card).set(812)
                hal.Pin('%s.stepgen.01.steppin' % card).set(815)
                hal.Pin('%s.stepgen.01.dirpin' % card).set(814)
                hal.Pin('%s.stepgen.02.steppin' % card).set(819)
                hal.Pin('%s.stepgen.02.dirpin' % card).set(818)
                hal.Pin('%s.stepgen.03.steppin' % card).set(916)
                hal.Pin('%s.stepgen.03.dirpin' % card).set(912)
                hal.Pin('%s.stepgen.04.steppin' % card).set(917)
                hal.Pin('%s.stepgen.04.dirpin' % card).set(918)
                for i in range(0, 4):
                        hal.Pin('%s.stepgen.0%s.position-scale' % (card, i)).set(50.92958)      
                # Machine power (enable stepper drivers)
                hal.net('emcmot.00.enable', 'bb_gpio.p9.out-23')
                # Tie machine power signal to the CRAMPS LED
                hal.net('emcmot.00.enable', 'bb_gpio.p9.out-25')
 
        if hardware == 'bbb-bebopr++':
                hal.Pin('%s.stepgen.00.steppin' % card).set(812)
                hal.Pin('%s.stepgen.00.dirpin' % card).set(811)
                hal.Pin('%s.stepgen.01.steppin' % card).set(816)
                hal.Pin('%s.stepgen.01.dirpin' % card).set(815)
                hal.Pin('%s.stepgen.02.steppin' % card).set(915)
                hal.Pin('%s.stepgen.02.dirpin' % card).set(923)
                hal.Pin('%s.stepgen.03.steppin' % card).set(922)
                hal.Pin('%s.stepgen.03.dirpin' % card).set(921)
                hal.Pin('%s.stepgen.04.steppin' % card).set(918)
                hal.Pin('%s.stepgen.04.dirpin' % card).set(917)
                for i in range(0, 4):
                        hal.Pin('%s.stepgen.0%s.position-scale' % (card, i)).set(4000)
                # Machine power (enable stepper drivers)
                # TODO

        # do some more setup of inputs
        setup_inputs()
        setup_signals(hardware, card)

def start_hal():
        hal.start_threads()

def setup_test_cramps():
	m0_pos = hal.newsig('m0_pos', hal.HAL_FLOAT)
	m0_pos.link('siggen.0.sine')
	m0_pos.link('hpg.stepgen.00.position-cmd')
	hal.Pin('hpg.stepgen.00.maxaccel').set(10)
	hal.Pin('hpg.stepgen.00.maxvel').set(10)
	hal.Pin('hpg.stepgen.00.enable').set(1)
	hal.Pin('siggen.0.frequency').set(0.5)

def setup_stepper_pid(servothread):
	for i in range (0, 3):
		pid = 'pid.stepgen-%i' % i
		pidComp = rt.newinst('pid', pid)
		hal.addf('%s.do-pid-calcs' % pidComp.name, servothread)

def setup_planners(servothread=None):
        rt.loadrt('pbmsgs')
        rt.newinst('jplan', 'jplan_x')
        rt.newinst('jplan', 'jplan_y')
        rt.newinst('jplan', 'jplan_z')
        hal.Pin('jplan_x.0.enable').set(1)
        hal.Pin('jplan_y.0.enable').set(1)
        hal.Pin('jplan_z.0.enable').set(1)
        hal.addf('jplan_x.update', servothread)
        hal.addf('jplan_y.update', servothread)
        hal.addf('jplan_z.update', servothread)
	

def setup_inputs():
	#set led to indicate system ready
	hal.Signal('emcmot.00.enable').set(1)

def setup_signals(hardware=None, card=None):
	# set signals
	speed = 'joint_speed'
	accel = 'joint_accel'
	s_speed = hal.newsig('joint_speed', hal.HAL_FLOAT)
	s_accel = hal.newsig('joint_accel', hal.HAL_FLOAT)
	s_speed.link('jplan_x.0.max-vel')
	s_accel.link('jplan_x.0.max-acc')
	s_speed.link('jplan_y.0.max-vel')
	s_accel.link('jplan_y.0.max-acc')
	s_speed.link('jplan_z.0.max-vel')
	s_accel.link('jplan_z.0.max-acc')
	hal.Signal(speed).set(700)
	hal.Signal(accel).set(1200)
	# link input switch
	s_input_switch_takeout = hal.newsig('input_switch_takeout', hal.HAL_BIT)
	s_input_switch_cart = hal.newsig('input_switch_cart', hal.HAL_BIT)
	s_go_jerry = hal.newsig('go_jerry', hal.HAL_BIT)
	s_go_jerry.set(1)
	# link stepgens to jplan outputs
	s_xpos = hal.newsig('xpos', hal.HAL_FLOAT)
	s_ypos = hal.newsig('ypos', hal.HAL_FLOAT)
	s_zpos = hal.newsig('zpos', hal.HAL_FLOAT)
	s_xpos.link('jplan_x.0.curr-pos')
	s_ypos.link('jplan_y.0.curr-pos')
	s_zpos.link('jplan_z.0.curr-pos')
        if hardware == 'bbb-cramps':
		s_xpos.link('pid.stepgen-0.command')
		s_ypos.link('pid.stepgen-1.command')
		s_zpos.link('pid.stepgen-2.command')
		s_speed = hal.Signal('joint_speed')
		s_accel = hal.Signal('joint_accel')
		for i in range (0, 3):
			s_speed.link('%s.stepgen.0%i.maxvel' % (card, i))
			s_accel.link('%s.stepgen.0%i.maxaccel' % (card, i))
			hal.Pin('%s.stepgen.0%i.enable' % (card, i)).set(True)
			hal.Pin('%s.stepgen.0%i.control-type' % (card, i)).set(True)
			hal.Pin('pid.stepgen-%i.Pgain' % i).set(90)
			hal.Pin('pid.stepgen-%i.Igain' % i).set(0)
			hal.Pin('pid.stepgen-%i.Dgain' % i).set(0)
			hal.Pin('pid.stepgen-%i.bias' % i).set(0)
			hal.Pin('pid.stepgen-%i.FF0' % i).set(0)
			hal.Pin('pid.stepgen-%i.FF1' % i).set(1)
			hal.Pin('pid.stepgen-%i.FF2' % i).set(0.00005)
			hal.Pin('pid.stepgen-%i.deadband' % i).set(0)
			hal.Pin('pid.stepgen-%i.maxoutput' % i).set(0)
			hal.Pin('pid.stepgen-%i.maxerror' % i).set(0.0005)
			hal.Pin('pid.stepgen-%i.error-previous-target' % i).set(True)
			hal.Pin('pid.stepgen-%i.enable' % i).set(1)
			# PID signals
			# PID output to Stepgen velocity command
			posCmd = hal.newsig('motor-%i-vel-cmd' % i, hal.HAL_FLOAT)
			posCmd.link('pid.stepgen-%i.output' % i)
			posCmd.link('%s.stepgen.0%s.velocity-cmd' % (card, i))
			# Stepgen position feedback to PID feedback
			posFb = hal.newsig('motor-%i-pos-fb' % i, hal.HAL_FLOAT)
			posFb.link('pid.stepgen-%i.feedback' % i)
			posFb.link('%s.stepgen.0%s.position-fb' % (card, i))

		s_input_switch_takeout.link('bb_gpio.p8.in-07')
		s_input_switch_cart.link('bb_gpio.p8.in-08')




		
