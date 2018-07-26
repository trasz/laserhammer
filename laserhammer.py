#!/usr/bin/env python3

import datetime
import re
import sys
import xml.etree.ElementTree

def unnewline(s):
    if not s:
        return ''

    t = ''
    tlen = 0
    for word in s.split():
        if tlen + len(word) >= 79 or (tlen > 0 and t[-1] in ['.', '!', '?']):
            t = t + '\n'
            tlen = 0
#            if word[0] == '.':
#                t = t + '\\&'
#                print('t = "' + t + '"')
        elif tlen > 0:
            t = t + ' '
            tlen = tlen + 1

        t = t + word
        tlen = tlen + len(word)

    return t

# Can't use ElementTree's .find(), as it can't be told to ignore namespaces.
def subfind(elt, name):
    for child in elt:
        tag = re.sub('\\{.*\\}', '', child.tag)
        if tag == name:
            return child

    sys.exit('<%s> not found' % name)

def get_title(elt):
    info = subfind(elt, 'info')
    title = subfind(info, 'title')
    title = title.text.replace(' ', '-').upper().replace('FREEBSD-', '')

    return title

def get_date(elt):
    info = subfind(elt, 'info')
    pubdate = subfind(info, 'pubdate')
    date = pubdate.text.split()
    parsed_date = datetime.datetime.strptime(date[3], '%Y-%m-%d')
    date = parsed_date.strftime('%b %d, %Y')

    return date

def lh(t, pp_allowed=True):
    literal = False
    tag = re.sub('\\{.*\\}', '', t.tag)

    if tag == 'info':
        return ''
    if tag == 'preface':
        return ''
    if tag == 'indexterm':
        return ''
    if tag == 'citerefentry':
        s = '\n.Xr %s %s\n' % (t[0].text, t[1].text)
        return s

    if tag == 'quote':
        s = '\n.Do\n'
    elif tag == 'trademark' or tag == 'acronym' or tag == 'command' or tag == 'filename':
        s = ' '
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        s = '\n.Bd -literal -offset indent\n'
        literal = True
    elif tag == 'listitem':
        s = '\n.It\n'
        pp_allowed = False
    elif tag == 'itemizedlist' or tag == 'variablelist':
        s = '\n.Bl -bullet -offset -compact\n'
    elif tag == 'para' and pp_allowed:
        s = '\n.Pp\n'
    else:
        s = ''

    if t.text:
        if literal:
            s = s + t.text
        else:
            s = s + unnewline(t.text)

    for elt in t:
        s = s + lh(elt, pp_allowed)
        if elt.tail:
            if literal:
                s = s + elt.tail
            else:
                s = s + unnewline(elt.tail)

    if tag == 'quote':
        s = s + '\n.Dc '
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        s = s + '\n.Ed\n'
    elif tag == 'itemizedlist' or tag == 'variablelist':
        s = s + '\n.El\n'
    elif tag == 'userinput':
        # We're not doing anything for the opening tag for this one.
        s = s + '\n'
    elif tag == 'title':
        s = '\n.Sh %s\n' % unnewline(s).upper()

    return s

if len(sys.argv) != 3:
    sys.exit('usage: %s input-file output-file' % sys.argv[0])

t = xml.etree.ElementTree.parse(sys.argv[1]).getroot()
title = get_title(t)
date = get_date(t)
s = lh(t)
s = re.sub('\n+', '\n', s)
outfile = open(sys.argv[2], "w")
outfile.write('.Dd %s\n' % date)
outfile.write('.Dt %s 7\n' % title)
outfile.write('.Os\n')
outfile.write(s)
