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
import plost
import scipy as sp

st.set_page_config(layout="wide")

st.title("OpenSecrets Graph Tool")
st.subheader("Select what you want to look for")
st.text('Once you select filters and hit submit, there will be a graph generated where each node represents a lobbying organization and an edge represents the number of common bills lobbied for.')

with st.form("graphForm", clear_on_submit=False):
    todays_date = date.today()
    dateRange = st.slider("Time Range", min_value=2010, max_value=todays_date.year, value=(2010,2015))
    # find the earliest year in the dataframe and replace 1985 with it. 
    industryOrTopic = st.multiselect("Chosen Sectors", [
        'Agribusiness', 'Construction', 'Communic/Electronics', 'Defense',
       'Energy/Nat Resource', 'Finance/Insur/RealEst', 'Misc Business',
       'Health', 'Other', 'Ideology/Single-Issue', 'Lawyers & Lobbyists',
       'Labor', 'Transportation', 'Unknown', 'Joint Candidate Cmtes',
       'Party Cmte', 'Candidate', 'Non-contribution'
    ], None)
    # keywords = st.text_input("Type Keywords Here (separated by spaces)")
    # listOfKeywords = []
    # if keywords:
    #     listOfKeywords = keywords.split()
    dollarThreshold = st.slider("$ Threshold for Relevance", 0, 1000000, 10000)
    commonBills = st.number_input('Number of bills in common', value=1, min_value=1)
    analysisTopics = st.multiselect("Choose Analysis Methods", (
        'Average Neighbor Degree', 'Degree Centrality', 'Eigenvector Centrality', 'Closeness Centrality', 'PageRank'
    ))
    submit = st.form_submit_button("Submit")


#st.write(dateRange[0])
#st.write("" + json.dumps(jsonObj))


# streamlit agraph component for visualizing the network a la lobbying_network_analysis
# after getting the dataframe from graph_backend
# https://blog.streamlit.io/the-streamlit-agraph-component/
with st.spinner('Wait for it...'):

    # Set info message on initial site load
    if industryOrTopic == 'None':
        st.text('Select a Sector to Get Started')
    # Create network graph when user selects a sector
    if submit:
        # Code for filtering dataframe and generating network
        lob_df = filter_spending(sectors=industryOrTopic, keywords=None, date_min=dateRange[0], date_max=dateRange[1])
        graph_df = format_graph_data(lob_df, minAmount=dollarThreshold, commonBills=commonBills)
        # st.write(graph_df.to_string())
        lobby_net = Network(height='1000px', width='100%', bgcolor='white', font_color='black')
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
        st.success('Done!')
        components.html(HtmlFile.read(), height=435)

        # Load KPIs and Dashboard with Visuals

        st.subheader('Graph Characteristics')

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Density", round(nx.density(G),2))
        col2.metric("Clustering Coefficient", round(nx.average_clustering(G),2))
        col3.metric("Number of Nodes", nx.number_of_nodes(G))
        col4.metric("Number of Edges", nx.number_of_edges(G))
        #col2.metric("Small World Coefficient", round(nx.sigma(G), 2))
        #col2.metric("Diameter", round(nx.diameter(G), 2))

        # st.write(nx.voterank(G))

        degree_freq_data = pd.DataFrame(
        nx.degree_histogram(G),
        columns=["Frequency of Degree Values"])

        plost.hist(
            data=degree_freq_data,
            x='Frequency of Degree Values',
            aggregate='count')

        # Form exportable data

        df_list = []

        for topic in analysisTopics:
            if topic == 'Average Neighbor Degree':
                degree_df = pd.DataFrame(nx.average_neighbor_degree(G).items(), columns=['Org', 'average_neighbor_degree'])
                df_list.append(degree_df)

                top_5_degree = degree_df.sort_values(by=['average_neighbor_degree'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by Average Neighbor Degree")
                st.table(top_5_degree)
                
            if topic == 'Degree Centrality':

                degree_centrality_df = pd.DataFrame(nx.degree_centrality(G).items(), columns=['Org', 'degree_centrality'])
                df_list.append(degree_centrality_df)

                top_5_degree_centrality = degree_centrality_df.sort_values(by=['degree_centrality'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by Degree Centrality")
                st.table(top_5_degree_centrality)

            if topic == 'Eigenvector Centrality':

                eigenvector_centrality_df = pd.DataFrame(nx.eigenvector_centrality(G).items(), columns=['Org', 'eigenvector_centrality'])
                df_list.append(eigenvector_centrality_df)

                top_5_eigenvector_centrality = eigenvector_centrality_df.sort_values(by=['eigenvector_centrality'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by Eigenvector Centrality")
                st.table(top_5_eigenvector_centrality)

            if topic == 'Closeness Centrality':

                closeness_centrality_df = pd.DataFrame(nx.closeness_centrality(G).items(), columns=['Org', 'closeness_centrality'])
                df_list.append(closeness_centrality_df)

                top_5_closeness_centrality = closeness_centrality_df.sort_values(by=['closeness_centrality'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by Closeness Centrality")
                st.table(top_5_closeness_centrality)

            if topic == 'Betweenness Centrality':

                betweenness_centrality_df = pd.DataFrame(nx.betweenness_centrality(G).items(), columns=['Org', 'betweenness_centrality'])
                df_list.append(betweenness_centrality_df)

                top_5_betweenness_centrality = betweenness_centrality_df.sort_values(by=['betweenness_centrality'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by Betweenness Centrality")
                st.table(top_5_betweenness_centrality)

            if topic == 'PageRank':

                pagerank_df = pd.DataFrame(nx.pagerank(G).items(), columns=['Org', 'pagerank'])
                df_list.append(pagerank_df)

                top_5_pagerank = pagerank_df.sort_values(by=['pagerank'], ascending=False).head(5)

                st.subheader("Top 5 Orgs by PageRank")
                st.table(top_5_pagerank)

        df_final = reduce(lambda left,right: pd.merge(left,right,on='Org'), df_list)
        print(df_final.head())

        if all(x in analysisTopics for x in ['PageRank','Degree Centrality']):
            plost.xy_hist(
                data=df_final,
                x='pagerank',
                y='degree_centrality',
                x_bin=dict(maxbins=20),
                y_bin=dict(maxbins=20),
                height=400,
            )
        
        @st.cache
        def convert_df(df):
            # IMPORTANT: Cache the conversion to prevent computation on every rerun
            return df.to_csv().encode('utf-8')

        csv = convert_df(df_final)

        def callback():
            st.balloons()

        st.subheader("Downloadable Network Analysis Data")

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

