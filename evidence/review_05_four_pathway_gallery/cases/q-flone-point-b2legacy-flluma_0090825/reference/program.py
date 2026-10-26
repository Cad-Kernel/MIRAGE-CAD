params = Parameters()
params.add('clamp_jaw_height', 13.5, min=5.0, max=28.0, expression='thickness * 1.5', semantic_type='clamp_jaw_height')
params.add('clamp_jaw_width', 15.57, min=6.0, max=28.0, expression='width * 0.18', semantic_type='clamp_jaw_width')
params.add('height', 42.3, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 2.12, min=1, max=8, semantic_type='hole_radius')
params.add('pocket_width', 16.88, min=8.0, max=40.0, expression='height * 0.399', semantic_type='pocket_width')
params.add('thickness', 9, min=3, max=25, semantic_type='thickness')
params.add('width', 86.5, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0090825', category='pipe_clamp', parameters=params, seed=20351339, sample_id='flluma_0090825', units='mm')
plate = part.plate(name='clamp_base', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
pocket = part.rectangular_pocket(name='pipe_clearance_channel', target=plate.top_face(), length=53.63, width=params['pocket_width'], depth=2.25, semantic_type='pocket')
holes = part.hole_pattern(name='clamp_bolt_holes', target=pocket.top_face(), radius=params['hole_radius'], depth='through', positions=[[-19.03, 0.0], [20.76, 5.076]], semantic_type='bolt_hole_pattern')
box = part.box(name='clamp_jaw_seed', length=params['clamp_jaw_width'], width=params['height'], height=params['clamp_jaw_height'], semantic_type='clamp_jaw')
moved = part.translate(name='place_clamp_jaw', target=box, offset=[35.465, 0.0, 11.05], semantic_type='placement')
mirror = part.mirror(name='mirror_clamp_jaw', target=moved, axis='X', plane=None, semantic_type='pattern')
join = part.boolean_join(name='join_clamp_jaws', target=holes, tool=mirror, semantic_type='mirrored_clamp_jaw')

__all__ = ['part']
