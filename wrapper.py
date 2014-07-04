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
    def digest(self):
        return [int(self.__hasblurb), int(self.__hasType), int(self.__dumped)]


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
    while True:
        arg = []
        for i in xrange(1, times+2):
            sdir = ''.join(['mdict', path.sep, '%d'%i, path.sep])
            file = fullpath(sdir, 'digest')
            if not os.path.exists(file):
                arg.append('python.exe -u voc_fetcher0.2.py %s %d' % (sdir, i))
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
    digest = json.dumps(ddg, cls=DjEncoder, separators=(',', ':'))
    dump(digest, ''.join([dir, 'digest']))
    pImg = re.compile(r'(?<=<)(img[^>]+)(?=>)', re.I)
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
    finally:
        [fw[i].close() for i in xrange(0, 3)]
    if logs:
        dump('\n'.join(logs), ''.join([dir, 'logs.txt']))
        print "Found some warnings, please look at %slogs.txt" % fullpath(dir)
    print "".join(["\n".join(filelist), "\n", "digest"])
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
