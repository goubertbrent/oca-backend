# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from oca.models.base_model_ import Model
from oca import util


class HomescreenContent(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, type=None, embedded_app=None):  # noqa: E501
        """HomescreenContent - a model defined in OpenAPI

        :param type: The type of this HomescreenContent.  # noqa: E501
        :type type: str
        :param embedded_app: The embedded_app of this HomescreenContent.  # noqa: E501
        :type embedded_app: str
        """
        self.openapi_types = {
            'type': str,
            'embedded_app': str
        }

        self.attribute_map = {
            'type': 'type',
            'embedded_app': 'embedded_app'
        }

        self._type = type
        self._embedded_app = embedded_app

    @classmethod
    def from_dict(cls, dikt) -> 'HomescreenContent':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HomescreenContent of this HomescreenContent.  # noqa: E501
        :rtype: HomescreenContent
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        """Gets the type of this HomescreenContent.


        :return: The type of this HomescreenContent.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this HomescreenContent.


        :param type: The type of this HomescreenContent.
        :type type: str
        """
        allowed_values = ["native", "embedded_app"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}"
                .format(type, allowed_values)
            )

        self._type = type

    @property
    def embedded_app(self):
        """Gets the embedded_app of this HomescreenContent.

        Only set when 'type' is embedded_app  # noqa: E501

        :return: The embedded_app of this HomescreenContent.
        :rtype: str
        """
        return self._embedded_app

    @embedded_app.setter
    def embedded_app(self, embedded_app):
        """Sets the embedded_app of this HomescreenContent.

        Only set when 'type' is embedded_app  # noqa: E501

        :param embedded_app: The embedded_app of this HomescreenContent.
        :type embedded_app: str
        """

        self._embedded_app = embedded_app
