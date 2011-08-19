#!/usr/bin/python -W ignore::DeprecationWarning
import MySQLdb, MySQLdb.cursors
import os
import sys
import math
import Image
import ImageFont
import ImageDraw
import ImageStat
import ImageChops
import ImageOps
import ImageEnhance
import ImageFilter
import urllib, cStringIO, cgi, csv
import random
import time
#from images2gif import writeGif

def distance(a, b) :
    a_x, a_y = a
    b_x, b_y = b
    return math.sqrt((a_x - b_x)**2 + (a_y - b_y)**2)

def isMajority(c, c1, c2, min_dif) :
    if c > c1 and c > c2 and c - c1 > min_dif and c - c2 > min_dif :
        return True
    return False

def pointInRect(p, x1, y1, x2, y2) :
    x, y = p
    if x >= x1 and x <= x2 and y >= y1 and y <= y2 :
        return True
    return False

def getImage(url):
    return Image.open(cStringIO.StringIO(urllib.urlopen(url).read()))

def getUrl():
    form = cgi.FieldStorage()
    data = []
    data.extend(csv.reader(open("data.csv", "rb")))
    item = data.pop(random.randint(0,len(data)-1))
    if form.has_key('R'):
        run = form['R'].value
    else:
        run = item[0]
    if form.has_key('C'):
        camcol = form['C'].value
    else:
        camcol = str(random.randint(1,6))
    if form.has_key('F'):
        field = form['F'].value
    else:
        field = str(random.randint(int(item[1]), int(item[2])))
    if form.has_key('Z'):
        z = form['Z'].value
    else: 
        z='0'
    url = "http://cas.sdss.org/dr7/en/get/frameByRCFZ.asp?R=" + run + "&C=" + camcol + "&F=" + field + "&Z=" + z +             "&submit1=Get+Image"
    return url, run, camcol, field

def findPixels(px, x1, y1, x2, y2, min_dif) :
    finds = { 'r' : [], 'g' : [], 'b' : [] }
    for x in range(x1, x2) :
        for y in range(y1, y2) :
            try :
                r, g, b = px[x, y]
            except TypeError: 
                print "x:" + str(x) + " y:" + str(y)
                print "x1:" + str(x1) + " x2:" + str(x2)
                print "y1:" + str(y1) + " y2:" + str(y2)
                sys.exit(1)
            if isMajority(g, r, b, min_dif) :
                finds['g'].append((x,y))
            elif isMajority(b, r, g, min_dif) :
                finds['b'].append((x,y))
            elif isMajority(r, g, b, min_dif) :
                finds['r'].append((x,y))
    return finds

def findPairs(finds, max_dist = 10) :
    colors = { 'r' : [], 'g' : [], 'b' : [] }
    print 'finding pairs:', len(finds['g']), len(finds['b'])
    if ((len(finds['g'])*len(finds['b'])) > 1000000):
        print 'WOAH TOO MANY PAIRS'
        return [] 
    for k in ['g', 'b'] :#finds.keys() :
        fs = finds[k]
        for f in fs :
            for f2 in fs :
                if f == f2 :
                    continue
                if distance(f, f2) < float(max_dist) :
                    x, y = f
                    x2, y2 = f2
                    colors[k].append( ((x + x2)/2, (y + y2)/2) )
        colors[k] = cluster(colors[k], max_dist / 4)
        print 'done grouping', k, 'found', len(colors[k]), 'clusters'

    points = []
    for g in colors['g'] :
        for b in colors['b'] :
            x_g, y_g = g
            x_b, y_b = b
            if distance(g, b) < max_dist :
                points.append( ((x_g + x_b)/2, (y_g + y_b)/2) )
    return points

    '''points = []
    for f_g in finds['g'] :
        for f_b in finds['b'] :
            x_g, y_g = f_g
            x_b, y_b = f_b
            if distance(f_b, f_g) < max_dist :
                points.append( ((x_g + x_b)/2, (y_g + y_b)/2) )
                break
    return points'''

def cluster(points, cluster_width = 20) :
    clusters = {}
    while len(points) > 0 :
        p = points.pop()
        min_key = None
        min_value = None
        for k in clusters.keys() :
            d = distance(k, p)
            if d <= cluster_width and (min_value == None or d < min_value) :
                min_value = d
                min_key = k
        if min_key == None :
            clusters[p] = {}
            clusters[p]['sum'] = p
            clusters[p]['points'] = [p]
            clusters[p]['passes'] = 1
        else :
            clusters[min_key]['sum'] = (clusters[min_key]['sum'][0] + p[0], clusters[min_key]['sum'][1] + p[1])
            clusters[min_key]['points'].append(p)
            cnew = clusters[min_key]
            del clusters[min_key]
            clusters[ (cnew['sum'][0] / len(cnew['points']), cnew['sum'][1] / len(cnew['points'])) ] = cnew
    return clusters

