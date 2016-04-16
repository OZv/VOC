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
import json
import string
import random
import urllib
import requests
import fileinput
from os import path
from datetime import datetime
from collections import OrderedDict
from bs4 import SoupStrainer
from bs4 import BeautifulSoup


ENTLINK = '<a href="entry://%s">%s</a>'
styled = {'v': '#539007', 'n': '#e3412f', 'j': '#f8b002', 'd': '#684b9d'}
session = None
dict = OrderedDict()
style = {}
base_dir = ''


def addref(word, type, clean=False):
    if word in dict:
        if type == 2:
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


def addrefs(html, type, clean=False):
    p = re.compile(r'<a>([^</>]+)</a>')
    html = p.sub(lambda m: addref(m.group(1), type, clean), html)
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


def randomstr(digit):
    return ''.join(random.sample(string.ascii_lowercase, 1)+
        random.sample(string.ascii_lowercase+string.digits, digit-1))


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
        self.__inst = OrderedDict()
        sdt = ''
        for dl in dll:
            dt = dl.find('dt').string
            sdt = dt if dt else sdt
            dds = dl.find_all('dd')
            dx = dl.find('dx')
            if dx:
                dds.extend(dd_ext[dx.string])
            sddl = ['<br>']
            sddl.extend(self.__transdd(dds))
            if not sdt in self.__inst:
                self.__inst[sdt] = []
            self.__inst[sdt].extend(sddl)

    def __transdd(self, dds):
        sddl = []
        for dd in dds:
            for a in dd.find_all('a', href=re.compile('javascript:')):
                a.decompose()
            al = dd.find_all('a')
            [a.attrs.clear() for a in al]
            divs = dd.find_all('div', {'class': 'definition'})
            for div in divs:
                div['class'] = 'g'
            sdd = unwraptag(dd)
            if sdd:
                sddl.append(sdd)
        return sddl

# start formatting from here
    def htmlstring(self, type, style):
        sty = propstyle(self.__propstr)
        k = ''.join(['a.', sty])
        if not k in style:
            style[k] = ''.join(['background-color:', styled[sty]])
        html = self.__prop % ''.join(['p ', sty])
        htmls = [html, ' <span class=t>', self.__meaning, '</span>']
        if self.__examples:
            htmls.append('<div class="d n">')
            for example in self.__examples:
                htmls.append(example)
                htmls.append('<br>')
            htmls[-1] = '</div>'
        CAPSTY = '<span onclick="v0r.h(this,%d)"class=y_>%s</span>'
        TXSTY = '<div class=p>%s</div>'
        caps = []
        txts = []
        if self.__inst:
            i = 0
            for caption, vl in self.__inst.iteritems():
                if type==0 and caption.startswith('Synonym'):
                    caption = 'Syn'
                elif type==0 and caption.startswith('Antonym'):
                    caption = 'Ant'
                elif type==0 and caption.startswith('Example'):
                    caption = 'Exp'
                elif caption.startswith('Types'):
                    if type != 0:
                        break
                    caption = 'Hypo'
                elif caption.startswith('Type of'):
                    if type != 0:
                        break
                    caption = 'Hyper'
                caps.append(CAPSTY % (i, caption.rstrip(':')))
                i += 1
                assert vl
                txts.append(TXSTY % addrefs(''.join(vl), type))
        if caps:
            htmls.extend(['<div class=y>', '<span class="h">|</span>'.join(caps), '</div>'])
        if txts:
            htmls.append('<div>')
            htmls.extend(txts)
            htmls.append('</div>')
        return htmls


