import json
import sys
src,out=(sys.argv[1],sys.argv[2]) if len(sys.argv)>2 else ('/home/claude/stack/src/reel.html','/home/claude/stack/out/wg-stack.html')
s=open(src).read()
d=open('/home/claude/stack/src/data.json').read()
assert '</script' not in d
s=s.replace('__DATA__',d)
open(out,'w').write(s);print(len(s))
