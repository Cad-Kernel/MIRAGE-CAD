import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-74,0))
r=w0.sketch().segment((-46,-20),(-3,-50)).segment((2,-44)).segment((40,-30)).segment((46,20)).segment((3,50)).segment((-2,44)).segment((-40,30)).segment((-44,-1)).arc((-45,-7),(-45,-13)).close().assemble().finalize().extrude(-26).union(w0.workplane(offset=174/2).cylinder(174,22))