import pandas as pd 
import numpy as np

#import dropbox
from contextlib import closing # this will correctly close the request
import io
import streamlit as st
import csv
from io import StringIO
import time

from sqlalchemy import create_engine

USERNAME = 'apatel31'
PG_STRING = 'postgresql://apatel31_demo_db_connection:3gjXR_RhCJXB3WHnriQ7qzLFqQD5C@db.bit.io?sslmode=prefer'


# establish dropbox connection
#dbx = dropbox.Dropbox('sl.BF3_ArVG9B5BJjsMdESYLtxs0mDWYFxG4metjhpjnArq4DFnkG966lMifPPNjKe2vC7oMchh2BpQsZSRgdoVZgt3u76oxvNNEdx6srzRYvTBoqVstTZtEdqZOAl-qETjy1TofCM')
##### Sector Options #######
"""['Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution']"""

# helper function to read dropbox files
# def stream_dropbox_file(path):
#     _,res=dbx.files_download(path)
#     with closing(res) as result:
#         byte_data=result.content
#         return io.BytesIO(byte_data)

sql_lob_lobbying = f'''
SELECT * FROM "{USERNAME}/OpenSecrets"."lob_lobbying";
'''
sql_lob_issue = f'''
SELECT * FROM "{USERNAME}/OpenSecrets"."lob_issue";
'''
sql_crp = f'''
SELECT * FROM "{USERNAME}/OpenSecrets"."crp_categories";
'''
sql_lob_bills = f'''
SELECT * FROM "{USERNAME}/OpenSecrets"."lob_bills";
'''


@st.cache
def filter_spending(sectors=False, keywords=False, date_min=False, date_max=False):
    """
    Given optional filter parameters, load and filter data to run through graph function.

    Sector: string, one of 18 sectors in dataset ex. 'Construction'
    Keywords: List of lowercase keywords ex. ['test', 'word']
    date_min: Year ex. 2019
    date_max: Year ex. 2021
    
    """
    engine = create_engine(PG_STRING)
    with engine.connect() as conn:
        conn.execute("SET statement_timeout = 600000;")
        lob_lobbying = pd.read_sql(sql_lob_lobbying, conn)
        lob_issue = pd.read_sql(sql_lob_issue, conn)
        industries = pd.read_sql(sql_crp, conn)
        lob_bills = pd.read_sql(sql_lob_bills, conn)

    # load lobbying transactions data
    #lob_lobbying = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_lobbying.txt'), names=['Uniqid', 'Registrant_raw','Registrant', 'Isfirm', 'Client_raw', 'Client', 'Ultorg', 'Amount', 'Catcode', 'Source', 'Self', 'IncludeNSFS', 'Use', 'Ind', 'Year', 'Type', 'Type_Long', 'Affiliate'], encoding='ISO-8859-1', low_memory=False)
    # only use rows marked as use (maybe only ind for unique payments?)
    lob_lobbying = lob_lobbying.loc[lob_lobbying['ind'] == 'y']
    #, ['Uniqid', 'Registrant', 'Client', 'Ultorg', 'Amount', 'Catcode', 'Use', 'Ind', 'Year', 'Type']

    # load issue data
    #lob_issue = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_issue.txt'), names=['SI_ID', 'Uniqid','IssueID', 'Issue','SpecificIssue', 'Year'], encoding='ISO-8859-1')
    # drop issues without descriptions
    #issue_notna = lob_issue.dropna(subset=["specificissue"]).copy()
    # make lowercase for standard searching
    #issue_notna.loc[:, 'specificissue'] = issue_notna['specificissue'].str.lower()
    # join in issues

    lob_lobbying = lob_lobbying.merge(lob_issue, 'left', on='uniqid').drop('year_y', axis=1).rename(columns={'year_x': 'year'})
    
    # if sector filter passed by user
    if sectors:
        # join in sector
        #industries = pd.read_csv(stream_dropbox_file('/OpenSecretsData/CRP_Categories.txt'), sep='\t')
        
        lob_lobbying = lob_lobbying.merge(industries, 'left', on='catcode')
        # include only selected sector
        lob_lobbying = lob_lobbying.loc[lob_lobbying['sector'].isin(sectors)]

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
        
    # load bills info data
    #lob_bills = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_bills.txt'), names=['B_ID', 'SI_ID','CongNo', 'Bill_Name'])
    # join in bills
    lob_lobbying  = pd.merge(lob_lobbying, lob_bills, on='si_id', how='left')

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