# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from oca.models.base_model_ import Model
from oca import util


class HomescreenNavigationButton(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, icon=None, label=None, action=None, badge_key=None):  # noqa: E501
        """HomescreenNavigationButton - a model defined in OpenAPI

        :param icon: The icon of this HomescreenNavigationButton.  # noqa: E501
        :type icon: str
        :param label: The label of this HomescreenNavigationButton.  # noqa: E501
        :type label: str
        :param action: The action of this HomescreenNavigationButton.  # noqa: E501
        :type action: str
        :param badge_key: The badge_key of this HomescreenNavigationButton.  # noqa: E501
        :type badge_key: str
        """
        self.openapi_types = {
            'icon': str,
            'label': str,
            'action': str,
            'badge_key': str
        }

        self.attribute_map = {
            'icon': 'icon',
            'label': 'label',
            'action': 'action',
            'badge_key': 'badge_key'
        }

        self._icon = icon
        self._label = label
        self._action = action
        self._badge_key = badge_key

    @classmethod
    def from_dict(cls, dikt) -> 'HomescreenNavigationButton':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HomescreenNavigationButton of this HomescreenNavigationButton.  # noqa: E501
        :rtype: HomescreenNavigationButton
        """
        return util.deserialize_model(dikt, cls)

    @property
    def icon(self):
        """Gets the icon of this HomescreenNavigationButton.


        :return: The icon of this HomescreenNavigationButton.
        :rtype: str
        """
        return self._icon

    @icon.setter
    def icon(self, icon):
        """Sets the icon of this HomescreenNavigationButton.


        :param icon: The icon of this HomescreenNavigationButton.
        :type icon: str
        """
        if icon is None:
            raise ValueError("Invalid value for `icon`, must not be `None`")  # noqa: E501

        self._icon = icon

    @property
    def label(self):
        """Gets the label of this HomescreenNavigationButton.


        :return: The label of this HomescreenNavigationButton.
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label):
        """Sets the label of this HomescreenNavigationButton.


        :param label: The label of this HomescreenNavigationButton.
        :type label: str
        """
        if label is None:
            raise ValueError("Invalid value for `label`, must not be `None`")  # noqa: E501

        self._label = label

    @property
    def action(self):
        """Gets the action of this HomescreenNavigationButton.


        :return: The action of this HomescreenNavigationButton.
        :rtype: str
        """
        return self._action

    @action.setter
    def action(self, action):
        """Sets the action of this HomescreenNavigationButton.


        :param action: The action of this HomescreenNavigationButton.
        :type action: str
        """
        if action is None:
            raise ValueError("Invalid value for `action`, must not be `None`")  # noqa: E501

        self._action = action

    @property
    def badge_key(self):
        """Gets the badge_key of this HomescreenNavigationButton.


        :return: The badge_key of this HomescreenNavigationButton.
        :rtype: str
        """
        return self._badge_key

    @badge_key.setter
    def badge_key(self, badge_key):
        """Sets the badge_key of this HomescreenNavigationButton.


        :param badge_key: The badge_key of this HomescreenNavigationButton.
        :type badge_key: str
        """

        self._badge_key = badge_key
