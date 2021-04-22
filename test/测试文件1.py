# -*- coding: utf-8 -*-
from excel_exporter import *

define = [
	# 第一列：Excel列名  第二列：导出字段名	  第三列：字段类型
	['编号', 'no', Int()],
	['整型', 'i', Int()],
	['浮点数', 'fl', Float()],
	['字符串', 'str', Str()],
	['字符串2', 'str2', Str()],
	['布尔值', 'bo', Bool()],
	['列表', 'li', List(Str())],
	['列表2', 'li2', List(List(Int(), ","), "|")],
	['元表', 'tu', Tuple(",", Int(), Str())],
	['字典', 'di', Dict(Str(), Float())],
]

config = {
	"source": "测试文件1.xlsx",
	"sheet": "Sheet1",
	"target": [
		["./test1.js", "js"],
		["./test1.lua", "lua"],
		["./test1.json", "json"],
		["./test1.py", "py"],
	],
	"key": "no"
}
