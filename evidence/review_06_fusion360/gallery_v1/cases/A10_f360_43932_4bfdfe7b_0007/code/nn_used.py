params = Parameters()
params.add('boss_height', 4.8, min=1.0, max=10.0, semantic_type='boss_height')
params.add('boss_radius', 9.83, min=3.0, max=16.0, semantic_type='boss_radius')
params.add('hole_radius', 1.46, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('thickness', 9.0, min=2.0, max=14.0, semantic_type='thickness')

part = Part('flluma_0076727', category='cross_tab_profile_mount', parameters=params, seed=20337241, sample_id='flluma_0076727', units='mm')
sketch = part.sketch_polygon(name='cross_tab_profile', points=[[-8.86, -36.8], [8.86, -36.8], [8.86, -13.25], [24.6, -13.25], [24.6, 13.25], [8.86, 13.25], [8.86, 36.8], [-8.86, 36.8], [-8.86, 13.25], [-24.6, 13.25], [-24.6, -13.25], [-8.86, -13.25]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_cross_tab_mount', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
cylinder = part.cylinder(name='cross_tab_center_boss_seed', radius=params['boss_radius'], height=params['boss_height'], semantic_type='boss')
moved = part.translate(name='place_cross_tab_center_boss', target=cylinder, offset=[0.0, 0.0, 6.7], semantic_type='placement')
join = part.boolean_join(name='join_cross_tab_center_boss', target=solid, tool=moved, semantic_type='joined_boss')
holes = part.hole_pattern(name='cross_tab_mount_holes', target=join.top_face(), radius=params['hole_radius'], depth='through', positions=[[0.0, -25.02], [16.73, 0.0], [0.0, 25.02], [-16.73, 0.0]], semantic_type='mounting_hole')

__all__ = ['part']