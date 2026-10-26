import cadquery as cq
w0=cq.Workplane('YZ',origin=(2,0,0))
r=w0.sketch().segment((-100,45),(-81,-46)).segment((100,-31)).segment((99,-23)).segment((82,-29)).segment((76,-14)).segment((-69,-14)).segment((-69,-11)).segment((-62,-11)).segment((-90,40)).segment((-75,46)).segment((-76,42)).segment((-87,49)).close().assemble().push([(0,-16)]).circle(9,mode='s').finalize().extrude(-4)