#!/usr/bin/env python
# -*- coding: utf-8 -*-
## voc_fetcher.py
## A helpful tool to fetch data from Vocabulary.com & generate mdx source file
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
import string
import random
import urllib
import fileinput
from os import path
from datetime import datetime
from multiprocessing import Manager
from urllib3 import PoolManager
from bs4 import SoupStrainer
from bs4 import BeautifulSoup


ENTLINK = '<a href="entry://%s">%s</a>'
styled = {'v': '#539007', 'n': '#e3412f', 'j': '#f8b002', 'd': '#684b9d'}
dictType = None
cleanTag = None
dict = {}
base_dir = ''


def addref(word, type, clean=False):
    if word in dict:
        if type == 1:
            if dict[word].hasType:
                html = ENTLINK % (word, word)
            elif clean:
                html = word
            else:
                html = ''.join(['<a>', word, '</a>'])
        elif type == 2:
            if dict[word].hasblurb:
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
    return addref(m.group(1), dictType, cleanTag)


def addrefs(html, type, clean=False):
    global dictType, cleanTag
    dictType = type
    cleanTag = clean
    p = re.compile(r'<a>([^</>]+)</a>')
    html = p.sub(subref, html)
    return html


def propstyle(prop):
    return 'd' if prop=='adv' else prop[-1]


def unwraptag(tag):
    return ''.join(str(content) for content in tag.contents)


def find_fulldefine(tags, p):
    if tags:
        for tag in tags:
            if p.search(tag.get_text()):
                return tag
    return None


class Definition:
# full definition data structure
    def __init__(self, define, dd_ext):
        h3 = define.find('h3', {'class': 'definition'})
        self.__propstr = h3.a.string
        self.__prop = ''
        if 'name' in h3.a.attrs:
            self.__prop = ''.join(['<a id="', h3.a['name'], '"></a>'])
            del h3.a['name']
        self.__prop += str(h3.a.extract())
        self.__meaning = h3.get_text(strip=True)
        self.__examples = []
        content = define.find('div', {'class': 'defContent'})
        examples = content.find_all('div', {'class': 'example'})
        p = re.compile(r'^\s*[^!-~]+|[^!-~]+\s*$')
        ps = re.compile(r'(</?)strong(?=>)', re.I)
        for example in examples:
            example = p.sub('', unwraptag(example))
            example = ps.sub(r'\1b', example)
            self.__examples.append(example)
        dll = content.find_all('dl', {'class': 'instances'})
        instances = []
        index = 0
        pos = -1
        self.__hascode = [False, False]
        for dl in dll:
            sdt = dl.find('dt').string
            if sdt:
                if pos<0 and sdt.startswith('Type'):
                    pos = index
            index += 1
            dds = dl.find_all('dd')
            dx = dl.find('dx')
            if dx:
                dds.extend(dd_ext[dx.string])
            sddl = []
            if dl.dd.a['href'].startswith('javascript:'):
                sddl.extend(self.__showmore(dl.dd.a, pos))
                assert dds[1].a['href'].startswith('javascript:')
                a = self.__addcode(dds[1].a, 'h')
                sddl.extend([str(a), '<br>'])
                sddl.extend(self.__transdd(dds[2:]))
                sddl.append('</div>')
            else:
                show = []
                more = []
                for dd in dds[::-1]:
                    if 'class' in dd.attrs:
                        if dd['class'][0]=='more':
                            more.append(dd)
                            dds.remove(dd)
                    else:
                        show.append(dd)
                        dds.remove(dd)
                assert len(more)<2
                if show:
                    sddl.extend(self.__transdd(show))
                if more:
                    showmore = self.__showmore(more[0].a, pos)
                    sddl.extend(showmore)
                    showless = showmore[1].replace('s(', 'h(')
                    sddl.extend([showless.replace('more', 'less'), '<br>'])
                    sddl.extend(self.__transdd(dds))
                    sddl.append('</div>')
                else:
                    assert not dds
            instances.append({sdt: ''.join(sddl)})
        if pos>0 and pos<len(instances):
            self.__synonym = instances[:pos]
            self.__type = instances[pos:]
        elif pos == 0:
            self.__synonym = None
            self.__type = instances
        else:
            self.__synonym = instances
            self.__type = None

    def __showmore(self, a, pos):
        self.__judgeHascode(pos)
        a = self.__addcode(a, 's')
        return ['<div>', str(a), '</div><div style="display:none">']

    def __addcode(self, a, func):
        a['onclick'] = ''.join([func, '(this)'])
        del a['class']
        a.string = a.string.replace('types', 'hyponyms')
        return a

    def __transdd(self, dds):
        sddl = []
        for dd in dds:
            al = dd.find_all('a')
            for a in al:
                del a['class']
                del a['href']
            divs = dd.find_all('div', {'class': 'definition'})
            for div in divs:
                div['class'] = 'g'
            sddl.append(unwraptag(dd))
        return sddl

    def __judgeHascode(self, pos):
        if pos >= 0:
            self.__hascode[1] = True
        else:
            self.__hascode[0] = True

    @property
    def hasType(self):
        return self.__type

    def hasCode(self, type):
        return self.__hascode[type]

