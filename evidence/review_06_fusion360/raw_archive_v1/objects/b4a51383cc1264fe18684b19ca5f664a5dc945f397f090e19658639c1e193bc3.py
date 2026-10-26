import cadquery as cq
w0=cq.Workplane('YZ',origin=(12,0,0))
r=w0.sketch().segment((-100,-62),(79,-63)).arc((89,-57),(98,-51)).segment((100,-41)).segment((100,41)).segment((98,41)).arc((89,57),(75,63)).segment((-100,63)).close().assemble().finalize().extrude(-24)