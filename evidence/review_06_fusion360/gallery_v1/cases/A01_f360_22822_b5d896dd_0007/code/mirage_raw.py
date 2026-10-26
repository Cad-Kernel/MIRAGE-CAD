params = Parameters()
params.add('boss_height', 13.1, min=3.0, max=24.0, expression='thickness * 0.91', semantic_type='boss_height')
params.add('boss_radius', 10.14, min=3.0, max=18.0, expression='hole_radius * 3.1', semantic_type='boss_radius')
params.add('hole_radius', 2.53, min=0.8, max=5.8, semantic_type='hole_radius')
params.add('thickness', 16, min=3, max=25, semantic_type='thickness')
params.add('width', 51.1, min=12, max=80, semantic_type='overall_width')

part = Part('flluma_0001001', category='stepped_profile_mount', parameters=params, seed=20261516, sample_id='flluma_0001001', units='mm')
sketch = part.sketch_polygon(name='stepped_outer_profile', points=[[-23.9, -25.5], [-5.47, -25.5], [-5.47, -9.12], [8.91, -9.12], [8.91, -25.5], [23.9, -25.5], [23.9, 23.3], [10.18, 23.3], [10.18, 8.92], [-8.91, 8.92], [-8.91, 26.2], [-23.9, 26.2]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_stepped_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
holes = part.hole_pattern(name='stepped_mount_holes', target=solid.top_face(), radius=params['hole_radius'], depth='through', positions=[[-15.5, -15.8], [16.5, 13.1]], semantic_type='mounting_hole')
cylinder = part.cylinder(name='stepped_mount_center_boss_seed', radius=params['boss_radius'], height=params['boss_height'], semantic_type='boss')
moved = part.translate(name='place_stepped_mount_center_boss', target=cylinder, offset=[0.0, 11.1, 10.1], semantic_type='placement')
join = part.boolean_join(name='join_stepped_mount_center_boss', target=holes, tool=moved, semantic_type='joined_boss')

__all__ = ['part']