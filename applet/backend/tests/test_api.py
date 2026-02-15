"""Unit tests for Flask API endpoints"""
import os
import sys
import unittest
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import app


class TestHealthEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_health_check(self):
        response = self.app.get('/api/health')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'healthy')


class TestModelStatusEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_model_status_initial(self):
        response = self.app.get('/api/model/status')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('model_loaded', data)
        self.assertIn('device', data)


class TestGenerateEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_generate_without_model(self):
        response = self.app.post(
            '/api/generate',
            data=json.dumps({'nu_value': 0.0, 'num_maps': 1}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])
    
    def test_generate_invalid_nu_value(self):
        response = self.app.post(
            '/api/generate',
            data=json.dumps({'nu_value': 0.5, 'num_maps': 1}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])
    
    def test_generate_invalid_num_maps(self):
        response = self.app.post(
            '/api/generate',
            data=json.dumps({'nu_value': 0.0, 'num_maps': 7}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])


class TestLoadModelEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_load_model_endpoint_exists(self):
        response = self.app.post('/api/model/load')
        self.assertNotEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
