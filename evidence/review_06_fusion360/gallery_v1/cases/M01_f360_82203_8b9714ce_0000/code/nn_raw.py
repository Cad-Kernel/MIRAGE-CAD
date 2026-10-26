params = Parameters()
params.add('boss_height', 2.7, min=1.0, max=10.0, semantic_type='boss_height')
params.add('boss_radius', 8.21, min=3.0, max=16.0, semantic_type='boss_radius')
params.add('hole_radius', 1.8, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('thickness', 6.3, min=2.0, max=14.0, semantic_type='thickness')

part = Part('flluma_0051078', category='cross_tab_profile_mount', parameters=params, seed=20311592, sample_id='flluma_0051078', units='mm')
sketch = part.sketch_polygon(name='cross_tab_profile', points=[[-8.91, -40.4], [8.91, -40.4], [8.91, -14.54], [24.75, -14.54], [24.75, 14.54], [8.91, 14.54], [8.91, 40.4], [-8.91, 40.4], [-8.91, 14.54], [-24.75, 14.54], [-24.75, -14.54], [-8.91, -14.54]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_cross_tab_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
cylinder = part.cylinder(name='cross_tab_center_boss_seed', radius=params['boss_radius'], height=params['boss_height'], semantic_type='boss')
moved = part.translate(name='place_cross_tab_center_boss', target=cylinder, offset=[0.0, 0.0, 4.3], semantic_type='placement')
join = part.boolean_join(name='join_cross_tab_center_boss', target=solid, tool=moved, semantic_type='joined_boss')
holes = part.hole_pattern(name='cross_tab_mount_holes', target=join.top_face(), radius=params['hole_radius'], depth='through', positions=[[0.0, -27.47], [16.83, 0.0], [0.0, 27.47], [-16.83, 0.0]], semantic_type='mounting_hole')

__all__ = ['part']