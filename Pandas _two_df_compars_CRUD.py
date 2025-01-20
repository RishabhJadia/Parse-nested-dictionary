import pandas as pd
from sqlalchemy import create_engine
import numpy as np

# Replace with your actual database connection string
engine = create_engine('your_database_connection_string') 

# Read existing data from the database
existing_df = pd.read_sql_query("SELECT * FROM your_table_name", con=engine) 

# Define matching columns
match_cols = ['name', 'jtype', 'machine', 'box']

# Read new data from CSV in chunks
chunksize = 100000  # Adjust chunk size as needed
for chunk in pd.read_csv('new_data.csv', chunksize=chunksize):

    # Group existing DataFrame for faster lookups
    existing_df_grouped = existing_df.groupby(match_cols) 

    # Vectorized status determination
    chunk['status'] = chunk.apply(lambda row: 
                                  'create' if not existing_df_grouped.groups.get(tuple(row[match_cols])) 
                                  else 'update' if not all(existing_df.loc[existing_df_grouped.groups.get(tuple(row[match_cols])), match_cols].values == row[match_cols].values) 
                                  else 'deactivate', 
                                  axis=1)

    # Handle create and update actions
    create_df = chunk[chunk['status'] == 'create']
    update_df = chunk[chunk['status'] == 'update']

    if not create_df.empty:
        create_df.to_sql('your_table_name', con=engine, if_exists='append', index=False)

    if not update_df.empty:
        for index, row in update_df.iterrows(): 
            existing_df.loc[existing_df_grouped.groups.get(tuple(row[match_cols])), match_cols] = row[match_cols] 

# Handle deactivations after processing all chunks
deactivate_df = existing_df[~existing_df.set_index(match_cols).index.isin(new_df.set_index(match_cols).index)]

if not deactivate_df.empty:
    # Deactivate records (example using a flag column)
    existing_df.loc[existing_df.set_index(match_cols).index.isin(deactivate_df.set_index(match_cols).index), 'active'] = 0 
    existing_df.to_sql('your_table_name', con=engine, if_exists='replace', index=False) 
