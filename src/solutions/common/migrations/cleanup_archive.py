from google.appengine.ext import ndb

class FacebookProfilePointerArchive(ndb.Model):
    pass

class FacebookUserProfileArchive(ndb.Model):
    pass

class FriendServiceIdentityConnectionArchive(ndb.Model):
    pass

class UserProfileArchive(ndb.Model):
    pass

class AvatarArchive(ndb.Model):
    pass

class FriendMapArchive(ndb.Model):
    pass

class UserDataArchive(ndb.Model):
    pass

class SolutionLoyaltyVisitLotteryArchive(ndb.Model):
    pass

class SolutionLoyaltyVisitStampsArchive(ndb.Model):
    pass

class SolutionLoyaltyVisitRevenueDiscountArchive(ndb.Model):
    pass

class AuthorizedUser(ndb.Model):
    pass

# from rogerthat.migrations.delete_all_models_by_kind import job
# job(...)