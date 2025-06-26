import datetime
import logging
import sys
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from axiomapy.axiomaapi import QuantityType, IdentifierType
from axiomapy.axiomaapi.portfolios import PortfoliosAPI
from axiomapy.portfoliohelpers import (Portfolio, Position,
                                       Quantity, Identifiers,
                                       Identifier)


class TestPortfolio(TestCase):
    def setUp(self):
        self.portfolio_name = "Test Portfolio"
        self.portfolio_date = "2025-06-25"
        self.portfolio_description = "A test portfolio"
        self.portfolio_currency = "USD"
        self.portfolio_positions = []
        self.portfolio = Portfolio(
            name=self.portfolio_name,
            date=self.portfolio_date,
            description=self.portfolio_description,
            currency=self.portfolio_currency,
            positions=self.portfolio_positions
        )
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        logging.root.setLevel(logging.DEBUG)

    @patch.object(PortfoliosAPI, 'post_portfolio',
                  return_value=MagicMock(headers={'location': '/api/v1/portfolios/42'}))
    def test_put_portfolio_creates_new(self, mock_post_portfolio):
        result = self.portfolio.put_portfolio()
        self.assertTrue(result)
        self.assertEqual(42, self.portfolio._portfolioId)

    @patch.object(PortfoliosAPI, 'get_positions_at_date',
                  return_value=MagicMock(json=lambda: {'items': []}))
    def test_get_positions_for_date_no_positions(self, mock_get_positions_at_date):
        self.portfolio._portfolioId = 42
        n = self.portfolio.get_positions_for_date(date=self.portfolio_date)
        self.assertEqual([], self.portfolio.positions)
        self.assertEqual(0, n)
        self.portfolio._portfolioId = None

    def test_add_position(self):
        position = Position(client_id="001",
                            identifiers=Identifiers([Identifier(
                                identifier_type=IdentifierType.TICKER,
                                identifier_id='AAPL')]),
                            quantity=Quantity(
                                value=100,
                                scale=QuantityType.NumberOfInstruments))
        self.portfolio.add_position(position)
        self.assertIn(position, self.portfolio.positions)

    def test_del_position_by_object(self):
        position = Position(client_id="002",
                            identifiers=Identifiers([Identifier(
                                identifier_type=IdentifierType.TICKER,
                                identifier_id='ZOOM')]),
                            quantity=Quantity(
                                value=100,
                                scale=QuantityType.NumberOfInstruments))
        self.portfolio.add_position(position)
        self.portfolio.del_position(position)
        self.assertNotIn(position, self.portfolio.positions)

    def test_del_position_by_client_id(self):
        position = Position(client_id="003",
                            identifiers=Identifiers([Identifier(
                                identifier_type=IdentifierType.TICKER,
                                identifier_id='INGP')]),
                            quantity=Quantity(
                                value=100,
                                scale=QuantityType.NumberOfInstruments))
        self.portfolio.add_position(position)
        self.portfolio.del_position("003")
        self.assertNotIn(position, self.portfolio.positions)

    def test_portfolio_name_property(self):
        self.assertEqual(self.portfolio_name, self.portfolio.portfolioName)
        self.portfolio.portfolioName = "Updated Portfolio"
        self.assertEqual("Updated Portfolio", self.portfolio.portfolioName)

    def test_benchmark_property(self):
        self.assertIsNone(self.portfolio.benchmark)
        self.portfolio.benchmark = "S&P 500"
        self.assertEqual("S&P 500", self.portfolio.benchmark)

    def test_date_property(self):
        self.assertEqual(datetime.date(2025, 6, 25), self.portfolio.date)
        self.portfolio.date = "2025-07-01"
        self.assertEqual(datetime.date(2025, 7, 1), self.portfolio.date)

    def test_currency_property(self):
        self.assertEqual("USD", self.portfolio.currency)
        self.portfolio.currency = "EUR"
        self.assertEqual("EUR", self.portfolio.currency)

    def test_description_property(self):
        self.assertEqual("A test portfolio", self.portfolio.description)
        self.portfolio.description = "An updated test portfolio"
        self.assertEqual("An updated test portfolio", self.portfolio.description)

    def test_get_all_portfolios(self):
        with patch.object(PortfoliosAPI, 'get_portfolios', return_value=MagicMock(
                json=lambda: {'items': [{'id': 1,
                                         'name': 'Portfolio 1',
                                         'description': 'First Portfolio'},
                                        {'id': 2,
                                         'name': 'Portfolio 2',
                                         'description': 'Second Portfolio'}]})):
            portfolios = Portfolio.get_all_portfolios()
            self.assertEqual(2, len(portfolios))
            self.assertEqual("Portfolio 1", portfolios[0].portfolioName)
            self.assertEqual("Portfolio 2", portfolios[1].portfolioName)

    def test_get_portfolio_by_name(self):
        with patch.object(PortfoliosAPI, 'get_portfolios',
                          return_value=MagicMock(
                json=lambda: {'items': [{'id': 3,
                                         'name': 'Named Portfolio',
                                         'description': 'Description'}]})):
            portfolio = Portfolio.get_portfolio_by_name("Named Portfolio")
            self.assertEqual("Named Portfolio", portfolio.portfolioName)
            self.assertEqual("Description", portfolio.description)

    @patch.object(PortfoliosAPI, 'delete_positions',
                  return_value=MagicMock(status_code=200))
    @patch.object(PortfoliosAPI, 'patch_positions',
                  return_value=MagicMock(status_code=200))
    def test_put_positions_updates_successfully(self,
                                                mock_patch_positions,
                                                mock_delete_positions):
        self.portfolio._portfolioId = 1
        self.portfolio.positions = [
            Position(client_id="001",
                     identifiers=MagicMock(
                         get_identifiers=lambda: {"idType": "CUSIP",
                                                  "idValue": "123456"}),
                     quantity=MagicMock(
                         get_dict=lambda: {"type": "SHARES",
                                           "value": 100}))
        ]
        result = self.portfolio.put_positions()
        self.assertTrue(result)

    def test_get_no_portfolio(self):
        with patch.object(PortfoliosAPI, 'get_portfolios',
                          return_value=MagicMock(status_code=404)):
            portfolio = Portfolio.get_portfolio_by_name("Nonexistent Portfolio")
            self.assertIsNone(portfolio)

    def test_str_representation(self):
        self.portfolio.positions = [
            Position(client_id="001",
                     identifiers=Identifiers([Identifier(
                         identifier_type=IdentifierType.TICKER,
                         identifier_id='ZOOM')]),
                     quantity=Quantity(
                         value=100,
                         scale=QuantityType.NumberOfInstruments)),
            Position(client_id="002",
                     identifiers=Identifiers([Identifier(
                         identifier_type=IdentifierType.TICKER,
                         identifier_id='IBM')]),
                     quantity=Quantity(
                         value=100,
                         scale=QuantityType.NumberOfInstruments)),
        ]
        expected_str = "Portfolio: Test Portfolio on 2025-06-25, # of positions : 2"
        self.assertEqual(expected_str, str(self.portfolio))
        expected_str = "Position: 001 : {'value': 100.0, 'scale': " \
            "'NumberOfInstruments'} of [{'type': 'TICKER', 'value': 'ZOOM'}]"
        self.assertEqual(expected_str, str(self.portfolio.positions[0]))
        expected_str = "Position: 002 : {'value': 100.0, 'scale': " \
            "'NumberOfInstruments'} of [{'type': 'TICKER', 'value': 'IBM'}]"
        self.assertEqual(expected_str, str(self.portfolio.positions[1]))


if __name__ == "__main__":
    unittest.main()