# start formatting from here
    def htmlstring(self, type, style):
        sty = propstyle(self.__propstr)
        k = ''.join(['a.', sty])
        if not k in style:
            style[k] = ''.join(['background-color:', styled[sty]])
        html = self.__prop % ''.join(['p ', sty])
        htmls = [html, ' <span class=t>', self.__meaning, '</span>']
        if type!=1 and self.__examples:
            htmls.append('<div class="d n">')
            for example in self.__examples:
                htmls.append(example)
                htmls.append('<br>')
            htmls[-1] = '</div>'
        if type != 1:
            instances = self.__synonym
        else:
            instances = self.__type
        CAPSTY = '<div class="y d">%s</div>'
        TXSTY = '<div class=p>%s</div>'
        if instances:
            for instance in instances:
                caption = instance.keys()[0]
                if caption:
                    if caption.startswith('Types'):
                        caption = 'Hyponyms:'
                    elif caption.startswith('Type of'):
                        caption = 'Hypernyms:'
                    htmls.append(CAPSTY % caption)
                if instance.values()[0]:
                    htmls.append(TXSTY % addrefs(instance.values()[0], type))
        return htmls


class Example:
# usage example data structure
    def __init__(self, rawdata):
        self.__offsets = rawdata['offsets']
        self.__sentence = rawdata['sentence']
        __volume = rawdata['volume']
        self.__corpusname = __volume['corpus']['name']
        date = __volume['dateAdded'][:10]
        self.__date = datetime.strptime(date, '%Y-%m-%d').strftime('%b %d, %Y')

# start formatting from here
    @property
    def htmlstring(self):
        bg = self.__offsets[0]
        ed = self.__offsets[1]
        str = self.__sentence
        html = '%s<b>%s</b>%s' % (str[:bg], str[bg:ed], str[ed:])
        STYLE = '<div class=n>%s</div><div class="g r">%s(%s)</div>'
        html = STYLE % (html, self.__corpusname, self.__date)
        return html


