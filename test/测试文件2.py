# -*- coding: utf-8 -*-
from excel_exporter import *

define = [
	# 第一列：Excel列名  第二列：导出字段名	  第三列：字段类型
	['编号', 'no', Int()],
	['职业', 'job', Int()],
	['等级', 'level', Int()],
]

config = {
	"source": "测试文件2.xlsx",
	"sheet": "Sheet1",
	"target": [
		["./test2.js", "js", ET_OPT],
		["./test2.lua", "lua", ET_OPT],
		["./test2.json", "json"],
		["./test2.py", "py"],
	],
	"key": "no",
}


def custom_key(key_value, row_dict):
	return "{}_{}".format(row_dict["job"], row_dict["level"])

# def custom_row(key_value, row_dict):
# 	if not (1 <= row_dict["job"] <= 3):
# 		raise TypeError("职业字段只能1,2,3")
# 	return row_dict

# def verify_table(table):
	# print("OK")