params = Parameters()
params.add('chamfer_distance', 0.14, min=0.1, max=1.0, semantic_type='chamfer_distance')
params.add('flange_radius', 18.62, min=12.0, max=44.0, expression='outer_radius * 2.15', semantic_type='primitive_radius')
params.add('flange_thickness', 5.2, min=2.0, max=8.0, semantic_type='thickness')
params.add('hole_radius', 0.94, min=0.5, max=4.0, semantic_type='hole_radius')
params.add('inner_radius', 3.88, min=2.0, max=12.0, semantic_type='inner_radius')
params.add('outer_radius', 8.66, min=5.0, max=18.0, expression='inner_radius + 4.78', semantic_type='outer_radius')

part = Part('flluma_0090079', category='revolved_hub_mount', parameters=params, seed=20350593, sample_id='flluma_0090079', units='mm')
sketch = part.sketch_polygon(name='hub_revolve_profile', points=[[params['inner_radius'], -4.8], [params['outer_radius'], -4.8], [params['outer_radius'], 4.8], [params['inner_radius'], 4.8]], closed=True, semantic_type='revolve_profile')
revolved = part.revolve(name='revolved_hub_body', profile=sketch, semantic_type='revolved_solid')
cylinder = part.cylinder(name='hub_mount_flange_seed', radius=params['flange_radius'], height=params['flange_thickness'], semantic_type='flange')
join = part.boolean_join(name='join_hub_to_flange', target=cylinder, tool=revolved, semantic_type='joined_boss')
holes = part.hole_pattern(name='hub_flange_bolt_holes', target=join.top_face(), radius=params['hole_radius'], depth='through', positions=[[12.66, 0.0], [0.0, 12.66], [-12.66, 0.0], [0.0, -12.66]], semantic_type='bolt_hole_pattern')
chamfer = part.chamfer(name='hub_mount_edge_chamfer', target=holes.top_outer_edges(), distance=params['chamfer_distance'], semantic_type='outer_chamfer')

__all__ = ['part']
