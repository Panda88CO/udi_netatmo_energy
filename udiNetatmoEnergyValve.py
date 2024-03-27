#!/usr/bin/env python3

"""
Polyglot v3 node server
Copyright (C) 2023 Universal Devices

MIT License
"""


import time
import traceback
import re

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)


#from nodes.controller import Controller
#from udi_interface import logging, Custom, Interface
'''
id = 'indoor'

drivers = [
            {'driver' : 'CLITEMP', 'value': 0,  'uom':4}, 
            {'driver' : 'CO2LVL', 'value': 0,  'uom':54}, 
            {'driver' : 'CLIHUM', 'value': 0,  'uom':22}, 
            {'driver' : 'GV3', 'value': 0,  'uom':4}, 
            {'driver' : 'GV4', 'value': 0,  'uom':4}, 
            {'driver' : 'GV5', 'value': 0,  'uom':25}, 
            {'driver' : 'GV6', 'value': 0,  'uom':44}, 
            {'driver' : 'GV7', 'value': 0,  'uom':51}, 
            {'driver' : 'GV8', 'value': 99,  'uom':25},          
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]
'''

class udiNetatmoEnergyValve(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY,  node_queue, wait_for_node_done, battery2ISY

    def __init__(self, polyglot, primary, address, name, myNetatmo, home,  valve_id):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot
        self.myNetatmo= myNetatmo
        self.valve_id = valve_id
        self.home_id = home['id']
        self._home = home
        self.primary = primary
        self.address = address
        self.name = name        
        self.n_queue = []
        self.id = 'room'
        self.drivers = [
            {'driver' : 'BATLVL', 'value': 99,  'uom':25}, 
            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 99,  'uom':25},       
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]

        self.node_ready = False
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(address)
        logging.info('Start {} valve Node'.format(self.name))  
        time.sleep(1)
        self.n_queue = []  
        self.nodeDefineDone = True
        self.node_ready = True

    
    


    def start(self):
        logging.debug('Executing udiNetatmoEnergyRoom start')
        self.updateISYdrivers()        


   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        
        #data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Valve module data:')
        if self.node is not None:
            if self.myNetatmo.get_online(self.module):
                self.node.setDriver('ST', self.state2ISY(self.myNetatmo.get_valve_online(self.home_id, self.valve_id)))
                self.node.setDriver('BATLVL', self.myNetatmo.get_valve_bat_level(self.home_id, self.valve_id), True, True, 0)
                self.node.setDriver('GV0', self.battery2ISY(self.myNetatmo.get_valve_bat_state(self.home_id, self.valve_id)))
                self.node.setDriver('GV1', self.get_valve_rf_strength(self.home_id, self.valve_id), False, False, 131)

            else:
                self.node.setDriver('BATLVL', 99, True, False, 25 )
                self.node.setDriver('GV0', 99, True, False, 25 )
                self.node.setDriver('GV1', 99, True, False, 25 )

                self.node.setDriver('ST', 0) 
                #self.node.setDriver('ERR', 1)                     
    


    def update(self, command = None):
        self.myNetatmo.self.myNetatmo.get_home_status(self._home)
        self.updateISYdrivers()


    commands = {        
                'UPDATE': update,
              }