class Example:
# usage example data structure
    def __init__(self, rawdata):
        self.__offsets = rawdata['offsets']
        self.__sentence = rawdata['sentence']
        vol = rawdata['volume']
        id = vol['corpus']['id']
        date = 'datePublished' if 'datePublished' in vol else 'dateAdded'
        if id=='LIT' or id=='GUT':
            title = vol['title']
            if len(title) > 35:
                title = ''.join(['<i title="', title.replace('"', '&quot;'), '">', title[:35].rstrip(' \n\r'), '</i>...'])
            else:
                title = ''.join(['<i>', title, '</i>'])
            p = re.compile(r'[\r\n]+')
            title = p.sub('\xE2\x80\x94', title)
            self.__corpusname = ''.join([vol['author'], ', ', title])
            self.__date = vol[date][:4]
        else:
            self.__corpusname = vol['corpus']['name']
            if int(vol[date][:4]) <= 1900:
                date = 'dateAdded'
            dt = datetime.strptime(vol[date][:10], '%Y-%m-%d')
            self.__date = dt.strftime('%b %d, %Y')


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
    def __init__(self, word=None, worddef=None, filter=None, usage=None, digest=None):
        if digest:
            self.__hasblurb = digest[0]
            self.__dumped = digest[1]
            self.__ffreq = digest[2]
            self.__filter = digest[3]
        else:
            self.__title = None
            self.__prns = []
            self.__sblurb = None
            self.__lblurb = None
            self.__hasblurb = False
            self.__chswdTt = None
            self.__chswdHd = None
            self.__chswdBd = None
            self.__fuldefs = [] # [[]]
            self.__fuldefindex = [] # [[]]
            self.__ffreq = -1
            self.__wdfrq = None
            self.__wdfmls = {}
            self.__dumped = False
            self.__dd_ext = {}
            self.__filter = filter
            if worddef and self.__initdef(word, worddef):
                self.initusage(usage)

    @property
    def digest(self):
        return [int(self.__hasblurb), int(self.__dumped), self.__ffreq, self.__filter]

    @property
    def title(self):
        return self.__title

    @property
    def hasblurb(self):
        return self.__hasblurb

    @property
    def dumped(self):
        return self.__dumped

    @property
    def ffreq(self):
        return self.__ffreq

    @property
    def filter(self):
        return self.__filter

    @property
    def html(self):
        return self.__htmlstring(0)

    @property
    def htmlBasic(self):
        return self.__htmlstring(1)

    @property
    def htmlLite(self):
        return self.__htmlstring(2)

    @property
    def usage(self):
        htmls = []
        for usage in self.__usages:
            htmls.append(usage.htmlstring)
        self.__dumped = True
        return ''.join(htmls)

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
        al = h1.find_all('a', class_='audio')
        if al:
            for a in al:
                self.__prns.append(str(a['data-audio']))

    def __transfchswdBd(self, div, link):
        tl = div.find_all(lambda e:
            (e.name=='p' or e.name=='a' or e.name=='div') and e.get_text(strip=True)=='')
        for tag in tl:
            tag.unwrap()
        tl = div.find_all(lambda e: e.name!='img')
        for tag in tl:
            del tag['class']
            del tag['id']
        sml = div.find_all('small')
        for sm in sml:
            sm.name = 'span'
            sm['class'] = 'r'
            if sm.parent.name=='em':
                sm.parent.replace_with(sm)
        pl = div.find_all('p', align='center')
        for p in pl:
            p.attrs.clear()
            p.name = 'div'
            p['class'] = 'e'
        pl = div.find_all('p')
        for p in pl:
            p['class'] = 'i'
        bl = div.find_all('blockquote')
        for blk in bl:
            pl = blk.find_all('p')
            if len(pl) == 1:
                pl[0].name = 'div'
                pl[0]['class'] = 'g q'
                blk.replace_with(pl[0])
            else:
                for p in pl:
                    p['class'] = 'q'
                blk.name = 'div'
                blk['class'] = 'g q'
        il = div.find_all('img')
        p = re.compile(r'font-size\s*:\s*\d+\s*(?:px|em|%)\s*;?\s*', re.I)
        for img in il:
            if 'class' in img.attrs and img['class'][0]=='main':
                img.extract()
                continue
            for attr in ['alt', 'class', 'width', 'height']:
                del img[attr]
            if img.previous_sibling and img.previous_sibling.name == 'img':
                img['style'] = 'margin:2px'
            if 'style' in img.attrs:
                img['style'] = p.sub('', img['style'])
                if len(img['style'].strip()) == 0:
                    del img['style']
            file, ext = path.splitext(img['src'])
            file = path.sep.join(['p', ''.join([randomstr(4), ext])])
            url = urllib.quote(img['src'])
            if url[0] != '/':
                url = ''.join([link, url])
            dump(getpage(url), file, 'wb')
            img['src'] = file.replace(path.sep, '/')
        adl = div.find_all('audio')
        for ad in adl:
            if 'src' in ad.attrs:
                src = ad['src']
            else:
                src = ad.source['src']
            del ad.contents[:]
            ad.name = 'img'
            ad.attrs.clear()
            ad['src'] = 'q.png'
            ad['onclick'] = ''.join(['v0r.l(this,\'', src, '\')'])
        sl = div.find_all('source')
        for source in sl:
            if source.parent.name == 'div':
                source.extract()
        self.__chswdBd = unwraptag(div).strip()
        p = re.compile(r'<iframe[^>]*>(\s*)</iframe>', re.I)
        self.__chswdBd = p.sub(r'\1', self.__chswdBd)
        p = re.compile(r'(</?)\s*strong\s*(?=>)', re.I)
        self.__chswdBd = p.sub(r'\1b', self.__chswdBd)
        p = re.compile(r'(</?)\s*em\s*(?=>)', re.I)
        self.__chswdBd = p.sub(r'\1i', self.__chswdBd)
        p = re.compile(r'\s+')
        self.__chswdBd = p.sub(r' ', self.__chswdBd)
        p = re.compile(r'\s*<br/?>\s*(</?div)')
        self.__chswdBd = p.sub(r'\1', self.__chswdBd)
        p = re.compile(r'\s*</img>\s*')
        self.__chswdBd = p.sub('', self.__chswdBd)

    def __getmore(self, link):
        page = getpage(link)
        article = SoupStrainer('div', class_='articlebody')
        soup = BeautifulSoup(page, parse_only=article)
        div = soup.find('div', {'class': 'articlebody'})
        assert div
        self.__transfchswdBd(div, link)

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
            self.__chswdTt = divbar.h3.string.rstrip(': ').upper()
            self.__chswdHd = divbar.h4.string
            a = divbar.find('a', {'class': 'readMore'})
            if a and a['href']:
                link = ''.join(['/', a['href'].strip('/ '), '/'])
                self.__getmore(link)
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
        wpg = SoupStrainer('div', class_=re.compile('[^<>]*?wordPage[^<>]*?'))
        soup = BeautifulSoup(data, parse_only=wpg)
        div = soup.find('div', class_=re.compile('[^<>]*?wordPage[^<>]*?'))
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
        tag = find_fulldefine(tags, re.compile(r'DEFINITIONS OF', re.I))
        if tag:
            self.__getfulldef(tag.parent)
        else:
            print("WARNING: %s HAS NO FULLDEFINITION" % self.__title)
            assert tag # to raise error and break
        div = soup.find('div', {'class': 'section family'})
        if div:
            self.__getwordfamily(div)
        return True

    def initusage(self, usage):
        if usage:
            sentences = usage['result']['sentences']
            self.__usages = []
            self.__dumped = False
            for sentence in sentences:
                exp = Example(sentence)
                self.__usages.append(exp)
