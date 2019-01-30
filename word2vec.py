# -*- coding: UTF-8 -*- 
import gensim
from multiprocessing import cpu_count
# import jieba
import re
# from snownlp import SnowNLP
import json

    # 尝试使用word2vec做event2vec
def allEvents2Vec(personManager):
    print('开始训练模型')
    person_array = personManager.person_array
    # 还要按时间进行排序
    events_cropus = []
    all_events = []

    # for person in person_array:
    #     year2event =  person.getYear2event()
    #     for year in year2event.keys():
    #         sort_events = year2event[year]
    #         life_events = []
    #         for event in sort_events:
    #             roles = event.roles
    #             for role in roles:
    #                 if role['person'] == person:
    #                     life_events.append(event.trigger.name + ' ' + role['role'])
    #                     all_events.append(event.trigger.name + ' ' + role['role'])           
    #         events_cropus.append(life_events)

    for person in person_array:
        sort_events = person.getSortedEvents()
        life_events = []

        index = 0
        for event in sort_events:
            if index>1:
                if event.time_range[1] - sort_events[index-1].time_range[0] > 5:
                    events_cropus.append(life_events)
                    life_events = []
                index += 1
            roles = event.roles
            for role in roles:
                if role['person'] == person:
                    life_events.append(event.trigger.name + ' ' + role['role'])
                    all_events.append(event.trigger.name + ' ' + role['role'])
        # life_events = [event.trigger.name for event in sort_events]
        events_cropus.append(life_events)

    print('数据加载完成')
    model = gensim.models.Word2Vec(events_cropus, workers=cpu_count(), window=5, min_count=1, size=1)

    def predict(object):
        print(object + '\n')
        for i in model.most_similar(object):
            print(i[0],i[1])
        print('\n')

    # predict("水")
    # predict("思")
    # predict("媚")
    model.save("./temp_data/Word2Vec_event.model")

    # 输出向量
    fvec = open("./temp_data/event_vec","w",encoding='utf-8')
    for key in model.wv.vocab:
        fvec.writelines("\t".join([str(elm) for elm in model.wv[key] ])+"\n")
    fvec.close()

    counts = {}
    for event in all_events:
        if event in counts.keys():
            counts[event] += 1
        else:
            counts[event] = 1

    fmetia = open("./temp_data/event_meta","w",encoding='utf-8')
    fmetia.writelines("word\tcount\n")
    for key in model.wv.vocab:
        fmetia.writelines(key + '\t' + str(counts[key]) + '\n')
    fmetia.close()


    event2vec = {}
    for key in model.wv.vocab:
    	event2vec[key] = str(model.wv[key][0])

    open('./temp_data/event2vec.json', 'w', encoding='utf-8').write(json.dumps(event2vec, indent=4, ensure_ascii = False))


def allPerson2Vec(personManager):
    print('开始训练模型')
    person_array = personManager.person_array
    # 还要按时间进行排序
    events_cropus = []
    all_events = []
    for person in person_array:
        sort_events = person.getSortedEvents()
        persons = []
        for event in sort_events:
            roles = event.roles
            for role in roles:
                persons.append(role['person'].id)
                all_events.append(role['person'].id)

        events_cropus.append(persons)
            
    # print(sentences)

    print('数据加载完成')
    model = gensim.models.Word2Vec(events_cropus, workers=cpu_count(), window=5, min_count=1, size=1)

    def predict(object):
        print(object + '\n')
        for i in model.most_similar(object):
            print(i[0],i[1])
        print('\n')

    # predict("水")
    model.save("./temp_data/Word2Vec_event.model")

    # 输出向量
    fvec = open("./temp_data/person_vec","w",encoding='utf-8')
    for key in model.wv.vocab:
        fvec.writelines("\t".join([str(elm) for elm in model.wv[key] ])+"\n")
    fvec.close()

    counts = {}
    for event in all_events:
        if event in counts.keys():
            counts[event] += 1
        else:
            counts[event] = 1

    fmetia = open("./temp_data/person_meta","w",encoding='utf-8')
    fmetia.writelines("word\tcount\tname\tbirth_year\tdeath_year\n")
    for key in model.wv.vocab:
        person = personManager.getPerson(key)
        fmetia.writelines(key + '\t' + str(counts[key]) +  '\t' + str(person.name) + '\t' + str(person.birth_year) + '\t' + str(person.death_year) + '\n')
    fmetia.close()


    event2vec = {}
    for key in model.wv.vocab:
        event2vec[key] = str(model.wv[key][0])

    open('./temp_data/person2vec.json', 'w', encoding='utf-8').write(json.dumps(event2vec, indent=4, ensure_ascii = False))


def pairHash(person1, person2):
    return (person1, person2)
    if person1.id < person2.id:
        return (person1, person2)
    else:
        return (person2, person1)

# 两两之间关系的embedding
def relationEmbedding(personManager):
    persons = personManager.person_array
    relation_set = {}
    for person in persons:
        events = person.getAllEvents()
        for event in events:
            roles  = event.roles
            if len(roles)!=2:
                continue
            
            main_role = None
            opp_role = None
            opp_person = None
            for role in roles:
                this_person = role['person']
                role = role['role']
                if this_person==person:
                    main_role = role
                else:
                    opp_role = role
                    opp_person = this_person

            hash_pair = pairHash(person, opp_person)
            if hash_pair not in relation_set:
                relation_set[hash_pair] = []
            relation_set[hash_pair].append( str(main_role) + '/' + str(event.trigger.name) + '/' + str(opp_role) )

    fs = open("./temp_data/data","w",encoding='utf-8')
    sentences = []
    for key in relation_set:
        events = relation_set[key]
        events = list(events)
        if len(events)>=2:
            sentences.append(events)
            fs.write(',  '.join(events)+'\n')

    # print(sentences)

    print('数据加载完成')
    model = gensim.models.Word2Vec(sentences, workers=cpu_count(), window=3, min_count=100, size=100)

    # 输出向量
    fvec = open("./temp_data/relation_vec","w",encoding='utf-8')
    for key in model.wv.vocab:
        fvec.writelines("\t".join([str(elm) for elm in model.wv[key] ])+"\n")
    fvec.close()

    fmetia = open("./temp_data/relation_meta","w",encoding='utf-8')
    # fmetia.writelines("word\n")
    for key in model.wv.vocab:
        fmetia.writelines(key + '\n')
    fmetia.close()


    event2vec = {}
    for key in model.wv.vocab:
        event2vec[key] = {
            'vec':str(model.wv[key]),
            'most_similars': getSim(key)
        }
    open('./temp_data/relationEmbedding.json', 'w', encoding='utf-8').write(json.dumps(event2vec, indent=4, ensure_ascii = False))
    print('训练完成')

def getSim(object, num = 5):
    most_similars = []
    for i in model.most_similar(object):
        # print(i[0],i[1])
        item = i[0].split('/')
        most_similars.append({
            'main_role': item[0],
            'events': item[1],
            'opp_role': item[2],
            'sim': float(i[1])
        })

    return sorted(most_similars, key=lambda item: item['sim'])[0:num]