class WordData:
# word data structure
    def __init__(self, word=None, worddef=None, usage=None, digest=None):
        if digest:
            self.__hasblurb = digest[0]
            self.__hasType = digest[1]
            self.__dumped = digest[2]
            self.__ffreq = digest[3]
        else:
            self.__title = None
            self.__prns = []
            self.__sblurb = None
            self.__lblurb = None
            self.__hasblurb = False
            self.__chswdHd = None
            self.__chswdBd = None
            self.__fuldefs = [] # [[]]
            self.__fuldefindex = [] # [[]]
            self.__hasType = False
            self.__hascode = [False, False]
            self.__ffreq = -1
            self.__wdfrq = None
            self.__wdfmls = {}
            self.__usages = []
            self.__dumped = False
            self.__dd_ext = {}
            if self.__initdef(word, worddef):
                self.__initusage(usage)

    @property
    def digest(self):
        return [int(self.__hasblurb), int(self.__hasType), int(self.__dumped),
            self.__ffreq]

    @property
    def title(self):
        return self.__title

    @property
    def hasblurb(self):
        return self.__hasblurb

    def hasCode(self, type):
        return self.__hascode[type]

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
    def htmlBasic(self):
        return self.__htmlstring(0)

    @property
    def htmlLinguistics(self):
        return self.__htmlstring(1)

    @property
    def htmlLearners(self):
        return self.__htmlstring(2)

    def __pre_process(self, page):
    # As BeautifulSoup will cause memory I/O error when the page is too large
        if page.find('<dl')>0:
            data = page.split('<dl')
            tag_dd = SoupStrainer('dd')
            for idx in xrange(1, len(data)):
                count = data[idx].count('<dd')
                if count > 5:
                    parts = data[idx].split('</dl>')
                    dds = parts[0].split('</dd>')
                    data[idx] = ''.join([dds[0], '</dd> <dx>%d</dx>'%idx,
                        dds[-1], '</dl>', ''.join(parts[1:])])
                    self.__dd_ext[str(idx)] =[]
                    for item in dds[1:-1]:
                        dd = BeautifulSoup(item, parse_only=tag_dd).dd
                        assert dd
                        self.__dd_ext[str(idx)].append(dd)
            return '<dl'.join(data)
        else:
            return page

    def __getwordtitle(self, h1):
        self.__title = h1.get_text(strip=True)
        al = h1.find_all('a', onclick=re.compile(r'^ *VCOM.playAudio'))
        if al:
            for a in al:
                self.__prns.append(str(a['name']))

    def __transfchswdBd(self, div):
        div['class'] = 'i'
        eml = div.find_all('em')
        for em in eml:
            em.name = 'span'
            em['class'] = 's'
        bl = div.find_all('blockquote')
        for blk in bl:
            blk.name = 'div'
            blk['class'] = 'g q'
        self.__chswdBd = str(div).strip()
        p = re.compile(r'(</?)\s*strong\s*(?=>)', re.I)
        self.__chswdBd = p.sub(r'\1b', self.__chswdBd)
        p = re.compile(r'<\s*p\s*>', re.I)
        self.__chswdBd = p.sub(r'', self.__chswdBd)
        p = re.compile(r'</\s*p\s*>\s*', re.I)
        self.__chswdBd = p.sub(r'<br>', self.__chswdBd)
        p = re.compile(r'\s+')
        self.__chswdBd = p.sub(r' ', self.__chswdBd)
        p = re.compile(r'\s*<br>\s*(</?div)')
        self.__chswdBd = p.sub(r'\1', self.__chswdBd)

    def __getmore(self, link):
        page = getpage(urllib.quote(link))
        article = SoupStrainer('div', class_='articlebody')
        soup = BeautifulSoup(page, parse_only=article)
        div = soup.find('div', {'class': 'articlebody'})
        assert div
        self.__transfchswdBd(div)

    def __getblurb(self, div):
        ps = div.find('p', {'class': 'short'})
        if ps:
            ps.name = 'div'
            ps['class'] = 'i t s'
            il = ps.find_all('i')
            for i in il:
                i.name = 'span'
                i['class'] = 's'
            self.__sblurb = str(ps).strip()
        pl = div.find('p', {'class': 'long'})
        if pl:
            pl.name = 'div'
            pl['class'] = 'a i'
            self.__lblurb = str(pl).strip()
        divbar = div.find('div', {'class': 'sidebar'})
        if divbar:
            self.__chswdHd = divbar.h4.string
            a = divbar.find('a', {'class': 'readMore'})
            if a and a['href']:
                self.__getmore(a['href'])
            else:
                div = divbar.find('div', {'class': 'body'})
                if div.a:
                    div.a.extract()
                self.__transfchswdBd(div)

    def __getfulldef(self, tag):
        grps = tag.find_all('div', {'class': 'group'})
        idx = 1
        for grp in grps:
            defs = grp.find_all('div', class_=re.compile(r'sord\d$'))
            defl = []
            propd ={}
            for define in defs:
                h3 = define.find('h3', {'class': 'definition'})
                if h3 and h3.a:
                    h3.a['class'] = '%s'
                    h3.a['href'] = 'entry://#_anchor_'
                    del h3.a['title']
                    h3.a.string = h3.a.string.strip()
                    if not h3.a.string in propd:
                        h3.a['name'] = '__%d__' % idx
                        propd[h3.a.string] = (h3.a['name'], idx)
                        idx += 1
                    else:
                        del h3.a['name']
                definition = Definition(define, self.__dd_ext)
                if not self.__hasType and definition.hasType:
                    self.__hasType = True
                for i in xrange(0, 2):
                    if not self.__hascode[i] and definition.hasCode(i):
                        self.__hascode[i] = True
                defl.append(definition)
            propd = sorted(propd.items(), key=lambda d: d[1][1])
            self.__fuldefindex.append(propd)
            self.__fuldefs.append(defl)

    def __getwordfamily(self, div):
        wordfamily = div.find('vcom:wordfamily')
        assert wordfamily
        data = str(wordfamily['data']).replace('&#034;', '"')
        words = json.loads(data)
        i = 0
        for word in words:
            if 'parent' in word:
                if not word['parent'] in self.__wdfmls:
                    self.__wdfmls[word['parent']] = (i, [])
                    i += 1
                self.__wdfmls[word['parent']][1].append(word['word'])
            elif not word['word'] in self.__wdfmls:
                self.__wdfmls[word['word']] = (i, [])
                i += 1
            if word['word'] == self.__title:
                if 'ffreq' in word:
                    ffreq = float(word['ffreq'])
                    if ffreq > 0.0:
                        pgc = int(4000/ffreq)+1
                        self.__wdfrq = ''.join(['once / ', str(pgc),
                         ' page', 's' if pgc>1 else ''])
                        self.__ffreq = pgc
                    else:
                        self.__wdfrq = 'extremely rare'
                else:
                    self.__wdfrq = 'extremely rare'

    def __initdef(self, word, data):
        data = self.__pre_process(data)
        wpg = SoupStrainer('div', class_='wordPage')
        soup = BeautifulSoup(data, parse_only=wpg)
        div = soup.find('div', {'class': 'wordPage'})
        assert div
        self.__getwordtitle(div.h1)
        if word != self.__title:
            self.__title = None
            return False
        div = soup.find('div', {'class': 'section blurb'})
        if div:
            self.__hasblurb = True
            self.__getblurb(div)
        tags = soup.find_all(re.compile(r'div|h2'), class_='sectionHeader')
        tag = find_fulldefine(tags, re.compile(r'DEFINITIONS OF'))
        if tag:
            self.__getfulldef(tag.parent)
        else:
            print("WARNING: %s HAS NO FULLDEFINITION" % self.__title)
            assert tag # to raise error and break
        div = soup.find('div', {'class': 'section family'})
        if div:
            self.__getwordfamily(div)
        return True

    def __initusage(self, usage):
        if usage:
            sentences = usage['result']['sentences']
            for sentence in sentences:
                exp = Example(sentence)
                self.__usages.append(exp)
