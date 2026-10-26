import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().segment((11,-100),(14,-100)).segment((14,-87)).segment((11,-84)).arc((-12,0),(11,84)).segment((11,100)).segment((13,100)).segment((13,87)).segment((11,87)).close().assemble().finalize().extrude(-14)