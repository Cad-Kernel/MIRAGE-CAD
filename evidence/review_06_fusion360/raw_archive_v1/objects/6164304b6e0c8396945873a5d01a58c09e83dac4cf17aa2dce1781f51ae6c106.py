import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().push([(0,-82.5)]).rect(70,35).push([(0,82.5)]).rect(70,35).push([(0,0)]).rect(70,10).push([(0,0.5)]).rect(10,9,mode='s').push([(0,20)]).rect(70,10).finalize().extrude(-200)