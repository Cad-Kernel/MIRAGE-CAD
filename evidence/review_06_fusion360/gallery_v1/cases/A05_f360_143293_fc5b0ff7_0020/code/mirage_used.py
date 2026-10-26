params = Parameters()
params.add('height', 10.1, min=2.0, max=18.0, semantic_type='primitive_height')
params.add('length', 10.1, min=3.0, max=24.0, semantic_type='primitive_length')
params.add('ltx', 4.14, min=0.0, max=20.0, expression='lwidth * 0.413', semantic_type='wedge_ltx')
params.add('width', 15.1, min=2.0, max=18.0, semantic_type='primitive_width')

part = Part('flluma_0005710', category='wedge_stock', parameters=params, seed=20266224, sample_id='flluma_0005710', units='mm')
wedge = part.wedge(name='wedge_stock_body', size=[params['length'], params['width'], params['height']], ltx=params['ltx'], semantic_type='primitive_stock')
box = part.box(name='wedge_flange_seed', length=params['length'], width=params['width'], height=params['height'], semantic_type='flange')
moved = part.translate(name='place_wedge_flange', target=box, offset=[0.0, 6.85, -4.455], semantic_type='placement')
join = part.boolean_join(name='join_wedge_to_flange', target=wedge, tool=moved, semantic_type='joined_stock')

__all__ = ['part']