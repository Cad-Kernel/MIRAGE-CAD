params = Parameters()
params.add('height', 11.27, min=3.0, max=28.0, semantic_type='primitive_height')
params.add('radius', 4.38, min=1.5, max=12.0, semantic_type='primitive_radius')

part = Part('flluma_0079997', category='prism_stock', parameters=params, seed=20340511, sample_id='flluma_0079997', units='mm')
prism = part.prism(name='prism_stock_body', radius=params['radius'], height=params['height'], sides=8, semantic_type='primitive_stock')

__all__ = ['part']