# start formatting from here
    def __formatdefindex(self, style, type):
        htmls = []
        if type == 2:
            LNK = '<a class="o %s">%s</a>'
        else:
            LNK = '<a href="entry://#%s"class="o %s">%s</a>'
        if len(self.__fuldefindex) == 1:
            for prop, name in self.__fuldefindex[0]:
                if type == 2:
                    htmls.append(LNK % (propstyle(prop), prop))
                else:
                    htmls.append(LNK % (name[0], propstyle(prop), prop))
        else:
            index = 1
            style['span.m'] = 'color:gray;margin-right:5px'
            GRP = '<span class=m>%d</span>'
            for defidx in self.__fuldefindex:
                htmls.append(GRP % index)
                index += 1
                for prop, name in defidx:
                    if type == 2:
                        htmls.append(LNK % (propstyle(prop), prop))
                    else:
                        htmls.append(LNK % (name[0], propstyle(prop), prop))
                htmls.append(' ')
            htmls[-1] = htmls[-1].rstrip()
        if htmls:
            style['div.h'] = 'font-family:Helvetica;font-weight:bold'
            htmls.insert(0, '<div class=h>')
            htmls.append('</div>')
        return htmls

    def __formatsidebar(self):
        return ['<fieldset class=a>',
                '<legend><span class=d>', self.__chswdTt, '</span></legend>',
                '<div class="l t">', self.__chswdHd, '</div><div class="i_">',
                self.__chswdBd, '</div><img src="x.png"onclick="v0r.x(this)"class=i_></fieldset>']

    def __hastitleword(self, v):
        for c in v[1]:
            if c == self.__title:
                return True
        return False

    def __formatwfgrp(self, htmls, p, v, type):
        htmls.append('<b>%s</b>: ' % addref(p, type))
        for c in v[1]:
            htmls.append(addref(c, type))
            htmls.append(', ')
        htmls[-1] = htmls[-1].rstrip(':, ')
        return htmls

    def __formatwdfmls(self, type):
        htmls = []
        hide = []
        if self.__title in self.__wdfmls:
            self.__formatwfgrp(htmls, self.__title, self.__wdfmls[self.__title], type)
        for p, v in sorted(self.__wdfmls.items(), key=lambda d: d[1][0]):
            if not htmls and self.__hastitleword(v):
                self.__formatwfgrp(htmls, p, v, type)
            elif p != self.__title:
                hide.append('|')
                self.__formatwfgrp(hide, p, v, type)
        if not htmls:
            raise AssertionError('%s'%self.__title)
        if hide:
            html = ''.join([''.join(htmls), '<span  onclick="v0r.o(this)"class=s_>+</span><span class=w_>', ''.join(hide), '</span>'])
            p =re.compile(r'(?<=<span class=w_>)\|')
            html = p.sub(r'<span onclick="v0r.b(this)"class=h>/</span>', html)
        else:
            html = ''.join(htmls)
        return ''.join(['<div class=a>', html.replace('|', '<span class=h>/</span>'), '</div>'])

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
                style['div.c'] = 'margin-left:1.2em;position:relative'
            style['span.o'] = 'display:inline-block;padding-top:2px;position:absolute;left:-1.1em'
            NSTYLE = '<span class=o>%d</span>'
            for define in defl:
                htmls.append('<div class=c>')
                htmls.append(NSTYLE % index)
                index += 1
                htmls.extend(define.htmlstring(type, style))
                htmls.append('</div>')
        return htmls

    def __fixanchor(self, html):
        for item in self.__fuldefindex:
            for k, v in item:
                html = html.replace(v[0], randomstr(4))
        return html

    def __htmlstring(self, type):
        style['div.t'] = 'font-family:"Lucida Grande","Open Sans","Lucida Sans Unicode"'
        style['div.b'] = 'color:blue;font-weight:bold;font-size:120%'
        style['div.m'] = 'padding-top:0.5em'
        MARGIN = '<div class=m></div>'
        acr = randomstr(4)
        htmls = ['<div class="b t"id="v5A"><a id="%s"></a>'%acr, self.__title]
        style['img.m'] = 'margin-left:0.6em;width:16px;height:16px;cursor:pointer'
        AUDIO = '<img src="p.png"onclick="v0r.v(this,\'%s\')"class=m>'
        for prn in self.__prns:
            htmls.append(AUDIO % prn)
        htmls.append('</div>')
        style['div.a'] = 'font-family:Helvetica'
        style['div.g'] = 'color:gray'
        style['div.d'] = 'font-size:90%'
        style['div.n'] = 'letter-spacing:0.5px;color:#369'
        FREQ = '<div class="a g d">(%s)</div>'
        htmls.append(FREQ % self.__wdfrq)
        htmls.append('<div class=v_>')
        style['div.v_'] = 'margin-top:1em'
        style['div.v_ i'] = 'font-family:"georgia","times"'
        style['a.p'] = 'text-decoration:none;padding:0 5px 1px;font-size:70%;font-weight:bold;color:white'
        style['a.o'] = 'text-decoration:none;padding:0 5px 1px;margin-right:3px;font-size:70%;font-weight:bold;color:white'
        htmls.extend(self.__formatdefindex(style, type))
        htmls.append('<hr class=s>')
        style['hr.s'] = 'height:1px;border:none;border-top:1px gray dashed;margin:2px 0'
        style['span.b'] = 'font-weight:bold;background-color:gray;color:white'
        if self.__hasblurb or self.__chswdHd:
            style['span.s'] = 'color:green'
            style['div.i'] = 'text-indent:1.2em'
        if self.__sblurb:
            style['div.s'] = 'font-size:110%'
            htmls.append(self.__sblurb)
        if self.__lblurb:
            htmls.append(self.__lblurb)
        style['span.c'] = 'font-family:"Trebuchet MS";font-size:80%;padding:0 3px 0 3px;letter-spacing:1px;border-radius:3px'
        SECHD = '<span class="b c">%s</span><br>'
        if self.__chswdHd:
            style['div.l'] = 'color:green;font-weight:bold'
            style['div.q'] = 'padding:0.3em 2.4em 0.3em'
            style['div.e'] = 'text-align:center'
            style['fieldset.a'] = 'font-family:Helvetica;border-radius:3px;border:1px dashed gray'
            style['span.d'] = 'font-family:Helvetica;font-size:90%;font-weight:bold'
            style['span.r'] = 'color:gray;font-size:90%'
            style['p.q'] = 'margin:0.3em 0'
            style['p.i'] = 'text-indent:1.2em;margin:0.3em 0'
            style['div.i_'] = 'overflow:hidden;-webkit-text-size-adjust:100%'
            style['img.i_, img.j_'] = 'width:16px;padding:0 1ex;position:relative;top:1ex;left:50%;margin-left:-1ex;cursor:pointer'
            style['img.i_:hover, img.j_:hover'] = 'background-color:#F2F2F2'
            style['img.j_'] = 'transform:scaleY(-1);-webkit-transform:scaleY(-1);filter:FlipV'
            htmls.append(MARGIN)
            htmls.extend(self.__formatsidebar())
        if self.__wdfmls:
            style['span.h'] = 'color:gray;font-family:"Trebuchet MS";padding:0 0.3em 0 0.3em'
            style['span.h[onclick]:hover'] = 'text-decoration:underline'
            style['span.s_'] = 'display:inline-block;margin-left:0.5em;padding:1px;font-size:80%;line-height:70%;font-family:Helvetica;color:#999;border:1px solid #CCC;white-space:nowrap'
            style['span.s_:hover'] = 'background-color:#EEF'
            style['span.w_'] = 'display:none'
            htmls.append(MARGIN)
            htmls.append(SECHD % 'WORD FAMILY')
            htmls.append(self.__formatwdfmls(type))
        style['div.r'] = 'font-size:80%'
        if self.__filter != '0':
            htmls.extend(['<input type="hidden"value="',
                self.__filter, '">'])
        htmls.append('<div id="vUi"class=a></div>')
        if type != 2:
            htmls.append('<div class="a m">')
            style['span.t'] = 'font-family:"Lucida Grande","Open Sans","Lucida Sans Unicode"'
            style['div.y'] = 'font-family:Helvetica;color:#398;font-size:85%;text-transform:uppercase'
            style['div.p'] = 'padding-left:1em;display:none'
            style['span.y_:hover'] = 'text-decoration:underline'
            if len(self.__fuldefs) == 1:
                htmls.extend(self.__formatfulldef(self.__fuldefs[0], type, style, False))
            else:
                index = 1
                style['div.c'] = 'margin-left:1.2em;position:relative'
                style['span.g'] = 'padding:0 5px 1px;font-family:Helvetica'
                GRP = '<span class="b g">%d</span><br>'
                for fuldef in self.__fuldefs:
                    htmls.append(GRP % index)
                    index += 1
                    htmls.extend(self.__formatfulldef(fuldef, type, style))
            htmls.append('</div>')
        htmls.append('</div>')
        self.__dumped = True
        style['span.n, span.s_, span.y_, span.h[onclick]'] = 'cursor:pointer;-webkit-user-select:none;-ms-user-select:none'
        style['span.e, span.n'] = 'display:inline-block;width:4em'
        style['span.e'] = 'cursor:default;color:gray;-webkit-user-select:none;-ms-user-select:none'
        style['span.n'] = 'color:blue'
        style['div.f'] = 'display:none;float:left;position:absolute;margin:-1.4em 0 0 -0.05em;padding-left:0.3em;width:8.5em;border:1px solid gray;border-radius:6px;box-shadow:1.5px 1.5px 3px #D9D9D9;background-color:#F2F2F2;color:gray;letter-spacing:1px;line-height:140%;font-family:Helvetica;font-size:85%;white-space:nowrap;cursor:pointer;z-index:999'
        style['div.m_'] = 'margin-top:1em'
        style['span.p'] = 'display:inline-block;line-height:110%;border:1px solid gray;border-radius:6px;box-shadow:-1px -1px 2px #D9D9D9 inset;background-color:#F2F2F2;letter-spacing:1px;font-family:Helvetica;font-size:85%;text-overflow:ellipsis;overflow:hidden;white-space:nowrap'
        style['span.k'] = 'margin:0.3em 1em 0.2em 0;padding-left:0.3em;width:8.5em;color:gray;cursor:pointer'
        style['span.q'] ='margin:0.3em 0 0.2em 0;width:8.8em'
        style['span.f'] ='display:block;text-overflow:ellipsis;overflow:hidden'
        style['span.f:hover'] = 'color:blue'
        html = self.__fixanchor(cleansp(''.join(htmls)))
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


