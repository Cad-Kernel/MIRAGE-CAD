params = Parameters()
params.add('chamfer_distance', 0.24, min=0.1, max=1.2, semantic_type='chamfer_distance')
params.add('cylinder_radius', 29.8, min=8.0, max=50.0, semantic_type='primitive_radius')
params.add('height', 29.2, min=8.0, max=45.0, semantic_type='overall_height')
params.add('hole_radius', 2.09, min=0.8, max=6.0, semantic_type='hole_radius')
params.add('length', 57.1, min=20.0, max=100.0, semantic_type='overall_width')
params.add('pocket_length', 19.24, min=8.0, max=48.0, expression='length * 0.337', semantic_type='pocket_length')
params.add('pocket_width', 17.64, min=5.0, max=28.0, expression='width * 0.357', semantic_type='pocket_width')
params.add('width', 49.4, min=14.0, max=80.0, semantic_type='primitive_width')

part = Part('flluma_0067789', category='intersected_mount_block', parameters=params, seed=20328303, sample_id='flluma_0067789', units='mm')
box = part.box(name='mount_block_stock', length=params['length'], width=params['width'], height=params['height'], semantic_type='primitive_stock')
cylinder = part.cylinder(name='round_intersection_tool', radius=params['cylinder_radius'], height=33.2, semantic_type='primitive_stock')
intersect = part.boolean_intersect(name='intersect_block_with_cylinder', target=box, tool=cylinder, semantic_type='intersection_solid')
pocket = part.rectangular_pocket(name='top_service_pocket', target=intersect.top_face(), length=params['pocket_length'], width=params['pocket_width'], depth=5.256, semantic_type='pocket')
holes = part.hole_pattern(name='intersected_mount_holes', target=pocket.top_face(), radius=params['hole_radius'], depth='through', positions=[[-14.85, 0.0], [14.85, 0.0]], semantic_type='mounting_hole')
chamfer = part.chamfer(name='intersected_block_edge_chamfer', target=holes.top_outer_edges(), distance=params['chamfer_distance'], semantic_type='outer_chamfer')

__all__ = ['part']