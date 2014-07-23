#!/usr/bin/env python
# -*- coding: utf-8 -*-
## wrapper.py
## wrapper for voc_fetcher.py to support multiprocessing
##
## Copyright (C) 2014 bt4baidu@pdawiki forum
## http://pdawiki.com/forum
##
## This program is a free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, version 3 of the License.
##
## You can get a copy of GNU General Public License along this program
## But you can always get it from http://www.gnu.org/licenses/gpl.txt
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
import os
import re
import time
import json
import urllib2
from os import path
from multiprocessing import Pool


def valid_proxylist(file):
# input file format samaple: 192.192.192.192\t8080\thttp(s)\n
# output file format: http(s)://192.192.192.192:8080\thttp(s)\n
    lines = readdata(file)
    p = re.compile(r'\s*\n\s*')
    lines = p.sub('\n', lines).strip()
    lines = lines.split('\n')
    if lines:
        proxy = {}
        for line in lines:
            adr = line.split('\t')
            url = '%s:%s' % (adr[0], adr[1])
            proxy[url] = adr[2].lower()
        for k in proxy.keys():
            try:
                pxy = '%s://%s' % (proxy[k], k)
                op = urllib2.build_opener(urllib2.ProxyHandler({'http': pxy}))
                urllib2.install_opener(op)
                urllib2.urlopen('http://www.vocabulary.com/dictionary/affect',
                    timeout=2)
                time.sleep(0.05)
            except:
                del proxy[k]
        pl = [(k+chr(9)+v) for k, v in proxy.iteritems()]
        dump('\n'.join(pl), 'newproxy.txt')


def fullpath(file, suffix=''):
    return ''.join([os.getcwd(), path.sep, file, suffix])


def readdata(file):
    fp = fullpath(file)
    if not path.exists(fp):
        print(file + " was not found under the same dir of this tool.")
    else:
        fr = open(fp, 'rU')
        try:
            return fr.read()
        finally:
            fr.close()
    return None


def dump(data, file):
    fname = fullpath(file)
    fw = open(fname, 'w')
    try:
        fw.write(str(data))
    finally:
        fw.close()


def getwordlist(file):
    words = readdata(file)
    if words:
        p = re.compile(r'\s*\n\s*')
        words = p.sub('\n', words).strip()
        return words.split('\n')
    print("Please put valid wordlist under the same dir with this tool.")
    return []


ddg = {}
dictType = None
ENTLINK = '<a href="entry://%s">%s</a>'


def addref(word, type, clean=True):
    if word in ddg:
        if type == 1:
            if ddg[word].hasType:
                html = ENTLINK % (word, word)
            elif clean:
                html = word
            else:
                html = ''.join(['<a>', word, '</a>'])
        elif type == 2:
            if ddg[word].hasblurb:
                html = ENTLINK % (word, word)
            elif clean:
                html = word
            else:
                html = ''.join(['<a>', word, '</a>'])
        else:
            html = ENTLINK % (word, word)
    elif clean:
        html = word
    else:
        html = ''.join(['<a>', word, '</a>'])
    return html


def subref(m):
    return addref(m.group(1), dictType)


def addrefs(html, type):
    global dictType
    dictType = type
    p = re.compile(r'<a>([^</>]+)</a>')
    html = p.sub(subref, html)
    return html


def convref(m):
    if m.group(2) in ddg:
        if dictType == 1:
            if ddg[m.group(2)].hasType:
                return ''.join([m.group(1), 'entry://', m.group(2), '"'])
        elif dictType == 2:
            if ddg[m.group(2)].hasblurb:
                return ''.join([m.group(1), 'entry://', m.group(2), '"'])
    return ''


def convrefs(html, type):
    global dictType
    dictType = type
    p = re.compile(r'( *href=")/?dictionary/([^"]+)"')
    html = p.sub(convref, html)
    p = re.compile(r'(?<=href=")(/[^"]+")')
    html = p.sub(r'http://www.vocabulary.com\1', html)
    p = re.compile(r'(<a +href="(?:http://|www.)[^">]+") *(?=>)')
    html = p.sub(r'\1target="_blank"', html)
    return html


class WordData:
# word data structure
    def __init__(self, digest):
        if digest:
            self.__hasblurb = digest[0]
            self.__hasType = digest[1]
            self.__dumped = digest[2]
            self.__ffreq = digest[3]

    @property
    def hasblurb(self):
        return self.__hasblurb

    @property
    def hasType(self):
        return self.__hasType

    @property
    def dumped(self):
        return self.__dumped

    @property
    def ffreq(self):
        return self.__ffreq

    @property
    def digest(self):
        return [int(self.__hasblurb), int(self.__hasType), int(self.__dumped),
            self.__ffreq]


class DjEncoder(json.JSONEncoder):
# WordData to digest
    def default(self, obj):
        if isinstance(obj, WordData):
            return obj.digest
        else:
            return json.JSONEncoder.default(self, obj)