def dump(data, file, mod='w'):
    fname = fullpath(file)
    fw = open(fname, mod)
    try:
        fw.write(data)
    finally:
        fw.close()


def removefile(file):
    if path.exists(file):
        os.remove(file)


def cleansp(html):
    p = re.compile(r'[\r\n\t]+|\s{2,}')
    html = p.sub(' ', html)
    p = re.compile(r'((?:\s|<br/?>)*)(<(?:/?(?:div|p)[^>]*|br/?)>)(?:\s|<br/?>)*', re.I)
    html = p.sub(r'\2', html)
    return html


def getpage(link, BASE_URL = 'http://www.vocabulary.com', time_out=10):
    r = session.get(''.join([BASE_URL, link]), timeout=time_out)
    if r.status_code==200:
        return r.content
    else:
        return None


def getdata(word, filter, domain=None):
    link = ['/api/1.0/examples.json?query=', urllib.quote(word),
        '&maxResults=3&startOffset=0']
    if domain:
        link.extend(['&domain=', domain])
    link.extend(['&filter=', filter])
    page = getpage(''.join(link), 'http://corpus.vocabulary.com')
    data = None
    if page:
        try:
            data = json.loads(page)
        finally:
            return data
    return data


def getfilter(page):
    p = re.compile(r'<vcom:examples[^>]+> *</vcom:examples>', re.I)
    m = p.search(page)
    p = re.compile(r'filter="(\d)"', re.I)
    m = p.search(m.group(0))
    return m.group(1)


