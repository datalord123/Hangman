#Game-API-Design: HangmanApi

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
3.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application. 
 
##Game Description:
 HangmanApi is a single-player word guessing game. Player picks the parameters for a english word generated randomly and then subsequently guesses the letters for that word. Along with his word parameters, player also inputs the maximum number of guesses that he will allow himself for that game.

Guesses are sent via the "make_move" endpoint, which will reply with a message saying whether the letter was correct, or incorrect, along with a visual representation of the "target" word at that point. "make_move"  will also communicate to player, the number of guesses he has remaining, and whether that game has already ended or not(if the maximum number of attempts has been reached, or if the player had previously guessed all the letters correctly). If the player guesses all the letteres in the word, then "make_move" will increase the value by 1 of the "num_win" property for the user, if the player runs out of guesses allowed, then
"make_move" will increase the value by 1 of the "num_loss" property for the user. Scores are inputed via the "end_game" method in the "Game" kind, and are calculated by subtracting the "attempts_remaining" from "attempts_allowed".

#Score-Keeping

Scores for a game are more or less represented by the number of incorrect guesses that the player needed in order to correctly guess all of the letters in the target word. Like golf, the players try seek the lowest score during their game.

 To get a ranking of the best scoring games, the "get_high_scores" method, ranks game scores in descending order by "attempts_allowed", and then in descending order by "guesses", which is an integer that represents the number of guesses attempted. Essentially the user with the lowest number of guesses allowed, and then the lowest number of guesses, has scored the best. 

Many different HangmanApi games can be played by many different users at any given time, and user have the ability to create & play different games at the same time.  Each game can be retrieved or played by using the path parameter `urlsafe_game_key`.


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 -wordsEn.txt: a text file that contains every word in the english language, from which a random word is chosen at the start of every game.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: `user_name`, `email` (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. `user_name` provided must be unique. Will raise a ConflictException if a User with this `user_name` already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: `user_name`, `attempts`,max_word_length,min_word_length
    - Returns: GameForm with game state.
    - Description: Creates a new Game. `user_name` provided must correspond to an existing user - will raise a NotFoundException if not. Also adds a task to a task queue to update the average moves remaining for active games. 'Attemps' are the maximum number of attempts the user allows himself in order to guess all the letters correctly in the target word. max_word_length and min_word_length are simply the maximum and minimum lenghths that the Player wants his random word to be.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: `urlsafe_game_key`
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: GameForms 
    - Description: Returns all the active games played by the user with this `user_name`
        
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: `urlsafe_game_key`, `guess`
    - Returns: GameForm with new game state.
    - Description: Accepts a `guess`,via a case-insensensitive single letter, and returns the updated state of the game. If this causes a game to end, a corresponding Score entity will be created.
 
  - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).

 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: ScoreForms
    - Description: Returns all Scores recorded by the provided player (unordered).Will raise a NotFoundException if the User does not exist.

 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: `user_name`
    - Returns: GameForms
    - Description: Returns all Active Games recorded by the provided player (unordered).Will raise a NotFoundException if the User does not exist.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: DELETE
    - Parameters: `urlsafe_game_key`
    - Returns: StringMessage with canceled `urlsafe_game_key`.
    - Description: Returns a message confirming the cancellation of the game. Canceling a completed game will raise "This game has ended" error

 - **get_high_scores**
    - Path: 'scores/high_scores'
    - Method: GET
    - Parameters: `number_of_results`
    - Returns: ScoreForms
    - Description: Returns number of Scores in the database limited by `number_of_results` and ordered by `attempts_allowed`, and `guesses` in ascending order. Will returns all Scores in the database if there's no value from `number_of_results`.
 
 - **get_user_rankings**
    - Path: 'scores/user_rankings'
    - Method: GET
    - Parameters: None
    - Returns: RankForms
    - Description: Returns all winning Scores in the database ordered by `win_ratio` in descending order.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: `urlsafe_game_key`
    - Returns: StringMessage
    - Description: Returns a list of dictionary-pairs of messages and guesses recorded in `make_move`.
    
 - **get_average_attempts**
    - Path: 'games/average_attempts'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Get the cached average moves remaining.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game properties and states including the target word, move history, and associated methods. Linked with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **RankForm**
    - Representation of a user ranking along with game history (user_name, email, num_win, num_loss, win_ratio).
 - **RankForms**
    - Multiple RankForm container.
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **GameForms**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,guesses,target,attemps_allowed).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.