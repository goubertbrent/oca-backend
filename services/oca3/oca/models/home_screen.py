# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from oca.models.base_model_ import Model
from oca.models.homescreen_bottom_navigation import HomescreenBottomNavigation
from oca.models.homescreen_bottom_sheet import HomescreenBottomSheet
from oca.models.homescreen_content import HomescreenContent
from oca import util

from oca.models.homescreen_bottom_navigation import HomescreenBottomNavigation  # noqa: E501
from oca.models.homescreen_bottom_sheet import HomescreenBottomSheet  # noqa: E501
from oca.models.homescreen_content import HomescreenContent  # noqa: E501

class HomeScreen(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, content=None, bottom_navigation=None, bottom_sheet=None, default_language=None, translations=None):  # noqa: E501
        """HomeScreen - a model defined in OpenAPI

        :param content: The content of this HomeScreen.  # noqa: E501
        :type content: HomescreenContent
        :param bottom_navigation: The bottom_navigation of this HomeScreen.  # noqa: E501
        :type bottom_navigation: HomescreenBottomNavigation
        :param bottom_sheet: The bottom_sheet of this HomeScreen.  # noqa: E501
        :type bottom_sheet: HomescreenBottomSheet
        :param default_language: The default_language of this HomeScreen.  # noqa: E501
        :type default_language: str
        :param translations: The translations of this HomeScreen.  # noqa: E501
        :type translations: Dict[str, Dict[str, str]]
        """
        self.openapi_types = {
            'content': HomescreenContent,
            'bottom_navigation': HomescreenBottomNavigation,
            'bottom_sheet': HomescreenBottomSheet,
            'default_language': str,
            'translations': Dict[str, Dict[str, str]]
        }

        self.attribute_map = {
            'content': 'content',
            'bottom_navigation': 'bottom_navigation',
            'bottom_sheet': 'bottom_sheet',
            'default_language': 'default_language',
            'translations': 'translations'
        }

        self._content = content
        self._bottom_navigation = bottom_navigation
        self._bottom_sheet = bottom_sheet
        self._default_language = default_language
        self._translations = translations

    @classmethod
    def from_dict(cls, dikt) -> 'HomeScreen':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HomeScreen of this HomeScreen.  # noqa: E501
        :rtype: HomeScreen
        """
        return util.deserialize_model(dikt, cls)

    @property
    def content(self):
        """Gets the content of this HomeScreen.


        :return: The content of this HomeScreen.
        :rtype: HomescreenContent
        """
        return self._content

    @content.setter
    def content(self, content):
        """Sets the content of this HomeScreen.


        :param content: The content of this HomeScreen.
        :type content: HomescreenContent
        """
        if content is None:
            raise ValueError("Invalid value for `content`, must not be `None`")  # noqa: E501

        self._content = content

    @property
    def bottom_navigation(self):
        """Gets the bottom_navigation of this HomeScreen.


        :return: The bottom_navigation of this HomeScreen.
        :rtype: HomescreenBottomNavigation
        """
        return self._bottom_navigation

    @bottom_navigation.setter
    def bottom_navigation(self, bottom_navigation):
        """Sets the bottom_navigation of this HomeScreen.


        :param bottom_navigation: The bottom_navigation of this HomeScreen.
        :type bottom_navigation: HomescreenBottomNavigation
        """
        if bottom_navigation is None:
            raise ValueError("Invalid value for `bottom_navigation`, must not be `None`")  # noqa: E501

        self._bottom_navigation = bottom_navigation

    @property
    def bottom_sheet(self):
        """Gets the bottom_sheet of this HomeScreen.


        :return: The bottom_sheet of this HomeScreen.
        :rtype: HomescreenBottomSheet
        """
        return self._bottom_sheet

    @bottom_sheet.setter
    def bottom_sheet(self, bottom_sheet):
        """Sets the bottom_sheet of this HomeScreen.


        :param bottom_sheet: The bottom_sheet of this HomeScreen.
        :type bottom_sheet: HomescreenBottomSheet
        """
        if bottom_sheet is None:
            raise ValueError("Invalid value for `bottom_sheet`, must not be `None`")  # noqa: E501

        self._bottom_sheet = bottom_sheet

    @property
    def default_language(self):
        """Gets the default_language of this HomeScreen.

        Language to use when the user his language is not one of the available ones in the translation mapping  # noqa: E501

        :return: The default_language of this HomeScreen.
        :rtype: str
        """
        return self._default_language

    @default_language.setter
    def default_language(self, default_language):
        """Sets the default_language of this HomeScreen.

        Language to use when the user his language is not one of the available ones in the translation mapping  # noqa: E501

        :param default_language: The default_language of this HomeScreen.
        :type default_language: str
        """

        self._default_language = default_language

    @property
    def translations(self):
        """Gets the translations of this HomeScreen.

        Translations for any string which could be translated on the homescreen. Properties that should be translated should contain a $ prefix. For example, label -> $trash_calendar  # noqa: E501

        :return: The translations of this HomeScreen.
        :rtype: Dict[str, Dict[str, str]]
        """
        return self._translations

    @translations.setter
    def translations(self, translations):
        """Sets the translations of this HomeScreen.

        Translations for any string which could be translated on the homescreen. Properties that should be translated should contain a $ prefix. For example, label -> $trash_calendar  # noqa: E501

        :param translations: The translations of this HomeScreen.
        :type translations: Dict[str, Dict[str, str]]
        """
        if translations is None:
            raise ValueError("Invalid value for `translations`, must not be `None`")  # noqa: E501

        self._translations = translations
