params = Parameters()
params.add('chamfer_distance', 0.16, min=0.1, max=1.0, semantic_type='chamfer_distance')
params.add('height', 10.1, min=3.0, max=20.0, semantic_type='overall_height')
params.add('hole_radius', 1.43, min=0.8, max=4.0, semantic_type='hole_radius')
params.add('shell_thickness', 0.8, min=0.4, max=3.0, semantic_type='shell_thickness')
params.add('thickness', 10.1, min=2.0, max=14.0, semantic_type='thickness')

part = Part('flluma_0004000', category='mass_centre_shell', parameters=params, seed=20264514, sample_id='flluma_0004000', units='mm')
sketch = part.sketch_polygon(name='shell_outer_profile', points=[[1.55, 4.94], [-0.69, 4.94], [-1.55, 3.08], [-0.69, 3.08], [0.69, 3.08], [1.55, 3.08], [0.69, 4.94], [1.55, 4.94]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_mass_centre_shell', profile=sketch, height=params['height'], semantic_type='shell')
shell = part.shell(name='join_mass_centre_shell', target=solid, thickness=params['shell_thickness'], semantic_type='shell')
cylinder = part.cylinder(name='mass_centre_hole_seed', radius=params['hole_radius'], height=params['height'], semantic_type='hole')
moved = part.translate(name='place_mass_centre_hole', target=cylinder, offset=[0.0, 0.0, 2.25], semantic_type='placement')
join = part.boolean_join(name='join_mass_centre_hole', target=shell, tool=moved, semantic_type='joined_boss')
holes = part.hole_pattern(name='mass_shell_hole_array', target=join.top_face(), radius=1.43, depth='through', positions=[[0.0, 2.94], [1.55, -1.54], [-0.69, -1.54]], semantic_type='mounting_hole')
chamfer = part.chamfer(name='shell_outer_chamfer', target=holes.top_outer_edges(), distance=0.24, semantic_type='outer_chamfer')

__all__ = ['part']