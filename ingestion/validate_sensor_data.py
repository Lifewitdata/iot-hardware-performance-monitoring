import argparse,json
import pandas as pd
from src.preprocessing import clean_readings

def main():
    p=argparse.ArgumentParser(); p.add_argument('csv'); a=p.parse_args()
    _,_,report=clean_readings(pd.read_csv(a.csv))
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
