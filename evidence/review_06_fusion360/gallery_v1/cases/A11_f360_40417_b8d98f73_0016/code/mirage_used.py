params = Parameters()
params.add('major_radius', 10.18, min=3.0, max=18.0, semantic_type='torus_major_radius')
params.add('minor_radius', 3.13, min=0.4, max=5.0, semantic_type='torus_minor_radius')

part = Part('flluma_0005001', category='torus_stock', parameters=params, seed=20265515, sample_id='flluma_0005001', units='mm')
torus = part.torus(name='torus_stock_body', major_radius=params['major_radius'], minor_radius=params['minor_radius'], semantic_type='primitive_stock')

__all__ = ['part']