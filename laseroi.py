#! /usr/bin/python3

import time,sys

try:   F=open(sys.argv[1],'r')
except: F=open('gcode.gcode','r')

try: POWER=sys.argv[2]    
except: POWER=975
try: SPEED=sys.argv[3]    
except: SPEED=600
try: FSPEED=sys.argv[4]    
except: FSPEED=2400
  
print(';Z removed, M3 and M5 added')
s=1
done=True
while s:
    s=F.readline()
    if s.find('M3')==0: print(';'+s)
    elif s.find('S1')==0: print(';'+s)
    elif s.find('G')==0:
        if s.find('64')==1: print(';'+s)
        elif s.find('94')==1: print(';'+s)
        elif s.find('04')==1: print(';'+s)
        elif s.find('00')==1:
            if s.find('Z')==4: print('M5')
            elif s.find('X')==4:
                print('F'+str(FSPEED))
                print(s)
        elif s.find('01')==1:
            if s.find('Z')==4:
                print('M3 S'+str(POWER))
                print('G01 F'+str(SPEED))
        else: print(s)
    else:
        print(s)


