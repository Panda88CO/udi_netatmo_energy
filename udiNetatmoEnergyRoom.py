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


from udiNetatmoEnergyValve import udiNetatmoEnergyValve

#from udi_interface import logging, Custom, Interface
#id = 'main_netatmo'

'''
      <st id="ST" editor="bool" />
      <st id="CLITEMP" editor="temperature" />
      <st id="GV1" editor="co2" />
      <st id="GV2" editor="humidity" />
      <st id="GV3" editor="noise" />
      <st id="GV4" editor="pressure" />
      <st id="GV5" editor="pressure" />
      <st id="GV6" editor="temperature" />
      <st id="GV7" editor="temperature" />
      <st id="GV8" editor="trend" />
      <st id="GV9" editor="trend" />
      <st id="GV10" editor="t_timestamp" />
      <st id="GV11" editor="wifi_rf_status" />
    </sts>
'''
'''
id = 'mainunit'

drivers = [
            {'driver' : 'CLITEMP', 'value': 0,  'uom':4}, 
            {'driver' : 'CO2LVL', 'value': 0,  'uom':54}, 
            {'driver' : 'CLIHUM', 'value': 0,  'uom':22}, 
            {'driver' : 'GV3', 'value': 0,  'uom':12}, 
            {'driver' : 'BARPRES', 'value': 0,  'uom':23}, 
            {'driver' : 'GV5', 'value': 0,  'uom':23}, 
            {'driver' : 'GV6', 'value': 0,  'uom':4}, 
            {'driver' : 'GV7', 'value': 0,  'uom':4}, 
            {'driver' : 'GV8', 'value': 0,  'uom':25}, 
            {'driver' : 'GV9', 'value': 0,  'uom':25}, 
            {'driver' : 'GV10', 'value': 0,  'uom':44},
            {'driver' : 'GV11', 'value': 0,  'uom':131},            
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
            ]
'''

