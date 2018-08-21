LaserHammer is a simple DocBook to mdoc(7) ("UNIX man page syntax") converter.
The command line utility is in scripts/ subdirectory, use it like this:
```
./laserhammer.py book.parsed.xml handbook.7
```
The 7 above stands for section 7 of man pages, the "miscellaneous documentation".
The 'book.parsed.xml' is a processed XML source of the FreeBSD Handbook; you can
use it as test sample.  
