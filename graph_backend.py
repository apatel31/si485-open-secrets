import pandas as pd 
import numpy as np

import dropbox
from contextlib import closing # this will correctly close the request
import io
import streamlit as st

# establish dropbox connection
dbx = dropbox.Dropbox('sl.BF3_ArVG9B5BJjsMdESYLtxs0mDWYFxG4metjhpjnArq4DFnkG966lMifPPNjKe2vC7oMchh2BpQsZSRgdoVZgt3u76oxvNNEdx6srzRYvTBoqVstTZtEdqZOAl-qETjy1TofCM')
##### Sector Options #######
"""['Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution']"""

# helper function to read dropbox files
def stream_dropbox_file(path):
    _,res=dbx.files_download(path)
    with closing(res) as result:
        byte_data=result.content
        return io.BytesIO(byte_data)


@st.cache
def filter_spending(sectors=False, keywords=False, date_min=False, date_max=False):
    """
    Given optional filter parameters, load and filter data to run through graph function.

    Sector: string, one of 18 sectors in dataset ex. 'Construction'
    Keywords: List of lowercase keywords ex. ['test', 'word']
    date_min: Year ex. 2019
    date_max: Year ex. 2021
    
    """


    # load lobbying transactions data
    lob_lobbying = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_lobbying.txt'), names=['Uniqid', 'Registrant_raw','Registrant', 'Isfirm', 'Client_raw', 'Client', 'Ultorg', 'Amount', 'Catcode', 'Source', 'Self', 'IncludeNSFS', 'Use', 'Ind', 'Year', 'Type', 'Type_Long', 'Affiliate'], encoding='ISO-8859-1', low_memory=False)
    # only use rows marked as use (maybe only ind for unique payments?)
    lob_lobbying = lob_lobbying.loc[lob_lobbying['Ind'] == 'y', ['Uniqid', 'Registrant', 'Client', 'Ultorg', 'Amount', 'Catcode', 'Use', 'Ind', 'Year', 'Type']]

    # load issue data
    lob_issue = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_issue.txt'), names=['SI_ID', 'Uniqid','IssueID', 'Issue','SpecificIssue', 'Year'], encoding='ISO-8859-1')
    # drop issues without descriptions
    issue_notna = lob_issue.dropna(subset=["SpecificIssue"]).copy()
    # make lowercase for standard searching
    issue_notna.loc[:, 'SpecificIssue'] = issue_notna['SpecificIssue'].str.lower()
    # join in issues
    lob_lobbying = lob_lobbying.merge(issue_notna, 'left', on='Uniqid').drop('Year_y', axis=1).rename(columns={'Year_x': 'Year'})
    
    # if sector filter passed by user
    if sectors:
        # join in sector
        industries = pd.read_csv(stream_dropbox_file('/OpenSecretsData/CRP_Categories.txt'), sep='\t')
        
        lob_lobbying = lob_lobbying.merge(industries, 'left', on='Catcode')
        # include only selected sector
        lob_lobbying = lob_lobbying.loc[lob_lobbying['Sector'].isin(sectors)]

    # if date filter is passed by user
    if date_min:
        # apply date range
        lob_lobbying = lob_lobbying.loc[(lob_lobbying['Year'] >= date_min) & (lob_lobbying['Year'] <= date_max)]
        
    # if keywords are passed by user
    if keywords:
        # join keywords into regex string
        regex = "|".join(keywords)
        # filter only rows containing keywords passed
        lob_lobbying_notna = lob_lobbying.dropna(subset=['SpecificIssue'])
        lob_lobbying = lob_lobbying_notna.loc[lob_lobbying_notna['SpecificIssue'].str.contains(regex, regex=True)]
        
    # load bills info data
    lob_bills = pd.read_csv(stream_dropbox_file('/OpenSecretsData/lob_bills.txt'), names=['B_ID', 'SI_ID','CongNo', 'Bill_Name'])
    # join in bills
    lob_lobbying  = pd.merge(lob_lobbying, lob_bills, on='SI_ID', how='left')

    return(lob_lobbying)

@st.cache
def format_graph_data(lob_df, minAmount, commonBills):
    """
    Given a pandas dataframe of cleaned/filtered lobbying data (returned from filter_spending), returns data formatted for graph diagram
    """

    lob_lobbying_group = lob_df[['Ultorg', 'Amount']].groupby(by='Ultorg', as_index=False).agg({'Amount': np.sum})
    
    #FIXME Minimum amount of money to be considered
    big_lobby = lob_lobbying_group[lob_lobbying_group['Amount'] >= minAmount]

    filtered_lobbying = lob_df[lob_df['Ultorg'].isin(big_lobby['Ultorg'].tolist())]

    orgs = filtered_lobbying['Ultorg'].unique()
    org_issue_dict = {}

    for org in orgs:
        org_lobbying = filtered_lobbying[filtered_lobbying['Ultorg'] == org]
        org_issue_dict[org] = org_lobbying['B_ID'].unique()


    rows_list = []

    for org in orgs:
        for org_issue in org_issue_dict.keys():
            weight = len([w for w in org_issue_dict[org_issue] if w in org_issue_dict[org]])
            
            # FIXME number of bills in common
            weight -= commonBills

            if weight > 0:
                source_amount = lob_lobbying_group[lob_lobbying_group['Ultorg'] == org]
                row = [org, org_issue, weight,source_amount.iloc[0]['Amount']]
                rows_list.append(row)
            else:
                continue

    graph_df = pd.DataFrame(rows_list, columns=['source', 'dest', 'weight', 'amount'])
    return(graph_df)



######## EXAMPLE CALL ##########

#lob_df = filter_spending(sector='Defense', date_min=2017, date_max=2020)
#graph_df = format_graph_data(lob_df, 1000)
#print(graph_df)