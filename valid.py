#!/usr/bin/python
import os.path
import csv, random
import urllib, cStringIO
import cgi, cgitb
import MySQLdb, MySQLdb.cursors
from PIL import Image

conn = MySQLdb.connect(db='nrl_asteroids', read_default_file="./.my.cnf", cursorclass=MySQLdb.cursors.DictCursor)

print "Content-type: text/html\n\n<html>"
cgitb.enable()

def es(string):
   return MySQLdb.escape_string(str(string))

def getDataFromDB(image_id):
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM images WHERE id=' + es(image_id))
   row = cursor.fetchone()
   return int(row['run']), int(row['camcol']), int(row['field'])

def getValidCount():
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) AS num FROM asteroids WHERE validations>0')
   return cursor.fetchone()['num']

def getVoteCount():
   cursor = conn.cursor()
   cursor.execute('SELECT SUM(validations) AS num FROM asteroids')
   return cursor.fetchone()['num']

def getImageCount():
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) AS num FROM images')
   return cursor.fetchone()['num']

def getValid():
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM asteroids WHERE validations>0 ORDER BY validations DESC')
   rows = cursor.fetchall()
   return rows

def buildURL(r,c,f):
   return "./detect.py?R=" + str(r) + "&C=" + str(c) + "&F=" + str(f)

def buildImageURL(r,c,f):
   return "http://cas.sdss.org/dr7/en/get/frameByRCFZ.asp?R=" + str(r) + "&C=" + str(c) + "&F=" + str(f) + "&Z=0&submit1=Get+Image"

def checkThumbnail(asteroid_id, r, c, f, x, y):
   if not os.path.isfile("./verified/" + asteroid_id + ".jpg"):
      im = Image.open(cStringIO.StringIO(urllib.urlopen(buildImageURL(r,c,f)).read()))
      im = im.crop((x-20, y-20, x+20, y+20))
      im.save("./verified/" + asteroid_id + ".jpg", "JPEG")

bigclusterdivs = "<div id='clusters'>"
css = "<style>"
css += "div.progress-container {border: 1px solid #ccc; width: 100px; margin: 2px 5px 2px 0; padding: 1px; background: white;}"
css += "div.progress-container > div { background-color: #ACE97C; height: 12px;}"
css += "#clusters{width:1000px;}"
css += ".bigcluster{float:left;width:40px;height:40px;border:2px solid;background-repeat:no-repeat;}"
css += ".bigclusterbox{float:left;border:1px solid #fff;font-family:monospace;padding:10px;background-color:#000;}"

valid = getValid()
for id, asteroid in enumerate(valid):
   asteroid_id = str(asteroid['id'])
   image_id = str(asteroid['image_id'])
   r,c,f = getDataFromDB(image_id)
   x = int(asteroid['x'])
   y = int(asteroid['y'])
  
   checkThumbnail(asteroid_id, r, c, f, x, y)

   conf = str(int(255*float(asteroid['confidence'])))
   global_id = str(asteroid['id'])

   #css += "#bc" + str(id) + "{border-color:rgb(0," + conf + ",0);background-image:url('verified/" + asteroid_id + ".jpg');}"
   css += "#bc" + str(id) + "{border:none; background-image:url('verified/" + asteroid_id + ".jpg');}"
   bigclusterdivs += "<div class='bigclusterbox'><a href=\"" + buildURL(r,c,f) + "\" TITLE=\"" + asteroid_id + "\"><div class='bigcluster' id='bc" + str(id) + "'></div></a></div>"

css += "</style>"
bigclusterdivs += "</div>"
print "<div style=\"width:1000px; margin-left: auto; margin-right: auto;\">"
print css
print "<h1>Verified Asteroids</h1>Asteroids verified by users from images from the <a href=\"http://cas.sdss.org/dr7/en/\">Sloan Digital Sky Survey</a>. Click on an  individual asteroid to continue to it's full image. <a href=\"http://dustingram.com/misc/astro/detect.py\">Click here to get a new random image to verify</a>.</br></br>"
print bigclusterdivs + "<div style='clear:both'></div>"
count = getImageCount()
percent = round((count/428016.0)*100.0,3)
print "<br/><div class=\"progress-container\"><div style=\"width:" + str(percent) + "%\"></div></div>"
print "<br/>Total processed images: " + str(count) + "/428016 (" + str(percent) + "%)"
print "<br/>Total validated asteroids: " + str(getValidCount())
print "<br/>Total submitted votes: " + str(getVoteCount()) + "</br>"
print "<br/>Created by <a href=\"mailto:dsi23@drexel.edu\">Dustin Ingram</a> and <a href=\"mailto:ar374@drexel.edu\">Aaron Rosenfeld</a>"
print "</div>"
print "</html>"
