from event_manager import eventManager, triggerManager
from person_manager import personManager
from addr_manager import addrManager
from neo4j_manager import graph
from py2neo import Graph,Node,Relationship,cypher
from time_manager import timeManager
# from relation2type import getRelTypes
from page_rank import pageRank

import json
from word2vec import allEvents2Vec,allPerson2Vec,relationEmbedding
import threading
import time
import json

personManager.registEventManager(eventManager)

def putAllInToNeo4j():
	object2node = {}
	for times in range(0,10):
		has1 = eventManager.loadRelationEvents(LIMIT = 1000,SKIP = 1000*times, person_id=3767)   #person_id=3767 苏轼
		has2 = eventManager.loadPostOfficeEvents(LIMIT = 1000,SKIP = 1000*times, person_id=3767)
		has3 = eventManager.loadTextEvents(LIMIT = 1000,SKIP = 1000*times, person_id=3767)
		has4 = eventManager.loadEntryEvents(LIMIT = 1000,SKIP = 1000*times, person_id=3767)
		if not has1  and not has2 and not has3 and not has4:
			break

	# 有问题，内存不够
	for times in range(0,100):
		graph.run("MATCH (n:Person)-[r]-() WITH r LIMIT 10000 DELETE r")
		graph.run('MATCH (n:Event)-[r]-() WITH r LIMIT 10000 DELETE r')
		graph.run('MATCH (n:Place)-[r]-() WITH r LIMIT 10000 DELETE r')

		graph.run('MATCH (n:Place) WITH n LIMIT 10000 DELETE n')
		graph.run('MATCH (n:Event) WITH n LIMIT 10000 DELETE n')
		graph.run('MATCH (n:Person) WITH n LIMIT 10000 DELETE n')

	tx = graph._graph.begin()
	for event in eventManager.event_array:
		object2node[event] = graph.EventNode(event)
		tx.create(object2node[event])

	for addr in addrManager.addr_array:
		# print(addr)
		object2node[addr] = graph.AddrNode(addr)
		tx.create(object2node[addr])

	for  person in personManager.person_array:
		object2node[person] = graph.PersonNode(person)
		tx.create(object2node[person])


	for event in eventManager.event_array:
		event_node = object2node[event]
		for elm in event.roles:
			person_node = object2node[elm['person']]
			role = elm['role']
			relation = Relationship(event_node, 'TAKE_PART_IN', person_node)
			relation['role'] = role
			tx.create(relation)

		if event.addr is not None:
			addr = event.addr
			# print(addr, str(addr))
			addr_node = object2node[event.addr]
			relation = Relationship(event_node, 'IS_IN', addr_node)
			tx.create(relation)

	tx.commit()





def getPersonStory(person_id, limit_depth = 3, period_year = None):
	print('开始爬取所有相关数据')
	has_pull = set()
	need_pull = set()
	person2depth = {}

	person_id = str(person_id)
	start_person = personManager.getPerson(person_id)
	need_pull.add(start_person)
	person2depth[hash(start_person)] = 1

	all_events = set()

	while(len(need_pull)!=0):
		person = need_pull.pop()
		has_pull.add(person)
		print(str(person))

		now_depth = person2depth[hash(person)]
		person.getAllEvents()
		events = person.event_array
		for event in events:
			all_events.add(event)

			roles = event.roles
			for role in roles:
				related_person = role['person']
				hash_vale = hash(related_person)
				if hash_vale in person2depth:    #更新子节点的depth
					this_depth = person2depth[hash_vale]
					if this_depth>now_depth+1:
						person2depth[hash_vale] = now_depth+1
						if this_depth>limit_depth and now_depth+1<limit_depth:   #如果发现层数更近恢复
							has_pull.remove(related_person)
							need_pull.add(related_person)
				else:
					person2depth[hash_vale] = now_depth+1
					if now_depth<limit_depth and related_person not in has_pull:
						need_pull.add(related_person)
		print(len(has_pull))

	persons = {}
	events = {}
	addrs = {}
	for event in all_events:
		# 只留下有关的事件
		# 暂时只筛选了时间，还应该考虑人物等
		if period_year is not None:
			time_range = event.time_range
			if (time_range[0]>(period_year+2) or time_range[0]<(period_year-2)) and (time_range[1]>(period_year+2) or time_range[1]<(period_year-2)):
				continue

		events[event.id] = event.toDict()
		if event.addr is not None:
			addrs[event.addr.id] = event.addr.toDict()
		for role in event.roles:
			person = role['person']
			# print(person)
			persons[person.id] = person.toDict()

	print(len(persons.keys()))
	print(len(events.keys()))
	print(len(addrs.keys()))

	data = {
		'persons': persons,
		'events': events,
		'addr': addrs
	}

	open('./temp_data/{}.json'.format(person_id), 'w', encoding='utf-8').write(json.dumps(data, ensure_ascii = False))

