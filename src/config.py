from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ANALOG = ['TP2','TP3','H1','DV_pressure','Reservoirs','Oil_temperature','Motor_current']
DIGITAL = ['COMP','DV_eletric','Towers','MPG','LPS','Pressure_switch','Oil_level','Caudal_impulses']
SENSORS = ANALOG + DIGITAL
SOURCE = 'https://archive.ics.uci.edu/dataset/791/metropt+3+dataset'
SEED = 42
