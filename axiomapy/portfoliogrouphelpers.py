# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 10:12:02 2025

@author: MMAD
"""


import json
import logging

from axiomapy.axiomaexceptions import AxiomaRequestValidationError
from axiomapy.odatahelpers import oDataFilterHelper as od
from axiomapy.axiomaapi import PortfolioGroupsAPI
from axiomapy import portfoliohelpers
    
class PortfolioGroup:
    """
    :ivar _portfolioGroupName: The name of the portfolio group.
    :type _portfolioGroupName: str
    :ivar _description: A brief description of the portfolio group.
    :type _description: str, optional
    :ivar _portfolios: The list of portfolios included in the portfolio group.
    :type _portfolios: list, portfolio ids
    :ivar _teams: The teams associated with the portfolio group.
    :type _teams: list,PortfolioGroupTeams, optional
    :ivar _users: The users associated with the portfolio group.
    :type _users: list,PortfolioGroupUsers, optional
    """

    _portfolioGroupName = None
    _description = None
    _portfolios = None
    _teams = None
    _users = None              

    def __init__(self,
                 name : str,
                 description : str = None,
                 portfolios : list = None):
        self._portfolioGroupName = name
        self._description = description
        self._portfolios = portfolios
        #self._teams = teams
        #self._users = users
        
    @property
    def portfolioGroupName(self):
        return self._portfolioGroupName

    @portfolioGroupName.setter
    def portfolioGroupName(self, value: str):
        self._portfolioGroupName = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value: str):
        self._description = value

    @property
    def portfolios(self):
        return self._portfolios

    @portfolios.setter
    def portfolios(self, value: list):
        self._portfolios = value
        
    def get_portfolio_group(self) -> dict:
        if self._portfolioGroupName is None:
            raise ValueError('Portfolio Group name cannot be null')     
        return dict(portfolioGroupName=self._portfolioGroupName,
                    description=self._description,
                    portfolios=self._portfolios)
    
    
    def add_portfolio_to_list(self, portfolios : list) -> None:  #check syntax
        for item in portfolios:
            if isinstance(item, portfoliohelpers.Portfolio):
                if item._portfolioId is None:
                    self.put_portfolio()
                self._portfolios.append(item._portfolioId)
            else:
                raise ValueError(f'{item.portfolioName} not found') 
        self._portfolios = sorted(self._portfolios)
                
    def remove_portfolio(self, portfolio: (str, portfoliohelpers.Portfolio)) -> None:
        if isinstance(portfolio, portfoliohelpers.Portfolio):
            portfolio = portfolio._portfolioId
        for p in self._portfolios:
            if p._portfolioId == portfolio:
                self._portfolios.remove(p)
                break
    
    
    def put_portfolio_group(self) -> bool:
        """
        """
        portfolio_group_struct = dict(name=self._portfolioGroupName,
                                description=self._description,
                                portfolios=self._portfolios)
        try:
            r = PortfolioGroupsAPI.post_portfolio_group(portfolio_group=portfolio_group_struct)
            pId = int(r.headers['location'].split('/')[-1])
        except AxiomaRequestValidationError as e:
            c = (json.loads(e.content))
            if c['message'] == 'Duplicate Resource':
                logging.info('Portfolio group already exists--fetching existing portfolio')
                r = PortfolioGroupsAPI.get_portfolio_group(
                    filter_results=od.equals('name', portfolio_group_struct['name']))
                c = r.json()
                pId = int(c['items'][0]['id'])
                try:
                    r = PortfolioGroupsAPI.put_portfolio(pId, portfolio_group=portfolio_group_struct)
                    assert r.json()['items'][0]['id'] == pId
                except AxiomaRequestValidationError as e:
                    logging.exception(
                        'Failed to update portfolio group in Axioma Risk %s: %s',
                        pId, e)
                    raise
            else:
                logging.exception('Failed to add portfolio group to Axioma Risk: %s', e)
                raise
        logging.info('Portfolio group ID is %d', pId)
        self._portfolioGroupId = pId
        return True       
    
    
    