def to_worddata(dict):
    for k, v in dict.iteritems():
        dict[k] = WordData(digest=v)
    return dict


def multiprocess_fetcher(wordlist, STEP, MAX_PROCESS):
    times = int(len(wordlist)/STEP)
    words = [wordlist[i*STEP: (i+1)*STEP] for i in xrange(0, times)]
    words.append(wordlist[times*STEP:])
    i = 1
    dir = fullpath('mdict')
    if not path.exists(dir):
        os.mkdir(dir)
    for wl in words:
        subdir = ''.join(['mdict', path.sep, '%d' % i])
        subpath = fullpath(subdir)
        if not path.exists(subpath):
            os.mkdir(subpath)
        i += 1
        file = ''.join([subdir, path.sep, 'wordlist.txt'])
        if not path.exists(file):
            dump('\n'.join(wl), file)
    pool = Pool(MAX_PROCESS)
    leni = times+2
    while 1:
        arg = []
        for i in xrange(1, times+2):
            sdir = ''.join(['mdict', path.sep, '%d'%i, path.sep])
            file = fullpath(sdir, 'digest')
            if not os.path.exists(file):
                arg.append('python -u voc_fetcher0.3.py %s %d' % (sdir, i))
        lenr = len(arg)
        if len(arg) > 0:
            if lenr >= leni:
                print "The following commands cann't be performed:"
                print "\n".join(arg)
                return -1
            else:
                pool.map(os.system, arg)
        else:
            break
        leni = lenr
    return times


def makeentry(title, cnt, ordered, sty):
    htmls = []
    htmls.extend(sty)
    htmls.extend(['<div class="b t"><b>', title,
        '</b></div><div class="a g d">(', str(cnt), ' words)</div><br>',
        '<div style="width:30%;height:30%;position:absolute;z-index:-999;visibility:hidden"onresize="w()"></div><div>'])
    cata = {}
    for word, entry in ordered:
        cap = word[0:1].upper()
        if cap>='A' and cap<='Z':
            if cap in cata:
                cata[cap].append(word)
            else:
                cata[cap] = [word]
        else:
            if '~' in cata:
                cata['~'].append(word)
            else:
                cata['~'] = [word]
    cata = sorted(cata.items(), key=lambda d: d[0])
    idx = []
    txt = []
    i = 0
    for k, vl in cata:
        idx.append('<span onclick="v(this,%d)"' % i)
        if i==0:
            idx.append('style="color:#369;border:1px solid #369;background-color:#CEE3F6"')
        idx.extend(['class=x>', k, '</span>'])
        vl.sort()
        txt.append('<div class=v>')
        for v in vl:
            txt.extend(['<a>', v, '</a><br>'])
        txt[-1] = '</a>'
        txt.append('</div>')
        i += 1
    htmls.extend(idx)
    htmls.append('</div><input type="hidden"value="0"><hr style="height:1px;border:none;border-top:1px gray dashed"><div>')
    htmls.extend(txt)
    htmls.append('</div><div id="Z1w"class=t></div>')
    return ''.join(htmls)


def gen_wordlist(ordered):
    pos = 0
    for item in ordered:
        if item[1].ffreq == -1:
            pos += 1
        else:
            break
    if pos>0 and pos<len(ordered):
        head = ordered[:pos]
        del ordered[:pos]
        ordered.extend(head)
    style = {}
    style['a'] = 'text-decoration:none'
    style['div.b'] = 'color:blue;font-size:120%'
    style['div.t'] = 'font-family:Tahoma'
    style['div.a'] = 'font-family:Arial'
    style['div.g'] = 'color:gray'
    style['div.d'] = 'font-size:90%'
    style['div.v'] = 'display:none'
    style['span.x'] = 'display:inline-block;margin:0.2em;width:1em;text-align:center;padding:0.1em 0.2em 0 0.2em;border:1px solid gray;border-radius:5px;background-color:#F2F2F2;font-family:Helvetica;font-weight:bold;color:gray;cursor:pointer'
    sty = ['<style>']
    for k, v in sorted(style.items(), key=lambda d: d[0]):
        sty.extend([k, '{', v, '}'])
    sty.extend(['</style><script>function v(c,n){with(c.parentNode){var b=nextSibling;var i=parseInt(b.value);if(i==n)return;b.value=n;with(childNodes[i].style){color="";border="1px solid gray";backgroundColor="";}b=b.nextSibling.nextSibling;u(b.childNodes[n],b.nextSibling);}with(c.style){color="#369";border="1px solid #369";backgroundColor="#CEE3F6";}}function d(w){var n=parseInt(w/90)+1;return n*90-w;}',
    'function u(p,l){l.innerHTML=p.innerHTML;var n=document.createElement("span");n.style.visibility="hidden";l.appendChild(n);var h="";var w=0;for(var i=0;i<l.childNodes.length-1;i++){with(l.childNodes[i]){if(typeof(offsetWidth)=="undefined"){n.innerText=nodeValue;w=n.offsetWidth;h+="<span style=\\"display:inline-block;white-space:nowrap;margin-right:"+d(w)+"px\\">"+nodeValue+" </span>";}else if(offsetWidth){innerText+=" ";w=offsetWidth;with(style){marginRight=d(w)+"px";whiteSpace="nowrap";}h+="<span>"+outerHTML+" </span>";}}}n.innerText="";l.innerHTML=h;}',
    'function w(){var v=document.getElementsByTagName("div");for(var i=0;i<v.length;i++){with(v[i]){if(id=="Z1w"){var n=parseInt(previousSibling.previousSibling.previousSibling.value);u(previousSibling.childNodes[n],v[i]);}}}}',
    'F=0;function i(){if(!F){F=1;w();if(!window.ActiveXObject&&window.addEventListener)window.addEventListener("resize",w,false);}}if(window.addEventListener)window.addEventListener("load",i,false);else window.attachEvent("onload",i);</script>'])
    levels = [2000, 1500, 1500, 1500, 1500, 2000, 2000, 3000, 2000, 3000]
    ldict = {}
    i = 1
    start = 0
    for cnt in levels:
        if start+cnt > len(ordered):
            break
        title = 'Level-%d' % i
        ldict[title] = makeentry(title, cnt, ordered[start:start+cnt], sty)
        i += 1
        start += cnt
    return ldict


