LaserHammer is a simple DocBook to mdoc(7) ("UNIX man page syntax") converter.

The command line utility resides in scripts/ subdirectory; use it like this:
```
./laserhammer.py book.parsed.xml book.7
```
The 7 above stands for section 7 of man pages, "miscellaneous documentation".
The 'book.parsed.xml' is a processed XML source of the FreeBSD Handbook; you can
use it as test sample.  The 'book.7' is the example translated into mdoc.

There's also a rudimentary Python module.  Use it like this:
```
import laserhammer

mdoc = laserhammer.laserhammer(file_path)
print(mdoc)
```
