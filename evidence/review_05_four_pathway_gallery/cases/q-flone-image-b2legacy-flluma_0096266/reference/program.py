params = Parameters()
params.add('fillet_radius', 0.14, min=0.05, max=2.0, semantic_type='edge_break_radius')
params.add('height', 53.0, min=12, max=80, semantic_type='overall_height')
params.add('hole_offset_x', 19.796, min=4.0, max=45.0, expression='width * 0.28', semantic_type='hole_spacing')
params.add('hole_offset_y', 13.25, min=3.0, max=35.0, expression='height * 0.25', semantic_type='hole_spacing')
params.add('hole_radius', 2.39, min=1, max=8, semantic_type='hole_radius')
params.add('pocket_depth', 3.7, min=1, max=8, expression='min(thickness * 0.308, thickness - 1.2)', semantic_type='pocket_depth')
params.add('pocket_length', 34.71, min=8, max=60, expression='width * 0.491', semantic_type='pocket_length')
params.add('pocket_width', 18.18, min=4, max=40, expression='height * 0.343', semantic_type='pocket_width')
params.add('thickness', 12, min=3, max=25, semantic_type='thickness')
params.add('width', 70.7, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0096266', category='pocketed_service_plate', parameters=params, seed=20356780, sample_id='flluma_0096266', units='mm')
plate = part.plate(name='base_plate', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
holes = part.hole_pattern(name='service_holes', target=plate.top_face(), radius=params['hole_radius'], depth='through', positions=[[-19.796, -13.25], [19.796, -13.25], [-19.796, 13.25], [19.796, 13.25]], semantic_type='service_hole')
pocket = part.rectangular_pocket(name='shallow_center_pocket', target=holes.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=params['pocket_depth'], semantic_type='pocket')
fillet = part.fillet(name='pocket_finish_radius', target=pocket.pocket_edges(), radius=params['fillet_radius'], semantic_type='edge_break')

__all__ = ['part']
