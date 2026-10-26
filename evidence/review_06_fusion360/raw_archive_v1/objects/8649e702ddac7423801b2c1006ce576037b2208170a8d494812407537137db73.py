import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().arc((-9,-9),(0,-8),(9,-4)).segment((9,4)).arc((0,8),(-9,9)).arc((-8,0),(-9,-9)).assemble().finalize().extrude(200)