eventManager.getAll()
# getPersonStory('1762', limit_depth=2, period_year = 1074)  	#王安石
# getPersonStory('3767', limit_depth=2, period_year = 1079) 	#苏轼
# getPersonStory('19713', limit_depth=4)				#你李清照
relationEmbedding(personManager)


# eventManager.getAll(get_times = 1000)
# pageRank()
# allEvents2Vec(personManager)
# allPerson2Vec(personManager)

# events = {}
# persons = {}
# addrs = {}
# # for event in eventManager.event_array:
# # 	events[event.id] = event.toDict()
# person2year = {}
# for person in personManager.person_array:
# 	personal_events = person.getSortedEvents()
# 	person2year[person.id] = set()
# 	for event in personal_events:
# 		events[event.id] = event.toDict()
# 		person2year[person.id].add(event.time_range[0])
# 	person2year[person.id] = list(person2year[person.id])

# 	# if len(personal_events)>10:
# 	# 	persons[person.id] = person.toDict()

# # for addr in addrManager.addr_array:
# # 	addrs[addr.id] = addr.toDict()

# results = {
# 	'event':  events,
# 	# 'person': persons,
# 	# 'addr': addrs
# }	
# open('./temp_data/total.json', 'w', encoding='utf-8').write(json.dumps(results, ensure_ascii = False))
# open('./temp_data/person2year.json', 'w', encoding='utf-8').write(json.dumps(person2year, ensure_ascii = False))

# data = open('./temp_data/total.json', 'r', encoding='utf-8').read()
# data = json.loads(data)
# year_count = {}
# for event in data['event']:
# 	event = data['event'][event]
# 	# print(event)
# 	time_range = event['time_range']
# 	for year in range(time_range[0],time_range[1]+1):
# 		if year in year_count.keys():
# 			year_count[year] += 1/(time_range[1]-time_range[0]+1)
# 		else:
# 			year_count[year] = 1/(time_range[1]-time_range[0]+1)
# open('./temp_data/时间事件数.json', 'w', encoding='utf-8').write(json.dumps(year_count, indent=5, ensure_ascii = False) )


# putAllInToNeo4j()
# getPersonStory(3767)

# t1 = threading.Thread(target=eventManager.loadRelationEvents, args=(1000, 1000*times, None))
# t2 = threading.Thread(target=eventManager.loadPostOfficeEvents, args=(1000, 1000*times, None))
# t3 = threading.Thread(target=eventManager.loadTextEvents, args=(1000, 1000*times, None))
# t4 = threading.Thread(target=eventManager.loadEntryEvents, args=(1000, 1000*times, None))
# t1.start()
# t2.start()
# t3.start()
# t4.start()
# t1.join()
# t2.join()
# t3.join()
# t4.join()


# print(len(eventManager.event_array))
# print(len(personManager.person_array))
# print(len(addrManager.addr_array))	

# allEvents2Vec(personManager)

# getPersonStory()



# for person in personManager.person_array:
# 	open('temp_data/people2events/'+str(person.id),'w',encoding='utf-8').write(person.allEvent2String())

# results = {}
# year2event = personManager.getPerson('3767').getYear2event()
# for  year in year2event.keys():
# 	year2event[year] = [event.toDict() for event in year2event[year]],

# open('./temp_data/苏轼.json', 'w', encoding='utf-8').write(json.dumps( year2event, indent=5, ensure_ascii = False))

# for times in range(0,10):
# 	eventManager.loadRelationEvents(LIMIT = 1000,SKIP = 1000*times, person_id='3767')


# print(timeManager.nian_hao)