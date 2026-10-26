params = Parameters()
params.add('hole_radius', 2.2, min=0.8, max=5.0, semantic_type='hole_radius')
params.add('slot_length', 20.3, min=6.0, max=34.0, semantic_type='pocket_length')
params.add('slot_width', 5.8, min=2.0, max=12.0, semantic_type='pocket_width')
params.add('thickness', 6.7, min=2.0, max=12.0, semantic_type='thickness')

part = Part('flluma_0096700', category='rounded_slot_profile_plate', parameters=params, seed=20357214, sample_id='flluma_0096700', units='mm')
sketch = part.sketch_polygon(name='rounded_octagon_outer_profile', points=[[-22.3, -30.7], [22.3, -30.7], [28.2, -24.8], [28.2, 24.8], [22.3, 30.7], [-22.3, 30.7], [-28.2, 24.8], [-28.2, -24.8]], closed=True, semantic_type='extrude_profile')
solid = part.extrude(name='extrude_rounded_slot_plate', profile=sketch, height=params['thickness'], semantic_type='extruded_plate')
pocket = part.rectangular_pocket(name='center_long_slot_recess', target=solid.top_face(), length=params['slot_length'], width=params['slot_width'], depth=2.68, semantic_type='slot')
holes = part.hole_pattern(name='rounded_slot_plate_holes', target=pocket.top_face(), radius=params['hole_radius'], depth='through', positions=[[-18.05, 15.35], [18.05, -15.35]], semantic_type='mounting_hole')

__all__ = ['part']
