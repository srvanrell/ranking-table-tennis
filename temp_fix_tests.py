import os

import pandas as pd

folder_path = "./tests/data_up_to_S2022T04"
filename = "ranking_df.csv"
backup_filename = f"{filename}.bkp"

fixing_file = os.path.join(folder_path, filename)
backup_file = os.path.join(folder_path, backup_filename)

if not os.path.exists(backup_file):
    os.system(f"cp -v {fixing_file} {backup_file}")

df = pd.read_csv(backup_file, index_col=0)
ordered_df = df.sort_values(["tid", "rating", "pid"], ascending=[True, False, True]).reset_index(drop=True)
ordered_df.to_csv(fixing_file)