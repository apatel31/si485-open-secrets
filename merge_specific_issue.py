import pandas as pd

lob_lobbying = pd.read_csv('./Data/lob_lobbying_issues.csv')
lob_issues = pd.read_csv('./Data/lob_issue.txt', names=['si_id', 'Uniqid','IssueID', 'Issue','SpecificIssue', 'Year'], encoding='ISO-8859-1')

lob_merge = pd.merge(lob_lobbying, lob_issues, on='si_id', how='left')
lob_merge.to_csv('lobbying_master.csv')