# KlipperMacroArgs

Cura post processing script for Klipper IDEX machines.

This replaces needing start gcode in slicer, you do everything in your Klipper start print macro.

## Install:
For version 5.2 (latest at time of release)
copy KlipperMacroArgs.py to %appdata%\Roaming\cura\5.2\scripts

### To enable script:
Extensions -> Post Processesing -> Modify G-Code -> Add a script
Choose KlipperMacroArgs then check enable for it.

#### Confirmed working on:
Cura 5.2

## Example to get the passed args:
    {% set BED_TEMP = params.BED_TEMP | default(0.0) | float %}
    {% set T0_TEMP = params.T0_TEMP | default(0.0) | float  %}
    {% set T1_TEMP = params.T1_TEMP | default(0.0) | float  %}
    {% set layer_height = params.LAYER_HEIGHT | default(0.2) | float %}
    {% set initial_extruder = params.INITIAL | default("T0") %}
    {% set T0_material = params.T0_MATERIAL | default("?") %}
    {% set T1_material = params.T1_MATERIAL | default("?") %}
    {% set T0_nozzle = params.T0_NOZZLE | default(0.4) | float %}
    {% set T1_nozzle = params.T1_NOZZLE | default(0.4) | float %}
    {% set T0_standby_temp = params.T0_STANDBY_TEMP | default(0.0) | float %}
    {% set T1_standby_temp = params.T1_STANDBY_TEMP | default(0.0) | float %}


![Screenshot](https://github.com/therealzoomgod/Cura-KlipperStartPrint/blob/main/ss.png "Screenshot")