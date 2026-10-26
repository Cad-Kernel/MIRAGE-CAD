import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-11,-7),(-11,-5)).segment((-9,-5)).segment((-9,-9)).arc((11,7),(-11,-7)).assemble().finalize().extrude(200)