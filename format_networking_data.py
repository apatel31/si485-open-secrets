import pandas as pd 
import numpy as np

lob_lobbying = pd.read_csv('Data/Lobby/lob_lobbying.txt', names=['Uniqid', 'Registrant_raw','Registrant', 'Isfirm', 'Client_raw', 'Client', 'Ultorg', 'Amount', 'Catcode', 'Source', 'Self', 'IncludeNSFS', 'Use', 'Ind', 'Year', 'Type', 'Type_Long', 'Affiliate'], encoding='ISO-8859-1')

lob_lobbying_group = lob_lobbying[['Ultorg', 'Amount']].groupby(by='Ultorg', as_index=False).agg({'Amount': np.sum})
big_lobby = lob_lobbying_group[lob_lobbying_group['Amount'] >= 200000000]

filtered_lobbying = lob_lobbying[lob_lobbying['Ultorg'].isin(big_lobby['Ultorg'].tolist())]

lob_issue = pd.read_csv('./Data/Lobby/lob_issue.txt', names=['SI_ID', 'Uniqid','IssueID', 'Issue','SpecificIssue', 'Year'], encoding='ISO-8859-1')
lob_bills = pd.read_csv('./Data/Lobby/lob_bills.txt', names=['B_ID', 'SI_ID','CongNo', 'Bill_Name'])

lob_lobbying_issues = pd.merge(filtered_lobbying, lob_issue, on='Uniqid', how='inner')
lob_lobbying_issues = pd.merge(lob_lobbying_issues, lob_bills, on='SI_ID', how='inner')

orgs = lob_lobbying_issues['Ultorg'].unique()
org_issue_dict = {}

for org in orgs:
    org_lobbying = lob_lobbying_issues[lob_lobbying_issues['Ultorg'] == org]
    org_issue_dict[org] = org_lobbying['B_ID'].unique()


rows_list = []

for org in orgs:
    for org_issue in org_issue_dict.keys():
        weight = len([w for w in org_issue_dict[org_issue] if w in org_issue_dict[org]])
        weight -= 250
        if weight > 0:
            source_amount = lob_lobbying_group[lob_lobbying_group['Ultorg'] == org]
            row = [org, org_issue, weight,source_amount.iloc[0]['Amount']]
            rows_list.append(row)
        else:
            continue

df = pd.DataFrame(rows_list, columns=['source', 'dest', 'weight', 'amount'])
df.to_csv('lobbying_network_sample.csv')


