params = Parameters()
params.add('chamfer_distance', 0.2, min=0.1, max=1.5, semantic_type='chamfer_distance')
params.add('height', 10.1, min=3.0, max=20.0, semantic_type='overall_height')
params.add('radius', 6.2, min=2.0, max=12.0, semantic_type='inner_radius')
params.add('work_radius', 10.1, min=4.0, max=14.0, semantic_type='inner_radius')

part = Part('flluma_0005000', category='revolved_boss', parameters=params, seed=20265514, sample_id='flluma_0005000', units='mm')
sketch = part.sketch_polygon(name='revolve_outer_profile', points=[[params['radius'], -5.05], [params['work_radius'], -5.05], [params['work_radius'], 5.05], [params['radius'], 5.05]], closed=True, semantic_type='revolve_profile')
solid = part.revolve(name='revolved_boss_body', profile=sketch, semantic_type='revolved_solid')
chamfer = part.chamfer(name='revolved_boss_edge_chamfer', target=solid.top_face(), distance=params['chamfer_distance'], semantic_type='edge_break')

__all__ = ['part']