"""Coordinate and shared-frame tests without CAD imports or scoring."""
import unittest
import numpy as np
from render_gallery import camera_for, corners, project, transform


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.config={"size":640,"frame_occupancy":.82}
        self.view={"name":"isometric","azimuth":45,"elevation":35.264389682754654}

    def test_inverse(self):
        v=np.array([[1,2,3],[-1,5,7]],float)
        out,record=transform(v,3,np.array([4,5,6]))
        restored=np.column_stack((out,np.ones(len(out))))@np.asarray(record["display_to_native"]).T
        np.testing.assert_allclose(restored[:,:3],v)

    def test_bbox_normalization(self):
        v=corners([-3,5,-20],[5,15,40])
        center=(v.min(axis=0)+v.max(axis=0))/2
        extent=np.max(np.ptp(v,axis=0))
        out,_=transform(v,1/extent,.5-center/extent)
        self.assertAlmostEqual(np.max(np.ptp(out,axis=0)),1)
        np.testing.assert_allclose((out.min(axis=0)+out.max(axis=0))/2,[.5,.5,.5])

    def test_camera_basis_orthonormal(self):
        c=camera_for(corners([0,0,0],[1,1,1]),self.view,self.config,"metric_space")
        b=np.asarray(c["basis"])
        np.testing.assert_allclose(b.T@b,np.eye(3),atol=1e-12)

    def test_fixed_cube_fits(self):
        v=corners([0,0,0],[1,1,1])
        c=camera_for(v,self.view,self.config,"metric_space")
        p=project(v,c)
        self.assertTrue((p[:,:2]>=0).all() and (p[:,:2]<640).all())
        self.assertAlmostEqual(float(np.max(np.ptp(p[:,:2],axis=0))),640*.82)

    def test_shared_union_not_independent_fit(self):
        small=corners([0,0,0],[1,1,1])
        big=corners([0,0,0],[1000,1000,1000])
        c=camera_for(np.concatenate((small,big)),self.view,self.config,"reference_world")
        a=np.max(np.ptp(project(small,c)[:,:2],axis=0))
        b=np.max(np.ptp(project(big,c)[:,:2],axis=0))
        self.assertAlmostEqual(b/a,1000)

    def test_dsl_inverse_is_not_best_fit(self):
        ref=corners([20,30,40],[40,70,50])
        extent=np.max(np.ptp(ref,axis=0))
        center=(ref.min(axis=0)+ref.max(axis=0))/2
        a,_=transform(np.array([[-100,0,0],[100,0,0]],float),extent/200,center)
        self.assertAlmostEqual(a[1,0]-a[0,0],extent)


if __name__=="__main__":
    unittest.main()