def filterClusters(im, clusters, max_brights = 10) :
    ret = clusters
    w, h = im.size
    pixels = im.load()
    scan = 20
    '''for k in clusters.keys() :
        x, y = k
        brights = 0
        for xi in range(max(0, x - scan), min(w, x + scan), 2) :
            if brights > max_brights :
                break
            for yi in range(max(0, y - scan), min(h, y + scan), 2) :
                if pixels[xi, yi][0] > 120 and pixels[xi, yi][1] > 120 and pixels[xi, yi][2] > 120 :
                    brights += 1
                    if brights > max_brights :
                        break
        if brights > max_brights :
            del ret[k]'''
    for k in clusters.keys() :
        center = k
        bright = 0
        radii = range(1, 10)
        angles = range(0, 359, 45)
        for r in radii :
            for a in angles :
                x = max(0, min(w - 1, center[0] + r*math.cos(a * math.pi / 180)))
                y = max(0, min(h - 1, center[1] + r*math.sin(a * math.pi / 180)))
                if pixels[x, y][0] > 130 and pixels[x, y][1] > 130 and pixels[x, y][2] > 130 :
                    bright += 1
        if bright > .25 * len(radii) * len(angles) :
            del ret[k]
    return ret

def draw(im, clusters, iters) :
    pixels = im.load()
    w, h = im.size
    draw = ImageDraw.Draw(im)
    for k in clusters.keys() :
        x, y = k
        passes = clusters[k]['passes']
        perc = float(passes) / float(iters)
        draw.rectangle( [ (x - 20, y - 20), (x + 20, y + 20) ], outline=(0, int(perc * 255), 0) )
        draw.line([(x-20, y-20), (x, y)], fill=(0,int(perc * 255),0) )
        draw.line([(x+20, y+20), (x, y)], fill=(0,int(perc * 255),0) )
        draw.line([(x+20, y-20), (x, y)], fill=(0,int(perc * 255),0) )
        draw.line([(x-20, y+20), (x, y)], fill=(0,int(perc * 255),0) )

def process(im) :
    px = im.load()
    w, h = im.size
    min_dif = 20

    pixels = findPixels(px, 0, 0, w, h, min_dif)

    pairs = findPairs(pixels)
    clusters = cluster(pairs)
    clusters = filterClusters(im, clusters)

    print 'Clusters:', len(clusters)
    i = 1
    accepted = len(clusters)
    while accepted > 3 :
        min_dif += 2
        accepted = 0
        for k in clusters.keys() :
            x, y = k
            pixels = findPixels(px, max(0, x - 20), max(0, y - 20), min(w, x + 20), min(h, y + 20), min_dif)
            pairs = findPairs(pixels)
            if len(pairs) > 0 :
                clusters[k]['passes'] += 1
                accepted += 1
        clusters = filterClusters(im, clusters)
        print '    iter:', i, ', clusters:', accepted
        if accepted > 0 :
            i += 1
    draw(im, clusters, i)
    return im, clusters, i

class MySQL:
    def __init__(self):
        self.conn = MySQLdb.connect(db = 'nrl_asteroids', read_default_file="./.my.cnf", cursorclass=MySQLdb.cursors.DictCursor)
        self.cursor = self.conn.cursor()

    def execute(self, query):
        try:
            self.cursor.execute(query)
        except MySQLdb.OperationalError, e:
            if e[0] == 2013:
                print "Lost connection to MySQL server during query, retrying."
                self.conn.close()
                self.__init__()
                self.execute(query) #RECURSIVE!!!

if __name__ == '__main__' :
    if len(sys.argv) > 1 :
        im, _, _ = process(getImage(sys.argv[1]))
        im.save('det.jpg')
    else :
        mysql = MySQL()
        while True :
            url, run, camcol, field = getUrl()
            mysql.execute('SELECT COUNT(*) AS num FROM images WHERE run=' + str(run) + ' AND camcol=' + str(camcol) + ' AND field=' + str(field))
            if int(mysql.cursor.fetchone()['num']) == 0 :
                im, clusters, iters = process(getImage(url))
                mysql.execute('INSERT INTO images (`run`, `camcol`, `field`) VALUES (' + str(run) + ', ' + str(camcol) + ', ' + str(field) + ')')
                image_id = mysql.cursor.lastrowid
                for k in clusters.keys() :
                    x, y = k
                    passes = clusters[k]['passes']
                    mysql.execute('INSERT INTO asteroids (image_id, x, y, confidence) VALUES (' + str(image_id) + ', ' + str(x) + ', ' + str(y) + ', ' + str(float(passes) / float(iters)) + ')')
                mysql.execute('UPDATE images SET num_asteroids=' + str(len(clusters)) + ' WHERE id=' + str(image_id))
                #im.save('images/' + run + '_' + camcol + '_' + field + '.jpg')
