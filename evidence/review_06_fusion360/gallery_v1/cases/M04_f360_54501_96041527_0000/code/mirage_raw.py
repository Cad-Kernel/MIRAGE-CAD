params = Parameters()
params.add('height', 10.64, min=4.0, max=28.0, semantic_type='primitive_height')
params.add('length', 10.1, min=8.0, max=32.0, semantic_type='primitive_length')
params.add('width', 13.1, min=5.0, max=21.0, semantic_type='primitive_width')

part = Part('flluma_0005001', category='wedge_stock', parameters=params, seed=20265515, sample_id='flluma_0005001', units='mm')
wedge = part.wedge(name='wedge_stock_body', length=params['length'], width=params['width'], height=params['height'], semantic_type='primitive_stock')

__all__ = ['part']