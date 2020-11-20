# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from oca.models.base_model_ import Model
from oca.models.home_screen_navigation_button import HomeScreenNavigationButton
from oca import util

from oca.models.home_screen_navigation_button import HomeScreenNavigationButton  # noqa: E501

class HomeScreenBottomNavigation(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, buttons=None):  # noqa: E501
        """HomeScreenBottomNavigation - a model defined in OpenAPI

        :param buttons: The buttons of this HomeScreenBottomNavigation.  # noqa: E501
        :type buttons: List[HomeScreenNavigationButton]
        """
        self.openapi_types = {
            'buttons': List[HomeScreenNavigationButton]
        }

        self.attribute_map = {
            'buttons': 'buttons'
        }

        self._buttons = buttons

    @classmethod
    def from_dict(cls, dikt) -> 'HomeScreenBottomNavigation':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HomeScreenBottomNavigation of this HomeScreenBottomNavigation.  # noqa: E501
        :rtype: HomeScreenBottomNavigation
        """
        return util.deserialize_model(dikt, cls)

    @property
    def buttons(self):
        """Gets the buttons of this HomeScreenBottomNavigation.


        :return: The buttons of this HomeScreenBottomNavigation.
        :rtype: List[HomeScreenNavigationButton]
        """
        return self._buttons

    @buttons.setter
    def buttons(self, buttons):
        """Sets the buttons of this HomeScreenBottomNavigation.


        :param buttons: The buttons of this HomeScreenBottomNavigation.
        :type buttons: List[HomeScreenNavigationButton]
        """

        self._buttons = buttons