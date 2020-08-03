# -*- coding: utf-8 -*-


def do_convert(table, save_path, export_type, define_module):
	"""
	导出目录文件
	:param table: 数据
	:param save_path: 保存的路径，可以相对于dir，也可以是绝对路径
	:param export_type: 导出类型
	:param define_module: 定义模块
	:return:
	"""

	def write_obj(obj, root=False):
		s = ''
		if isinstance(obj, bool):
			s += 'true' if obj else 'false'
		elif isinstance(obj, int) or isinstance(obj, float):
			s += str(obj)
		elif isinstance(obj, str):
			s += '"' + obj + '"'
		elif isinstance(obj, list) or isinstance(obj, tuple):
			s += '['
			for i in range(len(obj)):
				s += write_obj(obj[i])
				if i < len(obj) - 1:
					s += ', '
			s += ']'
		elif isinstance(obj, dict):
			if root:
				i = 0
				c = len(obj)
				keys = list(obj.keys())
				keys.sort()
				s += '{\n'
				for k in keys:
					v = obj[k]
					s += '\t' + write_obj(str(k), False) + ': '
					s += write_obj(v)
					if i < c - 1:
						s += ', '
					s += '\n'
					i += 1
				s += '}'
			else:
				i = 0
				c = len(obj)
				keys = list(obj.keys())
				keys.sort()
				s += '{'
				for k in keys:
					v = obj[k]
					s += write_obj(str(k), False) + ': '
					s += write_obj(v)
					if i < c - 1:
						s += ', '
					i += 1
				s += '}'
		return s

	content = write_obj(table, True)
	with open(save_path, 'wb') as f:
		f.write(content.encode("utf-8"))
