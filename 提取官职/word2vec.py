# -*- coding: UTF-8 -*- 
import gensim
from multiprocessing import cpu_count
import jieba
import re
from opencc import OpenCC 
import json

cc = OpenCC('t2s') 


office_text = cc.convert(open('宋代詞人職官和擔任年份.json', 'r', encoding='utf-8').read()).strip('\n').split('\n')[1:]
offices = []
for row in office_text:
	row = row.split('\t')
	offices.append(row[4])
	offices.append(row[5])
# print(offices)

mydict = cc.convert(open('mydict.txt', 'r', encoding='utf-8').read()).strip('\n').split('\n')
for word in mydict:
    jieba.suggest_freq(word, True)

stop_words = open('chinese-stopword', 'r', encoding='utf-8').read().strip('\n').split('\n')
stop_words = set(stop_words)

ping_words =['正一品','从一品','正二品','从二品','正三品','从三品','正四品上','正四品','正四品下','从四品上','从四品下','正五品上','正五品下','从五品上','从四品','从五品下','正六品上','正五品','正六品下','从五品','从六品上','正六品','从六品下','正七品上','正七品下','正八品下','正八品上','从八品下','从八品上','正九品下','从九品上','真九品下','从九品下']
for word in ping_words:
    jieba.suggest_freq(word, True)
seg_list = jieba.cut('宋朝淑妃属夫人阶,四妃之一,正一品')
print(list(seg_list))
sentences = cc.convert(open('词典纯文本Unicode.txt', 'r', encoding='utf-8').read()).strip('\n').replace('\n\n','\n。').replace('\n','').split('。')


# sentences = [re.sub("[0-9,a-z,A-Z,，.，、,？,|,<,>,‘,’,.,《,》,“,”,,①,·,、,«,»,,,),…,:,③,②,①,④,【,】,+,=,!,/,;,-,一]", " ", sentence) for sentence in sentences]
# print(sentences)

text_croups = []
for sentence in sentences:
	# print(sentences)
	seg_list = jieba.cut(sentence, cut_all=True)
	seg_list = [word for word in seg_list if word!='' and word != ' ' and word not in stop_words]
	# print(seg_list)
	text_croups.append(seg_list)
model = gensim.models.Word2Vec(text_croups, workers=cpu_count(), window=10, min_count=1, size=100)



# 输出向量
fvec = open("vec","w",encoding='utf-8')
for key in model.wv.vocab:
    fvec.writelines("\t".join([str(elm) for elm in model.wv[key] ])+"\n")
fvec.close()

counts = {}
fs = open('所有分词.txt', 'w', encoding='utf-8')
for sentence in text_croups:
	for word in sentence:
	    if word in counts:
	        counts[word] += 1
	    else:
	        counts[word] = 1
	fs.write(' '.join(sentence) + '\n')

fmetia = open("meta","w",encoding='utf-8')
fmetia.writelines("word\tcount\n")
for key in model.wv.vocab:
    fmetia.writelines(key + '\t' + str(counts[key]) + '\n')

offices2score = {}
remain = []
key_set = set(model.wv.vocab)
ping_words = [word  for word in ping_words if word in key_set]
print(ping_words)
for office in offices:
	if len(office)>10:
		continue
	if office in key_set:
		max_prob_score = ping_words[0]
		max_sim = model.similarity(office, ping_words[0])
		for word in ping_words[1:]:
			sim = model.similarity(office, word)
			if sim>max_sim:
				max_sim = sim
				max_prob_score = word
		offices2score[office] = {'品级': max_prob_score, '可能性': str(max_sim)}
	else:
		remain.append(office)
remain = list(set(remain))


open('./官职品级.json', 'w', encoding='utf-8').write(json.dumps(offices2score, indent=5, ensure_ascii = False) )
open('./未详官职品级.json', 'w', encoding='utf-8').write(json.dumps({'data': remain}, indent=5, ensure_ascii = False) )
print('成功！')