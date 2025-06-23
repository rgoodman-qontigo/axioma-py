"""
Copyright © 2024 Axioma by SimCorp.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

"""
import copy
import datetime
import json
import logging

from axiomapy.axiomaapi import PortfoliosAPI
from axiomapy.axiomaexceptions import AxiomaRequestValidationError
from axiomapy.odatahelpers import oDataFilterHelper as od


class Position:
    """
    Represents a client's position in Axioma Risk.

    This class encapsulates attributes related to a financial position, enabling the
    storage, comparison, and retrieval of key position details. It supports comparison
    operators for sorting and equality evaluation based on client identifiers. This
    class is designed to ensure encapsulation and validation of its data while
    interacting with external systems or workflows.

    :ivar _client_id: Unique identifier for the client.
    :type _client_id: str
    :ivar _identifiers: List of related identifiers for the position, such as security
    IDs. Defaults to None.
    :type _identifiers: list
    :ivar _quantity: Dictionary representing quantities or balances of financial
    instruments.
    :type _quantity: dict
    :ivar _instrumentMapping: Mapping or description of the financial instrument type.
    Defaults to 'Default'.
    :type _instrumentMapping: str
    """
    _client_id = None
    _identifiers = None
    _quantity = None
    _instrumentMapping = None

    def __init__(self,
                 client_id : str,
                 identifiers : list = None,
                 quantity : dict = None,
                 instrumentMapping : str = 'Default'):
        self.client_id = client_id
        self.identifiers = copy.copy(identifiers)
        self.quantity = copy.copy(quantity)
        self.instrumentMapping = instrumentMapping

    def __eq__(self, other):
        return self._client_id == other.client_id

    def __lt__(self, other):
        return self._client_id < other.client_id

    def __gt__(self, other):
        return self._client_id > other.client_id

    def __ge__(self, other):
        return self._client_id >= other.client_id

    def __le__(self, other):
        return self._client_id <= other.client_id

    @property
    def client_id(self) -> str:
        return self._client_id

    @client_id.setter
    def client_id(self, value: str) -> None:
        self._client_id = value

    @property
    def identifiers(self) -> list:
        return self._identifiers

    @identifiers.setter
    def identifiers(self, value: list) -> None:
        self._identifiers = value

    @property
    def quantity(self) -> dict:
        return self._quantity

    @quantity.setter
    def quantity(self, value: dict) -> None:
        self._quantity = value

    @property
    def instrumentMapping(self) -> str:
        return self._instrumentMapping

    @instrumentMapping.setter
    def instrumentMapping(self, value: str) -> None:
        self._instrumentMapping = value

    def get_position(self) -> dict:
        if self._client_id is None or \
           self._identifiers is None or \
           self._quantity is None or \
           self._instrumentMapping is None:
            raise ValueError('Must fill in all fields for position')
        return dict(client_id=self._client_id,
                    identifiers=self._identifiers,
                    quantity=self._quantity,
                    instrumentMapping=self._instrumentMapping)