class udiNetatmoEnergyRoom(udi_interface.Node):
    from udiNetatmoLib import bool2ISY, t_mode2ISY, node_queue, wait_for_node_done, con_state2ISY, convert_temp_unit
    def __init__(self, polyglot, primary, address, name, myNetatmo, home, room_id):
        super().__init__(polyglot, primary, address, name)

        self.poly = polyglot
        self.myNetatmo = myNetatmo
        self._home = home
        self.home_id = home['id']
        self.room_id = room_id
        self.node_ready = False
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        #self.module = {'module_id':module_info['main_module'], 'type':'MAIN', 'home_id':module_info['home'] }
        #logging.debug('self.module = {}'.format(self.module))
        self.id = 'house'
        self.drivers = [
            {'driver' : 'CLITEMP', 'value': 99,  'uom':25}, 
            {'driver' : 'CLISPH', 'value': 99,  'uom':25}, 
            {'driver' : 'CLIMD', 'value': 99,  'uom':25}, 
            {'driver' : 'GV0', 'value': 99,  'uom':25}, 
            {'driver' : 'GV1', 'value': 0,  'uom':2}, 
            {'driver' : 'GV2', 'value': 0,  'uom':2}, 
            {'driver' : 'GV3', 'value': 99,  'uom':25},      
            {'driver' : 'ST', 'value': 99,  'uom':25}, 
            ]
        self.primary = primary
        self.address = address
        self.name = name

        #self.myNetatmo = NetatmoWeather
        #self.home_id = module_info['home']
        #self.main_module_id = module_info['main_module']

        self.Parameters = Custom(self.poly, 'customparams')
        self.Notices = Custom(self.poly, 'notices')
        self.poly.subscribe(self.poly.START, self.start, address)
        #self.poly.subscribe(self.poly.STOP, self.stop)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)

        polyglot.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node_ready = True
        self.node = self.poly.getNode(address)
        logging.info('Start {} room Node'.format(self.name))  
        time.sleep(1)

       

    


    def start(self):
        logging.debug('Executing udiNetatmoEnergyHome start')
        self.addNodes()
        self.updateISYdrivers() 

    def stop (self):
        pass
    
    def addNodes(self):
        '''addNodes'''

        logging.debug('Adding valves to {}'.format(self.name))

        if 'modules' in self._home:
            for indx in range(0, len(self._home['modules'])):
                valve_info = self._home['modules'][indx]
                if valve_info['room_id'] == self.room_id and valve_info['type'] == 'NRV':
                    valve_name = valve_info['name']
                    node_name = self.poly.getValidName(valve_name)
                    valve_id = valve_info['id']
                    node_address = self.poly.getValidAddress(valve_id)
                    logging.debug('adding room node : {} {} {} {} {} {}'.format( self.primary, node_address, node_name, self.myNetatmo, self._home,  valve_id))

                    tmp_room = udiNetatmoEnergyValve(self.poly, self.primary, node_address, node_name, self.myNetatmo, self._home,  valve_id)
                    while not tmp_room.node_ready:
                        logging.debug( 'Waiting for node {}-{} to be ready'.format(valve_id, node_name))
                        time.sleep(4)



                
    def update(self, command = None):
        logging.debug('update room data {}'.format(self._home))
        self.myNetatmo.get_home_status(self._home)
        #self.myNetatmo.update_weather_info_instant(self.module['home_id'])
        self.updateISYdrivers()

   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        #data = self.myNetatmo.get_module_data(self.module)
        #logging.debug('Main module data: {}'.format(data))
        if self.node is not None:

            if self.myNetatmo.get_room_online(self.home_id, self.room_id):
                self.node.setDriver('ST', 1)
                logging.debug('TempUnit = {} {}'.format(self.myNetatmo.temp_unit, self.convert_temp_unit(self.myNetatmo.temp_unit)))
                if self.convert_temp_unit(self.myNetatmo.temp_unit) == 0:
                    self.node.setDriver('CLITEMP', round(self.myNetatmo.get_room_temp(self.home_id, self.room_id),1), True, False, 4 )
                    self.node.setDriver('CLISPH', round(self.myNetatmo.get_room_setpoint_temp(self.home_id, self.room_id),1), True, False, 4 )
                else:
                    self.node.setDriver('CLITEMP', (round(self.myNetatmo.get_room_temp(self.home_id, self.room_id))*9/5+32,1), True, False, 17 )
                    self.node.setDriver('CLISPH', (round(self.myNetatmo.get_room_setpoint_temp(self.home_id, self.room_id))*9/5+32,1), True, False, 17 )
                self.node.setDriver('CLIMD', self.t_mode2ISY(self.myNetatmo.get_room_setpoint_mode(self.home_id, self.room_id)))
                self.node.setDriver('GV0', self.myNetatmo.get_room_heat_power_request(self.home_id, self.room_id), True, False, 0)
                self.node.setDriver('GV1', self.bool2ISY(self.myNetatmo.get_room_open_window(self.home_id, self.room_id)))
                self.node.setDriver('GV2', self.bool2ISY(self.myNetatmo.get_room_anticipating(self.home_id, self.room_id)))
                self.node.setDriver('GV3', 0, True, True, 44)
 
            else:
                self.node.setDriver('CLITEMP', 99, True, False, 25 )
                self.node.setDriver('CLISPH', 99, True, False, 25 )
                self.node.setDriver('CLIMD', 99, True, False, 25 )
                self.node.setDriver('GV0', 99, True, False, 25 )
                self.node.setDriver('GV1', 99, True, False, 25 )
                self.node.setDriver('GV2', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('ST', 0) 
                  
    def set_set_point(self, command):
        logging.debug('set_set_point {} called'.format(command))

    def set_opmode(self, command):
        logging.debug('set_opmode {} called'.format(command))

    commands = {        
                'UPDATE'    : update,
                'SETPOINT'  : set_set_point,
                'OPMODE'    : set_opmode,
                }

        
