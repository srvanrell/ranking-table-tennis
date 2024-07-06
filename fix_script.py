import pandas as pd

csv_in = pd.read_csv("./tests/data_up_to_S2022T04/championship_details_in.csv", index_col=0)

print(csv_in)

# csv_out = csv_in.sort_index(ascending=True)
csv_out = csv_in.sort_values(
    ["tid", "category", "points", "pid"], ascending=[True, True, False, True]
).reset_index(drop=True)

print(csv_out)

csv_out.to_csv("./tests/data_up_to_S2022T04/championship_details_df.csv")
