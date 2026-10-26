import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,0,0))
r=w0.sketch().segment((-100,-82),(-96,-85)).segment((-11,-22)).arc((24,-7),(39,26)).segment((100,75)).segment((92,88)).segment((31,48)).arc((-1,35),(-20,6)).segment((-22,6)).segment((-22,25)).arc((-38,14),(-45,-4)).segment((-56,-4)).arc((-60,-16),(-70,-25)).segment((-57,-47)).close().assemble().finalize().extrude(-1)