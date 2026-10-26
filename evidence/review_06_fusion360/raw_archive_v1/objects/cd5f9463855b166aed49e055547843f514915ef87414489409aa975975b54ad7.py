import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,31))
r=w0.sketch().segment((83,-7),(100,-3)).segment((98,5)).segment((82,1)).arc((-100,1),(83,-7)).assemble().finalize().extrude(-62)