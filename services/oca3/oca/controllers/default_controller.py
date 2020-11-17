import connexion

from oca.db.communities import get_homescreen_ref
from oca.models.home_screen import HomeScreen  # noqa: E501


def update_home_screen(community_id, home_screen_id, home_screen=None):  # noqa: E501
    """Saves the home screen for a community

     # noqa: E501

    :param community_id: The id of the community to which this home screen belongs
    :type community_id: int
    :param home_screen_id: The id of the home screen
    :type home_screen_id: str
    :param home_screen:
    :type home_screen: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        home_screen = HomeScreen.from_dict(connexion.request.get_json())  # noqa: E501
    get_homescreen_ref(community_id, home_screen_id).set(home_screen.to_dict())
