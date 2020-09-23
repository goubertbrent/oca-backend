# coding: utf-8

from __future__ import absolute_import
import unittest

from flask import json
from six import BytesIO

from oca.models.home_screen import HomeScreen  # noqa: E501
from oca.test import BaseTestCase


class TestDefaultController(BaseTestCase):
    """DefaultController integration test stubs"""

    def test_update_home_screen(self):
        """Test case for update_home_screen

        Saves the homescreen for a community
        """
        home_screen = {
  "bottom_navigation" : {
    "buttons" : [ {
      "badge_key" : "messages",
      "icon" : "fa-envelope",
      "action" : "action",
      "label" : "Messages"
    }, {
      "badge_key" : null,
      "icon" : "fa-external-link",
      "action" : "https://google.com",
      "label" : "Google"
    } ]
  },
  "bottom_sheet" : {
    "header" : {
      "image" : "image",
      "subtitle" : "subtitle",
      "title" : "title"
    },
    "rows" : [ {
      "key" : "{}"
    }, {
      "key" : "{}"
    } ]
  },
  "translations" : {
    "key" : {
      "key" : "translations"
    }
  },
  "content" : {
    "embedded_app" : "embedded_app",
    "type" : "native"
  }
}
        headers = { 
            'Content-Type': 'application/json',
            'AppengineAuth': 'special-key',
        }
        response = self.client.open(
            '/api/homescreen/{community_id}'.format(community_id=56),
            method='POST',
            headers=headers,
            data=json.dumps(home_screen),
            content_type='application/json')
        self.assert200(response,
                       'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
