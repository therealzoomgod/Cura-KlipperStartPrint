"""
    File : KlipperStartPrint.py
    By   : therealzoomgod - https://github.com/therealzoomgod
    Desc : Script for Cura's Post Processing plugin to add a start print macro with extra options
    Usage: See included pdf for install and usage
           
    Tested on:
        Cura 5.2
"""

import os

from ..Script import Script
from cura.CuraApplication import CuraApplication

class KlipperStartPrint(Script):
    def __init__(self):
        super().__init__()
        
        # name mappings
        self._rename = {
            'machine_nozzle_size'                   : 'NOZZLE',
            'layer_height'                          : 'LAYER_HEIGHT',
            'material'                              : "MATERIAL",
            'material_bed_temperature_layer_0'      : 'BED_TEMP',
            'material_print_temperature_layer_0'    : 'EXTRUDER_TEMP',
            'material_standby_temperature'          : 'STANDBY_TEMP',
        }

        self._macro_args = []
        self._log_data = []

    def getSettingDataString(self):
        return """{
	        "name": "Klipper Start Print",
	        "key": "KlipperStartPrint",
	        "metadata": {},
	        "version": 2,
	        "settings": {
		        "enabled": {
			        "label": "Enable",
			        "description": "Enables this script",
			        "type": "bool",
			        "default_value": true
		        },
		        "macro": {
			        "label": "Macro",
			        "description": "Name of start print macro",
			        "type": "str",
			        "default_value": "START_PRINT"
		        },
		        "full_control": {
			        "label": "Full Control",
			        "description": "Strips out initial cura gcode for heaters",
			        "type": "bool",
			        "default_value": false
		        },
		        "bed": {
			        "label": "Bed Temp",
			        "description": "Include layer 0 bed temp. Variable: BED_TEMP",
			        "type": "bool",
			        "default_value": true
		        },
		        "hotend": {
			        "label": "Hotend Temp",
			        "description": "Include layer 0 hotend temp.  Variable: EXTRUDER_TEMP",
			        "type": "bool",
			        "default_value": true
		        },
		        "nozzle": {
			        "label": "Nozzle Size(s)",
			        "description": "Include nozzle size to extruder(s).  Variable: T0_NOZZLE etc",
			        "type": "bool",
			        "default_value": true
		        },
		        "material": {
			        "label": "Material Type(s)",
			        "description": "Include material type assigned to extruder(s).  Variable: T0_MATERIAL etc",
			        "type": "bool",
			        "default_value": true
		        },
		        "standby": {
			        "label": "Standby Temperature(s)",
			        "description": "Include initial extruder and standby temps (IDEX).  Variable: T0_STANDBY_TEMP etc",
			        "type": "bool",
			        "default_value": true
		        },
		        "layer": {
			        "label": "Layer height",
			        "description": "Include profile layer height.  Variable: LAYER_HEIGHT",
			        "type": "bool",
			        "default_value": true
		        }
	        }
        }"""
        
    def _translate_name(self, name):
        return self._rename.get(name, name)

    def _get_used_extruders(self, data):
        """ 
            Find in use extruders
            1st extruder is 0 
        """

        extruders = []

        for index, chunks in enumerate(data, start=0):

            for line in chunks.split('\n'):

                line = line.strip()

                if not line or line[0] == ';':
                    continue

                if line[0] == 'T' and line[1].isdigit():
                    ex = int(line[1])
                    if not ex in extruders:
                        extruders.append(ex)

        return extruders

    def _get_temps(self, data):

        """ Parse Cura's startup gcode for temps and extruder """

        bed = 0
        extruders = {}
        tool = 0

        for index, chunks in enumerate(data, start=0):
            for line in chunks.split('\n'):

                comment = line.find(';')
                if comment == 0:
                    continue

                if comment:
                    line = line.split(';')[0].strip()

                if not line:
                    continue

                if line.startswith('T') and line[1].isdigit():
                    tool = int(line[1])
                    extruders['initial'] = tool

                if line.startswith('M8'):
                    return bed, extruders

                if line.startswith('M140'):
                    bed = float(line.split('S')[1])
                elif line.startswith('M104'):
                    ch = line.split(' ')
                    if len(ch) == 2:
                        extruders[tool] = float(ch[1][1:])
                    else:
                        extruder_nr = int(ch[1][1])
                        extruders[extruder_nr] = float(ch[2][1:])

        # Should never land here unless user has start gcode in cura
        self._log('No temp info found to parse, exiting.')
        return None, {}

    def _add_entry(self, entry):
        # Just to avoid dupe entries
        if not entry in self._macro_args:
            self._macro_args.append(entry)
            self._log(entry)
        return 

    def _log(self, msg):
        self._log_data.append(';KlipperStartPrint: %s' % msg)

    def _write_log(self, data):

        if not len(self._log_data):
            return data

        for index, chunk in enumerate(data, start=0):
            lines = []
            changed = False
            for line in chunk.split('\n'):
                lines.append(line)
                if line.startswith(';Generated with'):
                    lines = lines + [';'] + self._log_data + [';']
                    changed = True

            if changed:
                data[index] = '\n'.join(lines)
                break

        return data

    def execute(self, data):

        macro_name       = self.getSettingValueByKey("macro")
        full_control     = self.getSettingValueByKey("full_control")
        add_bed_temp     = self.getSettingValueByKey("bed")
        add_hotend_temp  = self.getSettingValueByKey("hotend")
        add_nozzle       = self.getSettingValueByKey("nozzle")
        add_material     = self.getSettingValueByKey("material")
        add_layer        = self.getSettingValueByKey("layer")

        self._log_data = [';KlipperStartPrint: Ready']

        if macro_name == "" or not self.getSettingValueByKey("enabled"):
            return data

        extruder_stacks     = CuraApplication.getInstance().getExtruderManager().getActiveExtruderStacks()

        used_extruders      = self._get_used_extruders(data)
        bed, extruder_temps = self._get_temps(data)
        initial_extruder    = 0

        if bed == None:
            data = self._write_log(data)
            return data

        if 'initial' in extruder_temps:
            initial_extruder = extruder_temps['initial']
            del extruder_temps['initial']

        if len(used_extruders) == 0:
            used_extruders.append(0)

        # Get the extruder being used first
        #initial_extruder_nr = CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr()

        self._macro_args = [macro_name]

        self._add_entry('INITIAL=T%i' % (used_extruders[0]))
        initial_extruder_nr = used_extruders[0]

        if add_hotend_temp or full_control:
            for k, v in extruder_temps.items():
                self._add_entry('T%i_TEMP=%.1f' % (k, v))

        if add_bed_temp or full_control:
            self._add_entry('BED_TEMP=%.1f' % (bed))


        index = 0
        for extruder in extruder_stacks:
        
            if index == initial_extruder:

                # Same for every extruder so only add 1 without a prefix
                if add_layer:
                    var_type, var_value = self._get_value("resolution", extruder, "layer_height")
                    self._add_entry("%s=%s" % (self._translate_name("layer_height"), var_value))

            if add_material:
                material = extruder.material.getMetaData().get("material", "")
                self._add_entry("T%i_%s=\"%s\"" % (index, self._translate_name("material"), material))

            if add_nozzle:
                var_type, var_value = self._get_value("machine_settings", extruder, "machine_nozzle_size")
                if var_type:
                    self._add_entry("T%i_%s=%s" % (index, self._translate_name("machine_nozzle_size"), var_value))

            index += 1

        macro_str = " ".join(self._macro_args)

        #
        # Make sure macro is before any cura generated gcode
        # Note: It's not 1 line per index so have to split on \n
        #
        comment_idx = -1

        for index, line in enumerate(data, start=0):
            if comment_idx == -1 and line.find('Generated with') > -1:
                comment_idx = index
                break

        data = self._write_log(data)

        if comment_idx > -1 and macro_str != '':

            ff = []
            added_macro = False
            found_ext_mode = False

            for line in data[comment_idx].split('\n'):

                if added_macro and full_control:
                    if line.find('extrusion mode') > -1:
                        ff.append(line)
                        found_ext_mode = True
                    elif found_ext_mode:
                        ff.append(line)
                else:
                    ff.append(line)

                if line.find('Generated with') > -1:
                    ff.append(macro_str)
                    added_macro = True

            data[comment_idx] = "\n".join(ff) + '\n'

        return data

    def _get_value(self, section, stack, key):

        # This function is a stripped down version from the ImportExport plugin by 5@xes

        if stack.getProperty(key,"type") == "category":
            section=key
        else:
            if stack.getProperty(key,"enabled") == True:
                GetType=stack.getProperty(key,"type")
                GetVal=stack.getProperty(key,"value")
                
                if str(GetType)=='float':
                    GelValStr="{:.4f}".format(GetVal).rstrip("0").rstrip(".") # Formatage
                else:
                    GelValStr=str(GetVal)

                return str(GetType), GelValStr

        try:
            if len(CuraApplication.getInstance().getGlobalContainerStack().getSettingDefinition(key).children) > 0:
                for i in CuraApplication.getInstance().getGlobalContainerStack().getSettingDefinition(key).children:       
                    self._get_value(section, stack, i.key)     
        except:
            return None, None


