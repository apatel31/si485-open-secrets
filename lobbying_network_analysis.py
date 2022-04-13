# import sys
# sys.path.append('/opt/homebrew/lib/python3.9/site-packages')
# sys.executable
from pyvis import Network
import networkx as nx
import pandas as pd


lobby_net = Network(height='750px', width='100%', bgcolor='black', font_color='white')

# set the physics layout of the network
lobby_net.barnes_hut()
lobby_data = pd.read_csv('lobbying_network_sample.csv')

sources = lobby_data['source']
targets = lobby_data['dest']
weights = lobby_data['weight']
amounts = lobby_data['amount']

edge_data = zip(sources, targets, weights, amounts)

for e in edge_data:
    src = e[0]
    dst = e[1]
    w = e[2]
    amnt = e[3]

    lobby_net.add_node(src, src, title=src, size=amnt)
    lobby_net.add_node(dst, dst, title=dst, size=amnt)
    lobby_net.add_edge(src, dst, value=w)

neighbor_map = lobby_net.get_adj_list()

# add neighbor data to node hover data
for node in lobby_net.nodes:
    node['title'] += ' Neighbors:<br>' + '<br>'.join(neighbor_map[node['id']])
    node['value'] = len(neighbor_map[node['id']])

lobby_net.show_buttons(filter_=['physics'])
lobby_net.show('lobbying_network_sample.html')

network_info = nx.info(lobby_net)
