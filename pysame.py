#!/usr/bin/env python
# -*- coding: iso-8859-2 -*-
#
# Wojciech Muła, wojciech_mula[at]poczta[dot]onet[dot]pl
# 
# Licencse: BSD
# $Id: pysame.py,v 1.4 2006-12-04 23:05:33 wojtek Exp $

from Tkinter	import *
from sys		import *
from random		import choice, shuffle
from types		import *
import tkMessageBox
from os   import getlogin
from time import localtime

def tk_center_window(window, W, H):
	w = window.winfo_screenwidth()
	h = window.winfo_screenheight()
	window.geometry("%dx%d+%d+%d" % (W, H, (w-W)/2, (h-H)/2))

GAME_OVER			= 0
ADD_POINTS			= 1
POSSIBLE_POINTS		= 2
NO_SELECTION		= 3

def toint(x):
	if type(x) is IntType or type(x) is LongType:
		return x
	else:
		raise TypeError("Integer expeced")

class GameBoard:
	def __init__(self, parent, rows, cols, cellsize, callback=None):
		"""
		rows     -- number of rows
		cols     -- number of columns
		cellsize -- width/height of cell (bbox of circle)
		"""

		# description of board
		self.rows     = toint(rows)
		self.cols     = toint(cols)
		self.cellsize = toint(cellsize)
		
		# function called by board, when some events occur
		self.callback = callback
	
		# list of columns of balls
		self.Columns = []
	
		# create Tkinter canvas
		w = cols*cellsize
		h = rows*cellsize
		self.canvas = Canvas(parent, width=w, height=h, background="black")
		self.canvas.pack()
		
		# create Tkinter objects (balls)
		self.array = []
		for row in xrange(rows):
			self.array.append([(None,False)]*cols)

		r = self.cellsize
		for row in xrange(self.rows):
			y = row*r
			for col in xrange(self.cols):
				x = col*r
				self.array[self.rows-row-1][col] = (self.canvas.create_oval(x,y,x+r,y+r, fill="#555"), 'empty', False)

		# tables of colour
		self.light_colors = {}
		self.dark_colors  = {}
		
		self.light_colors['empty']	= self.dark_colors['empty'] = 'black'
		
		v = 255
		self.light_colors['red']	= '#%02x0000' % v
		self.light_colors['green']	= '#00%02x00' % v
		self.light_colors['blue']	= '#0000%02x' % v
		self.light_colors['yellow']	= '#%02x%02x00' % (v, v)
	
		v = 128
		self.dark_colors['red']		= '#%02x0000' % v
		self.dark_colors['green']	= '#00%02x00' % v
		self.dark_colors['blue']	= '#0000%02x' % v
		self.dark_colors['yellow']	= '#%02x%02x00' % (v, v)

		self.markedcount = 0		# number of currently selected balls
									# 0 if none selected
		self.cangroup    = False	# is there any possilbe group?
									# (if not, game over)
	
		# bind events
		self.canvas.bind("<Motion>", self.Mark)
		self.canvas.bind("<Button-1>", self.Delete)

		# eop
	
	# internal procedures
	def __map(self):
		"""
		Maps internal structures onto screen.
		"""
		for col in xrange(self.cols):
			for row in xrange(self.rows):
				try:
					color, marked = self.Columns[col][row]
					oval, rcolor, cmarked = self.array[row][col]
					if color != rcolor or marked != cmarked:
						if marked:
							self.canvas.itemconfigure(oval, fill=self.light_colors[color])
						else:
							self.canvas.itemconfigure(oval, fill=self.dark_colors[color])

						self.array[row][col] = (oval, color, marked)
				except IndexError:
					oval, color, _ = self.array[row][col]
					if color != 'empty':
						self.array[row][col] = (oval, 'empty', False)
						self.canvas.itemconfigure(oval, fill=self.light_colors['empty'])
	
	def __markall(self, row, col, group_color):
		"""
		Mark all neighbour balls of ball at (row,col) that has same
		color (group_color). Returns number of marked balls.
		(It is a simple floodfill).
		"""

		try:
			if row < 0 or col < 0:
				raise IndexError
			color, marked = self.Columns[col][row]
			if marked or color != group_color:
				return 0
			else:
				self.Columns[col][row] = (color, True)
				return 1 + self.__markall(row-1,col,group_color) + self.__markall(row+1,col,group_color) + self.__markall(row,col-1,group_color) + self.__markall(row,col+1,group_color)

			self.__mark
		except IndexError:
			return 0
	
	def __unmarkall(self):
		"""
		Remove marks from all balls. Returns number of changes (if no changes, then
		update of view is not necessary).
		"""

		if self.markedcount == 0: # nothing to do
			return 0

		count = 0
		for col in xrange(len(self.Columns)):
			for row, item in enumerate(self.Columns[col]):
				color, marked = self.Columns[col][row]
				if marked:
					count += 1
				self.Columns[col][row] = (color, False)

		return count
	
	def __deletemarked(self):
		"""
		Remove all marked balls from the board.
		"""

		# remove marked balls
		for col in xrange(len(self.Columns)):
			self.Columns[col] = [item for item in self.Columns[col] if item[1]==False]

		# remove empty columns
		self.Columns = [column for column in self.Columns if column != [] ]
	
	def __cangroup(self):
		"""
		Retuns true or false (and also sets self.cangroup) depending on
		possibility to mark a group of balls. It is possible only if
		exist a pair of adjecent balls with same color.
		"""
		
		for col in xrange(len(self.Columns)):
			for row, item in enumerate(self.Columns[col]):
				color, _ = item # colors of 'this' ball

				# determine color of next ball in same column
				try:
					cu, _ = self.Columns[col][row+1]
				except IndexError:
					cu = 'empty'

				# determine color of next ball from next column
				try:
					cl, _ = self.Columns[col+1][row]
				except:
					cl = 'empty'

				if color == cu or color == cl:
					self.cangroup = True
					return True

		self.cangroup = False
		return False
	
	def __call_callback(self, what, data=None):
		"""
		A wrapper to callback
		"""
		if self.callback != None:
			self.callback(what, data)

	def New(self):
		"""
		Starts new game.
		"""
		self.cangroup = True
		self.Columns = []
		for col in xrange(self.cols):
			n = self.rows/4
			
			tmp = [('red',    False) for i in xrange(n)] + \
			      [('green',  False) for i in xrange(n)] + \
			      [('blue',   False) for i in xrange(n)] + \
			      [('yellow', False) for i in xrange(n)]
			
			shuffle(tmp)
			self.Columns.append ( tmp )
		
		self.__map() # update view
	
	def CanGroup(self):
		"""
		Returns true if there is any group on the board.
		"""
		return self.cangroup

	def Empty(self):
		"""
		Returns true if gamer clear all board.
		"""
		return self.Columns == []
	
	def Delete(self, event):
		"""
		Event handler that deletes marked group.
		"""

		if not self.cangroup: # no groups, nothing to do
			return
		if self.markedcount > 1: # if two or more element group are marked

			# tell about it
			self.__call_callback(ADD_POINTS, self.markedcount)

			# delete group
			self.__deletemarked()

			# if no grouos left... GAME OVER 
			if self.__cangroup() == False:
				self.__call_callback(GAME_OVER)

			# update view
			self.__map()
			self.canvas.event_generate('<Motion>', x=event.x, y=event.y)
	
	def Mark(self, event):
		"""
		Event handler that mark groups.
		"""
		
		if not self.cangroup:
			return

		# translate mouse coords into board coords
		row = self.rows-event.y/self.cellsize-1
		col = event.x/self.cellsize

		try:
			color, marked = self.Columns[col][row]
			if marked: # if cursor points again on group,
				return # there is nothing to do

			# remove marks from previous group
			self.__unmarkall()

			# mark group (if any), get count of balls
			self.markedcount = self.__markall(row, col, color)

			# if group exists
			if self.markedcount > 0:

				# but has one member, we don't allow to mark it
				if self.markedcount == 1:
					self.Columns[col][row] = (color, False)
					self.__call_callback(NO_SELECTION)
				else:
					self.__call_callback(POSSIBLE_POINTS, self.markedcount )
				
				self.__map()

		except IndexError:
			# exception means that user point cursor on the black
			# area of board -- so we unmark group (if any)
			if self.__unmarkall() > 0:
				self.__call_callback(NO_SELECTION)
				self.__map()

