# -*- coding: utf-8 -*-
import os
import excel_exporter
import re
regex = '^[A-Za-z_][A-Za-z0-9_]*'


def do_convert(table, save_path, export_type, define_module):
	"""
	导出目录文件
	:param table: 数据
	:param save_path: 保存的路径，可以相对于dir，也可以是绝对路径
	:param export_type: 导出类型
	:param define_module: 定义模块
	"""
	if export_type == excel_exporter.ET_OPT:
		convert_lua_strip(table, save_path, define_module)
	else:
		convert_lua_simple(table, save_path, define_module)


def isidentifier(str):
	"""是否是标识符"""
	return re.search(regex, str)


def write_obj(obj, root=False, iskey=False):
	""" 导出对象为字符串 """
	s = ''
	if isinstance(obj, bool):
		s += 'true' if obj else 'false'
	elif isinstance(obj, int) or isinstance(obj, float):
		if iskey:
			s += '[' + str(obj) + ']'
		else:
			s += str(obj)
	elif isinstance(obj, str):
		if iskey:
			if isidentifier(obj):
				s += obj
			else:
				s += "['{}']".format(obj)
		else:
			s += '"' + obj + '"'
	elif isinstance(obj, tuple) or isinstance(obj, list):
		s += '{'
		for i in range(len(obj)):
			s += write_obj(obj[i])
			if i == 0 or i < len(obj) - 1:
				s += ', '
		s += '}'
	elif isinstance(obj, dict):
		if root:
			keys = list(obj.keys())
			keys.sort()
			s += '{\n'
			for k in keys:
				v = obj[k]
				s += '\t' + write_obj(k, False, True) + ' = '
				s += write_obj(v) + ', \n'
			s += '}'
		else:
			i = 0
			c = len(obj)
			keys = list(obj.keys())
			keys.sort()
			s += '{'
			for k in keys:
				v = obj[k]
				s += write_obj(k, False, True) + ' = '
				s += write_obj(v)
				if i < c - 1:
					s += ', '
				i += 1
			s += '}'
	return s


def convert_lua_simple(table, save_path, define_module):
	"""简单的转化为一个table"""

	def get_col_desc():
		ls = []
		define_items = define_module.define
		for item in define_items:
			ls.append("-- {} = {}".format(item[1], item[0]))
		return "\n".join(ls)

	basename = os.path.splitext(os.path.split(save_path)[1])[0]
	excel_path = define_module.config["source"]
	sheet = define_module.config.get("sheet", "Sheet1")
	s = "-- %s:%s\n" % (excel_path, sheet)
	s = s + get_col_desc() + "\n\n"
	s = s + 'local ' + basename + ' = ' + write_obj(table, True)
	s = s + '\nreturn ' + basename

	with open(save_path, 'wb') as f:
		f.write(s.encode("utf-8"))


def convert_lua_strip(table, save_path, define_module):
	"""转化为数组的形式"""

	def make_col_map_str(define_items):
		"""生成列索引字符串:"""
		str = "local key_map = {\n"
		for i, item in enumerate(define_items):
			str += "\t-- {}\n".format(item[0])
			str += "\t{} = {},\n".format(item[1], i+1)
		str += "}"
		return str

	def make_data_item(rowobj, define_items):
		"""生成数据项，优化成一个数组"""
		ret = []
		for i, de_item in enumerate(define_items):
			name = de_item[1]
			if name in rowobj:
				ret.append(rowobj[name])
			else:
				ret.append("")
		return ret

	def make_data_dict(table, define_items):
		"""生成优化过的数据"""
		ret = {}
		for key, rowobj in table.items():
			ret[key] = make_data_item(rowobj, define_items)
		return ret

	def make_data_dict_str(data_dict, basename):
		str = "local {} = ".format(basename)
		str += write_obj(data_dict, True)
		return str

	basename = os.path.splitext(os.path.split(save_path)[1])[0]
	excel_path = define_module.config["source"]
	sheet = define_module.config.get("sheet", "Sheet1")
	excel_path = "%s:%s" % (excel_path, sheet)

	define_items = define_module.define
	col_map_str = make_col_map_str(define_items)
	data_dict = make_data_dict(table, define_items)
	data_dict_str = make_data_dict_str(data_dict, basename)

	str = """-- %s

%s

%s

do
	local item_metatable = {
		__index = function (t, k)
			local pos = key_map[k]
			if pos then
				return rawget(t, pos)
			else
				return nil
			end
		end,
	}

	local setmetatable = setmetatable
	for _, date_item in pairs(%s) do
		setmetatable(date_item, item_metatable)
	end
end

return %s
""" % (excel_path, col_map_str, data_dict_str, basename, basename)

	with open(save_path, 'wb') as f:
		f.write(str.encode("utf-8"))