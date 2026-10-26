"""Focused CPU tests: identical projection, no independent fitting, real raster output."""
import tempfile
import unittest
import numpy as np
from pathlib import Path
from render_cpu import camera_for, project, render_mesh
from render_common import read, OUT


class RenderContract(unittest.TestCase):
    def setUp(self):
        self.points = np.array([[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]],float)
        self.view = {"azimuth":45.,"elevation":35.264389682754654}

    def test_identical_mesh_identical_projection(self):
        cam = camera_for(self.points,self.view,640)
        np.testing.assert_array_equal(project(self.points,cam),project(self.points.copy(),cam))

    def test_translation_is_not_recentered(self):
        cam = camera_for(self.points,self.view,640)
        baseline = project(self.points,cam)
        moved = project(self.points+[100,0,0],cam)
        self.assertGreater(np.abs(moved[:,:2]-baseline[:,:2]).max(),640)

    def test_scale_difference_preserved(self):
        cam = camera_for(self.points,self.view,640)
        small = project(self.points,cam)
        large = project(self.points*2,cam)
        np.testing.assert_allclose(np.ptp(large[:,:2],axis=0),np.ptp(small[:,:2],axis=0)*2)

    def test_union_frame_contains_both(self):
        other = self.points+[20,0,0]
        cam = camera_for(np.concatenate([self.points,other]),self.view,640,"supplemental_shared_union_frame")
        p = project(np.concatenate([self.points,other]),cam)
        self.assertGreaterEqual(p[:,:2].min(),0)
        self.assertLess(p[:,:2].max(),640)

    def test_shared_camera_and_raster_nonblank(self):
        faces=np.array([[0,1,2],[0,2,3],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])
        config=dict(read(OUT/"render_protocol.json")["image"],size=128)
        camera=camera_for(self.points,self.view,128)
        # render_mesh's artifact paths are package-relative; keep fixtures under OUT.
        with tempfile.TemporaryDirectory(dir=OUT) as directory:
            record=render_mesh(self.points,faces,camera,Path(directory)/"cube.png",config)
            self.assertGreater(record["foreground_pixels"],100)
            self.assertEqual(record["out_of_frame_vertices"],0)


if __name__ == "__main__":
    unittest.main()