class Portfolio:
    """
    Represents a financial portfolio, managing its properties, positions, and
    interaction with external systems.

    This class is designed to provide a structured representation of a financial
    portfolio, including its metadata (e.g., name, description, currency, and date)
    and associated positions. The portfolio can interact with Axioma Risk APIs to
    manage its state. Positions can also be dynamically managed (added or removed)
    and accurately tracked.

    :ivar _portfolioName: The name of the portfolio.
    :type _portfolioName: str
    :ivar _description: A brief description of the portfolio.
    :type _description: str, optional
    :ivar _currency: The default currency of the portfolio.
    :type _currency: str, optional
    :ivar _portfolioDate: The effective date of the portfolio.
    :type _portfolioDate: datetime.date
    :ivar _portfolioId: The internal identifier of the portfolio in the external system.
    :type _portfolioId: int, optional
    """

    _portfolioName = None
    _description = None
    _currency = None
    _portfolioDate = None
    _portfolioId = None

    def __init__(self,
                 name : str,
                 date : (str, datetime.date),
                 description : str = None,
                 currency : str = None,
                 positions : list = None):
        self._description = description
        self._portfolioName = name
        self._currency = currency
        if isinstance(date, str):
            assert len(date) == 10, 'Date must be a string of format YYYY-MM-DD'
            date = datetime.date(int(date[:4]), int(date[5:7]), int(date[8:10]))
        self._portfolioDate = date
        self._my_positions = sorted(positions) if positions is not None else []

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, value: str):
        self._currency = value

    @property
    def portfolioName(self):
        return self._portfolioName

    @portfolioName.setter
    def portfolioName(self, value: str):
        self._portfolioName = value

    @property
    def portfolioDate(self):
        return self._portfolioDate

    @portfolioDate.setter
    def portfolioDate(self, value : (str, datetime.date)):
        if isinstance(value, str):
            assert len(value) == 10, 'Date must be a string of format YYYY-MM-DD'
            value = datetime.date(int(value[:4]), int(value[5:7]), int(value[8:10]))
        self._portfolioDate = value

    @property
    def positions(self) -> list:
        return self._my_positions

    def add_position(self, position : Position) -> None:
        self._my_positions.append(position)
        self._my_positions = sorted(self._my_positions)

    def del_position(self, position : (str, Position)) -> None:
        if isinstance(position, Position):
            position = position.client_id
        for p in self._my_positions:
            if p.client_id == position:
                self._my_positions.remove(p)
                break

    @positions.setter
    def positions(self, value: list) -> None:
        self._my_positions = sorted(value)

    def put_portfolio(self) -> bool:
        """
        Add or update a portfolio in Axioma Risk.

        This function attempts to add a portfolio defined by the instance's attributes
        to Axioma Risk using the `post_portfolio` method. If the portfolio with the
        same name already exists, it retrieves the existing portfolio's ID and updates
        it using the `put_portfolio` method. The portfolio's ID will be stored in the
        instance attribute `_portfolioId`.

        :raises AxiomaRequestValidationError: If an error occurs while adding or
            updating the portfolio in Axioma Risk that is not related to a duplicate
            resource.
        :raises ConnectionError: If there is an issue communicating with the Axioma
            Risk API during either portfolio creation or update.

        :return: True if the portfolio was successfully added or updated in Axioma Risk.
        :rtype: bool
        """
        portfolio_struct = dict(name=self._portfolioName,
                                longName=self._description,
                                defaultCurrency=self._currency)
        try:
            r = PortfoliosAPI.post_portfolio(portfolio=portfolio_struct)
            pId = int(r.headers['location'].split('/')[-1])
        except AxiomaRequestValidationError as e:
            c = (json.loads(e.content))
            if c['message'] == 'Duplicate Resource':
                logging.info('Portfolio already exists--fetching existing portfolio')
                r = PortfoliosAPI.get_portfolios(
                    filter_results=od.equals('name', portfolio_struct['name']))
                c = r.json()
                pId = int(c['items'][0]['id'])
                try:
                    r = PortfoliosAPI.put_portfolio(pId, portfolio=portfolio_struct)
                    assert r.json()['items'][0]['id'] == pId
                except AxiomaRequestValidationError as e:
                    logging.exception(
                        'Failed to update portfolio in Axioma Risk %s: %s',
                        pId, e)
                    raise
            else:
                logging.exception('Failed to add portfolio to Axioma Risk: %s', e)
                raise
        logging.info('Portfolio ID is %d', pId)
        self._portfolioId = pId
        return True

    def get_portfolio(self) -> dict:
        if self._portfolioDate is None:
            raise ValueError('Must set portfolio date')
        return dict(
            portfolioDate=self._portfolioDate,
            positions=[p.get_position() for p in self._my_positions]
        )

    def put_positions(self) -> bool:
        """
        Handles the addition, deletion, and updating of positions within a portfolio
        in Axioma Risk.

        The method is responsible for deleting existing portfolio positions for a
        specified date and replacing them with new positions provided. To improve
        performance, the new positions are processed in chunks. If errors occur
        during the process, appropriate logs are generated and the method returns a
        failure status.

        :return: Returns ``True`` if all portfolio positions are successfully processed,
                 otherwise returns ``False``.

        :raises Exception: An exception is raised if an unexpected error occurs during
                           the deletion or updating of portfolio positions.

        :rtype: bool
        """
        if self._portfolioId is None:
            if not self.put_portfolio():
                return False
        try:
            logging.info('Deleting positions for portfolio %s on date %s',
                         self._portfolioId, self._portfolioDate)
            delete_positions = PortfoliosAPI.delete_positions(
                portfolio_id=self._portfolioId,
                as_of_date=str(self._portfolioDate))
            if delete_positions.status_code in range(200, 299):
                logging.info(
                    'Successfully deleted positions for portfolio %s on date %s \
                    with status code %s',
                    self._portfolioId, self._portfolioDate,
                    delete_positions.status_code)
            else:
                logging.error(
                    'Delete positions failed for portfolio %s on date %s with status \
                    code %s',
                    self._portfolioId, self._portfolioDate,
                    delete_positions.status_code)
                return False
        except Exception as ex:  # pylint: disable=broad-except
            logging.exception(
                'Failed to delete positions for portfolio %s on date %s: %s',
                self._portfolioId, self._portfolioDate, ex)
            return False
        chunk_size = 10000
        chunked_positions = [self._my_positions[i:i + chunk_size]
                             for i in range(0, len(self._my_positions), chunk_size)]
        logging.info(
            'Adding %s positions for portfolio %s on date %s in chunks of max \
            %s assets',
            len(self._my_positions), self._portfolioId, self._portfolioDate,
            chunk_size)
        try:
            for i, chunk in enumerate(chunked_positions):
                positions = []
                for a in chunk:
                    positions.append(dict(clientId=a.client_id,
                                          identifiers=a.identifiers,
                                          quantity=a.quantity))
                patch = PortfoliosAPI.patch_positions(
                    as_of_date=str(self._portfolioDate),
                    portfolio_id=self._portfolioId,
                    positions_upsert=positions,
                    positions_remove=[])
                if patch.status_code in range(200, 299):
                    logging.info(
                        'Successfully patched positions chunk %s of %s with %s \
                        positions for portfolio %s on date %s with status code %s',
                        i + 1, len(chunked_positions), len(chunk), self._portfolioId,
                        self._portfolioDate, patch.status_code)
                else:
                    logging.info(
                        'Failed to patch positions chunk %s of %s with %s \
                        positions for portfolio %s on date %s with status code %s',
                        i + 1, len(chunked_positions), len(chunk), self._portfolioId,
                        self._portfolioDate, patch.status_code)
                    return False
        except Exception as ex:  # pylint: disable=broad-except
            logging.exception(
                'Failed to load positions for portfolio %s on date %s: %s',
                self._portfolioId, self._portfolioDate, ex)
            return False

        return True
