import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-35,-55),(23,-50)).segment((35,30)).segment((-17,55)).arc((-22,2),(-35,-55)).assemble().finalize().extrude(-200)