import nokoplot as n

for y in range(0,n.MAX_Y-1,10000):
        n.Move(0,y)
        n.Pen('DOWN')
        n.Move(n.MAX_X-1,y)
        n.Pen('UP')

for x in range(0,n.MAX_X-1,10000):
        n.Move(x,0)
        n.Pen('DOWN')
        n.Move(x,n.MAX_Y-1)
        n.Pen('UP')
