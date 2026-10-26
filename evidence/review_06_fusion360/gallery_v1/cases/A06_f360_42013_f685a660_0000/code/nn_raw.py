params = Parameters()
params.add('radius_x', 7.09, min=1.0, max=12.0, semantic_type='ellipsoid_radius_x')
params.add('radius_y', 3.82, min=1.0, max=12.0, semantic_type='ellipsoid_radius_y')
params.add('radius_z', 6.09, min=1.0, max=12.0, semantic_type='ellipsoid_radius_z')

part = Part('flluma_0033985', category='ellipsoid_stock', parameters=params, seed=20294499, sample_id='flluma_0033985', units='mm')
ellipsoid = part.ellipsoid(name='ellipsoid_stock_body', radii=[params['radius_x'], params['radius_y'], params['radius_z']], semantic_type='primitive_stock')

__all__ = ['part']