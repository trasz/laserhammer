#!/usr/bin/env python3

import datetime
import re
import sys
import xml.etree.ElementTree

def reflow(s):
    if not s:
        return ''

    t = ''
    tlen = 0

    for word in s.split():
        if tlen + len(word) >= 79:
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

        if t[-1] in ['.', '!', '?']:
            t = t + '\n'
            tlen = 0

    # Preserve leading and trailing whitespace, it's crucial
    # for eg the text after acronyms.
    if s[0] == ' ':
        t = ' ' + t

    if s[-1] == ' ':
        t = t + ' '

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

    return title.text

def get_date(elt):
    info = subfind(elt, 'info')
    pubdate = subfind(info, 'pubdate')
    date = pubdate.text.split()
    parsed_date = datetime.datetime.strptime(date[3], '%Y-%m-%d')
    date = parsed_date.strftime('%b %d, %Y')

    return date

def laserhammer(elt, pp_allowed=True, below_sect1=False, below_varlistentry=False):
    literal = False
    ignore_text = False
    tag = re.sub('\\{.*\\}', '', elt.tag)

    if tag == 'info':
        return ''
    if tag == 'preface':
        return ''
    if tag == 'indexterm':
        return ''
    if tag == 'citerefentry':
        return '\n.Xr %s %s' % (elt[0].text, elt[1].text)
    if tag == 'envar':
        return '\n.Ev %s\n' % elt.text
    if tag == 'filename':
        return '\n.Pa %s' % elt.text
    if tag == 'option':
        return '\n.Ar %s' % elt.text

    mdoc = ''
    if tag == 'sect1':
        below_sect1 = True
    elif tag == 'quote':
        mdoc = '\n.Do\n'
    elif tag == 'acronym' or tag == 'application' or tag == 'command' or tag == 'link' or tag == 'trademark':
        mdoc = ''
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        mdoc = '\n.Bd -literal -offset indent\n'
        literal = True
    elif tag == 'varlistentry':
        mdoc = ''
        below_varlistentry = True
    elif tag == 'listitem':
        if not below_varlistentry:
            mdoc = '\n.It\n'
        pp_allowed = False
        ignore_text = True
    elif tag == 'itemizedlist':
        mdoc = '\n.Bl -bullet -offset -compact\n'
    elif tag == 'variablelist':
        mdoc = '\n.Bl -hang -offset -compact\n'
    elif tag == 'para' and pp_allowed:
        mdoc = '\n.Pp\n'
    elif tag == 'term' and below_varlistentry:
        mdoc = '\n.It '

    if elt.text and not ignore_text:
        if literal:
            mdoc = mdoc + elt.text
        else:
            #mdoc = mdoc + '{' + reflow(elt.text) + '}'
            mdoc = mdoc + reflow(elt.text)

    for child in elt:
        mdoc = mdoc + laserhammer(child, pp_allowed, below_sect1, below_varlistentry)
        if child.tail:
            if literal:
                mdoc = mdoc + child.tail
            else:
                #mdoc = mdoc + '{' + reflow(child.tail) + '}'
                mdoc = mdoc + reflow(child.tail)

    if tag == 'quote':
        mdoc = mdoc + '\n.Dc '
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        mdoc = mdoc + '\n.Ed\n'
    elif tag == 'itemizedlist' or tag == 'variablelist':
        mdoc = mdoc + '\n.El\n'
    elif tag == 'userinput':
        # We're not doing anything for the opening tag for this one.
        mdoc = mdoc + '\n'
    elif tag == 'term' and below_varlistentry:
        mdoc = mdoc + '\n'
    elif tag == 'title':
        if below_sect1:
            mdoc = '\n.Ss %s\n' % reflow(mdoc).upper()
        else:
            mdoc = '\n.Sh %s\n' % reflow(mdoc).upper()

    return mdoc

if len(sys.argv) != 3:
    sys.exit('usage: %s input-file output-file' % sys.argv[0])

root = xml.etree.ElementTree.parse(sys.argv[1]).getroot()
title = get_title(root)
date = get_date(root)
mdoc = laserhammer(root)
mdoc = re.sub('\n+', '\n', mdoc)

outfile = open(sys.argv[2], "w")
outfile.write('.Dd %s\n' % date)
outfile.write('.Dt %s 7\n' % title.replace(' ', '-').upper().replace('FREEBSD-', ''))
outfile.write('.Os\n')
outfile.write('.Sh NAME\n')
outfile.write('.Nm %s\n' % title.replace(' ', '-').lower().replace('freebsd-', ''))
outfile.write('.Nd %s' % title)
outfile.write(mdoc)
