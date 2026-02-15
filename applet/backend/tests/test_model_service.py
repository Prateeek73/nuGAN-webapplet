"""Unit tests for ModelService class"""
import os
import sys
import unittest
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from services.model_service import ModelService


class TestModelServiceInit(unittest.TestCase):
    def test_init_default_device(self):
        service = ModelService()
        self.assertIsNotNone(service.device)
        self.assertFalse(service.is_loaded())
    
    def test_init_cpu_device(self):
        service = ModelService(device='cpu')
        self.assertEqual(str(service.device), 'cpu')
    
    def test_model_not_loaded_initially(self):
        service = ModelService()
        self.assertFalse(service.is_loaded())
        self.assertIsNone(service.model)


class TestModelServiceConstants(unittest.TestCase):
    def test_valid_nu_values(self):
        self.assertEqual(ModelService.VALID_NU_VALUES, [0.0, 0.1, 0.4, 0.8, 1.2])
    
    def test_valid_num_maps(self):
        self.assertEqual(ModelService.VALID_NUM_MAPS, [1, 2, 3, 5, 10, 20])
    
    def test_nz_dimension(self):
        self.assertEqual(ModelService.NZ, 200)
    
    def test_mchn_value(self):
        self.assertEqual(ModelService.MCHN, 2)


class TestLatentVectorGeneration(unittest.TestCase):
    def setUp(self):
        self.service = ModelService(device='cpu')
    
    def test_gaussian_prior(self):
        z = self.service.draw_latent_z(10, prior='gaussian')
        self.assertEqual(z.shape, (10, 200))
    
    def test_uniform_prior(self):
        z = self.service.draw_latent_z(5, prior='uniform')
        self.assertEqual(z.shape, (5, 200))
        self.assertTrue((z >= 0).all())
        self.assertTrue((z <= 1).all())
    
    def test_beta_prior(self):
        z = self.service.draw_latent_z(5, prior='beta')
        self.assertEqual(z.shape, (5, 200))
    
    def test_invalid_prior(self):
        with self.assertRaises(ValueError):
            self.service.draw_latent_z(5, prior='invalid')


class TestModelLoading(unittest.TestCase):
    def setUp(self):
        self.service = ModelService(device='cpu')
    
    def test_load_nonexistent_model(self):
        result = self.service.load_model('/nonexistent/path/model.pt')
        self.assertFalse(result)
        self.assertFalse(self.service.is_loaded())
    
    def test_get_device(self):
        device_str = self.service.get_device()
        self.assertIsInstance(device_str, str)


class TestModelInfo(unittest.TestCase):
    def test_model_info_not_loaded(self):
        service = ModelService(device='cpu')
        info = service.get_model_info()
        self.assertFalse(info['loaded'])
        self.assertIn('device', info)


class TestInputValidation(unittest.TestCase):
    def setUp(self):
        self.service = ModelService(device='cpu')
    
    def test_generate_without_loading(self):
        with self.assertRaises(RuntimeError):
            self.service.generate_maps(0.0, 1)
    
    def test_invalid_nu_value_validation(self):
        with self.assertRaises(RuntimeError):
            self.service.generate_maps(0.5, 1)


class TestModelServiceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 
            'best_model_state_dict.pt'
        )
        cls.model_exists = os.path.exists(cls.model_path)
    
    def setUp(self):
        if not self.model_exists:
            self.skipTest("Model file not found")
        self.service = ModelService(device='cpu')
    
    def test_load_model(self):
        result = self.service.load_model(self.model_path)
        self.assertTrue(result)
        self.assertTrue(self.service.is_loaded())
    
    def test_generate_single_map(self):
        self.service.load_model(self.model_path)
        map_data = self.service.generate_single_map(0.0, seed=42)
        self.assertIsInstance(map_data, np.ndarray)
        self.assertEqual(len(map_data.shape), 2)
    
    def test_generate_multiple_maps(self):
        self.service.load_model(self.model_path)
        maps = self.service.generate_maps(0.4, num_maps=3, seed=42)
        self.assertIsInstance(maps, np.ndarray)
        self.assertEqual(maps.shape[0], 3)
    
    def test_reproducibility_with_seed(self):
        self.service.load_model(self.model_path)
        map1 = self.service.generate_single_map(0.1, seed=123)
        map2 = self.service.generate_single_map(0.1, seed=123)
        np.testing.assert_array_almost_equal(map1, map2)
    
    def test_different_nu_values(self):
        self.service.load_model(self.model_path)
        for nu in ModelService.VALID_NU_VALUES:
            map_data = self.service.generate_single_map(nu, seed=42)
            self.assertIsInstance(map_data, np.ndarray)
    
    def test_model_info_loaded(self):
        self.service.load_model(self.model_path)
        info = self.service.get_model_info()
        self.assertTrue(info['loaded'])
        self.assertIn('total_parameters', info)
        self.assertEqual(info['nz'], 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
