import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().segment((-57,-2),(57,-2)).segment((57,1)).segment((48,1)).arc((42,2),(36,1)).segment((-31,1)).arc((-43,2),(-55,1)).segment((-57,1)).close().assemble().finalize().extrude(-200)