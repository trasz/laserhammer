#!/usr/bin/env python3
#
# Copyright (c) 2018 Edward Tomasz Napierala <trasz@FreeBSD.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

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

        if t[-1] in ('.', '!', '?'):
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

def concat(first, second):
    if not first:
        return second
    if not second:
        return first

    if first[-1] == '\n':
        if second[0] == '\n' or second[0] == ' ':
            second = second[1:]
    if first[-1] == ' ':
        if second[0] == ' ':
            second = second[1:]

    return first + second

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
        return '\n.Xr %s %s ' % (subfind(elt, 'refentrytitle').text, subfind(elt, 'manvolnum').text)
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
        below_varlistentry = True
    elif tag == 'listitem':
        if not below_varlistentry:
            mdoc = '\n.It\n'
        pp_allowed = False
        ignore_text = True
    elif tag == 'itemizedlist':
        mdoc = '\n.Bl -bullet -offset -compact\n'
    elif tag == 'variablelist':
        mdoc = '\n.Bl -tag -offset -compact\n'
    elif tag == 'para' and pp_allowed:
        mdoc = '\n.Pp\n'
    elif tag == 'term' and below_varlistentry:
        mdoc = '\n.It '

    if elt.text and not ignore_text:
        if literal:
            mdoc = mdoc + elt.text
        else:
            mdoc = concat(mdoc, reflow(elt.text))

    for child in elt:
        mdoc = concat(mdoc, laserhammer(child, pp_allowed, below_sect1, below_varlistentry))
        if child.tail:
            if literal:
                mdoc = mdoc + child.tail
            else:
                mdoc = concat(mdoc, reflow(child.tail))

    if tag == 'quote':
        mdoc = concat(mdoc, '\n.Dc ')
    elif tag == 'literallayout' or tag == 'programlisting' or tag == 'screen':
        mdoc = concat(mdoc, '\n.Ed\n')
    elif tag == 'itemizedlist' or tag == 'variablelist':
        mdoc = concat(mdoc, '\n.El\n')
    elif tag == 'userinput':
        # We're not doing anything for the opening tag for this one.
        mdoc = concat(mdoc, '\n')
    elif tag == 'term' and below_varlistentry:
        mdoc = concat(mdoc, '\n')
    elif tag == 'title':
        if below_sect1:
            mdoc = '\n.Ss %s\n' % reflow(mdoc).upper()
        else:
            mdoc = '\n.Sh %s\n' % reflow(mdoc).upper()

    return mdoc

def main():
    if len(sys.argv) > 3:
        sys.exit('usage: %s [input-file [output-file]]' % sys.argv[0])

    if len(sys.argv) > 2:
        outfile = open(sys.argv[2], "w")
    else:
        outfile = sys.stdout

    if len(sys.argv) > 1:
        infile = sys.argv[1]
    else:
        # This '.buffer' thing is a workaround for an encoding problem;
        # see https://github.com/lincolnloop/python-qrcode/issues/67.
        infile = sys.stdin.buffer

    root = xml.etree.ElementTree.parse(infile).getroot()
    title = get_title(root)
    date = get_date(root)
    mdoc = laserhammer(root)
    mdoc = re.sub('\n+', '\n', mdoc)

    outfile.write('.Dd %s\n' % date)
    outfile.write('.Dt %s 7\n' % title.replace(' ', '-').upper().replace('FREEBSD-', ''))
    outfile.write('.Os\n')
    outfile.write('.Sh NAME\n')
    outfile.write('.Nm %s\n' % title.replace(' ', '-').lower().replace('freebsd-', ''))
    outfile.write('.Nd %s' % title)
    outfile.write(mdoc)

if __name__ == '__main__':
    main()
