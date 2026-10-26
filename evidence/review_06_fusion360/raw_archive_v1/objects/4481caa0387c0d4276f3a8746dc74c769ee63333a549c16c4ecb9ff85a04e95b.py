import cadquery as cq
w0=cq.Workplane('YZ',origin=(8,0,0))
r=w0.sketch().segment((-43,-51),(100,-92)).segment((100,92)).segment((-43,51)).arc((-100,0),(-43,-51)).assemble().push([(-54,0)]).circle(25,mode='s').finalize().extrude(-16)