# start formatting from here
    def __formatdefindex(self, style):
        htmls = []
        LNK = '<a href="entry://#%s"class="p %s">%s</a> '
        if len(self.__fuldefindex) == 1:
            for prop, name in self.__fuldefindex[0]:
                htmls.append(LNK % (name[0], propstyle(prop), prop))
        else:
            index = 1
            style['span.m'] = 'color:gray;margin-right:5px'
            GRP = '<span class=m>%d</span>'
            for defidx in self.__fuldefindex:
                htmls.append(GRP % index)
                index += 1
                for prop, name in defidx:
                    htmls.append(LNK % (name[0], propstyle(prop), prop))
        if htmls:
            htmls.insert(0, '<div style="font-family:Helvetica;word-break:break-all"><b>')
            htmls.append('</b></div>')
        return htmls

    def __formatsidebar(self):
        FIELD = '<fieldset style="font-family:Arial;font-size:90%%;border-radius:3px;border:1px dashed gray"><legend><span style="font-family:Helvetica"><b>CHOOSE YOUR WORDS</b></span></legend>%s</fieldset>'
        html = '<div class="l t"><b>%s</b></div>%s'
        html %= (self.__chswdHd, self.__chswdBd)
        html = FIELD % html
        return html

    def __formatwdfmls(self, type):
        htmls = ['<div class=a>']
        for p, v in sorted(self.__wdfmls.items(), key=lambda d: d[1][0]):
            htmls.append('<b>%s</b>: ' % addref(p, type))
            for c in v[1]:
                htmls.append(addref(c, type))
                htmls.append(', ')
            htmls[-1] = htmls[-1].rstrip(':, ')
            htmls.append('|')
        html = ''.join(htmls).rstrip('|')
        return ''.join([html.replace('|', '<span class=h>/</span>'), '</div>'])

    def __formatfulldef(self, defl, type, style, lmargin=True):
        htmls = []
        if len(defl) == 1:
            if lmargin:
                htmls.append('<div class=c>')
                htmls.extend(defl[0].htmlstring(type, style))
                htmls.append('</div>')
            else:
                htmls = defl[0].htmlstring(type, style)
        else:
            index = 1
            if not lmargin:
                style['div.c'] = 'margin-left:1.2em'
            style['div.o'] = 'float:left;overflow:hidden;width:1em;padding-right:4px;text-align:right;'
            NSTYLE = '<div class="o t">%d</div>'
            for define in defl:
                htmls.append(NSTYLE % index)
                index += 1
                htmls.append('<div class=c>')
                htmls.extend(define.htmlstring(type, style))
                htmls.append('</div>')
        return htmls

    def __rdmstr(self):
        return ''.join(random.sample(string.ascii_letters, 1)+
                    random.sample(string.ascii_letters+string.digits, 3))

    def __fixanchor(self, html):
        for item in self.__fuldefindex:
            for k, v in item:
                html = html.replace(v[0], self.__rdmstr())
        return html

    def __htmlstring(self, type):
        style = {}
        style['div.t'] = 'font-family:Tahoma'
        style['div.b'] = 'color:blue;font-size:120%'
        TITLE = '<div class="b t"id="v5A"><a id="%s"></a><b>%s</b>'
        style['div.m'] = 'margin-top:0.5em'
        MARGIN = '<div class=m></div>'
        acr = self.__rdmstr()
        htmls = [TITLE % (acr, self.__title)]
        if type != 1:
            AUDIO = '<img src="p.png"style="margin-left:0.6em;width:16px;height:16px;cursor:pointer"onclick="l(this,\'%s\')"/>'
            for prn in self.__prns:
                htmls.append(AUDIO % prn)
        htmls.append('</div>')
        style['div.a'] = 'font-family:Arial'
        style['div.g'] = 'color:gray'
        style['div.d'] = 'font-size:90%'
        style['div.n'] = 'color:navy'
        FREQ = '<div class="a g d">(%s)</div>'
        htmls.append(FREQ % self.__wdfrq)
        htmls.append('<br>')
        style['a.p'] = 'text-decoration:none;padding:0 5px 1px;font-size:70%;font-weight:bold;color:white'
        htmls.extend(self.__formatdefindex(style))
        HR = '<hr style="height:1px;border:none;border-top:1px gray dashed">'
        htmls.append(HR)
        style['span.b'] = 'font-weight:bold;background-color:gray;color:white'
        if type != 1:
            if self.__hasblurb or self.__chswdHd:
                style['span.s'] = 'color:green'
                style['div.i'] = 'text-indent:1.2em'
            if self.__sblurb:
                style['div.s'] = 'font-size:110%'
                htmls.append(self.__sblurb)
            if self.__lblurb:
                htmls.append(self.__lblurb)
            style['span.c'] = 'font-family:\'Trebuchet MS\';font-size:80%;padding:0 3px 0 3px;letter-spacing:1px;border-radius:3px'
            SECHD = '<span class="b c">%s</span><br>'
            if self.__chswdHd:
                style['div.l'] = 'color:green'
                style['div.q'] = 'text-indent:0;padding:0.3em 2em 0.3em'
                htmls.append(MARGIN)
                htmls.append(self.__formatsidebar())
            if self.__wdfmls:
                style['span.h'] = 'color:gray;font-family:\'Trebuchet MS\';padding:0 0.3em 0 0.3em'
                htmls.append(MARGIN)
                htmls.append(SECHD % 'WORD FAMILY')
                htmls.append(self.__formatwdfmls(type))
            if self.__usages:
                style['div.r'] = 'font-size:80%'
                htmls.append(MARGIN)
                htmls.append(SECHD % 'USAGE EXAMPLES')
                htmls.append('<div id="vUi"class=a><div>')
                for usage in self.__usages:
                    htmls.append(usage.htmlstring)
                htmls.append('</div></div>')
        htmls.append('<div class="a m">')
        style['span.t'] = 'font-family:Tahoma'
        style['div.y'] = 'font-family:Helvetica;color:#2F6771;font-weight:bold'
        style['div.p'] = 'padding-left:1em'
        if len(self.__fuldefs) == 1:
            htmls.extend(self.__formatfulldef(self.__fuldefs[0], type, style, False))
        else:
            index = 1
            style['div.c'] = 'margin-left:1.2em'
            style['span.g'] = 'padding:0 5px 1px;font-family:Helvetica'
            GRP = '<span class="b g">%d</span><br>'
            for fuldef in self.__fuldefs:
                htmls.append(GRP % index)
                index += 1
                htmls.extend(self.__formatfulldef(fuldef, type, style))
        htmls.append('</div>')
        sty = ['<style>']
        for k, v in sorted(style.items(), key=lambda d: d[0]):
            sty.extend([k, '{', v, '}'])
        sty.append('</style>')
        code = '<script>function s(c){with(c.parentNode){style.display="none";nextSibling.style.display="block";}}function h(c){with(c.parentNode){previousSibling.style.display="block";style.display="none";}}</script>'
        if (type==1 and self.__hascode[1]) or (type!=1 and self.__hascode[0]):
            sty.append(code)
        if type!=1:
            sty.append('<script src="j.js"type="text/javascript"async></script><script src="http://rawgithub.com/OZv/E/G/j.js"type="text/javascript"async></script>')
        sty.extend(htmls)
        self.__dumped = True
        html = self.__fixanchor(cleansp(''.join(sty)))
        return html.replace('#_anchor_', ''.join(['#', acr]))


