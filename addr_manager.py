from re import match
from db_manager import dbManager as db
from neo4j_manager import graph

class AddrManager(object):
	"""docstring for AddrManager"""
	def __init__(self):
		self.id2addr = {}
		self.addr_id_set = set()
		self.addr_array = []
		# 加载CBDB上的所有地址
		addr_data = graph.run('MATCH (n:Addr_codes) RETURN id(n), n').data()
		for data in addr_data:
			addr_node = data['n']
			self.createAddr(addr_node)

		addr_belong_data = graph.run('MATCH (n1:Addr_codes)-->(:Addr_belongs_data)-->(n2:Addr_codes) RETURN n1.c_addr_id as son_id, n2.c_addr_id as parent_id').data()
		for data in addr_belong_data:
			son_id = data['son_id']
			parent_id = data['parent_id']
			son = self.getAddr(son_id)
			parent = self.getAddr(parent_id)

			parent.addSon(son)
			son.addParent(parent)

		# 加载所有的地点关系的树形结构

		print('加载地址')

	def createAddr(self, addr_node):
		addr_id = addr_node['c_addr_id']
		if addr_id not in self.addr_id_set:
			self.id2addr[addr_id] = Addr(addr_node)
			self.addr_id_set.add(addr_id)
			self.addr_array.append(self.id2addr[addr_id])
		return self.id2addr[addr_id]

	def getXY(self, addr):
		return []

	def getAddr(self, addr):
		if match('[0-9]+', str(addr)):  #如果是'c_addr_id'
			if addr in self.id2addr.keys():
				return self.id2addr[addr]
		print('ERROR:没有找到地址', addr)
		return None
		# 如果是名字,需要遍历


class Addr(object):
	"""docstring for Addr"""
	def __init__(self, addr_node):
		self.id = addr_node['c_addr_id']
		self.name = addr_node['c_name_chn']

		self.first_year = addr_node['c_firstyear']
		self.last_year = addr_node['c_lastyear']

		self.x = addr_node['x_coord']
		self.y = addr_node['y_coord']

		self.notes = addr_node['c_notes']
		self.alt_names = addr_node['c_alt_names']

		self.parents = []
		self.sons = []

		self.time_range = [-9999,9999]

		if self.first_year is not None and self.first_year!=0 and self.first_year!='0' and self.first_year!='None':
			year = int(self.first_year)
			self.time_range[0] = year
		else:
			self.first_year = self.time_range[0]
		if self.last_year is not None and self.last_year!=0 and self.last_year!='0' and self.last_year!='None':
			year = int(self.last_year)
			self.time_range[1] = year
		else:
			self.last_year = self.time_range[1]

	# 输入是否为他的父节点
	def isParent(self, addr):
		isParent = False
		for son in self.sons:
			if son == addr:
				print(str(self) + '是' + str(addr) + '父节点')
				return True
			isParent = son.isParent(addr)
			if isParent:
				return isParent
		return isParent

	def addSon(self, addr):
		if addr not in self.sons:
			self.sons.append(addr)

	def addParent(self, addr):
		if addr not in self.parents:
			self.parents.append(addr)

	def getParent(self):
		return self.parents

	def getSons(self):
		return self.sons

	def __str__(self):
		return '[(地点) id:{}, 地名:{}, x:{}, y:{}]'.format(str(self.id), str(self.name), str(self.x), str(self.y))

	def __hash__(self):
		return hash(str(self))
	
	def toDict(self):
		return {
			'id':self.id,
			'name':self.name,
			'first_year':self.first_year,
			'last_year':self.last_year,
			'x':self.x,
			'y':self.y,
			'alt_names':self.alt_names,
			# 'time_range': self.time_range,
			'parents': [addr.id for addr in self.parents],
			'sons': [addr.id for addr in self.sons]
		}

addrManager = AddrManager()


if __name__ == '__main__':
	print('地点模块测试')
	print(addrManager.id2addr)