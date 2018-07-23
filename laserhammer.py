#!/usr/bin/env python3

import re
import sys
import xml.etree.ElementTree

def unnewline(s):
    if not s:
        return ''

    # Strip newlines.
    s = s.replace('\r', '').replace('\n', ' ')

    return s

def dump(t, off, no_para=False):
    tag = re.sub('\{.*\}', '', t.tag)

    if tag == 'info':
        return ''
    if tag == 'preface':
        return ''
    if tag == 'indexterm':
        return ''
    if tag == 'title':
        return '\n.Sh %s\n' % unnewline(t.text).upper()
    if tag == 'citerefentry':
        s = '\n.Xr %s %s\n' % (t[0].text, t[1].text)
        return s

    if tag == 'quote':
        s = '\n.Do\n%s' % unnewline(t.text)
    elif tag == 'trademark' or tag == 'acronym' or tag == 'command' or tag == 'filename':
        s = ' ' + unnewline(t.text)
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        s = '\n.Bd -literal -offset indent\n'
        if t.text:
            s = s + t.text
    elif tag == 'listitem':
        s = '\n.It\n'
        no_para = True
    elif tag == 'itemizedlist':
        s = '\n.Bl -bullet -offset -compact\n'
    elif tag == 'para' and not no_para:
        s = '\n.Pp\n%s' % unnewline(t.text)
    else:
        if t.text:
            s = unnewline(t.text)
        else:
            s = ''

    for elt in t:
        s = s + dump(elt, off + 1, no_para)
        if elt.tail:
            s = s + unnewline(elt.tail)

    if tag == 'quote':
        s = s + '\n.Dc '
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        s = s + '\n.Ed\n'
    elif tag == 'itemizedlist':
        s = s + '\n.El\n'
    elif tag == 'userinput':
        # We're not doing anything for the opening tag for this one.
        s = s + '\n'

    return s

if len(sys.argv) != 3:
    sys.exit('usage: %s input-file output-file' % sys.argv[0])

t = xml.etree.ElementTree.parse(sys.argv[1]).getroot()
s = dump(t, 0)

# Normalize whitespace.
s = re.sub('[ \t]+', ' ', s)
s = re.sub('\n+', '\n', s)

outfile = open(sys.argv[2], "w")
outfile.write('.Dd fake\n')
outfile.write('.Dt fake\n')
outfile.write('.Os\n')
outfile.write(s)
