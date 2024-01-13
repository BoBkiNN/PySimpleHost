"""Logger module
   ~~~~~~~~~~~~~
   Owner: @bobkinn_

   You are not allowed to claim rights for this module. You allowed to use and modify this file without publishing

   Copyright 2023 BoBkiNN
   
   Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
   The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE."""
import os
from datetime import datetime

import colorama
import pytz
from tzlocal import get_localzone
from termcolor import colored

def init(console=True, file=True, color=True, timezone=pytz.timezone(str(get_localzone())), dateF="[%d/%m/%Y %H:%M:%S]", dir=os.getcwd() + os.sep + "logs"):
	global logToConsole, logToFile, coloredLog, dateFormat, tz, folder
	logToConsole = console
	logToFile = file
	coloredLog = color
	tz = timezone
	dateFormat = dateF
	folder = dir
	if os.name == "nt":
		colorama.init(autoreset=True)

def getDate() -> str:
	"""Get formatted date in Moscow

	Returns:
		str: Formatted date
	"""
	d = datetime.now(tz)
	ret = d.strftime(dateFormat)
	return ret
	
def getObjsStr(objs: tuple) -> str:
	"""Get string from objects list

	Args:
		objs (tuple): Objects tuple

	Returns:
		str: Formatted string
	"""
	msg = ""
	for o in objs:
		msg += str(o)+" "
	return msg

def info(*obj):
	"""Log INFO"""
	log(getObjsStr(obj), levelPrefix="[INFO]", color="green")
	
def warn(*obj):
	"""Log WARN"""
	log(getObjsStr(obj), levelPrefix="[WARN]", color="yellow")
	
def error(*obj):
	"""Log ERROR"""
	log(getObjsStr(obj), levelPrefix="[ERROR]", color="red")
	
def log(obj, levelPrefix: str = None, color: str = None):
	"""Primitive log

	Args:
		obj (Any): message
		levelPrefix (str, optional): prefix ([INFO] and etc).
		color (str, optional): color. If None, message will be not colored.
	"""
	msg = getDate()
	if levelPrefix != None:
		msg += f"{levelPrefix}: "
	else:
		msg += ": "
	msg += str(obj)
	
	global logToConsole, coloredLog
	if logToConsole == True:
		if color != None and coloredLog == True:
			print(colored(msg, color, attrs=["bold"]))
		else:
			print(msg)
	
	writeF(msg)

def writeF(msg: str):
	"""Write message to file

	Args:
		msg (str): message
	"""
	global logToFile
	if not logToFile:
		return
	if not os.path.exists(folder):
		os.mkdir(folder)
	latestPath = folder + os.sep + "latest.log"
	if not os.path.exists(latestPath):
		with open(latestPath,"w") as f:
			f.close()
	else:
		c_time = os.path.getmtime(latestPath)
		ct = datetime.fromtimestamp(c_time).date()
		now = datetime.now(tz).date()
		
		fsize = os.stat(latestPath).st_size // 1024 // 1024 # mb
		if ct.day != now.day or fsize > 10:
			# file is old or size more than 10 mb
			fileNum = 1
			while True:
				fName = str(ct.day) + "_" + str(ct.month) + "_" + str(ct.year) + f"-{fileNum}.log"
				try:
					os.rename(latestPath, folder + os.sep + fName)
				except FileExistsError:
					fileNum += 1
					continue
				else:
					break
	
	if not os.path.exists(latestPath):
		with open(latestPath,"w") as f:
			f.close()
	
	with open(latestPath, "a", encoding="utf-8") as f:
		print(msg,file=f)
	
if __name__ == "__main__":
	# debug
	init()
	info("sjsi",727,{"sj":28})
	warn("Warining")
	error("ошишка")
	log("log")
