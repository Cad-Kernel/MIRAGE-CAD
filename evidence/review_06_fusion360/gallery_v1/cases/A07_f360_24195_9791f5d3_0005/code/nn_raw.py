params = Parameters()
params.add('clip_size', 11.96, min=6.0, max=24.0, semantic_type='clip_size')
params.add('offset_distance', 0.08, min=0.05, max=1.0, semantic_type='offset_distance')
params.add('sphere_radius', 10.26, min=4.0, max=18.0, semantic_type='sphere_radius')

part = Part('flluma_0021473', category='intersection_offset_stock', parameters=params, seed=20281987, sample_id='flluma_0021473', units='mm')
stock = part.clipped_offset_stock(name='grown_clipped_stock', clip_size=params['clip_size'], sphere_radius=params['sphere_radius'], offset_distance=params['offset_distance'], semantic_type='clipped_offset_stock')

__all__ = ['part']