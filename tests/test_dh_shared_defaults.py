"""The released seeds must permit unvisited shared LOD requests."""
from pathlib import Path
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SharedLodDefaultsTests(unittest.TestCase):
    def config(self, side):
        return tomllib.loads((ROOT / f'pack/{side}-overrides/config/DistantHorizons.toml').read_text('utf-8-sig'))

    def test_server_serves_the_authorized_pregen_coverage(self):
        config = self.config('server')
        self.assertEqual(config['common']['worldGenerator']['generationMaxChunkRadius'], 625)
        self.assertEqual(config['common']['worldGenerator']['chunkGeneratorMode'], 'PRE_EXISTING_ONLY')
        server = config['server']
        self.assertGreaterEqual(server['maxGenerationRequestDistance'], 625)
        self.assertGreaterEqual(server['maxSyncOnLoadRequestDistance'], server['maxGenerationRequestDistance'])
        self.assertTrue(server['synchronizeOnLoad'])
        self.assertTrue(server['enableRealTimeUpdates'])
        self.assertEqual(server['realTimeUpdateDistanceRadiusInChunks'], 256)

    def test_fresh_clients_do_not_keep_the_legacy_origin_boundary(self):
        config = self.config('client')
        self.assertEqual(config['common']['worldGenerator']['generationMaxChunkRadius'], 0)
        self.assertEqual(config['client']['advanced']['graphics']['quality']['lodChunkRenderDistanceRadius'], 256)
        self.assertFalse(config['client']['advanced']['autoUpdater']['enableAutoUpdater'])


if __name__ == '__main__':
    unittest.main()
