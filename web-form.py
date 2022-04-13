from re import sub
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
from functools import reduce

st.title("OpenSecrets Graph Analyzer Tool")
st.subheader("Select what you want to look for")
st.text('Description of how to use the tool here')

with st.form("graphForm", clear_on_submit=False):
    todays_date = date.today()
    dateRange = st.slider("Time Range", min_value=1985, max_value=todays_date.year, value=(2010,2015))
    # find the earliest year in the dataframe and replace 1985 with it. 
    industryOrTopic = st.multiselect("Chosen Sectors", [
        'Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution'
    ], None)
    keywords = st.text_input("Type Keywords Here (separated by spaces)")
    listOfKeywords = []
    if keywords:
        listOfKeywords = keywords.split()
    dollarThreshold = st.slider("$ Threshold for Relevance", 0, 100000, 10000)
    commonBills = st.number_input('Number of bills in common', value=1, min_value=1)
    analysisTopics = st.multiselect("Choose Analysis Methods", (
        'degree_centrality', 'eigenvector_centrality', 'closeness_centrality', 'betweenness_centrality'
    ))
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
if submit:
    # Code for filtering dataframe and generating network
    lob_df = filter_spending(sectors=industryOrTopic, keywords=listOfKeywords, date_min=dateRange[0], date_max=dateRange[1])
    graph_df = format_graph_data(lob_df, minAmount=dollarThreshold, commonBills=commonBills)
    # st.write(graph_df.to_string())
    lobby_net = Network(height='1000px', width='100%', bgcolor='black', font_color='white')
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

    # Load KPIs and Dashboard with Visuals

    st.subheader('Graph Characteristics')

    col1, col2, col3 = st.columns(3)
    col1.metric("Density", round(nx.density(G),2))
    col2.metric("Number of Nodes", nx.number_of_nodes(G))
    col3.metric("Number of Edges", nx.number_of_edges(G))

    degree_freq_data = pd.DataFrame(
     nx.degree_histogram(G),
     columns=["Frequency of Degree Values"])

    st.bar_chart(degree_freq_data)

    # Form exportable data

    df_list = []

    for topic in analysisTopics:
        if topic == 'degree_centrality':
            degree_centrality_df = pd.DataFrame(nx.degree_centrality(G).items(), columns=['Org', 'degree_centrality'])
            df_list.append(degree_centrality_df)
        if topic == 'eigenvector_centrality':
            eigenvector_centrality_df = pd.DataFrame(nx.eigenvector_centrality(G).items(), columns=['Org', 'eigenvector_centrality'])
            df_list.append(eigenvector_centrality_df)
        if topic == 'closeness_centrality':
            closeness_centrality_df = pd.DataFrame(nx.closeness_centrality(G).items(), columns=['Org', 'closeness_centrality'])
            df_list.append(closeness_centrality_df)
        if topic == 'betweenness_centrality':
            betweenness_centrality_df = pd.DataFrame(nx.betweenness_centrality(G).items(), columns=['Org', 'betweenness_centrality'])
            df_list.append(betweenness_centrality_df)

    df_final = reduce(lambda left,right: pd.merge(left,right,on='Org'), df_list)

    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(df_final)

    def callback():
        st.balloons()

    st.dataframe(df_final)
    st.download_button(
        label="Download analysis data as CSV",
        data=csv,
        file_name='analysis_data.csv',
        mime='text/csv',
        on_click=callback,
        key='callback'
    )




# to do:
# how to host this online
# loading widget while graph is being generated?
# show message if nothing in graph?
# remove links back to themselves for nodes
# make bills in common never go below 1

