"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from utils import pick_word

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    num_win = ndb.IntegerProperty(default = 0)
    num_loss = ndb.IntegerProperty(default = 0)
    win_ratio = ndb.FloatProperty()
    def rank_form(self):
        return RankForm(user_name = self.name,
                        email = self.email,
                        win_ratio = float(self.num_win)/(float(self.num_win)+float(self.num_loss)),
                        num_win = self.num_win,
                        num_loss = self.num_loss)

class Game(ndb.Model):
    """Game object"""
    target = ndb.StringProperty(required=True)
    attempts_allowed = ndb.IntegerProperty(required=True)
    attempts_remaining = ndb.IntegerProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    correct = ndb.IntegerProperty(repeated = True)
    history = ndb.PickleProperty(required=True, default=[])
    @classmethod
    def new_game(cls, user, min, max, attempts):
        """Creates and returns a new game"""
        game = Game(user=user,
                    target=pick_word(min,max),
                    attempts_allowed=attempts,
                    attempts_remaining=attempts,
                    game_over=False,
                    )
        game.history = []
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.message = message
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining,
                      target=self.target,
                      attempts_allowed=self.attempts_allowed)
        score.put()
    
    def add_game_history(self, result, guess):
            self.history.append({'message': result, 'guess': guess})
            self.put()

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    target = ndb.StringProperty()
    attempts_allowed = ndb.IntegerProperty(required = True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         won=self.won,
                         date=str(self.date), 
                         guesses=self.guesses,
                         target = self.target,
                         attempts_allowed = self.attempts_allowed)

class RankForm(messages.Message):
    user_name = messages.StringField(1,required = True)
    email = messages.StringField(2)
    win_ratio = messages.FloatField(3) 
    num_win = messages.IntegerField(4)
    num_loss = messages.IntegerField(5)

class RankForms(messages.Message):
    """Retrn multiple GameForms"""
    items = messages.MessageField(RankForm,1,repeated = True)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)

class GameForms(messages.Message):
    """Retrn multiple GameForms"""
    items = messages.MessageField(GameForm,1,repeated = True)

class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)

class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    min_word_length = messages.IntegerField(2, required = True)
    max_word_length = messages.IntegerField(3, required = True)
    attempts = messages.IntegerField(4, default=5)

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    target = messages.StringField(5)
    attempts_allowed =  messages.IntegerField(6)

class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
