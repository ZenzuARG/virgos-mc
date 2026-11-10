from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MenuAndBackpackRegressionTest(unittest.TestCase):
    def source(self, relative):
        return (ROOT / relative).read_text(encoding='utf-8')

    def test_backpack_key_guard_allows_hovered_backpack_in_container_screens(self):
        text = self.source('dev/dh-compat/src/main/java/mc/virgos/dhcompat/mixin/BackpackKeyGuardMixin.java')
        self.assertNotIn('screen instanceof AbstractContainerScreen<?>', text)
        self.assertIn('BackpackScreen', text)

    def test_virgos_menu_renders_guide_after_closing_menu(self):
        text = self.source('dev/virgos-core/src/main/java/mc/virgos/TownServices.java')
        clicked = text.split('public void clicked', 1)[1].split('public ItemStack quickMoveStack', 1)[0]
        self.assertIn('PlayerGuide.show', clicked)
        self.assertIn('var server=p.getServer()', clicked)
        self.assertIn('server.execute', clicked)
        self.assertLess(clicked.index('closeContainer'), clicked.index('PlayerGuide.show'))


if __name__ == '__main__':
    unittest.main()
