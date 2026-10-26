import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-16,-3),(-11,-3)).arc((-7,-2),(-3,-3)).segment((1,-3)).arc((-7,-1),(-13,3)).segment((-16,3)).close().assemble().reset().face(w0.sketch().segment((13,-3),(16,-3)).segment((16,3)).segment((13,3)).arc((14,0),(13,-3)).assemble()).finalize().extrude(-200)