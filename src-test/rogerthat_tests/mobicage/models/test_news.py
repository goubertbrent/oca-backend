from datetime import date

from dateutil.relativedelta import relativedelta
from google.appengine.ext import db

import mc_unittest
from rogerthat.bizz.news.matching import _match_target_audience_of_item
from rogerthat.models import UserProfile
from rogerthat.models.news import NewsItem
from rogerthat.rpc import users
from rogerthat.utils import get_epoch_from_datetime, now


class TestNewsItem(mc_unittest.TestCase):

    def test_news_item_target_audience(self):
        today = date.today()
        date_old = today + relativedelta(years=-40)
        date_ancient = today + relativedelta(years=-500)
        date_young = today + relativedelta(years=-10)

        empty_profile = UserProfile(birthdate=None, gender=None,
                                    key=UserProfile.createKey(users.User('user0@example.com')))
        profile_old_male = UserProfile(birthdate=get_epoch_from_datetime(date_old),
                                       gender=UserProfile.GENDER_MALE,
                                       key=UserProfile.createKey(users.User('user1@example.com')))
        profile_old_female = UserProfile(birthdate=get_epoch_from_datetime(date_old),
                                         gender=UserProfile.GENDER_FEMALE,
                                         key=UserProfile.createKey(users.User('user2@example.com')))
        profile_ancient_female = UserProfile(birthdate=get_epoch_from_datetime(date_ancient),
                                             gender=UserProfile.GENDER_FEMALE,
                                             key=UserProfile.createKey(users.User('user3@example.com')))
        young_female = UserProfile(birthdate=get_epoch_from_datetime(date_young),
                                   gender=UserProfile.GENDER_FEMALE,
                                   key=UserProfile.createKey(users.User('user4@example.com')))
        db.put([profile_old_male, profile_old_female, profile_ancient_female, young_female])

        news_item0 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              target_audience_enabled=False)

        self.assertTrue(_match_target_audience_of_item(profile_old_male.user, news_item0))
        self.assertTrue(_match_target_audience_of_item(young_female.user, news_item0))
        self.assertTrue(_match_target_audience_of_item(empty_profile.user, news_item0))

        news_item1 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              target_audience_enabled=True,
                              target_audience_min_age=0,
                              target_audience_max_age=100,
                              target_audience_gender=UserProfile.GENDER_FEMALE)

        self.assertFalse(_match_target_audience_of_item(empty_profile.user, news_item1))
        self.assertFalse(_match_target_audience_of_item(profile_old_male.user, news_item1))
        self.assertTrue(_match_target_audience_of_item(profile_old_female.user, news_item1))
        self.assertFalse(_match_target_audience_of_item(profile_ancient_female.user, news_item1))
        self.assertTrue(_match_target_audience_of_item(young_female.user, news_item1))

        news_item2 = NewsItem(sticky=False,
                              sender=users.User('hello@mail.com'),
                              app_ids=['rogerthat'],
                              timestamp=now(),
                              target_audience_enabled=True,
                              target_audience_min_age=18,
                              target_audience_max_age=99,
                              target_audience_gender=UserProfile.GENDER_MALE_OR_FEMALE)

        self.assertFalse(_match_target_audience_of_item(empty_profile.user, news_item2))
        self.assertTrue(_match_target_audience_of_item(profile_old_male.user, news_item2))
        self.assertTrue(_match_target_audience_of_item(profile_old_female.user, news_item2))
        self.assertFalse(_match_target_audience_of_item(profile_ancient_female.user, news_item2))
        self.assertFalse(_match_target_audience_of_item(young_female.user, news_item2))
