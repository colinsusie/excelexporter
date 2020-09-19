# -*- coding: utf-8 -*-
# @Author: colin
# Excel表出工具

import sys
import sxl
import os
import time
import datetime
import traceback
import type_converter

# 导出的字段类型
Int = type_converter.Int
Str = type_converter.Str
Float = type_converter.Float
Bool = type_converter.Bool
List = type_converter.List
Tuple = type_converter.Tuple
Dict = type_converter.Dict

# 导出类型
ET_SIMPLE = 0		# 简单类型，即一个简单的字典表
ET_OPT = 1			# 优化类型，根据不同的语言作不同的优化


def debuglog(log):
	"""输出到stdout"""
	tm = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
	str = "{} [INFO] => {}".format(tm, log)
	print(str)

def errorlog(log):
	"""输出到stderr"""
	tm = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
	str = "{} [INFO] => {}".format(tm, log)
	print(str, file=sys.stderr)	
	

def get_abspath(directory, filename):
	"""取文件的绝对路径"""
	if not os.path.isabs(filename):
		return os.path.abspath(os.path.join(directory, filename))
	else:
		return filename


def get_basename(path):
	"""取文件的基础名，不包括后缀"""
	filename = os.path.split(path)[1]
	return os.path.splitext(filename)[0]


def get_modify_time(f):
	"""取文件的修改时间"""
	if not os.path.exists(f):
		return 0
	else:
		return os.path.getmtime(f)


def scan_define_files(path):
	"""扫描配置定义文件"""
	define_files = []
	for file_name in os.listdir(path):
		if file_name.endswith(".py"):
			define_files.append(file_name)
	return define_files


def do_export_excel(define_dir, define_file, export_all):
	""" 导出Excel文件
	:param define_dir: 定义文件的路径
	:param define_file: 定义文件名
	:param export_all: 是否全导
	:return:
	"""
	if define_dir not in sys.path:
		sys.path.append(define_dir)
	mod_name = get_basename(define_file)
	define_module = __import__(mod_name)

	if not hasattr(define_module, "define"):
		errorlog("  错误：定义文件不存在define块：%s" % define_file)
		return

	if not hasattr(define_module, "config"):
		errorlog("  错误：定义文件不存在config块：%s" % define_file)
		return

	excel_file = define_module.config.get("source", None)
	if excel_file is None:
		errorlog("  错误：必须指定Excel文件, source: %s" % define_file)
		return
	excel_full_path = get_abspath(define_dir, excel_file)
	if not os.path.exists(excel_full_path):
		errorlog("  错误：Excel文件不存在, source:  %s" % excel_file)
		return

	target_infos = define_module.config.get("target", None)
	if target_infos is None:
		errorlog("  错误：必须指定导出的目标文件: %s" % define_file)
		return

	if define_module.config.get("key", None) is None:
		errorlog("  错误：未指定键名")
		return

	if not export_all and not need_export(define_dir, define_file, define_module):
		return

	# 对define块，进行一些检查
	sheet_name = define_module.config.get('sheet')
	tkeyset = set()
	for idex, tdata in enumerate(define_module.define):
		tkey = tdata[1]
		if tkey in tkeyset:
			errorlog("{}.{} 存在相同的数据key:{}".format(excel_file, sheet_name, tkey))
			return
		tkeyset.add(tkey)
		if len(tdata) < 3:
			errorlog("{} {} define项数据不足".format(excel_file, idex))
			return

	# 从Excel中取出Sheet出来
	excel_sheet = get_excel_sheet(define_dir, excel_file, sheet_name)
	if excel_sheet is None:
		return

	sheet_name = (sheet_name or "Sheet1")
	table = make_table(excel_file, excel_sheet, define_module, sheet_name)
	if table is None:
		return

	write_to_targets(define_dir, table, define_module)

	targets = [info[0] for info in target_infos]
	debuglog("成功导出：%s-%s => %s" % (excel_file, sheet_name, targets))


def need_export(define_dir, define_file, define_module):
	"""是否需要导出，通过比较修改时间"""
	source_mtime = 0
	excel_file = get_abspath(define_dir, define_file)
	source_mtime = max(source_mtime, get_modify_time(excel_file))
	excel_file = get_abspath(define_dir, define_module.config["source"])
	source_mtime = max(source_mtime, get_modify_time(excel_file))

	target_mtime = time.time()
	for target in define_module.config["target"]:
		file_path = get_abspath(define_dir, target[0])
		if os.path.exists(file_path):
			target_mtime = min(target_mtime, get_modify_time(file_path))
		else:
			return True
	return target_mtime < source_mtime


