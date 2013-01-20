
import datetime
import dateutil
import logging
from tornado import web, escape

import base
import models
import util

class ThisWeekHandler(base.BaseHandler):
    @web.asynchronous
    def get(self, uid):
        user = self.get_current_user()
        data_user = models.User.objects(id=uid).first()
        if not data_user.public and (not user or user.email != data_user.email):
            self.write_error(403)
            return
        date = models._current_monday()
        this_week_runs = models.Run.this_week_runs(data_user)

        expected_dates = set()
        for x in range(7):
            expected_dates.add(date)
            date += dateutil.relativedelta.relativedelta(days=1)

        runs = []
        dates = set()
        for r in this_week_runs:
            if r.date not in dates:
                runs.append({'x': r.date.strftime("%c"), 'y': r.distance})
            else:
                # find and add data
                for r2 in runs:
                    if r2['x'] == r.date.strftime("%c"):
                        r2['y'] += float(r.distance)
            dates.add(r.date)

        # for days without runs yet, add 0 mileage
        for d in expected_dates - dates:
            runs.append({'x': d.strftime("%c"), 'y': 0.0})

        data = {
                'xScale': 'ordinal',
                'yScale': 'linear',
                'main': [
                    {
                        'data': runs
                    }
                ]
        }

        self.finish(data)


class WeeklyMileageHandler(base.BaseHandler):
    @web.asynchronous
    def get(self, uid):
        user = self.get_current_user()
        since = self.get_argument('since', '')
        window_weeks = self.get_argument('window_weeks', '')

        data_user = models.User.objects(id=uid).first()
        if not data_user.public and (not user or user.email != data_user.email):
            self.write_error(403)
            return

        if window_weeks:
            window_weeks = dateutil.relativedelta.relativedelta(weeks=int(window_weeks))

        try:
            since = int(since)
        except ValueError:
            since = None

        if since:
            since = datetime.date(since, 1, 1)
            weeks = models.Week.objects(user=data_user, date__gte=since)
        else:
            if window_weeks:
                weeks = models.Week.objects(user=data_user, date__gte=datetime.date.today() - window_weeks)
            else:
                weeks = models.Week.objects(user=data_user)

        weeks = [week for week in weeks]

        weeks = sorted(weeks, key=lambda w: w.date)
        last_date = weeks[0].date
        offset = dateutil.relativedelta.relativedelta(days=7)
        for x in range(1, len(weeks)):
            if last_date + offset != weeks[x].date:
                while last_date + offset != weeks[x].date:
                    w = models.Week(distance=0, time=0, date=last_date+offset)
                    weeks.append(w)
                    last_date += offset
            last_date += offset

        # handle the beginning of the year
        year = datetime.date.today().year
        if since and weeks[0].date != datetime.date(year, 1, 1):
            # manually build a partial week
            runs = models.Run.objects(user=data_user, date__lt=weeks[0].date, date__gte=datetime.date(year, 1, 1))
            week = models.Week(user=data_user)
            week.date = datetime.date(year, 1, 1)
            for run in runs:
                week.distance += run.distance
                week.time += run.time
            weeks.insert(0, week)

        weeks = sorted(weeks, key=lambda w: w.date)

        weeks = [ {'x': w.date.strftime('%m-%d-%Y'), 'y': w.distance} for w in weeks]

        # if the user only has 1 week display the last week too
        if len(weeks) == 1:
            last_monday = dateutil.parser.parse(weeks[0]['x']) - dateutil.relativedelta.relativedelta(days=7)
            weeks.append({'x': last_monday.strftime('%m-%d-%Y'), 'y': 0})

        data = {
                'xScale': 'time',
                'yScale': 'linear',
                'main': [
                    {
                        'data': weeks
                    }
                ]
        }

        # 0 fill some data if there is none so that the graph shows
        if since and not weeks:
            weeks.append({'x': since.strftime('%x'), 'y':0})
            weeks.append({'x': (since + dateutil.relativedelta.relativedelta(days=7)).strftime('%m-%d-%Y'), 'y':0})
            data['yMin'] = 0
            data['yMax'] = 100

        self.finish(data)

