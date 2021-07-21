# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 20:51:29 2019

@author: Trang
"""
class Player:
    
    #constants related to setup
    BOARD_LENGTH = 10
    NUM_OF_SHIPS = 5
    CELL_RADIO_ACTIVE = -1
    CELL_DEFAULT_VALUE = 0
    
    # constants related to strategies
    # Maximum number of times that all ships can be moved for the duration of the game
    MAX_NO_OF_SHIP_MOVE = 2 
    # Threshold number of ships remaining at which moving a ship is allowed
    DANGEROUS_NO_OF_SHIPS = 2
    # if a ship is surrounded by these number of mines, it is in dangerous state
    CELL_MAX_NO_OF_NEARBY_MINES = 2
    # list of ships that can be moved
    PRIORITIZED_SHIPS = [1]
    # The number of consecutive unsuccessful rounds after which strategy should be changed
    MAX_NUM_OF_INEFFICIENT_SHOT = 4
        
    def __init__(self):
      
        # simulation of my board and opponent board
        self.myBoard = None
        self.opponentBoard = None
        # shipList is a dictionary which contains the coordinates of ships
        self.shipDict = None
        self.name = "Group 6"
        # there are 3 states of a player: SEARCH, ATTACK and DEFENSE
        self.state = "SEARCH"
        # self.ship_frequency_statistics: the map indicates the likelihood that each cell is part of an opponent’s ship
		# this map,in the form of a dictionary, key is the rank, value is the list of coordinates in the rank
		# this map is used for finding opponent's ships at the start and when we don't have any successful hits
        self.ship_frequency_statistics = {}
        self.ship_frequency_helper_board = None
        # self.opponent_heat_map: a map that is updated based on successful hits on the opponent’s ships 
		# this map is used for shooting when we know there are some successful hits
        self.opponent_heat_map = None
        # self.ship_move_count: the number of ship moves so far
        self.ship_move_count = 0
        
        # temp variables, to be reset contiuously in each state : ATTACK or SEARCH 
        self.attack_time_current_round = 0
        self.picked_cell_for_next_attack = []
         
    def setup_ships(self):
        # to place ships and initialize all data structures
        # input: None
        # output: None
        from random import randint
                     
        # a random number to choose ship placement strategy
        lucky_number = randint(1,5)
        grid = self.setup_ships_with_lucky_number(lucky_number)   
                  
        self.set_my_board(grid)
        self.set_opponent_board()
        self.set_shipDict()
        self.set_up_ship_frequency_reference()
        self.set_opponent_heat_map()
             
        return grid
    
    def setup_ships_with_lucky_number(self,lucky_number):
        # to set up a ships given a random number
        # input: a random integer
        # output: the configuration of our board
        
        grid = [ [0 for i in range(10)] for j in range(10)]
        
        """
        Below are 5 positions that we think are hard to guess
        Placing strategies:
            1. Ships are not next to each other
            2. 2 ships are in the L shapes
            3. Ships are not at the center
            4. Do not place ships symmetrical
            5. Be unpredictable, use random function
        """
        if lucky_number == 1:
                grid[3][9] = 1
                for row in range(6,8): grid[row][0] = 2
                for col in range(3,6): grid[7][col] = 3
                for row in range(5,9): grid[row][8] = 4
                for col in range(2,7): grid[1][col] = 5
            
        elif lucky_number == 2:
                grid[7][0] = 1
                for row in range(4,6): grid[row][7] = 2  
                for row in range(3,6): grid[row][2] = 3
                for col in range(5,9): grid[1][col] = 4
                for col in range(4,9): grid[8][col] = 5
            
        elif lucky_number == 3:
                grid[0][1] = 1
                for col in range(7,9): grid[8][col] = 2  
                for row in range(6,9): grid[row][1] = 3
                for row in range(5,9): grid[row][4] = 4
                for col in range(3,8): grid[2][col] = 5
                    
        elif lucky_number == 4:
                grid[3][9] = 1
                for row in range(3,5): grid[row][1] = 2  
                for col in range(2,5): grid[8][col] = 3
                for row in range(4,8): grid[row][7] = 4
                for col in range(3,8): grid[1][col] = 5
            
        elif lucky_number == 5:
                grid[8][9] = 1
                for row in range(7,9): grid[row][1] = 2  
                for row in range(1,4): grid[row][8] = 3
                for col in range(2,6): grid[4][col] = 4
                for col in range(1,6): grid[1][col] = 5
                
        return grid
    
    def take_turn(self, history):
        
        myShots = []
        
        #update my boards using the no of hits and opponent's incoming shots
        if history: 
            latestEntry = history[len(history)-1]
            self.update_my_board_with_opponent_shots(latestEntry)
            self.update_heat_map_with_my_hits(latestEntry)
            
        """    
        -----------  DEFENSE mode  ------------------------------------------
        Start every move by checking if there is any ship in danger
        If there is an allowed move for our ships, return the instruction
        Otherwise, change to either ATTACK or SEARCH mode
        """
        endangered_list = self.get_ships_in_danger()
        if endangered_list:
            # only move ships whe we havent exceeded the max number of moves and 
			# the remaining number of ships is <= 2
            if self.ship_move_count < Player.MAX_NO_OF_SHIP_MOVE and \
            len(self.shipDict) <= Player.DANGEROUS_NO_OF_SHIPS:
            
                ship_move_instruction = self.find_ship_move_solution(endangered_list)
                
                if ship_move_instruction:
                    #print("I am in Defense Mode")
                    # if we want to move ship, update the current ship positions
                    self.update_ship_positions(ship_move_instruction)
                    return ship_move_instruction
        
    
        #Based on the previous number of hits, decdie if we should Search or Attack
        self.state = self.decide_search_or_attack(history)
        
        """    
        -------------  SEARCH mode   ------------------------------------------
        This strategy is used at the beginning of the game
        or when we had 4 unsuccessful attacks
        In this strategy, no of hits is NOT used to determine shot locations
        """
        if self.state == "SEARCH":
            #print("I am in Search Mode")
            # reset the count of attack rounds to 0 when we are in SEARCH mode
            self.attack_time_current_round= 0
            
            MaxNoOfShots = len(self.shipDict)
            ## find the next shots using SEARCH strategy
            myShots = self.identify_search_shots(MaxNoOfShots)
            
           
        """    
        -------------  ATTACK mode   ------------------------------------------
        This strategy is used when we know there is some hit and continue to 
        attack the nearby cells to get more hits.
        In this strategy, no of hits is used to make predictions.
        """
        if self.state == "ATTACK":
            print("I am in Attack Mode")
            # increase the count of attack rounds when we are in ATTACK mode
            self.attack_time_current_round += 1
            MaxNoOfShots = len(self.shipDict)
            
            # find the next shots using ATTACK strategy
            myShots = self.identify_attack_shots(MaxNoOfShots)
            
        #Before sending my shots, update the opponent’s board and potential shot list for future shots
       
        if myShots: 
            if 'list' in str(type(myShots)):
                # update my records of shooting
                self.update_opponent_board_with_my_shots(myShots)
                self.update_my_potential_shot_list(myShots)
            
        return myShots
    
    
    def get_name(self): 
        # return the player's name
        # input: None
        # output: name of player in string type
        return self.name
    
    
    """ ----------------------------------------------------------------------
        The following codes are for making Strategy Decision 
    """
    
    def decide_search_or_attack(self,history):
        # the default mode is Search
        # if there is some hit, move to ATTACK state
        # After 4 consecutive rounds without hits, move back to SEARCH mode
        # input: the entire history
        # output: either ATTACK or SEARCH
        currentState = self.state
        
        # if there are any successful hits in the previous round, then stay in ATTTACK mode
        if history:
            latestEntry = history[len(history)-1]
            latestHits = latestEntry['hits']
            if latestHits > 0:
                return "ATTACK"
        
        # If there are any successful hits in the last 4 rounds, stay in ATTACK mode
        # If not, switch back to search mode
        if history:
            if len(history)>= Player.MAX_NUM_OF_INEFFICIENT_SHOT:
                for i in range (-Player.MAX_NUM_OF_INEFFICIENT_SHOT,0):
                    entry = history[i]
                    noOfHits = entry.get('hits')
                    if noOfHits > 0:
                        return "ATTACK"
                
                if self.attack_time_current_round >= Player.MAX_NUM_OF_INEFFICIENT_SHOT :
                    return "SEARCH"
        
        # if there is no change, keep the current state
        return currentState
       
    
    """ ----------------------------------------------------------------------
        The following code is for Attack Mode 
    """          
    
    def identify_attack_shots(self,MaxNoOfShots):
        # find the list of shots using ATTACK strategy
        # input: max no of shots we can have
        # output: a list of shots, in the form of a list of tuples
        shotList = []
        # list of shots that are chosen for current round
        self.picked_cell_for_next_attack = []
        
        for i in range (0, MaxNoOfShots):
            nextShot = self.identify_next_attack_shot()
            if nextShot:
                shotList.append(nextShot)
                # mark the cell that it is chosen for current round
                self.picked_cell_for_next_attack.append(nextShot)
        return shotList
    
    
    def identify_next_attack_shot(self):
        # find a single shot using ATTACK strategy
        # input: None
        # output: a tuple, which indicate a single shot
        
        # Return cell with the highest value from the heat map
        next_shot = self.identify_next_attack_shot_by_stats()
        
        if not next_shot:
            # if we cannot find any cell with probability > 0
            # need to find a shot using search strategy
            next_shot = self.identify_next_search_shot()
            
        if not next_shot:
            # if no shot is found, return None
            next_shot = None
            
        return next_shot
        
    def identify_next_attack_shot_by_stats(self):
        # traverse through the array of heatmap, find the cell with max likelihood
        # avoid the shots we already made
        # avoid the shots that are picked for the current round
        # input : None
        # output: a tuple which represent a shot
        next_shot = None
        max_cell_likelihood = Player.CELL_DEFAULT_VALUE
        
        for x in range (0,Player.BOARD_LENGTH):
            for y in range (0,Player.BOARD_LENGTH):
                if self.opponent_heat_map[x][y] > max_cell_likelihood \
                and self.is_my_prev_shot(x,y)==False and ((x,y) in self.picked_cell_for_next_attack) == False:
                    
                    max_cell_likelihood = self.opponent_heat_map[x][y]
                    next_shot = (x,y)
                  
        return next_shot        

    
    """ ----------------------------------------------------------------------
        The following codes are for Search Mode 
    """ 
    
    def identify_search_shots(self,MaxNoOfShots):
        # find the list of shots using SEARCH strategy
        # input: max no of shots we can have
        # output: a list of shots, in the form of a list of tuples
        shotList = []
        for i in range (0, MaxNoOfShots):
            nextShot = self.identify_next_search_shot()
            if nextShot:
                shotList.append(nextShot)
        return shotList
                  
    def identify_next_search_shot(self):
        # find the next shot using SEARCH strategy
        # based on  the patterns on self.ship_frequency_statistics
        # input : None
        # output: a tuple which represents the next shot
        target = None

        if self.ship_frequency_statistics.keys():
            maxFrequency = max(self.ship_frequency_statistics.keys())
            possibleTargets = self.ship_frequency_statistics.get(maxFrequency)
            assert(len(possibleTargets)>0)
                        
            # Choose coordinates that we have not used in the previous rounds 
            # and have not yet chosen for this current round
            for target in possibleTargets:
                x = target[0]
                y = target[1]
                
                if self.is_my_prev_shot(x,y) == False and ((x,y) in self.picked_cell_for_next_attack) == False:
                                      
                    self.ship_frequency_statistics.get(maxFrequency).remove((x,y))
                    # If all coordinates for a given rank in the ship_frequency_statistics grid 
					# have been hit by the opponent, then remove the rank
                    if self.ship_frequency_statistics.get(maxFrequency) is not None:
                        if(len(self.ship_frequency_statistics.get(maxFrequency)) == 0):
                            self.ship_frequency_statistics.pop(maxFrequency)
                    
                    return (x,y)
        return target
    
    
        
    """ ----------------------------------------------------------------------
        The following codes are for Defense Mode 
    """
    
    def find_ship_move_solution(self,endangered_list):
        # Determines which ship to move away from danger and sends move instruction
        # input: list of ships in danger (list of integers)
        # output: a tuple in the form (shipNo, moveDirection)
        
        assert(len(endangered_list) > 0)
        ship_move_instruction = None
        
        # give priority to smaller ship
		# For current strategy we only want to move ship 1 
        ship_to_move = min(endangered_list)
        ship_move_instruction = self.move_ship(ship_to_move)
                    
        return ship_move_instruction
    
    def move_ship(self, shipNo):
        # as for now, we only want to move ship 1
        coordindates = self.shipDict.get(shipNo)
        # with the current strategy, we only concern about ship 1
        if shipNo == 1:
            x = coordindates[0][0]
            y = coordindates[0][1]
               
            # move up
            if self.is_safe_available_cell(x-1,y):
                return (1,0)
            # move down   
            if self.is_safe_available_cell(x+1,y):
                return (1,2)
            # move left   
            if self.is_safe_available_cell(x,y-1):
                return (1,3)
            # move right   
            if self.is_safe_available_cell(x,y+1):
                return (1,1)
        
        return None
     
    def get_ships_in_danger(self):
        # get the list of all ships in danger
        # input: None
        # output: : list of ships under attack (with at least 2 radioactive neighbouring cells)
        
        endangered_ships_list = []
        
        # only want to check the important ships
		# for the current strategy, we are only concerned about ship 1
        for shipNo in Player.PRIORITIZED_SHIPS:
            if self.is_ship_in_danger(shipNo):
                endangered_ships_list.append(shipNo)
        return endangered_ships_list
                
    def is_ship_in_danger(self,shipNo):
        # check if a ship is in dangerous conditions and need to be moved
        # we only consider ships that are movable
        # input: ship No
        # output : True/ False
        if self.is_ship_movable(shipNo) == True:
            # with the current strategy, we only concern about ship 1
            if shipNo == 1: 
                coordindates = self.shipDict.get(1)
                # this list has only 1 tuple
                x = coordindates[0][0]
                y = coordindates[0][1]
                
                return self.is_dangerous_cell(x,y)
                    
        return False
    
        
    def is_ship_movable(self, shipNo):
        # to check if a ship has not been shot and can be moved
        # input: ship number
        # output: True / False
        if self.shipDict:
            if shipNo in self.shipDict.keys():
                ship_active_cells = self.shipDict[shipNo]
                if len(ship_active_cells) == shipNo:
                    return True
        return False
          
    def is_safe_available_cell(self,x,y):
        # check if a cell is safe (not radioactive, not dangerous)to move the new ship to
        # input: x and y coordinates
        # output: True/ False
        if y in range (0,Player.BOARD_LENGTH) and x in range (0,Player.BOARD_LENGTH) \
        and self.is_cell_radioactive(x,y)==False and self.is_dangerous_cell(x,y)==False and self.is_ship_placed(x,y)== False:  
            return True
        else: 
            return False
    
    def is_dangerous_cell(self,x,y):
         # a cell is considered dangerous if at least 2 out of 4 cells nearby are radio active
         # input : x and y coordinates of a cell
         # output : True / False
        if x in range(0,Player.BOARD_LENGTH) and y in range(0,Player.BOARD_LENGTH):
            NoOfThreats = 0
            # check all 4 cells nearby
            if self.is_cell_radioactive(x+1, y) == True:
                NoOfThreats += 1
            if self.is_cell_radioactive(x-1, y) == True:
                NoOfThreats += 1
            if self.is_cell_radioactive(x, y+1) == True:
                NoOfThreats += 1
            if self.is_cell_radioactive(x, y-1) == True:
                NoOfThreats += 1
            
            if NoOfThreats >= Player.CELL_MAX_NO_OF_NEARBY_MINES:
                return True
        return False
    
    def is_cell_radioactive(self, x_co, y_co):
        # to check if a cell is radioactive
        # if not, then the ship can be moved to that cell
        # input: x and y coordinates of a cell
        # output: True / False
        if x_co in range (0,Player.BOARD_LENGTH) and y_co in range (0,Player.BOARD_LENGTH) \
        and self.myBoard[x_co][y_co] == Player.CELL_RADIO_ACTIVE:
            return True
        return False
    
    def is_ship_placed(self,x,y):
        # to check if a cell is occupied by a ship
        # input: x and y coordinates of a cell
        # output: True / False
        cell_value = self.myBoard[x][y]
        if cell_value > Player.CELL_DEFAULT_VALUE:
            return True
        return False    

    def update_ship_positions(self,ship_move_instruction):
        # to update my board after a ship is moved
        # input is a tuple (shipNo,moveDirection)
        # output: no output, just update the related board and ship dictionary

        shipNo = ship_move_instruction[0]
        moveDirection = ship_move_instruction[1]
        # for the current strategy, we only concern about ship 1
        if shipNo == 1:
            # remove previous ship location from my board and ship dictionary
            prev_position = self.shipDict[1][0]
            prev_x = prev_position[0]
            prev_y = prev_position[1]
            self.myBoard[prev_x][prev_y] = Player.CELL_DEFAULT_VALUE
            self.shipDict[1].clear()
            
            # add new ship location to my board and ship dictionary
            new_x = prev_x
            new_y = prev_y
            
            if moveDirection == 0:
                new_x = prev_x - 1
            
            if moveDirection == 1:
                new_y = prev_y + 1
                
            if moveDirection == 2:
                new_x = prev_x + 1
                
            if moveDirection == 3:
                new_y = prev_y - 1
            
            new_position = (new_x,new_y)
            self.shipDict[1].append(new_position)
            self.myBoard[new_x][new_y] = shipNo
            
            self.ship_move_count += 1
               
    """ ----------------------------------------------------------------------
        The following codes are for Get/ Set / Support methods 
    """
    def set_my_board(self,board):
        self.myBoard = board
    
    def set_opponent_board(self):
        # initially, there is no shot in opponent's board so all values are DEFAULT 
        self.opponentBoard = [ [0 for i in range(Player.BOARD_LENGTH)] for j in range(Player.BOARD_LENGTH)]
                        
    def set_shipDict(self):
        if self.myBoard:
            self.shipDict = {}
            # the key is the ship no, the value is the list of coordinates of the ship
            for i in range (1, Player.NUM_OF_SHIPS+1):
                self.shipDict[i] = []
        
            # update the shipList with the values from myboard
            for x in range (0,len(self.myBoard)):
                for y in range (0,len(self.myBoard[0])):
                    if self.myBoard[x][y] > 0:
                        shipNo = self.myBoard[x][y]
                        self.shipDict[shipNo].append((x,y))
            
            # double check the constraints on the number of ships
            for y in range (1,Player.NUM_OF_SHIPS+1):
                assert(len(self.shipDict[i]) == i)
                                        
                  
                
    def update_my_board_cell(self,x_co,y_co):
        # update my board and dictionary of ships with opponents's incoming shots
        # input: x and y coordinates of a shot from the opponent
        # output: None
		
		# if a shot hits an empty cell, mark the cell as radioactive on my board
        if self.myBoard[x_co][y_co] in (Player.CELL_DEFAULT_VALUE,Player.CELL_RADIO_ACTIVE):
            self.myBoard[x_co][y_co] = Player.CELL_RADIO_ACTIVE
       
        else: 
            # for x_coordinate and y_coordinate
            # check my board to find the ship that was hit
            # remove the coordinates of the hit cell from the ship dictionary
            # if all the cells of a ship have been hit, remove the ship from the ship dictionary
            shipNo = self.myBoard[x_co][y_co]
            
            if shipNo in self.shipDict.keys():
                if (x_co,y_co) in self.shipDict[shipNo]:
                    self.shipDict[shipNo].remove((x_co,y_co))
                
                    if len(self.shipDict[shipNo]) == 0:
                        self.shipDict.pop(shipNo)
                
                # finally, mark the hit cell as radioactive on my board
                self.myBoard[x_co][y_co] = Player.CELL_RADIO_ACTIVE
                
    def update_my_board_with_opponent_shots(self,latestEntry):
        # update my board with opponent's incoming shots
        # input: the latest entry in the history
        # output: NOne
        
        # latestIncoming is a list of tuple
        latestIncoming = latestEntry['incoming']
        
        if(len(latestIncoming)>0):
            for shotsTuple in latestIncoming:
                row = shotsTuple[0]
                col = shotsTuple[1]
                self.update_my_board_cell(row,col)
        
    
    def update_heat_map_with_my_hits(self,latestEntry):
        # after any successful hits on opponent’s ships, update the heatmap to rank neigbouring cells around shots sent 
        # in order of probability of having ships
        # input: latest entry in history
        # output: None
        NoOfHits = latestEntry["hits"]
        previousShots = latestEntry["shots"]
        
        # check if I have shot the opponent or move the ship in prev round
        # if shots were sent, previousShots is a list
        # otherwise, it is a tuple and there is no need to update heatmap
        if NoOfHits > 0 and ('list' in str(type(previousShots))):
            if len(previousShots)>0:
                hitPercentage = NoOfHits / len(previousShots)

                for shot in previousShots:
                    x = shot[0]
                    y = shot[1]
                    # mark the cell we already shot
                    self.opponent_heat_map[x][y] = Player.CELL_RADIO_ACTIVE 
                    
                    # increase the hit percentage for 4 nearby cells if the cell was not shot yet
                    if(x+1) in range(0,Player.BOARD_LENGTH):
                        if self.opponent_heat_map[x+1][y] != Player.CELL_RADIO_ACTIVE:
                            self.opponent_heat_map[x+1][y] += hitPercentage
                        
                    if(x-1) in range(0,Player.BOARD_LENGTH):
                        if self.opponent_heat_map[x-1][y] != Player.CELL_RADIO_ACTIVE:
                            self.opponent_heat_map[x-1][y] += hitPercentage
                        
                    if(y+1) in range(0,Player.BOARD_LENGTH):
                        if self.opponent_heat_map[x][y+1] != Player.CELL_RADIO_ACTIVE:
                            self.opponent_heat_map[x][y+1] += hitPercentage
                        
                    if(y-1) in range(0,Player.BOARD_LENGTH):
                        if self.opponent_heat_map[x][y-1] != Player.CELL_RADIO_ACTIVE:
                            self.opponent_heat_map[x][y-1] += hitPercentage
        
    
    
    def is_my_prev_shot(self,x_co,y_co):
        # to check if a cell is shot by me previously
        # input: x and y coordinates of a cell
        # output: True or False
        if x_co in range (0,Player.BOARD_LENGTH) and y_co in range (0,Player.BOARD_LENGTH)\
		and self.opponentBoard[x_co][y_co] == Player.CELL_RADIO_ACTIVE:
            return True
        return False

           
    def update_opponent_board_with_my_shots(self,myShotList):
        # mark the cells on opponent's board that were shot by me
        # input: my most recent list of shots
        # output: NOne
        assert(len(myShotList) > 0)
        assert(len(self.shipDict) > 0)
        for myShot in myShotList:
            if myShot:
                x = myShot[0]
                y = myShot[1]
                self.opponentBoard[x][y] = Player.CELL_RADIO_ACTIVE
                self.opponent_heat_map[x][y] = Player.CELL_RADIO_ACTIVE
    
    
    def update_my_potential_shot_list(self,myShotList):
        # If a cell has been shot, remove it from the potential shooting list (myShotList)
        # input: my most recent list of shots
        # output: None
        assert(len(myShotList) > 0)
        assert(len(self.shipDict) > 0)
      
        for myShot in myShotList:
            if myShot:
                x = myShot[0]
                y = myShot[1]
                
                rank = self.ship_frequency_helper_board[x][y]
                if(rank in self.ship_frequency_statistics.keys() and myShot in self.ship_frequency_statistics[rank]):
                    self.ship_frequency_statistics[rank].remove(myShot)
                    
                if self.ship_frequency_statistics.get(rank) is not None:
                    if(len(self.ship_frequency_statistics.get(rank)) == 0):
                        self.ship_frequency_statistics.pop(rank)
                
     
    def set_up_ship_frequency_reference(self):
        # set up the map indicates the likelihood that each cell is part of an opponent’s ship
		# this map, in the form of a dictionary, shows a fixed pattern of movement based on these likelihood
		# coordinates with higher rank will be shot first
		# this map is used for finding opponent's ships at the start and when we don't have any successful hits
        reference_grid=[[100, 50, 69, 19, 71, 22, 73, 24, 75, 25],
                        [49, 99, 20, 70, 21, 72, 23, 74, 26, 76],
                        [98, 48, 68, 18, 53, 4, 55, 5, 77, 27],
                        [47, 97, 17, 67, 3, 54, 6, 56, 28, 78],
                        [96, 46, 66, 16, 52, 2, 57, 7, 79, 29],
                        [45, 95, 15, 65, 1, 51, 8, 58, 30, 80],
                        [94, 44, 64, 13, 62, 11, 60, 9, 81, 31],
                        [43, 93, 14, 63, 12, 61, 10, 59, 32, 82],
                        [92, 41, 90, 39, 88, 37, 86, 35, 84, 33],
                        [42, 91, 40, 89, 38, 87, 36, 85, 34, 83]]
      		
		#this board indicates the rank of a ship given x_coordinate and y_coordinate
        self.ship_frequency_helper_board = reference_grid
	    
        # in this dictionary,the key is the rank, the values is the list of coordinates in the rank
        for i in range(1,max(reference_grid[0])+1):
            self.ship_frequency_statistics[i] = []
       
        # place the cell/ tuple in the dictionary according to their rank
        for x in range (0,len(reference_grid)):
            for y in range (0,len(reference_grid[0])):
                value = reference_grid[x][y]
                self.ship_frequency_statistics[value].append((x,y))
    
    def set_opponent_heat_map(self):
        # initially, there is no shot in opponent's board so all values are DEFAULT 
        self.opponent_heat_map = [ [0 for i in range(Player.BOARD_LENGTH)] for j in range(Player.BOARD_LENGTH)]          
        
              
    def displayMyBoard(self):
        print("This is my board")
        if self.myBoard:
            for i in range (0, len(self.myBoard)):
                row = ''
                for y in range (0, len(self.myBoard[0])):
                    row += str(self.myBoard[i][y])
                    NoOfSpace = 4 - len(str(self.myBoard[i][y]))
                    for s in range(0,NoOfSpace):
                        row += ' '
                row +='\n'
                print(row)
        else:
            print ("My board is not set up yet")
    
    def displayOpponentBoard(self):
        print("This is my opponent's board after my moves")
        if self.opponentBoard:
            for i in range (0, len(self.opponentBoard)):
                row = ''
                for y in range (0, len(self.opponentBoard[0])):
                    row += str(self.opponentBoard[i][y])
                    NoOfSpace = 4 - len(str(self.opponentBoard[i][y]))
                    for s in range(0,NoOfSpace):
                        row += ' '
                row +='\n'
                print(row)
        else:
            print ("Opponent board is not set up yet")
    
    def displayHeatMap(self):
        print("This is my heat map after knowing my hits in previous rounds")
        if self.opponent_heat_map:
            for i in range (0, len(self.opponent_heat_map)):
                row = ''
                for y in range (0, len(self.opponent_heat_map[0])):
                    row += str(round(self.opponent_heat_map[i][y],1))
                    NoOfSpace = 4 - len(str(self.opponent_heat_map[i][y]))
                    for s in range(0,NoOfSpace):
                        row += ' '
                row +='\n'
                print(row)
        else:
            print ("Opponent heat map is not set up yet")
    
    def displayShipDict(self):
        print("This is my ship list fter knowing my opponents' shots")
        if self.shipDict:
            # ship Dict starts at 1 
            for i in self.shipDict.keys():
                    print(str(i) + ' : ' + str(self.shipDict[i]))
        else:
            print ("Ship Dict is not set up yet")