def fetchdata(word):
    page = None
    try:
        page = getpage(''.join(['/dictionary/', urllib.quote(word)]))
    except Exception:
        print "%s failed" % word
    exm = None
    filter = None
    if page:
        filter = getfilter(page)
    return page, filter


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
    filter = None
    if page:
        filter = getfilter(page)
        exm = getdata(word, filter)
    return page, exm, filter


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
    count = 1
    for word in wordlist:
        if count % 100 == 0:
            if count % 500 == 0:
                print count,
            else:
                print ".",
        worddef, filter = fetchdata(word)
        if worddef:
            wordentry = WordData(word, worddef, filter)
            if wordentry.title:
                if not word in mdict or not mdict[word].dumped:
                    mdict[word] = wordentry
                count += 1
            else:
                failed.append(word)
        else:
            failed.append(word)
    return failed


def makeusgs(wordlist, mdict):
    failed = []
    count = 1
    for word in wordlist:
        if count % 100 == 0:
            if count % 500 == 0:
                print count,
            else:
                print "*",
        exm = None
        try:
            exm = getdata(word, mdict[word].filter)
        except Exception:
            print "%s failed." % word
        if exm:
            mdict[word].initusage(exm)
            count += 1
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


def downloadloop(mdict, wordlist, failedlist, func):
    l = len(wordlist)
    print("%s downloading...using 1 thread" % info(l))
    lenr = len(wordlist)
    leni = lenr + 1
    failed = []
    while lenr>0 and lenr<leni:
        leni = lenr
        failed = func(wordlist, mdict)
        wordlist = failed
        lenr = len(failed)
    failedlist.extend(failed)
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


