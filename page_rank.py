from db_manager import dbManager as db
from neo4j_manager import graph
from event_manager import eventManager, triggerManager
from person_manager import personManager
from relation2type import getEventScore
import json
import networkx as nx 
# import matplotlib.pyplot as plt 

def pageRank():
	event_array = eventManager.event_array
	G = nx.DiGraph()
	for event in event_array:
		score = getEventScore(event)
		roles = event.roles
		if len(roles)==1:
			node_id = roles[0]['person'].id
			G.add_node(node_id)
			G.add_weighted_edges_from([(node_id, node_id, score)])
		else:
			from_node = None
			to_node = None
			for elm in roles:
				person = elm['person']
				role = elm['role']
				if role == '主角':
					from_node = person.id
				else:
					to_node = person.id
			if from_node is not None and to_node is not None:
				G.add_node(from_node)
				G.add_node(to_node)
				G.add_weighted_edges_from([(from_node, to_node, score)])
			else:
				# print('Error:没有凑齐一对节点')
				print(str(event))
	pr=nx.pagerank(G, weight='weight')
	person_rank = {}
	for person_id in pr:
		person_name = personManager.getPerson(person_id).name
		person_rank[person_name] = pr[person_id]
	open('./temp_data/pageRank.json', 'w', encoding='utf-8').write(json.dumps(person_rank, indent=3, ensure_ascii = False) )