def fullpath(file, suffix=''):
    if base_dir:
        return ''.join([os.getcwd(), path.sep, base_dir, file, suffix])
    else:
        return ''.join([os.getcwd(), path.sep, file, suffix])


def readdata(file):
    fp = fullpath(file)
    if not path.exists(fp):
        print(file+" was not found under the same dir of this tool.")
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


def removefile(file):
    if path.exists(file):
        os.remove(file)


def cleansp(html):
    p = re.compile(r'\s+')
    html = p.sub(' ', html)
    p = re.compile(r'\s*(<(?:/div|br)>)\s*')
    html = p.sub(r'\1', html)
    p = re.compile(r'\s+(<div>)')
    html = p.sub(r'\1', html)
    return html


def getpage(link, BASE_URL = 'http://www.vocabulary.com'):
    http = PoolManager()
    r = http.request('GET', ''.join([BASE_URL, link]))
    if r.status == 200:
        return r.data
    else:
        return None


def loaddata(page):
    data = None
    if page:
        try:
            data = json.loads(page)
        finally:
            return data
    return data


def getdata(word, domain=None):
    link = ['/api/1.0/examples.json?query=', urllib.quote(word),
        '&maxResults=5&startOffset=0']
    if domain:
        link.extend(['&domain=', domain])
    data = loaddata(getpage(''.join(link), 'http://corpus.vocabulary.com'))
    if data and len(data['result']['sentences'])==0:
        link.append('&filter=2')
        data = loaddata(getpage(''.join(link), 'http://corpus.vocabulary.com'))
    return data


