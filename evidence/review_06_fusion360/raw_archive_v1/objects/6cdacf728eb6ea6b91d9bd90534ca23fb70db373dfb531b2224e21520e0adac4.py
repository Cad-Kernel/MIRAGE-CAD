import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().segment((-67,-38),(65,-38)).arc((100,0),(65,38)).segment((-67,38)).arc((-100,0),(-67,-38)).assemble().finalize().extrude(-38)