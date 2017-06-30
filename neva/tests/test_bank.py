"""
...
"""

from __future__ import division
import unittest
import neva


class TestBank(unittest.TestCase):
    """..."""
    def setUp(self):
        self.bank1 = neva.Bank(name='1')

    def test_naiveequity(self):
        """..."""
        self.bank1.extasset = 1.0
        self.bank1.extliab = 0.5
        self.bank1.ibliabtot = 0.1
        self.assertAlmostEqual(self.bank1.get_naiveequity(), 0.4)

    def test_ibasset_level0(self):
        """..."""
        with self.assertRaises(TypeError):
            self.bank1.set_ibasset('interbank asset')

    def test_ibasset_level1(self):
        """..."""
        with self.assertRaises(TypeError):
            self.bank1.set_ibasset(['interbank asset'])

    def test_ibasset_level2a(self):
        """..."""
        with self.assertRaises(TypeError):
            self.bank1.set_ibasset(['bank', 1.0])

    def test_ibasset_level2b(self):
        """..."""
        bank2 = neva.Bank(name='2')
        with self.assertRaises(TypeError):
            self.bank1.set_ibasset([bank2, 'interbank asset'])


class TestTwoBanks(unittest.TestCase):
    """..."""
    def setUp(self):
        self.value = 0.1
        self.bank1 = neva.Bank(extasset=1.0, extliab=0.5, ibliabtot=0.2, name='1')
        self.bank2 = neva.Bank(ibliabtot=self.value, name='2')
        self.bank1.set_ibasset([(self.bank2, self.value)])

    def test_getibassettot(self):
        """..."""
        self.assertAlmostEqual(self.bank1.get_ibassettot(), self.value)

    def test_get_naive_equity(self):
        """..."""
        self.assertAlmostEqual(self.bank1.get_naiveequity(), 0.4)


class TestThreeBanks(unittest.TestCase):
    """..."""
    def setUp(self):
        self.bank1 = neva.Bank(extasset=1.0, extliab=0.5, ibliabtot=0.2, name='1')
        self.bank2 = neva.Bank(ibliabtot=0.1, name='2')
        self.bank3 = neva.Bank(ibliabtot=0.2, name='3')
        self.bank1.set_ibasset([(self.bank2, self.bank2.ibliabtot), (self.bank3, self.bank3.ibliabtot)])

    def test_getibassettot(self):
        """..."""
        self.assertAlmostEqual(self.bank1.get_ibassettot(), 0.3)

    def test_get_naive_equity(self):
        """..."""
        self.assertAlmostEqual(self.bank1.get_naiveequity(), 0.6)


if __name__ == '__main__':
    unittest.main()
