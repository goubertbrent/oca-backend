# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from oca.models.base_model_ import Model
from oca.models.homescreen_bottom_sheet_header import HomescreenBottomSheetHeader
from oca import util

from oca.models.homescreen_bottom_sheet_header import HomescreenBottomSheetHeader  # noqa: E501

class HomescreenBottomSheet(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, header=None, rows=None):  # noqa: E501
        """HomescreenBottomSheet - a model defined in OpenAPI

        :param header: The header of this HomescreenBottomSheet.  # noqa: E501
        :type header: HomescreenBottomSheetHeader
        :param rows: The rows of this HomescreenBottomSheet.  # noqa: E501
        :type rows: List[Dict[str, object]]
        """
        self.openapi_types = {
            'header': HomescreenBottomSheetHeader,
            'rows': List[Dict[str, object]]
        }

        self.attribute_map = {
            'header': 'header',
            'rows': 'rows'
        }

        self._header = header
        self._rows = rows

    @classmethod
    def from_dict(cls, dikt) -> 'HomescreenBottomSheet':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HomescreenBottomSheet of this HomescreenBottomSheet.  # noqa: E501
        :rtype: HomescreenBottomSheet
        """
        return util.deserialize_model(dikt, cls)

    @property
    def header(self):
        """Gets the header of this HomescreenBottomSheet.


        :return: The header of this HomescreenBottomSheet.
        :rtype: HomescreenBottomSheetHeader
        """
        return self._header

    @header.setter
    def header(self, header):
        """Sets the header of this HomescreenBottomSheet.


        :param header: The header of this HomescreenBottomSheet.
        :type header: HomescreenBottomSheetHeader
        """
        if header is None:
            raise ValueError("Invalid value for `header`, must not be `None`")  # noqa: E501

        self._header = header

    @property
    def rows(self):
        """Gets the rows of this HomescreenBottomSheet.


        :return: The rows of this HomescreenBottomSheet.
        :rtype: List[Dict[str, object]]
        """
        return self._rows

    @rows.setter
    def rows(self, rows):
        """Sets the rows of this HomescreenBottomSheet.


        :param rows: The rows of this HomescreenBottomSheet.
        :type rows: List[Dict[str, object]]
        """
        if rows is None:
            raise ValueError("Invalid value for `rows`, must not be `None`")  # noqa: E501

        self._rows = rows