def dumpstyle():
    if base_dir:
        dump(json.dumps(style, separators=(',', ':')), 'style')
    else:
        sty = []
        for k, v in sorted(style.iteritems(), key=lambda d: d[0]):
            sty.extend([k, '{', v, '}'])
        dump(''.join(sty), 'v.css')


def makeentry(key, content):
    return '\n'.join([key, ''.join(['<link rel="stylesheet"href="v.css"type="text/css">',
    content, '<script src="j.js"type="text/javascript"></script>']), '</>\n'])


def add_to_buf(buf, word, entry):
    key = word.lower()
    if key in buf:
        buf[key].append((word, entry))
    else:
        buf[key] = [(word, entry)]


def dumpwords(mdict, sfx='', finished=True):
    if mdict:
        dict.update(mdict)
        buf = [OrderedDict(), OrderedDict(), OrderedDict()]
        for word, entry in mdict.iteritems():
            if not entry.dumped:
                if entry.hasblurb:
                    add_to_buf(buf[0], word, entry.htmlLite)
                add_to_buf(buf[1], word, entry.htmlBasic)
                add_to_buf(buf[2], word, entry.html)
        filelist = ['vocabulary_lite.txt', 'vocabulary_basic.txt', 'vocabulary.txt']
        f = [fullpath(fn, sfx) for fn in filelist]
        mod = 'a' if sfx else 'w'
        fw = [open(f[i], mod) for i in xrange(0, len(f))]
        try:
            for i in xrange(0, 3):
                for k, v in buf[i].iteritems():
                    v = sorted(v, key=lambda d: d[0], reverse=True)
                    fw[i].write(makeentry(v[0][0], '<div class="m_"></div>'.join([e for w, e in v])))
            dumpstyle()
            digest = json.dumps(mdict, cls=DjEncoder, separators=(',', ':'))
            dump(digest, 'digest')
        finally:
            mdict.clear()
            [fw[i].close() for i in xrange(0, len(f))]
    if sfx and finished:
        removefile(fullpath('failed.txt'))
        fixrefs([(f[0], 2), (f[1], 1), (f[2], 0)])
        l = -len(sfx)
        cmd = '\1'
        nf = [f[i][:l] for i in xrange(0, len(f))]
        if path.exists(nf[0]) or path.exists(nf[1]):
            msg = "Found voc*.txt in the same dir, delete?(default=y/n)"
            cmd = 'y'#raw_input(msg)
        if cmd == 'n':
            return
        elif cmd != '\1':
            [removefile(nf[i]) for i in xrange(0, len(nf))]
        [os.rename(f[i], nf[i]) for i in xrange(0, len(f))]