def fetchdata(word):
    page = None
    try:
        page = getpage(''.join(['/dictionary/', urllib.quote(word)]))
    except Exception:
        print "%s failed" % word
    exm = None
    if page:
        exm = getdata(word)
    return page, exm


def dummyfetchdata(word):
# for debug, read page from local file
    fp = ''.join([os.getcwd(), path.sep, 'dummy', path.sep, 'd_', word])
    fr = open(fp, 'rU')
    page = None
    try:
        page = fr.read()
    finally:
        fr.close()
    exm = None
    if page:
        exm = getdata(word)
    return page, exm


def getwordlist(file):
    words = readdata(file)
    if words:
        p = re.compile(r'\s*\n\s*')
        words = p.sub('\n', words).strip()
        return words.split('\n')
    print("Please put valid wordlist under the same dir with this tool.")
    return []


def makewords(wordlist, mdict):
    failed = []
    count = 0
    for word in wordlist:
        count += 1
        if count % 100 == 0:
            print ".",
        worddef, usages = fetchdata(word)
        if worddef:
            wordentry = WordData(word, worddef, usages)
            if wordentry.title:
                if not word in mdict or not mdict[word].dumped:
                    mdict[word] = wordentry
            else:
                failed.append(word)
        else:
            failed.append(word)
    return failed


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


