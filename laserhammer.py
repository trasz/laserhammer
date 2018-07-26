#!/usr/bin/env python3

import re
import sys
import xml.etree.ElementTree

def unnewline(s):
    if not s:
        return ''

    # Strip newlines.
    s = s.replace('\r', '').replace('\n', ' ')

    # Normalize whitespace.
    s = re.sub('[ \t]+', ' ', s)

    return s

def lh(t, pp_allowed=True):
    literal = False
    tag = re.sub('\{.*\}', '', t.tag)

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
s = lh(t)

s = re.sub('\n+', '\n', s)

outfile = open(sys.argv[2], "w")
outfile.write('.Dd fake\n')
outfile.write('.Dt fake\n')
outfile.write('.Os\n')
outfile.write(s)