def get_excel_sheet(define_dir, excel_file, sheet_name=None):
	"""从Excel中取出Sheet"""
	try:
		excel_file = get_abspath(define_dir, excel_file)
		source_doc = sxl.Workbook(excel_file)
		if not sheet_name:
			excel_sheet = None
			errorlog("  错误：没有指定sheet字段：%s" % (excel_file))
		else:
			excel_sheet = source_doc.sheets[sheet_name]
	except:
		errorlog("  错误：打开源文件失败：%s" % (excel_file))
		traceback.print_exc()
		return None
	return excel_sheet


def get_define_item(define_module, name):
	"""根据字段名取得定义项"""
	for define_item in define_module.define:
		if define_item[0] == name:
			return define_item
	return None


def check_define_item(define_module, excel_col_list, excel_file, sheet_name):
	"""检查不存在的导出列"""
	for define_item in define_module.define:
		exist = False
		if define_item[0] in excel_col_list:
			exist = True
		if not exist:
			errorlog("excel:{},sheet:{} 不存在导出列:{}".format(excel_file, sheet_name, define_item[0]))


def make_table(excel_file, excel_sheet, define_module, sheet_name):
	"""从Sheet取出table来"""
	table = {}
	col_list = []
	col_defines = {}
	key_name = define_module.config['key']
	for row, row_values in enumerate(excel_sheet.rows):
		if row == 0:	# 第1列为字段
			for col_name in row_values:
				col_list.append(col_name)
				col_defines[col_name] = get_define_item(define_module, col_name)
		else:
			row_dict = {}
			key_value = None
			col_name = None
			value = ""
			try:
				for col, value in enumerate(row_values):
					col_name = col_list[col]
					define_item = col_defines.get(col_name, None)
					if define_item:
						if value == None:
							value = ""
						elif type(value) == float and int(value) == value:
							value = str(int(value))
						else:
							value = str(value)
						if define_item[1] == key_name:
							if value == '':
								key_value = None
								break
						value = define_item[2].convert(value)
						row_dict[define_item[1]] = value
						if define_item[1] == key_name:
							key_value = value
			except:
				errorlog("错误信息： file: %s sheet: %s  row: %s, col: %s, value: %s" % (excel_file, sheet_name, row, col_name, value))
				raise
			if key_value is not None:
				# 支持自定义格式
				if hasattr(define_module, "custom_key"):
					key_value = define_module.custom_key(key_value, row_dict)
					row_dict[key_name] = key_value
				if hasattr(define_module, "custom_row"):
					row_dict = define_module.custom_row(key_value, row_dict)
				if key_value in table:
					errorlog("  错误：存在相同的键值：%s : %s" % (excel_file, key_value))
					return None
				else:
					table[key_value] = row_dict

	check_define_item(define_module, col_list, excel_file, sheet_name)
	if hasattr(define_module, "verify_table"):
		define_module.verify_table(table)

	return table


def write_to_targets(define_dir, table, define_module):
	target_infos = define_module.config.get("target", ())
	for target_info in target_infos:
		target_path = get_abspath(define_dir, target_info[0])
		export_type = target_info[2] if len(target_info) >= 3 else ET_SIMPLE
		name = target_info[1] + "_converter"
		converter = __import__(name)
		if converter and converter.do_convert:
			converter.do_convert(table, target_path, export_type, define_module)
		elif not converter.do_convert:
			errorlog("  错误：转换器必须提供do_convert方法: %s" % name)
		else:
			errorlog("  错误：不支持导出文件的类型: %s" % target_path)


def export_excel(define_path, export_all):
	"""
	:param define_path: 定义文件的路径，可以是具体的文件，也可以是一个目录
	:param export_all: 是否全导，如果不全导，则只导修改过的Excel文件
	:return:
	"""
	if os.path.isdir(define_path):
		define_files = scan_define_files(define_path)
		for define_file in define_files:
			do_export_excel(define_path, define_file, export_all)
	elif os.path.isfile(define_path):
		define_path, define_file = os.path.split(define_path)
		do_export_excel(define_path, define_file, export_all)
	else:
		errorlog("  错误：未知定义文件")


def main():
	import argparse
	parser = argparse.ArgumentParser(description=u'Excel Expoter')
	parser.add_argument('-p', '--path', type=str, required=True, help=u"指定导表定义文件的路径，可以是具体的文件，也可以是一个目录")
	parser.add_argument('-a', '--all', type=int, default=False, help=u"是否全导，如果不，则只导修改过的文件")
	args = parser.parse_args()

	debuglog("开始导出")
	export_excel(args.path, args.all)
	debuglog("导出完毕!!!")


if __name__ == "__main__":
	main()
