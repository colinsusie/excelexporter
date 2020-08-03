# coding: utf-8
# @Author: colin
# 字段的类型转换器

class ConvertError(TypeError):
	pass


class Converter(object):
	def get_error_desc(self, data):
		return "%s 不是有效的 %s" % (data, self.__class__.__name__)


class Int(Converter):
	"""整型转换器"""

	def convert(self, data):
		try:
			if data == '':
				d = self.get_default()
			elif type(data) == str:
				d = int(float(data))
			else:
				d = int(data)
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return d

	@staticmethod
	def get_default():
		return 0


class Str(Converter):
	"""字符串转换器"""

	def convert(self, data):
		data = str(data)
		data = data.replace("\r\n", "\\n")
		data = data.replace("\n", "\\n")
		data = data.replace("\"", "\\\"")
		return data


class Float(Converter):
	"""浮点数转换器"""

	def convert(self, data):
		try:
			if data == '':
				d = self.get_default()
			else:
				d = float(data)
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return d

	@staticmethod
	def get_default():
		return 0.0


class Bool(Converter):
	"""布尔值转换器"""

	def convert(self, data):
		try:
			if data == '':
				d = self.get_default()
			else:
				d = bool(int(float(data)))
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return d

	@staticmethod
	def get_default():
		return False


class List(Converter):
	"""列表转换器"""

	def __init__(self, itemtype, separator="|"):
		"""
		:param itemtype: 子项类型
		:param separator: 分隔符
		"""
		self.itemtype = itemtype
		self.separator = separator

	def convert(self, data):
		data = str(data)
		if data == '':
			return self.get_default()
		try:
			l = data.split(self.separator)
			d = [self.itemtype.convert(x) for x in l]
			if l[-1] == '': d.pop(-1)
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return d

	@staticmethod
	def get_default():
		return []


class Tuple(Converter):

	"""元表转换器"""
	def __init__(self, separator, *itemtypes):
		"""
		:param itemtypes: 元表每一项的类型
		:param separator: 分隔符
		"""
		self.itemtypes = itemtypes
		self.separator = separator

	def convert(self, data):
		data = str(data)
		try:
			if data == '':
				d = (itemtype.convert("") for itemtype in self.itemtypes)
			else:
				l = data.split(self.separator)
				d = (self.itemtypes[i].convert(x) for i, x in enumerate(l))
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return tuple(d)


class Dict(Converter):
	"""字典转换器"""

	def __init__(self, keytype, valuetype, separator="|"):
		"""
		:param keytype: Key的类型
		:param valuetype: Value的类型
		:param separator: 分隔符
		"""
		self.keytype = keytype
		self.datatype = valuetype
		self.separator = separator

	def convert(self, data):
		data = str(data)
		if data == '':
			return self.get_default()
		try:
			d = [keyval for keyval in data.split(self.separator)]
			if d[-1] == '': d.pop(-1)
			dictobj = {}
			for keyval in d:
				(key, val) = keyval.split(":")
				dictobj[self.keytype.convert(key)] = self.datatype.convert(val)
		except Exception as e:
			raise ConvertError(self.get_error_desc(data)) from e
		return dictobj

	@staticmethod
	def get_default():
		return {}