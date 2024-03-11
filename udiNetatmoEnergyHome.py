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


from udiNetatmoEnergyRoom import udiNetatmoEnergyRoom

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

class udiNetatmoEnergyHome(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, myNetatmo, home):
        super().__init__(polyglot, primary, address, name)

        self.poly = polyglot
        self.myNetatmo = myNetatmo
        self._home = home
        self.home_id = home['id']
        self.node_ready = False
        self.n_queue = []
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        #self.module = {'module_id':module_info['main_module'], 'type':'MAIN', 'home_id':module_info['home'] }
        #logging.debug('self.module = {}'.format(self.module))
        self.id = 'house'
        self.drivers = [
            {'driver' : 'CLITEMP', 'value': 99,  'uom':25}, 
            {'driver' : 'CO2LVL', 'value': 99,  'uom':25}, 
            {'driver' : 'CLIHUM', 'value': 0,  'uom':51}, 
            {'driver' : 'GV3', 'value': 0,  'uom':12}, 
            {'driver' : 'BARPRES', 'value': 0,  'uom':117}, 
            {'driver' : 'GV5', 'value': 0,  'uom':117}, 
            {'driver' : 'GV6', 'value': 0,  'uom':4}, 
            {'driver' : 'GV7', 'value': 0,  'uom':4}, 
            {'driver' : 'GV8', 'value': 99,  'uom':25}, 
            #{'driver' : 'GV9', 'value': 0,  'uom':25}, 
            {'driver' : 'GV10', 'value': 0,  'uom':44},
            {'driver' : 'GV11', 'value': 99,  'uom':25},         
            {'driver' : 'ST', 'value': 0,  'uom':2}, 
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
        logging.info('Start {} main module Node'.format(self.name))  
        time.sleep(1)

       
    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()
    
    
    def getValidName(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        return re.sub(r"[^A-Za-z0-9_ ]", "", name)

    # remove all illegal characters from node address
    def getValidAddress(self, name):
        name = bytes(name, 'utf-8').decode('utf-8','ignore')
        tmp = re.sub(r"[^A-Za-z0-9_]", "", name.lower())
        logging.debug('getValidAddress {}'.format(tmp))
        return tmp[:14]
    
    def rfstate2ISY(self, rf_state):
        if rf_state.lower() == 'full':
            rf = 0
        elif rf_state.lower() == 'medium':
            rf = 1
        elif rf_state.lower() == 'low':
            rf = 2
        else:
            rf= 99
            logging.error('Unsupported RF state {}'.format(rf_state))
        return(rf)
    

    def battery2ISY(self, batlvl):
        if batlvl == 'max':
            state = 0
        elif batlvl == 'full':
            state = 1
        elif batlvl == 'high':
            state = 2
        elif batlvl == 'medium':
            state = 3
        elif batlvl == 'low':
            state = 4
        elif batlvl == 'very low':
            state = 5
        else:
            state = 99
        return(state)
    
    def trend2ISY (self, trend):
        if trend == 'stable':
            return(0)
        elif trend == 'up':
            return(1)
        elif trend =='down':
            return(2)
        else:
            logging.error('unsupported temperature trend: {}'.format(trend))
            return(99)    


    def convert_temp_unit(self, tempStr):
        if tempStr.capitalize()[:1] == 'F':
            return(1)
        elif tempStr.capitalize()[:1] == 'C':
            return(0)
        
    


    def start(self):
        logging.debug('Executing udiNetatmoEnergyHome start')
        self.addNodes()
        self.update() # get latest data 

    def stop (self):
        pass
    
    def addNodes(self):
        '''addNodes'''

        logging.debug('Adding rooms to {}'.format(self.name))

        if 'rooms' in self._home:
            for indx in range(0, len(self._home['rooms'])):
                room_info = self._home['rooms'][indx]
                rm_name = room_info['name']
                node_name = self.poly.getValidName(rm_name)
                room_id = room_info['id']
                node_address = self.poly.getValidAddress(room_id)
                tmp_room = udiNetatmoEnergyRoom(self.poly, self.primary, node_address, node_name, self.myNetatmo, room_info)
                while not tmp_room.node_ready:
                    logging.debug( 'Waiting for node {}-{} to be ready'.format(room_id, node_name))
                    time.sleep(4)



                
    def update(self, command = None):

        self.myNetatmo.get_home_status(self.home_id)
        #self.myNetatmo.update_weather_info_instant(self.module['home_id'])
        self.updateISYdrivers()

   
        
    def updateISYdrivers(self):
        logging.debug('updateISYdrivers')
        data = self.myNetatmo.get_module_data(self.module)
        logging.debug('Main module data: {}'.format(data))
        if self.node is not None:
            if self.myNetatmo.get_online(self.module):
                self.node.setDriver('ST', 1)
                logging.debug('TempUnit = {} {}'.format(self.myNetatmo.temp_unit, self.convert_temp_unit(self.myNetatmo.temp_unit)))
                if self.convert_temp_unit(self.myNetatmo.temp_unit) == 0:
                    self.node.setDriver('CLITEMP', round(self.myNetatmo.get_temperature_C(self.module),1), True, False, 4 )
                    self.node.setDriver('GV6', round(self.myNetatmo.get_min_temperature_C(self.module),1), True, False, 4 )
                    self.node.setDriver('GV7', round(self.myNetatmo.get_max_temperature_C(self.module),1), True, False, 4 )
                else:
                    self.node.setDriver('CLITEMP', (round(self.myNetatmo.get_temperature_C(self.module)*9/5+32,1)), True, False, 17 )
                    self.node.setDriver('GV6', (round(self.myNetatmo.get_min_temperature_C(self.module)*9/5+32,1)), True, False, 17 )
                    self.node.setDriver('GV7', (round(self.myNetatmo.get_max_temperature_C(self.module)*9/5+32,1)), True, False, 17 )                     
                self.node.setDriver('CO2LVL', self.myNetatmo.get_co2(self.module), True, False, 54)
                self.node.setDriver('CLIHUM', self.myNetatmo.get_humidity(self.module), True, False, 51)
                self.node.setDriver('GV3', round(self.myNetatmo.get_noise(self.module),0), True, False, 12)
                self.node.setDriver('BARPRES', round(self.myNetatmo.get_pressure(self.module),0), True, False, 117)
                self.node.setDriver('GV5', round(self.myNetatmo.get_abs_pressure(self.module),0), True, False, 117)

                temp_trend = self.myNetatmo.get_temp_trend(self.module)
                self.node.setDriver('GV8', self.trend2ISY(temp_trend))

                #hum_trend= self.myNetatmo.get_hum_trend(self.module)
                #self.node.setDriver('GV9', trend_val)
                self.node.setDriver('GV10', self.myNetatmo.get_time_since_time_stamp_min(self.module) , True, False, 44)
                rf1, rf2 = self.myNetatmo.get_rf_info(self.module) 
                self.node.setDriver('GV11', self.rfstate2ISY(rf1) )
                #self.node.setDriver('ERR', 0)    
            else:
                self.node.setDriver('CLITEMP', 99, True, False, 25 )
                self.node.setDriver('GV6', 99, True, False, 25 )
                self.node.setDriver('GV7', 99, True, False, 25 )
                self.node.setDriver('CO2LVL', 99, True, False, 25 )
                self.node.setDriver('CLIHUM', 99, True, False, 25 )
                self.node.setDriver('GV3', 99, True, False, 25 )
                self.node.setDriver('BARPRES', 99, True, False, 25 )
                self.node.setDriver('GV5', 99, True, False, 25 )
                self.node.setDriver('GV8', 99, True, False, 25 )
                #self.node.setDriver('GV9', 99, True, False, 25 )
                self.node.setDriver('GV10', 99, True, False, 25 )
                self.node.setDriver('GV11', 99, True, False, 25 )
                self.node.setDriver('ST', 0) 
                #self.node.setDriver('ERR', 1)                     



    commands = {        
                'UPDATE': update,
                }

        
