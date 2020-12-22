import glob
import pandas as pd 

num_csv = 0
for f in glob.glob("WIKI-ORCL-*.csv"):
    if not num_csv:
        df = pd.read_csv(f)
    else:
        df = pd.concat([df, pd.read_csv(f)])
    num_csv += 1

df.sort_values("Date", inplace=True)

df.to_csv("ORCL.csv", index=False)