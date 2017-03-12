#!/usr/bin/env python

import os
import sys
from machinekit import hal
from machinekit import rtapi as rt
from machinekit import config as c

hardware = None

hardwarelist = {
	'none' : ['setup without hardware', 'none'],
	'mesa-5i20' : ['mesanet 5i20 anything IO FPGA card','hm2_5i20.0'],
	'mesa-5i25-7i76' : ['mesanet 5i25 anything IO FPGA card with 7i76 daughter card','hm2_5i25.0'],
	'bbb-cramps' : ['BeagleBone Black (PRU) with CRAMPS cape', 'hpg'],
	'bbb-bebopr++' : ['BeagleBone Black (PRU) with BeBoPr++ cape', 'hpg'],
	'matilda' : ['Matilda Robot', 'hm2_5i25.0']
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
        rt.init_RTAPI()
        # load 1 siggen component to verify workings
        rt.loadrt('siggen')

        # give name to servothread and create thread
        servothread = "servo_thread"
        rt.newthread('%s' % servothread, 1000000, fp=True)

        if (hardware == 'none'):
                # add functions in between
                hal.addf('siggen.update' % card, servothread)
                # and here        
                pass

        if ((hardware == 'mesa-5i20') or (hardware == 'mesa-5i25-7i76')):
                hal.addf('%s.read' % card, servothread)
                hal.addf('%s.write' % card, servothread)
                # add functions in between here
                hal.addf('siggen.update' % card, servothread)
                # and here
                hal.addf('%s.pet_watchdog' % card, servothread)

        if ((hardware == 'bbb-cramps') or (hardware == 'bbb-bebopr++')) :
                hal.addf('%s.capture-position' % card, servothread)
                hal.addf('bb_gpio.read', servothread)
                # add functions in between
                hal.addf('siggen.update' % card, servothread)
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
                        hal.Pin('%s.stepgen.0%s.position-scale' % (card, i)).set(4000)      
                # Machine power (enable stepper drivers)
                hal.net('emcmot.00.enable', 'bb_gpio.p9.out-23')
                # Tie machine power signal to the CRAMPS LED
                hal.net('emcmot.00.enable', 'bb_gpio.p9.out-25')
                for i in range(0, 4):
                        hal.Pin('%s.stepgen.0%s.position-scale' % (card, i)).set(4000)

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