def dumpusgs(mdict, sfx='', finished=True):
    f = fullpath('usages.txt', sfx)
    mod = 'a' if sfx else 'w'
    fw = open(f, mod)
    try:
        for word, entry in mdict.iteritems():
            if not entry.dumped and entry.usage:
                fw.write('\n'.join([word, entry.usage, '</>\n']))
        digest = json.dumps(mdict, cls=DjEncoder, separators=(',', ':'))
        dump(digest, 'digest')
    finally:
        mdict.clear()
        fw.close()
    if sfx and finished:
        removefile(fullpath('failedusg.txt'))
        l = -len(sfx)
        nf = f[:l]
        removefile(nf)
        os.rename(f, nf)


def fetchdata_and_make_mdx(mdict, inputfile, suffix=''):
    wordlist = getwordlist(inputfile)
    l = len(wordlist)
    failedlist = []
    cmd = 'y'
    while not cmd or cmd.lower()=='y':
        cmd = downloadloop(mdict, wordlist, failedlist, makewords)
        wordlist = failedlist
        failedlist = []
    f = len(wordlist)
    print "%s downloaded" % info(l-f),
    if wordlist:
        dump('\n'.join(wordlist), 'failed.txt')
        print ", %s failed, please look at failed.txt." % info(f)
        dumpwords(mdict, '.part', False)
    else:
        print ", 0 word failed"
        dumpwords(mdict, suffix)


