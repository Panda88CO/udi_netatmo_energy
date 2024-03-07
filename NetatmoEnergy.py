
#!/usr/bin/env python3
from  NetatmoOauth import NetatmoCloud 
import urllib.parse
from datetime import datetime, timezone

#from oauth import OAuth
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)



class NetatmoEnergy(NetatmoCloud):
    def __init__(self, polyglot):
        super().__init__(polyglot, 'read_thermostat write_thermostat')
        logging.info('NetatmoEnergy initializing')
        self.poly = polyglot
        self._dev_list  = ['NAPlug', 'NRV', 'NATherm1']

        self.instant_data = {}
     
        self.energy_data = {}
        self.GW_modules = ['NAPlug']
        self.valves =['NRV']
        self.thermostat = ['NATherm1']

    # should not be necesary - filtered by token    
    #def get_energy_stations (self):
    #    logging.debug('get_energy_stations')
    #    all_systems = 


    def update_energy_info_cloud (self, home_id):
        ''' Polls latest data stored in cloud - more data available'''
        logging.debug('get_energy_info_cloud')
        try:
            tmp = self.get_modules(home_id)
            logging.debug('tmp = {}'.format(tmp))
            self.cloud_data[home_id] = {}
            for dev_id in tmp:
                if tmp[dev_id]['type'] in self.GW_modules:
                    
                    dev_id_str = urllib.parse.quote_plus(dev_id )

                    api_str = '/getstationsdata?device_id='+str(dev_id_str)+'&get_favorites=false'
                    
                    temp_data = self._callApi('GET', api_str )

                    logging.debug('dev Id {}, data: {} '.format(dev_id, temp_data))

                    #test = self._callApi('GET', '/getstationsdata' )
                    #logging.debug(temp_data)
                    if 'status'  in temp_data:
                        if temp_data['status'] == 'ok':
                            if len(temp_data['body']['devices'] ) == 1:
                                temp_data = temp_data['body']['devices'][0]  # there should only be 1 dev_id
                            else:
                                logging.error('Code only handles 1st main energy station : {} found'.format(len(temp_data['body']['devices'])))
                                logging.error('Processing first one')
                                temp_data = temp_data['body']['devices'][0]
                            logging.debug('past temp data {}'.format(temp_data))
                            self.cloud_data[home_id] = {}
                            self.cloud_data[home_id]['GW'] = {}
                            self.cloud_data[home_id]['INDOOR'] = {}
                            self.cloud_data[home_id]['OUTDOOR'] = {}
                            self.cloud_data[home_id]['RAIN'] = {}
                            self.cloud_data[home_id]['WIND'] = {}
                            self.cloud_data[home_id]['GW'][dev_id] = {}
                            self.cloud_data[home_id]['GW'][dev_id]['reachable'] = temp_data['reachable']
                            self.cloud_data[home_id]['GW'][dev_id]['data_type'] = temp_data['data_type']
                            if 'dashboard_data' in temp_data:
                                self.cloud_data[home_id]['GW'][dev_id] = temp_data['dashboard_data']
                                self.cloud_data[home_id]['GW'][dev_id]['online'] = True
                            else:
                                self.cloud_data[home_id]['GW'][dev_id]['online'] = True
                            logging.debug('past main {}'.format(self.cloud_data))
                            for module in range(0,len(temp_data['modules'])):
                                mod = temp_data['modules'][module]
                                logging.debug('{} {}c data {}, mod  {}'.format(self.module_type(mod['type']),mod['_id'], self.cloud_data, mod))
                                self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']] = {}
                                if 'dashboard_data' in mod:
                                    self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']]['online'] = True 
                                    self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']] = mod['dashboard_data']
                                else:
                                    self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']]['online'] = False                                   
                                self.cloud_data[home_id][self.module_type(mod['type'])][mod['_id']]['data_type'] = mod['data_type']
                        logging.debug('data before merge: {}'.format(self.cloud_data))
                        self.merge_data(home_id)         
            return(self.cloud_data)
        except Exception as e:
            logging.error('update_energy_info_cloud failed : {}'.format(e))
            return({})


    def module_type (self, type):
        if type in self.GW_modules:
            return('GATEWAY')
        if type in self.valves:
            return('VALVE')
        if type in self.thermostat:
            return('THERMOSTAT')
              

    
    def get_homes(self):
        '''get_homes'''
        home_list = self.get_homes_info()
        self.energy_in_homes = {}
        for home in home_list:
            found = False
            home_id = home['id']
            if 'modules' in home:                
                for module in home['module']:
                    if module['type'] in self._dev_list:
                        found = True
                        if module['type'] in self.GW_modules:
                            logging.debug('Gateway found {}'.format(module['type'] ))


            for mod_type in tmp[home_id]['module_types']:
                if mod_type in  self._dev_list:
                    found = True
            if found:
                self.energy_in_homes[home_id] = tmp[home_id]
        return(self.energy_in_homes)

    def get_GW_modules(self, home_id):
        '''get_GW_modules '''
        tmp = self._get_modules(home_id, self.GW_modules)
        logging.debug('get_GW_modules {}'.format(tmp))
        return(self._get_modules(home_id, self.GW_modules))
    



    def _get_energy_data(self, home_id, dev_id, mod_type):
        '''Get data function'''
        if home_id in self.energy_data:
            if mod_type in self.energy_data[home_id]:
                if dev_id in self.energy_data[home_id][mod_type]:
                    return(self.energy_data[home_id][mod_type][dev_id])
        else:
            logging.warning('No data fouond for {0} {1}'.format(home_id, dev_id))
    '''
    def get_main_module_data(self, home_id, dev_id):
        #Get data from main module
        logging.debug('get_main_module_data')
        #data_list = ['Temperature', 'CO2', 'Humidity', 'Noise', 'Pressure', 'AbsolutePressure', 'min_temp', 'max_temp', 'date_max_temp', 'date_min_temp', 'temp_trend', 'reachable']
        return(self._get_energy_data(home_id, dev_id, 'GW'))
    '''    

    def get_module_data(self, module):
        logging.debug('get_indoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(module['home_id'], module['module_id'], module['type']))
               
    '''
    def get_outdoor_module_data(self, home_id, dev_id=None):
        logging.debug('get_outdoor_module_data')
        #data_list = ['temperature', 'co2', 'humidity', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'OUTDOOR'))

    def get_rain_module_data(self, home_id, dev_id=None):
        logging.debug('get_rain_module_data')
        #data_list = ['rain', 'sum_rain_1', 'sum_rail_24', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'RAIN'))

    def get_wind_module_data(self, home_id, dev_id=None):
        logging.debug('get_wind_module_data')
        #data_list = ['wind_strength', 'wind_angle', 'wind+gust', 'wind_gust_angle', 'last_seen', 'battery_state', 'ts']
        return(self._get_energy_data(home_id, dev_id, 'WIND'))
    '''

    def get_temperature_C(self, module):
        try:
            logging.debug('get_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['temperature'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['temperature'])       
        except Exception as e:
            logging.error('get_temperature_C exception; {}'.format(e))
            return(None)
    def get_max_temperature_C (self, module):
        try:
            logging.debug('get_max_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_temp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_temp'])       
        except Exception as e:
            logging.error('get_max_temperature_C exception; {}'.format(e))
            return(None)

    def get_min_temperature_C(self, module):
        try:
            logging.debug('get_min_temperature_C {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['min_temp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['min_temp'])       
        except Exception as e:
            logging.error('get_min_temperature_C exception; {}'.format(e))
            return(None)

    def get_co2(self, module):
        try:
            logging.debug('get_co2 {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['co2'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['co2'])       
        except Exception as e:
            logging.error('get_co2 exception; {}'.format(e))
            return(None)

    def get_noise(self, module):
        try:
            logging.debug('get_noise {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['noise'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['noise'])       
        except Exception as e:
            logging.error('get_co2 exception; {}'.format(e))
            return(None)
        
    def get_humidity(self, module):
        try:
            logging.debug('get_humidity {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['humidity'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['humidity'])       
        except Exception as e:
            logging.error('get_humidity exception; {}'.format(e))
            return(None)

    def get_pressure(self, module):
        try:
            logging.debug('get_pressure {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure'])       
        except Exception as e:
            logging.error('get_pressure exception; {}'.format(e))
            return(None)

    def get_abs_pressure(self, module):
        try:
            logging.debug('get_abs_pressure {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['absolute_pressure'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['absolute_pressure'])       
        except Exception as e:
            logging.error('absolute_pressure exception; {}'.format(e))
            return(None)        

    def get_time_stamp(self, module):
        try:
            logging.debug('get_time_stamp {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['time_stamp'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['time_stamp'])       
        except Exception as e:
            logging.error('get_time_stamp exception: {}'.format(e))
            return(None)        
             
    def get_time_since_time_stamp_min(self, module):
        unix_timestamp = datetime.now(timezone.utc).timestamp()
        meas_time = self.get_time_stamp(module)        
        delay = unix_timestamp - meas_time
        return( round(delay/60, 2)) #delay min

    def get_temp_trend(self, module):
        try:
            trend = self.energy_data[module['home_id']][module['type']][module['module_id']]['temp_trend']
            return(trend)       
        except Exception as e:
            logging.error('get_temp_trend exception; {}'.format(e))
            return( None)
    
    def get_hum_trend(self, module):
        try:
            trend = self.energy_data[module['home_id']][module['type']][module['module_id']]['pressure_trend']
   
        except Exception as e:
            logging.error('get_hum_trend exception; {}'.format(e))
            return( None, None)
        

    def get_rain(self, module):
        try:
            logging.debug('get_rain {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['rain'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['rain'])       
        except Exception as e:
            logging.error('get_rain exception; {}'.format(e))
            return(None)      

    def get_rain_1hour(self, module):
        try:
            logging.debug('get_rain_1hour {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_1'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_1'])       
        except Exception as e:
            logging.error('get_rain_1hour {}'.format(e))
            return(None)  
    
    def get_rain_24hours(self, module):
        try:
            logging.debug('get_rain_24hours {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_24'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['sum_rain_24'])       
        except Exception as e:
            logging.error('get_rain_24hours exception; {}'.format(e))
            return(None)  

    def get_wind_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['windangle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['windangle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_wind_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['windstrength'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['windstrength'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)  

    def get_gust_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['gustangle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['gustangle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_gust_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['guststrength'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['guststrength'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)  
        
    def get_max_wind_angle(self, module):
        try:
            logging.debug('get_wind_angle {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_angle'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_angle'])       
        except Exception as e:
            logging.error('get_wind_angle exception; {}'.format(e))
            return(None)  

    def get_max_wind_strength(self, module):
        try:
            logging.debug('get_wind_strength {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_str'],module['home_id'], module['type'], module['module_id'] ))
            return(self.energy_data[module['home_id']][module['type']][module['module_id']]['max_wind_str'])       
        except Exception as e:
            logging.error('get_wind_strength exception; {}'.format(e))
            return(None)          

    def get_battery_info(self, module):
        try:
            bat1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['battery_state']
            bat2 = self.energy_data[module['home_id']][module['type']][module['module_id']]['battery_level']
            return (bat1, bat2)
        except Exception as e:
            logging.error('get_battery_info exception: {}'.format(e))
            return( None, None)
        
    def get_rf_info(self, module):
        try:
            rf1 = None
            rf2 = None
            if 'rf_state' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['rf_state']               
            if 'wifi_state' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf1 = self.energy_data[module['home_id']][module['type']][module['module_id']]['wifi_state']
            if 'rf_strength' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf2 = -self.energy_data[module['home_id']][module['type']][module['module_id']]['rf_strength']
            if 'wifi_strength' in self.energy_data[module['home_id']][module['type']][module['module_id']]:
                rf2 = -self.energy_data[module['home_id']][module['type']][module['module_id']]['wifi_strength']           
            return(rf1, rf2)
        except Exception as e:
            logging.error('get_rf_info exception; {}'.format(e))
            return(None, None)

    def get_online(self, module):
        try:
            #logging.debug('module {} '.format(module) )
            #logging.debug('module data1: {}'.format(self.energy_data))
            #logging.debug('module data2: {} - {} - {}'.format(module['home_id'], module['type'],module['module_id']))
            #logging.debug('module data3: {}'.format(self.energy_data[module['home_id']]))
            #logging.debug('module data4: {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]))
            #logging.debug('get_online {} {} {} {}'.format(self.energy_data[module['home_id']][module['type']][module['module_id']]['online'],module['home_id'], module['type'], module['module_id'] ))
            if 'online' in self.energy_data[module['home_id']][module['type']][module['module_id']]:    
                return(self.energy_data[module['home_id']][module['type']][module['module_id']]['online'])
            else:
                return(False)      
        except Exception as e:
            logging.warning('No online data exists - Assume off line : {} - {}'.format(e, module))
            return(False)