###########################################################################

# highscore is a tuple: gamer, point, date
highscore = []
try:
	file = open('pysame.score', 'r')
	for line in file:
		who, points, date = line.split('\t')
		highscore.append( (who, int(points), date.rstrip()) )
	
	file.close()
except:
	pass

root = Tk()
root.title('PySame')
w = root.winfo_screenwidth()
h = root.winfo_screenheight()

ROWS = 12
COLS = 20

CELLSIZE = min( h/(ROWS+1), w/(COLS+1) )

tk_center_window(root, COLS*CELLSIZE, (ROWS+1)*CELLSIZE)
root.resizable(0,0)

def callback(what, data):
	global gameboard, info, points, highscore

	bonus = 1000
	def calc_points(x):
		if x > 2:
			return (x-2)**2
		else:
			return 0

	if what == GAME_OVER:
		if gameboard.Empty():
			info.set("You've finished with score %d points (+%d extra points)!" % (points, bonus))
			points += bonus
		else:
			info.set("You've finished with score %d points!" % points)

		date  = map(str, localtime())
		date  = "-".join(date[:3]) + " " + ":".join(date[3:5])
		gamer = getlogin()

		highscore.append( (gamer, points, date) )

	elif what == ADD_POINTS:
		points += calc_points(data)
		info.set("Your score: %d" % points)
	
	elif what == POSSIBLE_POINTS:
		data = calc_points(data)
		if data > 0:
			info.set("Your score: %d (+%d)" % (points, data))
		else:
			info.set("Your score: %d" % points)
	elif what == NO_SELECTION:
		info.set("Your score: %d" % points)

gameboard = GameBoard(root, ROWS, COLS, CELLSIZE, callback)

def newgame():
	global gameboard, info, points

	if gameboard.CanGroup() and points:
		if not tkMessageBox.askyesno('Question', "You haven't finished the game. Do you want to start new game?"):
			return

	points = 0
	info.set("Making new game")
	gameboard.New()
	info.set("New game started")

points = 0
info = StringVar()
info.set("Welcome in PySame")
Label(root, font=("Halvetica", -24), padx=3, pady=3, textvariable=info).pack(side=LEFT)

Button(root, text="New game", command=newgame).pack(side=RIGHT)

root.mainloop()

try:
	file = open('pysame.score', 'w')
	def sf(a,b):
		return cmp(b[1], a[1])

	highscore.sort(sf)
	highscore = highscore[:10]

	for gamer, points, date in highscore:
		file.write("%s\t%d\t%s\n" % (gamer, points, date) )

	file.close()
except:
	pass

# vim: ts=4 sw=4 ai
