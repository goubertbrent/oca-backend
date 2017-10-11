# create default calendars
import logging
from google.appengine.ext import db

from rogerthat.bizz.job import run_job
from rogerthat.dal import parent_key, put_and_invalidate_cache

from solutions.common.bizz import SolutionModule
from solutions.common.models import SolutionSettings
from solutions.common.models.agenda import SolutionCalendar


# provisioning.put_agenda
def _create_default_calendar(sln_settings_key):
    sln_settings = db.get(sln_settings_key)

    if not sln_settings:
        return

    if SolutionModule.AGENDA not in sln_settings.modules:
        return

    if not sln_settings.default_calendar:
        def trans():
            sc = SolutionCalendar(parent=parent_key(sln_settings.service_user, sln_settings.solution),
                                    name="Default",
                                    deleted=False)
            sc.put()
            sln_settings.default_calendar = sc.calendar_id
            put_and_invalidate_cache(sln_settings)
            return sc

        logging.debug('Creating default calendar for: %s', sln_settings.service_user)
        xg_on = db.create_transaction_options(xg=True)
        db.run_in_transaction_options(xg_on, trans)


def _all_solution_settings():
    return SolutionSettings.all(keys_only=True)


def job():
    run_job(_all_solution_settings, [], _create_default_calendar, [])
