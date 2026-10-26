params = Parameters()
params.add('clamp_jaw_height', 10.1, min=3.0, max=24.0, expression='thickness * 1.15', semantic_type='clamp_jaw_height')
params.add('clamp_jaw_width', 10.1, min=4.0, max=24.0, expression='width * 0.166', semantic_type='clamp_jaw_width')
params.add('height', 30.1, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 1.54, min=1, max=8, semantic_type='hole_radius')
params.add('pocket_width', 15.1, min=8.0, max=40.0, expression='width * 0.499', semantic_type='pocket_width')
params.add('thickness', 12, min=3, max=25, semantic_type='thickness')
params.add('width', 54.1, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0001000', category='pipe_clamp', parameters=params, seed=20261514, sample_id='flluma_0001000', units='mm')
plate = part.plate(name='clamp_base', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
pocket = part.rectangular_pocket(name='pipe_clearance_channel', target=plate.top_face(), length=20.002, width=params['pocket_width'], depth=3.0, semantic_type='pocket')
holes = part.hole_pattern(name='clamp_bolt_holes', target=pocket.top_face(), radius=params['hole_radius'], depth='through', positions=[[-11.902, 0.0], [13.064, 6.012]], semantic_type='bolt_hole_pattern')
box = part.box(name='clamp_jaw_seed', length=params['clamp_jaw_width'], width=params['thickness'], height=params['clamp_jaw_height'], semantic_type='clamp_jaw')
moved = part.translate(name='place_clamp_jaw', target=box, offset=[21.995, 0.0, 10.45], semantic_type='placement')
mirror = part.mirror(name='mirror_clamp_jaw', target=moved, axis='Y', plane=None, semantic_type='pattern')
join = part.boolean_join(name='join_clamp_jaws', target=holes, tool=mirror, semantic_type='joined_clamp_jaw')

__all__ = ['part']