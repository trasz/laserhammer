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

def unnamespace(tag):
    return re.sub('\\{.*\\}', '', tag)

# Can't use ElementTree's .find(), as it can't be told to ignore namespaces.
def subfind(elt, name):
    for child in elt:
        if unnamespace(child.tag) == name:
            return child

    sys.exit('<%s> not found' % name)

def get_title(elt):
    info = subfind(elt, 'info')
    title = subfind(info, 'title')

    return title.text

def get_date(elt):
    info = subfind(elt, 'info')
    pubdate = subfind(info, 'pubdate')
    if not pubdate.text:
        return ''
    date = pubdate.text.split()
    parsed_date = datetime.datetime.strptime(date[3], '%Y-%m-%d')
    date = parsed_date.strftime('%b %d, %Y')

    return date

def concat(first, second):
    if first and first[-1] == '\n':
        if second and second[0] in ('\n', ' '):
            second = second[1:]
    if first and first[-1] == ' ':
        if second and second[0] == ' ':
            second = second[1:]
    if second and second[0] == '\n':
        if first and first[-1] == ' ':
            first = first[:-1]

    return first + second

def laserhammer(elt, pp_allowed=True, below_sect1=False, below_table=False, below_varlistentry=False, below_title=False):
    literal = False
    grab_text = False
    append_newline = False
    tag = unnamespace(elt.tag)

    if tag in ('figure', 'glossary', 'indexterm', 'info', 'preface'):
        return ''
    if tag == 'citerefentry':
        if below_title:
            return '%s' % (subfind(elt, 'refentrytitle').text)
        return '\n.Xr %s %s ' % (subfind(elt, 'refentrytitle').text, subfind(elt, 'manvolnum').text)

    # Do not insert any markup in what's supposed to be the title.
    if below_title:
        if elt.text:
            return elt.text
        return ''

    mdoc = ''
    if tag == 'sect1':
        below_sect1 = True
    elif tag == 'example':
        # Ignore <title> tags inside <example>.
        below_table = True
    elif tag == 'quote':
        mdoc = '\n.Do\n'
        grab_text = True
    elif tag in ('acronym', 'address', 'application',
                 'citetitle', 'city', 'country',
                 'emphasis', 'fax', 'function', 'keycap', 'link', 'otheraddr',
                 'phone', 'phrase', 'postcode', 'prompt',
                 'replaceable', 'state', 'street', 'trademark',
                 'userinput'):
        grab_text = True
    elif tag in ('arg', 'option', 'optional', 'parameter'):
        mdoc = '\n.Ar '
        grab_text = True
        append_newline = True
    elif tag in ('buildtarget', 'computeroutput', 'constant',
                 'errortype', 'firstterm',
                 'guibutton', 'guimenu', 'guimenuitem',
                 'literal', 'package', 'revnumber', 'systemitem'):
        mdoc = '\n.Ql '
        grab_text = True
        append_newline = True
    elif tag == 'command':
        mdoc = '\n.Cm '
        grab_text = True
        append_newline = True
    elif tag == 'entry' and below_table:
        mdoc = '\n.Ta\n'
        grab_text = True
    elif tag == 'email':
        mdoc = '\n.Mt '
        grab_text = True
        append_newline = True
    elif tag in ('envar', 'varname'):
        mdoc = '\n.Ev '
        grab_text = True
        append_newline = True
    elif tag == 'errorname':
        mdoc = '\n.Er '
        grab_text = True
        append_newline = True
    elif tag == 'filename':
        mdoc = '\n.Pa '
        grab_text = True
        append_newline = True
    elif tag in ('literallayout', 'programlisting', 'screen'):
        mdoc = '\n.Bd -literal -offset indent\n'
        literal = True
        grab_text = True
    elif tag == 'varlistentry':
        below_varlistentry = True
        grab_text = True
    elif tag == 'listitem':
        if not below_varlistentry:
            mdoc = '\n.It\n'
        pp_allowed = False
    elif tag == 'itemizedlist':
        mdoc = '\n.Bl -bullet -offset -compact\n'
    elif tag == 'orderedlist':
        mdoc = '\n.Bl -enum -offset -compact\n'
        # Ignore <title> tags inside <orderedlist>.
        below_table = True
    elif tag == 'variablelist':
        mdoc = '\n.Bl -tag -offset -compact\n'
    elif tag == 'para':
        if pp_allowed:
            mdoc = '\n.Pp\n'
        grab_text = True
    elif tag == 'row' and below_table:
        mdoc = '\n.It '
    elif tag in ('table', 'informaltable'):
        # XXX: We're doing three ugly hacks here: we don't know how wide
        #      the columns should be, so let's assume 14.  We don't know
        #      the number of columns either, so let's assume 5.  Plus one
        #      "hidden" column, because we suck at .Ta placement.
        mdoc = '\n.Bl -column -offset -compact ""'
        for i in range(5):
            mdoc = mdoc + ' "' + ' ' * 14 + '"'
        mdoc = mdoc + '\n'
        below_table = True
    elif tag == 'term' and below_varlistentry:
        mdoc = '\n.It '
        grab_text = True
        append_newline = True
    elif tag == 'title':
        grab_text = True
        below_title = True
    elif tag == 'uri':
        mdoc = '\n.Lk '
        grab_text = True
        append_newline = True

    if elt.text and grab_text:
        if literal:
            mdoc = mdoc + elt.text
        else:
            mdoc = concat(mdoc, reflow(elt.text))

    if elt.text and elt.text.strip() and not grab_text:
        print('%s: ignoring text "%s", tag <%s>' % (sys.argv[0], elt.text, tag))

    for child in elt:
        mdoc = concat(mdoc, laserhammer(child, pp_allowed, below_sect1, below_table, below_varlistentry, below_title))
        if child.tail and grab_text:
            if literal:
                mdoc = mdoc + child.tail
            else:
                mdoc = concat(mdoc, reflow(child.tail))

        if child.tail and child.tail.strip() and not grab_text:
            print('%s: ignoring tail "%s", tag <%s>' % (sys.argv[0], child.tail, tag))

    if append_newline:
        mdoc = concat(mdoc, '\n')

    if tag == 'function':
        mdoc = '\n.Fn %s\n' % mdoc.split('(')[0]
    elif tag == 'quote':
        mdoc = concat(mdoc, '\n.Dc\n')
    elif tag in ('literallayout', 'programlisting', 'screen'):
        mdoc = concat(mdoc, '\n.Ed\n')
    elif tag in ('itemizedlist', 'orderedlist', 'informaltable', 'table', 'variablelist'):
        mdoc = concat(mdoc, '\n.El\n')
    elif tag == 'link' and not mdoc and '{http://www.w3.org/1999/xlink}href' in elt.attrib:
        # If there's no link description, try inserting the URL instead.
        # In theory using .Lk here would be a good idea, in practice
        # it looks rather ugly.
        #mdoc = '\n.Lk %s\n' % elt.attrib['{http://www.w3.org/1999/xlink}href']
        mdoc = '%s' % elt.attrib['{http://www.w3.org/1999/xlink}href']
    elif tag == 'title':
        if below_table:
            mdoc = ''
        elif below_sect1:
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

    outfile.write('.Dd %s\n' % date)
    outfile.write('.Dt %s 7\n' % title.replace(' ', '-').upper().replace('FREEBSD-', ''))
    outfile.write('.Os\n')
    outfile.write('.Sh NAME\n')
    outfile.write('.Nm %s\n' % title.replace(' ', '-').lower().replace('freebsd-', ''))
    outfile.write('.Nd %s' % title)
    outfile.write(mdoc)

if __name__ == '__main__':
    main()