def combinefiles(times):
    dir = ''.join(['mdict', path.sep])
    mdg = fullpath(dir, 'digest')
    if path.exists(mdg):
        return
    filelist = ['vocabulary.txt', 'vocabulary_Linguistics.txt',
        'vocabulary_Learners.txt']
    mfile = [fullpath(dir, f) for f in filelist]
    fw = [open(f, 'w') for f in mfile]
    global ddg
    for i in xrange(1, times+2):
        subdir = ''.join([dir, '%d'%i, path.sep])
        data = readdata(''.join([subdir, 'digest']))
        ddg.update(json.loads(data, object_hook=to_worddata))
    print "%d entries totally." % len(ddg.keys())
    ordered = sorted(ddg.items(), key=lambda d: d[1].ffreq)
    ldict = gen_wordlist(ordered)
    dump('\n'.join(['\t'.join([w[0], str(w[1].ffreq)]) for w in ordered]),
        ''.join([dir, 'wordfreq.txt']))
    digest = json.dumps(ddg, cls=DjEncoder, separators=(',', ':'))
    dump(digest, ''.join([dir, 'digest']))
    pImg = re.compile(r'(?<=<)(img +(?!src\="p.png")[^>]+)(?=>)', re.I)
    pHref = re.compile(r'href=(?!["\'](?:entry|http|www.|javascript))[^>]+>', re.I)
    logs = []
    try:
        for idx in xrange(1, times+2):
            subdir = ''.join([dir, '%d'%idx, path.sep])
            cnt = len(getwordlist(''.join([subdir, 'wordlist.txt'])))
            fn = [''.join([subdir, f]) for f in filelist]
            mdata = [addrefs(convrefs(readdata(fn[i]).strip(), i), i) for i in xrange(0, 3)]
            warning = []
            if mdata[0].count('\n')+1 != cnt*3:
                warning.append('WARNING: Entries of file %s is not equal to its wordlist\'s' % fn[0])
            if mdata[0].count('<span class="b c">WORD FAMILY</span>') != cnt:
                warning.append('WARNING: Some entries of file %s is not completed' % fn[0])
            mdata = [pImg.sub(r'!--\1--', mdata[i]) for i in xrange(0, 3)]
            img = pImg.findall(mdata[0])
            link = pHref.findall(mdata[0])
            if warning or img or link:
                logs.append(fn[0])
                logs.extend(warning)
                logs.extend(img)
                logs.extend(link)
            [fw[i].write(''.join([mdata[i], '\n']) if mdata[i] else '') for i in xrange(0, 3)]
        for k, v in sorted(ldict.iteritems(), key=lambda d: d[0]):
            [fw[i].write('\n'.join([k, addrefs(v, i), '</>\n'])) for i in [0, 2]]
    finally:
        [fw[i].close() for i in xrange(0, 3)]
    if logs:
        dump('\n'.join(logs), ''.join([dir, 'logs.txt']))
        print "Found some warnings, please look at %slogs.txt" % fullpath(dir)
    print "".join(["\n".join(filelist), "\n", "wordfreq.txt", "\n", "digest"])
    print "was generated at %s" % fullpath(dir)


if __name__ == '__main__':
    STEP = 1000
    MAX_PROCESS = 20
    wordlist = getwordlist('wordlist.txt')
    if len(wordlist):
        times = multiprocess_fetcher(wordlist, STEP, MAX_PROCESS)
        if times >= 0:
            combinefiles(times)
        print "Done!"
    else:
        print "No word to download, please check wordlist.txt"
