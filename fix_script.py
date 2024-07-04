import pandas as pd

csv_in = pd.read_csv("./tests/data_up_to_S2022T04/rating_details_df.csv", index_col=0)

print(csv_in)

csv_out = csv_in.sort_index(ascending=True)

print(csv_out)

csv_out.to_csv("./tests/data_up_to_S2022T04/rating_details_df_new.csv")
