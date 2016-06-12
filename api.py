import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms,GameForms,RankForm,RankForms
from utils import get_by_urlsafe,set_score_at


NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

GET_HIGH_SCORE_REQUEST = endpoints.ResourceContainer(
        number_of_results=messages.IntegerField(1),)

GET_USER_RANK = endpoints.ResourceContainer(User)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='hangman',version='v1')
class PlayHangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')

    def create_user(self, request):
        """Create a User. Requires a unique username"""
    	if User.query(User.name == request.user_name).get():
        	raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))
    
    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self,request):
      """Creates new game"""
      user = User.query(User.name == request.user_name).get()
      if not user:
        msg = 'A User with that name does not exist!'
      else:
        if request.max_word_length<request.min_word_length:
          msg = 'max word length must be greater than min word length!'
        elif request.max_word_length>=request.min_word_length:
          game = Game.new_game(user.key, request.min_word_length,
            request.max_word_length, request.attempts)
          msg = 'Good luck playing Hangman!'
        else:
          msg = 'Unable to recognize inputs, please make sure your parameters are correct.'
        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form(msg)

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
          if game.game_over:
            return game.to_form('This game has ended')
          else:
            return game.to_form('Game ongoing. Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')
    
    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self,request):
      """Makes a move. Returns a game state with a message"""
      game = get_by_urlsafe(request.urlsafe_game_key, Game)
      user = game.user.get()
      if game.game_over:
    		return game.to_form('Game has ended!')
      secretWord = list(game.target)
      score = []
      [score.append('_') for i in range(len(secretWord))]
      guess = request.guess.upper()
      if len(guess) != 1:
        msg = 'Please enter a SINGLE letter.'
      elif guess.isalpha() == False:
        msg = 'Please enter a LETTER.'
      else:
        if guess not in secretWord:
          game.attempts_remaining -=1
          if game.attempts_remaining > 0:
            [set_score_at(score,secretWord,i) for i in game.correct]
            msg = "Incorrect, you have {} attempts remaining. {}".format(game.attempts_remaining,score)
            game.add_game_history(msg,guess)
            game.put()
          else:
            msg = "Out of Tries. The answer was {}. Game Over".format(secretWord)
            user.num_loss +=1
            user.put()
            game.add_game_history(msg,guess)       
            game.end_game()
        elif guess in secretWord:
          [game.correct.append(i) for i in range(len(secretWord)) if secretWord[i] == guess and i not in game.correct]
          game.put()
          [set_score_at(score,secretWord,i) for i in game.correct]
          msg = "Correct,{}".format(score)
          if len(game.correct) == len(secretWord):
            user.num_win +=1
            user.put()
            game.end_game(True)
            msg = "You've won. The word was \n {}".format(game.target)
            game.add_game_history(msg,guess)
      return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self,request):
      """
      return all scores
      """
      return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self,request):
      """Returns all of an individual User's scores"""
      user = User.query(User.name == request.user_name).get()
      if not user:
        raise endpoints.NotFoundException(
          'A User with that name does not exist!')
      scores = Score.query(Score.user == user.key)
      return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message = USER_REQUEST,
                      response_message = GameForms,
                      path = "games/user/{user_name}",
                      name = "get_user_games",
                      http_method = 'GET')  
    def get_user_games(self,request):
      """Returns all of an individual User's active games"""
      user = User.query(User.name == request.user_name).get()
      if not user:
        raise endpoints.NotFoundException(
          'A User with that name does not exist!')
      games = Game.query(Game.user == user.key).filter(Game.game_over == False)
      return GameForms(items=[game.to_form('Time to make a move!') for game in games])
    
    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self,request):
      """Cancel an active game by deleting it"""
      game = get_by_urlsafe(request.urlsafe_game_key,Game)
      if game:
        if game.game_over:
          return StringMessage(message = 'This game has ended')
        else:
          game.key.delete()
          return StringMessage(message = 'Game Canceled!')
      else:
        return StringMessage(message = "Game doesn't exist") 

    @endpoints.method(request_message = GET_HIGH_SCORE_REQUEST,
                      response_message = ScoreForms,
                      path = 'scores/high_scores',
                      name ='get_high_scores',
                      http_method='GET')
    def get_high_scores(self,request):
      """Return all scores ordered by total points"""
      if request.number_of_results:
        scores = Score.query(Score.won == True).order(Score.attempts_allowed,Score.guesses).fetch(request.number_of_results)
      else:
        scores = Score.query(Score.won == True).order(Score.attempts_allowed,Score.guesses).fetch()
      return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=RankForms,
                      path='scores/user_rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return all users ordered by win ratio"""
        users = User.query().order(-User.win_ratio)
        return RankForms(items=[user.rank_form() for user in users])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Returns a summary of a game's guesses."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found')
        return StringMessage(message=str(game.history))

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
      """
      Get the cached average moves remaining
      """
      return StringMessage(message = memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
      """Populates memcache with the average moves remaining of Games"""
      games = Game.query(Game.game_over == False).fetch()
      if games:
        count = len(games)
        total_attempts_remaining = sum([game.attempts_remaining
                                          for game in games])
        average = float(total_attempts_remaining)/count
        memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))

api = endpoints.api_server([PlayHangmanApi])