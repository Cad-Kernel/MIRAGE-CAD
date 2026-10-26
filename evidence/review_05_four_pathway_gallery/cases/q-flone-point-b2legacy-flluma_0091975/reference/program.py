params = Parameters()
params.add('chamfer_distance', 0.11, min=0.1, max=2.0, semantic_type='chamfer_distance')
params.add('height', 28.2, min=12, max=80, semantic_type='overall_height')
params.add('hole_radius', 2.17, min=1, max=8, semantic_type='hole_radius')
params.add('hole_spacing', 24.99, min=5.0, max=45.0, expression='width * 0.294', semantic_type='hole_spacing')
params.add('thickness', 6, min=3, max=25, semantic_type='thickness')
params.add('width', 85.0, min=20, max=120, semantic_type='overall_width')

part = Part('flluma_0091975', category='control_plate', parameters=params, seed=20352489, sample_id='flluma_0091975', units='mm')
plate = part.plate(name='control_base_plate', width=params['width'], height=params['height'], thickness=params['thickness'], semantic_type='base_plate')
holes = part.hole_pattern(name='control_clearance_holes', target=plate.top_face(), radius=params['hole_radius'], depth='through', positions=[[-24.99, 0.0], [0.0, 0.0], [24.99, 0.0]], semantic_type='clearance_hole')
chamfer = part.chamfer(name='outer_chamfer', target=holes.top_outer_edges(), distance=params['chamfer_distance'], semantic_type='outer_edge_break')

__all__ = ['part']
