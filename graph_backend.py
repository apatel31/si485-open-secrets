import pandas as pd 
import numpy as np

#import dropbox
from contextlib import closing # this will correctly close the request
import io
import streamlit as st

#!/usr/bin/env python3
import csv
from io import StringIO
import time

import pandas as pd
from sqlalchemy import create_engine

USERNAME = 'apatel31_demo_db_connection'
PG_STRING = 'postgresql://apatel31_demo_db_connection:3isXQ_rVv3fP9mkpugUUuXf3u7V7W@db.bit.io?sslmode=prefer'

engine = create_engine(PG_STRING, pool_pre_ping=True)


# from sqlalchemy import create_engine
# from google.oauth2 import service_account
# from google.cloud import bigquery

##### Sector Options #######
"""['Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution']"""


# # Create API client.
# credentials = service_account.Credentials.from_service_account_info(
#     st.secrets["gcp_service_account"]
# )
# client = bigquery.Client(credentials=credentials)

# # Perform query.
# # Uses st.experimental_memo to only rerun when the query changes or after 10 min.
# @st.experimental_memo(ttl=600)
# def run_query(query):
#     query_job = client.query(query)
#     rows_raw = query_job.result()
#     # Convert to list of dicts. Required for st.experimental_memo to hash the return value.
#     rows = [dict(row) for row in rows_raw]
#     return rows

@st.cache
def filter_spending(sectors=False, keywords=False, date_min=False, date_max=False):
    """
    Given optional filter parameters, load and filter data to run through graph function.

    Sector: string, one of 18 sectors in dataset ex. 'Construction'
    Keywords: List of lowercase keywords ex. ['test', 'word']
    date_min: Year ex. 2019
    date_max: Year ex. 2021
    
    """
    # lob_lobbying = pd.read_csv('./Data/lob_lobbying_issues.csv')

    # # if sector filter passed by user
    # if sectors:
    #     lob_lobbying = lob_lobbying[lob_lobbying['Sector'].isin(sectors)]

    if len(sectors) > 1:
        sectors_tup = "(\'" + "\',\'".join(sectors) + "\')"
        query = f'''SELECT * FROM "apatel31/OpenSecrets"."master" WHERE sector IN {sectors_tup};'''

        with engine.connect() as conn:
                # Set 1 minute statement timeout (units are milliseconds)
            conn.execute("SET statement_timeout = 600000;")
            lob_lobbying = pd.read_sql(query, conn)
        # cur.execute()
        # pprint(cur.fetchone())
    else:
        sector = "\'" + sectors[0] + "\'"
        query = f'''SELECT * FROM "apatel31/OpenSecrets"."master" WHERE sector={sector};'''

        with engine.connect() as conn:
            # Set 1 minute statement timeout (units are milliseconds)
            conn.execute("SET statement_timeout = 600000;")
            lob_lobbying = pd.read_sql(query, conn)
        print(lob_lobbying.head())
        # cur.execute()
        # pprint(cur.fetchone())

    lob_lobbying = lob_lobbying.loc[lob_lobbying['ind'] == 'y']

    # if date filter is passed by user
    if date_min:
        # apply date range
        lob_lobbying = lob_lobbying.loc[(lob_lobbying['year'] >= date_min) & (lob_lobbying['year'] <= date_max)]
        
    # if keywords are passed by user
    if keywords:
        # join keywords into regex string
        regex = "|".join(keywords)
        # filter only rows containing keywords passed
        lob_lobbying_notna = lob_lobbying.dropna(subset=['specificissue'])
        lob_lobbying = lob_lobbying_notna.loc[lob_lobbying_notna['specificissue'].str.contains(regex, regex=True)]
        

    return(lob_lobbying)

@st.cache
def format_graph_data(lob_df, minAmount, commonBills):
    """
    Given a pandas dataframe of cleaned/filtered lobbying data (returned from filter_spending), returns data formatted for graph diagram
    """

    lob_lobbying_group = lob_df[['ultorg', 'amount']].groupby(by='ultorg', as_index=False).agg({'amount': np.sum})
    
    #FIXME Minimum amount of money to be considered
    big_lobby = lob_lobbying_group[lob_lobbying_group['amount'] >= minAmount]

    filtered_lobbying = lob_df[lob_df['ultorg'].isin(big_lobby['ultorg'].tolist())]

    orgs = filtered_lobbying['ultorg'].unique()
    org_issue_dict = {}

    for org in orgs:
        org_lobbying = filtered_lobbying[filtered_lobbying['ultorg'] == org]
        org_issue_dict[org] = org_lobbying['b_id'].unique()


    rows_list = []

    for org in orgs:
        for org_issue in org_issue_dict.keys():
            weight = len([w for w in org_issue_dict[org_issue] if w in org_issue_dict[org]])
            
            # FIXME number of bills in common
            weight -= commonBills

            if weight > 0:
                source_amount = lob_lobbying_group[lob_lobbying_group['ultorg'] == org]
                row = [org, org_issue, weight,source_amount.iloc[0]['amount']]
                rows_list.append(row)
            else:
                continue

    graph_df = pd.DataFrame(rows_list, columns=['source', 'dest', 'weight', 'amount'])
    return(graph_df)



######## EXAMPLE CALL ##########

#lob_df = filter_spending(sector='Defense', date_min=2017, date_max=2020)
#graph_df = format_graph_data(lob_df, 1000)
#print(graph_df)