def info(l, s='word'):
    return '%d %ss' % (l, s) if l>1 else '%d %s' % (l, s)


def downloadloop((mdict, failedlist, wordlist)):
    lenr = len(wordlist)
    leni = lenr + 1
    failed = []
    while lenr>0 and lenr<leni:
        leni = lenr
        failed = makewords(wordlist, mdict)
        wordlist = failed
        lenr = len(failed)
        time.sleep(5)
    failedlist.extend(failed)


def startdownload(wordlist, failedlist, mdict):
    l = len(wordlist)
    print("%s downloading...using 1 thread" % info(l))
    downloadloop((mdict, failedlist, wordlist))
#    pool.map(downloadloop, [(mdict, failedlist, wl) for wl in wls])
    if failedlist:
        msg = "%s failed, retry?(default=y/n)\n" % info(len(failedlist))
        return raw_input(msg)
    return 'n'


def fixrefs(files):
    global dict
    dict = json.loads(readdata('digest'), object_hook=to_worddata)
    if dict:
        cln = False if base_dir else True
        for file, typ in files:
            fw = open(''.join([file, '.tmp']), 'w')
            try:
                lines = []
                for line in fileinput.input(file):
                    line = line.strip()
                    if line == '</>':
                        fw.write(''.join([lines[0], '\n']))
                        fw.write(''.join([addrefs(lines[1], typ, cln), '\n']))
                        fw.write(''.join([line, '\n']))
                        lines = []
                    elif line:
                        lines.append(line)
            finally:
                fw.close()
            os.remove(file)
            os.rename(''.join([file, '.tmp']), file)


