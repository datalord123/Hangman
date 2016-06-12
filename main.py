#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import webapp2
from google.appengine.api import mail, app_identity
from api import PlayHangmanApi
from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to the users who haven't completed the games they started.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        for user in users:
            active_games = Game.query(Game.user == user.key).filter(Game.game_over != True)
            for game in active_games:
                subject = 'REMINDER'
                body ='You had one Job {}'.format(user.name)
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                    user.email,
                    subject,
                    body)

class UpdateAverageMovesRemaining(webapp2.RequestHandler):
    def post(self):
        """Update game listing announcement in memcache."""
        PlayHangmanApi._cache_average_attempts()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_attempts', UpdateAverageMovesRemaining),
], debug=True)