def fetch_usg(mdict, inputfile, suffix=''):
    wordlist = getwordlist(inputfile)
    l = len(wordlist)
    failedlist = []
    cmd = 'y'
    while not cmd or cmd.lower()=='y':
        cmd = downloadloop(mdict, wordlist, failedlist, makeusgs)
        wordlist = failedlist
        failedlist = []
    f = len(wordlist)
    print "%s downloaded" % info(l-f),
    if wordlist:
        dump('\n'.join(wordlist), 'failedusg.txt')
        print ", %s failed, please look at failedusg.txt." % info(f)
        dumpusgs(mdict, '.part', False)
    else:
        print ", 0 word failed"
        dumpusgs(mdict, suffix)


def start(dir, diff):
    global base_dir
    base_dir = dir
    if base_dir:
        base_dir = base_dir.strip('/\\ ').replace('/', '\\')
        base_dir = ''.join([path.sep.join(base_dir.split('\\')), path.sep])
    picdir = fullpath('p')
    if not path.exists(picdir):
        os.mkdir(picdir)
    fp1 = fullpath('digest')
    if diff != 'e':
        fp2 = fullpath('vocabulary.txt.part')
        fp3 = fullpath('failed.txt')
        if path.exists(fp1) and path.exists(fp2) and path.exists(fp3):
            print "Continue last failed"
            mdict = json.loads(readdata('digest'), object_hook=to_worddata)
            fetchdata_and_make_mdx(mdict, 'failed.txt', '.part')
        elif not path.exists(fp1):
            print "New session started"
            mdict = OrderedDict()
            fetchdata_and_make_mdx(mdict, 'wordlist.txt')
    else:
        if not path.exists(fullpath('usages.txt')) and path.exists(fp1) and path.exists(fullpath('vocabulary.txt')):
            mdict = json.loads(readdata('digest'), object_hook=to_worddata)
            if path.exists(fullpath('usages.txt.part') and fullpath('failedusg.txt')):
                print "Downloading usages, continue last failed"
                fetch_usg(mdict, 'failedusg.txt', '.part')
            else:
                print "Downloading usages, new session started"
                fetch_usg(mdict, 'wordlist.txt')


if __name__=="__main__":
    import sys
    reload(sys)
    sys.setdefaultencoding('utf-8')
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", nargs="?", help="sub dir under cwd")
    parser.add_argument("index", nargs="?", help="block number")
    parser.add_argument("diff", nargs="?", help="[e] to download usages")
    args = parser.parse_args()
    import socket
    socket.setdefaulttimeout(120)
    if args.index:
        no = ' ' + args.index
    else:
        no = ''
    HEADER = 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
    session = requests.Session()
    session.headers['User-Agent'] = HEADER
    print "Block%s start at %s" % (no, datetime.now())
    start(args.dir, args.diff)
    print "Block%s finished at %s" % (no, datetime.now())
    print "\nDone."
