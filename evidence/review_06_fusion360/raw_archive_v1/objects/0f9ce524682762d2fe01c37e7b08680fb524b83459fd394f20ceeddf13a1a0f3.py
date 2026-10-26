import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().rect(120,18).push([(-43,0)]).circle(8,mode='s').push([(44,1)]).circle(4,mode='s').finalize().extrude(-200)