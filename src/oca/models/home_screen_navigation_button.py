# coding: utf-8

"""
    Our City App

    Our City App internal apis  # noqa: E501

    The version of the OpenAPI document: 0.0.1
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six

from oca.configuration import Configuration


class HomeScreenNavigationButton(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'icon': 'str',
        'label': 'str',
        'action': 'str'
    }

    attribute_map = {
        'icon': 'icon',
        'label': 'label',
        'action': 'action'
    }

    def __init__(self, icon=None, label=None, action=None, local_vars_configuration=None):  # noqa: E501
        """HomeScreenNavigationButton - a model defined in OpenAPI"""  # noqa: E501
        if local_vars_configuration is None:
            local_vars_configuration = Configuration()
        self.local_vars_configuration = local_vars_configuration

        self._icon = None
        self._label = None
        self._action = None
        self.discriminator = None

        self.icon = icon
        self.label = label
        self.action = action

    @property
    def icon(self):
        """Gets the icon of this HomeScreenNavigationButton.  # noqa: E501


        :return: The icon of this HomeScreenNavigationButton.  # noqa: E501
        :rtype: str
        """
        return self._icon

    @icon.setter
    def icon(self, icon):
        """Sets the icon of this HomeScreenNavigationButton.


        :param icon: The icon of this HomeScreenNavigationButton.  # noqa: E501
        :type: str
        """
        if self.local_vars_configuration.client_side_validation and icon is None:  # noqa: E501
            raise ValueError("Invalid value for `icon`, must not be `None`")  # noqa: E501

        self._icon = icon

    @property
    def label(self):
        """Gets the label of this HomeScreenNavigationButton.  # noqa: E501


        :return: The label of this HomeScreenNavigationButton.  # noqa: E501
        :rtype: str
        """
        return self._label

    @label.setter
    def label(self, label):
        """Sets the label of this HomeScreenNavigationButton.


        :param label: The label of this HomeScreenNavigationButton.  # noqa: E501
        :type: str
        """
        if self.local_vars_configuration.client_side_validation and label is None:  # noqa: E501
            raise ValueError("Invalid value for `label`, must not be `None`")  # noqa: E501

        self._label = label

    @property
    def action(self):
        """Gets the action of this HomeScreenNavigationButton.  # noqa: E501


        :return: The action of this HomeScreenNavigationButton.  # noqa: E501
        :rtype: str
        """
        return self._action

    @action.setter
    def action(self, action):
        """Sets the action of this HomeScreenNavigationButton.


        :param action: The action of this HomeScreenNavigationButton.  # noqa: E501
        :type: str
        """
        if self.local_vars_configuration.client_side_validation and action is None:  # noqa: E501
            raise ValueError("Invalid value for `action`, must not be `None`")  # noqa: E501

        self._action = action

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, HomeScreenNavigationButton):
            return False

        return self.to_dict() == other.to_dict()

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        if not isinstance(other, HomeScreenNavigationButton):
            return True

        return self.to_dict() != other.to_dict()
