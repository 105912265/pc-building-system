"""Run from project root: python -m unittest backend.tests.test_opendb_importer"""
import unittest
from uuid import UUID
from backend.import_opendb import normalize, name_key, combine_specs, plan_rows

class TestOpenDBImporter(unittest.TestCase):
    def test_cpu_normalisation(self):
        uid = 'e0230286-0549-4da9-8115-9d1fbdcc2979'
        raw = {
            'opendb_id': uid,
            'metadata': {'name': 'AMD Ryzen 5 7600', 'manufacturer': 'AMD', 'releaseYear': 2023},
            'socket': 'AM5', 'cores': {'total': 6, 'threads': 12},
            'clocks': {'performance': {'base': 3.8}},
            'specifications': {'tdp': 65, 'memory': {'types': ['DDR5']}}
        }
        norm = normalize('CPU', uid, raw, 2020)
        self.assertIsNotNone(norm)
        self.assertEqual(norm['specifications']['socket'], 'AM5')
        self.assertEqual(norm['specifications']['cores'], 6)
        self.assertEqual(norm['specifications']['wattage'], 65)
        self.assertEqual(norm['specifications']['source']['id'], uid)

    def test_excludes_outdated_cpu(self):
        uid = '83aee1bc-820b-42e4-a062-efb06b659df2'
        self.assertIsNone(normalize('CPU', uid, {
            'opendb_id': uid,
            'metadata': {'name': 'Intel Core i5 9600KF', 'manufacturer': 'Intel', 'releaseYear': 2019}
        }, 2020))

    def test_compatible_gpu_generation(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        gpu = {'opendb_id': uid,
               'metadata': {'name': 'ASUS ProArt GeForce RTX 5070 Ti', 'manufacturer': 'ASUS', 'releaseYear': 2025},
               'chipset': 'GeForce RTX 5070 Ti', 'tdp': 300, 'memory': 16}
        self.assertEqual(normalize('GPU', uid, gpu, 2020)['specifications']['vram'], '16GB')

    def test_2017_gtx_1080_ti_is_included(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        gpu = {
            'opendb_id': uid,
            'metadata': {'name': 'EVGA GeForce GTX 1080 Ti SC', 'manufacturer': 'EVGA', 'releaseYear': 2017},
            'chipset': 'GeForce GTX 1080 Ti', 'memory': 11, 'tdp': 250
        }
        self.assertIsNotNone(normalize('GPU', uid, gpu, 2017))
        self.assertIsNone(normalize('GPU', uid, gpu, 2020))

    def test_2016_gpu_and_undated_gpu_are_excluded(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        gpu = {
            'opendb_id': uid,
            'metadata': {'name': 'NVIDIA GeForce GTX 1080', 'manufacturer': 'NVIDIA', 'releaseYear': 2016},
            'chipset': 'GeForce GTX 1080', 'memory': 8
        }
        self.assertIsNone(normalize('GPU', uid, gpu, 2017))
        del gpu['metadata']['releaseYear']
        self.assertIsNone(normalize('GPU', uid, gpu, 2017))

    def test_rtx_20_series_allowed(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        gpu = {
            'opendb_id': uid,
            'metadata': {'name': 'GeForce RTX 2080 Ti', 'manufacturer': 'NVIDIA', 'releaseYear': 2018},
            'chipset': 'GeForce RTX 2080 Ti'
        }
        self.assertIsNotNone(normalize('GPU', uid, gpu, 2017))

    def test_existing_name_is_linked_no_fake_price(self):
        uid = 'e0230286-0549-4da9-8115-9d1fbdcc2979'
        cpu = {'opendb_id': uid,
               'metadata': {'name': 'AMD Ryzen 5 7600', 'manufacturer': 'AMD', 'releaseYear': 2023},
               'socket': 'AM5'}
        db = {name_key('CPU', 'AMD', 'Ryzen 5 7600'): {
            'component_id': 64, 'specifications': '{"cores":6}'}}
        plan, stats, sample = plan_rows(iter([('CPU', uid, cpu)]), db, {}, 2020, None)
        self.assertEqual(stats['link_existing'], 1)
        self.assertEqual(plan[0][2], 64)
        combined = combine_specs('{"cores":6,"socket":"AM5"}', {'socket':'other','source':{'id': uid}})
        self.assertEqual(combined['socket'], 'AM5')

    def test_board_partner_not_misclassified_as_chipset_vendor(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        raw = {'opendb_id': uid,
               'metadata': {'name': 'EVGA GeForce GTX 1080 Ti FTW3 GAMING 11GB GDDR5X',
                            'manufacturer': 'NVIDIA', 'releaseYear': 2017},
               'chipset': 'GeForce GTX 1080 Ti'}
        item = normalize('GPU', uid, raw, 2017)
        self.assertEqual(item['manufacturer'], 'EVGA')
        self.assertEqual(item['model'], 'GeForce GTX 1080 Ti FTW3 GAMING 11GB GDDR5X')

    def test_repeated_brand_removed_from_display_model(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        raw = {'opendb_id': uid,
               'metadata': {'name': 'MSI MSI GeForce GTX 1080 Ti GAMING X 11G',
                            'manufacturer': 'MSI', 'releaseYear': 2017},
               'chipset': 'GeForce GTX 1080 Ti'}
        item = normalize('GPU', uid, raw, 2017)
        self.assertEqual(item['manufacturer'], 'MSI')
        self.assertEqual(item['model'], 'GeForce GTX 1080 Ti GAMING X 11G')

    def test_plain_chipset_vendor_and_founders_edition(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        raw = {'opendb_id': uid,
               'metadata': {'name': 'NVIDIA Founders Edition GeForce GTX 1080 Ti',
                            'manufacturer': 'NVIDIA', 'releaseYear': 2017},
               'chipset': 'GeForce GTX 1080 Ti'}
        item = normalize('GPU', uid, raw, 2017)
        self.assertEqual(item['manufacturer'], 'NVIDIA')
        self.assertEqual(item['model'], 'Founders Edition GeForce GTX 1080 Ti')

    def test_chipset_vendor_then_explicit_board_brand(self):
        uid = '4da6c444-076c-4868-a0e9-e2369761fbc5'
        raw = {'opendb_id': uid,
               'metadata': {'name': 'NVIDIA EVGA GeForce GTX 1080 Ti',
                            'manufacturer': 'NVIDIA', 'releaseYear': 2017},
               'chipset': 'GeForce GTX 1080 Ti'}
        item = normalize('GPU', uid, raw, 2017)
        self.assertEqual(item['manufacturer'], 'EVGA')
        self.assertEqual(item['model'], 'GeForce GTX 1080 Ti')

    def test_idempotent_mapping(self):
        uid = 'e0230286-0549-4da9-8115-9d1fbdcc2979'
        cpu = {'opendb_id':uid,'metadata': {'name':'AMD Ryzen 5 7600','manufacturer':'AMD','releaseYear':2023},'socket':'AM5'}
        plan, stats, _ = plan_rows(iter([('CPU',uid,cpu)]), {}, {uid:64}, 2020, None)
        self.assertEqual(stats['update_linked'], 1)
        self.assertEqual(plan[0][2], 64)

if __name__ == '__main__':
    unittest.main()
