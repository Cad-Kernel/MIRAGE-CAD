params = Parameters()
params.add('height', 5.61, min=2.0, max=18.0, semantic_type='primitive_height')
params.add('length', 6.76, min=3.0, max=24.0, semantic_type='primitive_length')
params.add('ltx', 3.55, min=0.0, max=20.0, expression='length * 0.525', semantic_type='wedge_ltx')
params.add('width', 4.27, min=2.0, max=18.0, semantic_type='primitive_width')

part = Part('flluma_0057500', category='wedge_stock', parameters=params, seed=20318014, sample_id='flluma_0057500', units='mm')
wedge = part.wedge(name='wedge_stock_body', ltx=params['ltx'], size=[params['length'], params['width'], params['height']], semantic_type='primitive_stock')

__all__ = ['part']