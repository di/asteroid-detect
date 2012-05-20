#!/usr/bin/python
import csv, random
import urllib, cStringIO, os
import cgi, cgitb
import MySQLdb, MySQLdb.cursors

conn = MySQLdb.connect(db='nrl_asteroids', read_default_file="./.my.cnf", cursorclass=MySQLdb.cursors.DictCursor)

print "Content-type: text/html\n\n<html>"
cgitb.enable()

def es(string):
   return MySQLdb.escape_string(str(string))

def getDataFromDB(run = None, camcol = None, field = None):
   cursor = conn.cursor()
   if run == None :
      cursor.execute('SELECT * FROM images WHERE num_asteroids>0 ORDER BY RAND() LIMIT 1')
   else :
      cursor.execute('SELECT * FROM images WHERE run=' + es(run) + ' AND camcol=' + es(camcol) + ' AND field=' + str(field))
   row = cursor.fetchone()
   return int(row['run']), int(row['camcol']), int(row['field']), int(row['id']) 

def getClusters(image_id):
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM asteroids WHERE image_id=' + es(image_id) + ' ORDER BY confidence DESC')
   rows = cursor.fetchall()
   return rows

def submitVote(cluster_id):
   cursor = conn.cursor()
   cursor.execute('UPDATE asteroids SET validations=validations+1 WHERE id=' + es(cluster_id)) 

def checkPost():
   form=cgi.FieldStorage()
   if len(form.keys()) > 0:
      for key in form.keys():
         if key.find('checkbox') >= 0:
            asteroid_id = form.getvalue(key)
            submitVote(asteroid_id)
            logIP(asteroid_id)

def buildURL(r,c,f,z):
   return "http://cas.sdss.org/dr7/en/get/frameByRCFZ.asp?R=" + str(r) + "&C=" + str(c) + "&F=" + str(f) + "&Z=" + str(z) + "&submit1=Get+Image"

def getData():
   form = cgi.FieldStorage()
   if form.has_key('R') and form.has_key('C') and form.has_key('F'):
      run,camcol,field,image_id = getDataFromDB(form['R'].value, form['C'].value, form['F'].value)
   else:
      run,camcol,field,image_id = getDataFromDB()
   return run,camcol,field,image_id

def logIP(asteroid_id):
  ip = cgi.escape(os.environ["REMOTE_ADDR"])
  f = open('ips.txt', 'a')
  f.write(ip + "\t" + str(asteroid_id) + "\n")
  f.close()

checkPost()
run,camcol,field,image_id = getData()
url0 = buildURL(run,camcol,field,0)
url1 = buildURL(run,camcol,field,1)
clusters = getClusters(image_id) 
clusterdivs = "<div id='frame'>"
bigclusterdivs = "<div id='clusters'>"
css = "<style>"
css += ".cluster{position:absolute;width:20px;height:20px;border:1px solid;}"
css += ".clusternum{position:absolute;width:20px;height:20px;font-family:monospace}"
css += ".bigcluster{float:left;width:40px;height:40px;border:2px solid;background-repeat:no-repeat;}"
css += ".bigclusterbox{float:left;border:1px solid #fff;font-family:monospace;padding:10px;background-color:#000;width:70}"
css += "#frame{position:relative;width:992px;height:680px;background-image:url('" + url1 + "'); background-repeat:no-repeat}"
for id, cluster in enumerate(clusters) :
   conf = str(int(255*float(cluster['confidence'])))
   global_id = str(cluster['id'])
   x = int(cluster['x'])
   y = int(cluster['y'])

   css += "#c" + str(id) + "{border-color:rgb(0," + conf + ",0);top:" + str(y/2-11) + "px;left:" + str(x/2-11) + "px}\n"
   css += "#cn" + str(id) + "{color:rgb(0," + conf + ",0);top:" + str(y/2+10) + "px;left:" + str(x/2+10) + "px}\n"
   css += "#bc" + str(id) + "{border-color:rgb(0," + conf + ",0);background-image:url('" + url0 + "');background-position:"
   if x < 20:
      css += str(20-x) + "px "
   else:
      css += "-" + str(x-20) + "px "
   if y < 20:
      css += str(20-y) + "px"
   else:
      css += "-" + str(y-20) + "px"
   css += "}\n"
   clusterdivs += "<div class='cluster' id='c" + str(id) + "'></div>"
   clusterdivs += "<div class='clusternum' id='cn" + str(id) + "'>" + str(id) + "</div>"
   bigclusterdivs += "<div class='bigclusterbox'><div class='bigcluster' id='bc" + str(id) + "'></div><div style='float:left'><input type='checkbox' name='checkbox" + str(id) + "'  value='" + str(global_id) + "'/><br/>&nbsp;<span style='color:rgb(0," + conf + ",0)'>" + str(id) + "</span></div></div>"
css += "</style>"
clusterdivs += "</div>"
bigclusterdivs += "</div>"
print css
print "<div style=\"width:1000px; margin-left: auto; margin-right: auto;\">"
print "<h1>Automatic Asteroid Detection & Verifier</h1>A random image from the <a href=\"http://cas.sdss.org/dr7/en/\">Sloan Digital Sky Survey</a>, with potential asteroids automatically detected and ranked by confidence. Select each actual asteroid's checkbox and press the button to validate. If none are found, simply press the button to get a new random image. <a href=\"http://dustingram.com/misc/astro/valid.py\">Click here to see all user-verified asteroids</a>.</br></br>"
print clusterdivs
print "<br/>Are any of these asteroids? <a href=\"valid.py\">Click here for some examples if you're unsure.</a><br/>"
print "<br/><form method='post' action='./detect.py'><div style='width:992px'>" + bigclusterdivs + "<div style='clear:both'></div></div><br/><input type='submit' value='None of these are Asteroids'><input type='submit' value='Verify Checked Asteroids'></form>"
print "<br/>Run: " + str(run) + ", Camcol: " + str(camcol) + ", Field:  " + str(field) + "\n<br/>Original Image: <a href=\"" + url0 + "\">" + url0 + "</a><br/>" + "Permalink to this page: <a href=\"" + "./detect.py?R=" + str(run) + "&C=" + str(camcol) + "&F=" + str(field) + "\">link</a><br/>"
print "<br/>Created by <a href=\"mailto:dsi23@drexel.edu\">Dustin Ingram</a> and <a href=\"mailto:ar374@drexel.edu\">Aaron Rosenfeld</a>"
print "</div>"
print "</html>"