def dumpwords(mdict, sfx='', finished=True):
    if mdict:
        dict.update(mdict)
        filelist = ['vocabulary_Learners.txt', 'vocabulary.txt',
            'vocabulary_Linguistics.txt']
        f = [fullpath(fn, sfx) for fn in filelist]
        mod = 'a' if sfx else 'w'
        fw = [open(f[i], mod) for i in xrange(0, 3)]
        try:
            for word, entry in sorted(mdict.iteritems(), key=lambda d: d[0]):
                if not entry.dumped:
                    if entry.hasblurb:
                        fw[0].write('\n'.join([word, entry.htmlLearners, '</>\n']))
                    fw[1].write('\n'.join([word, entry.htmlBasic, '</>\n']))
                    if entry.hasType:
                        fw[2].write('\n'.join([word, entry.htmlLinguistics, '</>\n']))
            digest = json.dumps(mdict, cls=DjEncoder, separators=(',', ':'))
            dump(digest, 'digest')
        finally:
            mdict.clear()
            [fw[i].close() for i in xrange(0, 3)]
    if sfx and finished:
        fixrefs([(f[0], 2), (f[1], 0), (f[2], 1)])
        l = -len(sfx)
        cmd = '\1'
        nf = [f[i][:l] for i in xrange(0, 3)]
        if path.exists(nf[0]) or path.exists(nf[1]) or path.exists(nf[2]):
            msg = "Found voc*.txt in the same dir, delete?(default=y/n)"
            cmd = raw_input(msg)
        if cmd == 'n':
            return
        elif cmd != '\1':
            [removefile(nf[i]) for i in xrange(0, 3)]
        [os.rename(f[i], nf[i]) for i in xrange(0, 3)]


def fetchdata_and_make_mdx(mdict, inputfile, suffix=''):
    wordlist = getwordlist(inputfile)
    l = len(wordlist)
    failedlist = Manager().list()
    cmd = 'y'
    while not cmd or cmd.lower()=='y':
        cmd = startdownload(wordlist, failedlist, mdict)
        wordlist = failedlist
        failedlist = Manager().list()
    f = len(wordlist)
    print "%s downloaded" % info(l-f),
    if wordlist:
        dump('\n'.join(wordlist), 'failed.txt')
        print ", %s failed, please look at failed.txt." % info(f)
        dumpwords(mdict, '.part', False)
    else:
        print ", 0 word failed"
        dumpwords(mdict, suffix)


def start(dir):
    global base_dir
    base_dir = dir
    if base_dir:
        base_dir = base_dir.strip('/\\ ').replace('/', '\\')
        base_dir = ''.join([path.sep.join(base_dir.split('\\')), path.sep])
    fp1 = fullpath('digest')
    fp2 = fullpath('vocabulary.txt.part')
    fp3 = fullpath('failed.txt')
    if path.exists(fp1) and path.exists(fp2) and path.exists(fp3):
        print ("Continue last failed")
        mdict = json.loads(readdata('digest'), object_hook=to_worddata)
        fetchdata_and_make_mdx(mdict, 'failed.txt', '.part')
    elif not path.exists(fp1):
        print ("New session started")
        mdict = {}
        fetchdata_and_make_mdx(mdict, 'wordlist.txt')


if __name__=="__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", nargs="?", help="sub dir under cwd")
    parser.add_argument("index", nargs="?", help="block number")
    args = parser.parse_args()
    import socket
    socket.setdefaulttimeout(120)
    time.sleep(0.1)
    if args.index:
        no = ' ' + args.index
    else:
        no = ''
    print "Block%s start at %s" % (no, datetime.now())
    start(args.dir)
    print "Block%s finished at %s" % (no, datetime.now())
    print "\nDone."
