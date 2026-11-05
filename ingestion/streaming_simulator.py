"""Replay recorded data as JSONL; this is not a live hardware integration."""
import argparse,json,time
import pandas as pd

def replay(path,limit=100,delay=0):
    sent=0
    for chunk in pd.read_csv(path,chunksize=10000):
        for row in chunk.to_dict('records'):
            if sent>=limit: return
            yield json.dumps(row,allow_nan=False)
            sent+=1
            if delay: time.sleep(delay)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('csv'); p.add_argument('--limit',type=int,default=100); p.add_argument('--delay',type=float,default=0); a=p.parse_args()
    if a.limit<0 or a.delay<0: p.error('limit and delay must be nonnegative')
    for line in replay(a.csv,a.limit,a.delay): print(line,flush=True)
