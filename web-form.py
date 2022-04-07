import streamlit as st
import datetime as datetime
import json
import pandas as pd 
import numpy as np
from graph_backend import *
from datetime import date, time
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.title("OpenSecrets Graph Analyzer Tool")
st.subheader("Select what you want to look for")
st.text('Description of how to use the tool here')



with st.form("graphForm", clear_on_submit=False):
    todays_date = date.today()
    dateRange = st.slider("Time Range", min_value=1985, max_value=todays_date.year, value=(2010,2015))
    # find the earliest year in the dataframe and replace 1985 with it. 
    industryOrTopic = st.selectbox("Chosen Sector", (
        'None','Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution'
    ), index=0)
    keywords = st.text_input("Type Keywords Here (separated by spaces)")
    listOfKeywords = []
    if keywords:
        listOfKeywords = keywords.split()
    dollarThreshold = st.slider("$ Threshold for Relevance", 0, 100000, 10000)
    commonBills = st.number_input('Number of bills in common', value=1)
    submit = st.form_submit_button("Submit")


#st.write(dateRange[0])
#st.write("" + json.dumps(jsonObj))



# streamlit agraph component for visualizing the network a la lobbying_network_analysis
# after getting the dataframe from graph_backend
# https://blog.streamlit.io/the-streamlit-agraph-component/


# Set info message on initial site load
if industryOrTopic == 'None':
   st.text('Select a Sector to Get Started')
# Create network graph when user selects a sector
else:
   # Code for filtering dataframe and generating network
    lob_df = filter_spending(sector=industryOrTopic, keywords=listOfKeywords, date_min=dateRange[0], date_max=dateRange[1])
    graph_df = format_graph_data(lob_df, minAmount=dollarThreshold, commonBills=commonBills)
    # st.write(graph_df.to_string())
    lobby_net = Network(height='750px', width='100%', bgcolor='white', font_color='black')
    G = nx.from_pandas_edgelist(graph_df, 'source', 'dest', 'weight')
    lobby_net.from_nx(G)
    # Generate network with specific layout settings
    lobby_net.repulsion(node_distance=420, central_gravity=0.33,
                       spring_length=110, spring_strength=0.10,
                       damping=0.95)
    # Save and read graph as HTML file (on Streamlit Sharing)
    try:
        path = '/tmp'
        lobby_net.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Save and read graph as HTML file (locally)
    except:
        path = './html_files'
        lobby_net.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Load HTML file in HTML component for display on Streamlit page
    components.html(HtmlFile.read(), height=435)

# to do:
# how to host this online
# loading widget while graph is being generated?
# show message if nothing in graph?
# remove links back to themselves for nodes
# make bills in common never go below 1

