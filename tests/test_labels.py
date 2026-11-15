import unittest
from backend.config import default_config, merge, validate

class LabelTests(unittest.TestCase):
    def test_existing_configuration_gains_labels(self):
        old=default_config();del old['labels']
        current=validate(merge(default_config(),old))
        self.assertEqual(current['labels']['title'],'DYSTOPIAN / SURVEILLANCE')

    def test_display_name_does_not_change_panel_id(self):
        config=default_config();config['panels'][0]['name']='Mi cámara'
        config['labels']['title']='Mi escritorio'
        self.assertEqual(validate(config)['panels'][0]['id'],'cam-1')
        config['labels']['title']=' '
        with self.assertRaises(ValueError):validate(config)
