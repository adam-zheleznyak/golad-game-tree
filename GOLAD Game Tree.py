#!/usr/bin/python

# This is a script to make a game tree for the Game of Life and Death with the modification that a player who plays into a board they played into before loses and if there is a tie (all cells die on the same turn), whoever played last loses

from copy import copy, deepcopy
import json

# Board formatting:
# 2D array where " " means empty, "R" means red, and "B" means blue
# Top left corner of the board is (0,0) where a cell at (i,j) corresponds to board[j][i]

def emptyBoard(height, width):
    return [[" " for i in range(0, width)] for j in range(0, height)]

def printBoard(board):
    for j in range(0, len(board)):
        row = "|"
        for i in range(0, len(board[j])):
            row += str(board[j][i]) + "|"
        print(row)
    print("") #empty line

def lifeIterate(originalBoard):
    # Create a newboard (don't want to modify the original)
    newBoard = deepcopy(originalBoard)
    for j in range(0, len(originalBoard)):
        for i in range(0, len(originalBoard[j])):
            red = 0
            blue = 0
            # dy and dx are used to count all surrounding cells for the cell at (i,j)
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    # to prevent counting the cell itself
                    if not (dx is 0 and dy is 0):
                        # to prevent errors from counting past the border
                        if 0 <= j+dy <= len(originalBoard) - 1:
                            if 0 <= i+dx <= len(originalBoard[j+dy]) - 1:
                                if originalBoard[j+dy][i+dx] is "R":
                                    red += 1
                                elif originalBoard[j+dy][i+dx] is "B":
                                    blue += 1
            # birth
            if originalBoard[j][i] is " ":
                if red + blue is 3:
                    if red > blue:
                        newBoard[j][i] = "R"
                    else:
                        newBoard[j][i] = "B"
            # death
            elif originalBoard[j][i] is "R" or originalBoard[j][i] is "B":
                if red + blue < 2 or red + blue > 3:
                    newBoard[j][i] = " "
    return newBoard

class GameState:
    def __init__(self, board, turn=0, prevBoards=[], loser=False, lossReason=""):
        self.board = deepcopy(board)
        
        # turn is 0 for red is playing next, and is 1 for blue is playing next
        self.turn = turn
        
        # prevBoards is a list of all previous boards (excluding the current one) to be checked that there are no repetitions
        self.prevBoards = deepcopy(prevBoards)
        
        # loser is false if the the game isn't over
        self.loser = loser
        self.lossReason = lossReason
    
    def __str__(self):
        # This defines how GameState is printed
        
        out = ""
        for j in range(0, len(self.board)):
            row = "|"
            for i in range(0, len(self.board[j])):
                row += str(self.board[j][i]) + "|"
            out += row + "\n"
        if self.loser:
            out += self.loser + " lost because they " + self.lossReason + "!\n\n"
        else:
            if self.turn is 0:
                out += "Red plays next...\n"
            elif self.turn is 1:
                out += "Blue plays next...\n"
        return out
    
    def iterate(self, boardBeforeMove):
        # this function mutates the game state
        
        self.prevBoards.append((boardBeforeMove, self.turn)) # appending a tuple
        self.board = lifeIterate(self.board)
        self.turn = (self.turn + 1) % 2
        
        # check for losses due to no cells
        anyRed = any("R" in row for row in self.board)
        anyBlue = any("B" in row for row in self.board)
        
        # if there is a tie, whoever played last loses
        if not anyRed and not anyBlue:
            # if it is now blue's turn, red played into the tie and vice versa
            if self.turn is 1:
                self.loser = "Red"
            elif self.turn is 0:
                self.loser = "Blue"
            self.lossReason = "played into a tie"
            return self
        if not anyRed:
            self.loser = "Red"
            self.lossReason = "were eliminated"
            return self
        if not anyBlue:
            self.loser = "Blue"
            self.lossReason = "were eliminated"
            return self
        
        # check for repeats
        for state in self.prevBoards:
            sameBoard = True
            for j in range(len(self.board)):
                if not self.board[j] == state[0][j]:
                    sameBoard = False
            if sameBoard and self.turn == state[1]:
                # if it is now blue's turn, red played into the repeat and vice versa
                if self.turn is 1:
                    self.loser = "Red"
                elif self.turn is 0:
                    self.loser = "Blue"
                self.lossReason = "played into a repeated state"
                return self
        
        return self

class Node:
    def __init__(self, gameState, move=""):
        self.gameState = gameState
        self.parent = None
        self.children = []
        # losing defines who this is a losing gamestate for
        self.losing = None
        # String that shows what was the previous move e.g. "D:2,4" means destroyed the cell in the 2nd column, 4th row and "C:3,3-2,2;1,2" means created a cell at (3,3) by sacrifcing the cells at (2,2) and (1,2)
        self.move = move
        
    def setParent(self, parent):
        self.parent = parent
        if self not in parent.children:
            parent.addChild(self)
    
    def addChild(self, child):
        self.children.append(child)
        if not self is child.parent:
            child.setParent(self)
    
    def turnNumber(self):
        # Returns based on what turn of the game it is. Game starts at 0. Assuming red plays first, if it is red's turn next then turn is 0 mod 2, blue is 1 mod 2.
        if self.parent is None:
            return 0
        return self.parent.turn() + 1
        
    def addMoves(self):
        # Only add moves if this game still hasn't ended
        if not self.gameState.loser:
            addAllMoves(self)

def addAllMoves(parent):
    # This function takes a node in the GameTree and adds a child for each possible move
    
    # A player has 2 possible moves:
        # destroy a cell (any color)
        # sacrifice two cells and create a cell anywhere (own color)
    
    # to type less
    gameState = parent.gameState
    
    # red's turn
    if gameState.turn is 0:
        # destroy a cell
        for j in range(0,len(gameState.board)):
            for i in range(0,len(gameState.board[j])):
                if gameState.board[j][i] is "R" or gameState.board[j][i] is "B":
                    next = deepcopy(gameState)
                    next.board[j][i] = " "
                    next.iterate(gameState.board)
                    move = "D:" + str(i) + "," + str(j)
                    parent.addChild(Node(next, move))
        
        # destroy 2 red cells and birth 1
        # begin with destroy #1
        for j1 in range(0,len(gameState.board)):
            for i1 in range(0,len(gameState.board[j])):
                if gameState.board[j1][i1] is "R":
                    next1 = deepcopy(gameState)
                    next1.board[j1][i1] = " "
                    
                    # destroy #2
                    for j2 in range(0,len(gameState.board)):
                        for i2 in range(0,len(gameState.board[j])):
                            if next1.board[j2][i2] is "R":
                                next2 = deepcopy(next1)
                                next2.board[j2][i2] = " "
                                
                                # birth (can't be where a cell was sacrificed)
                                for j3 in range(0,len(gameState.board)):
                                    for i3 in range(0,len(gameState.board[j])):
                                        if (j3 is j1 and i3 is i1) or (j3 is j2 and i3 is i2):
                                            continue
                                        if next2.board[j3][i3] is " ":
                                            next3 = deepcopy(next2)
                                            next3.board[j3][i3] = "R"
                                            next3.iterate(gameState.board)
                                            move = "C:" + str(i3) + "," + str(j3) + "-" + str(i1) + "," + str(j1) + ";" + str(i2) + "," + str(j2)
                                            parent.addChild(Node(next3, move))
    
    # blue's turn
    if gameState.turn is 1:
        # destroy a cell
        for j in range(0,len(gameState.board)):
            for i in range(0,len(gameState.board[j])):
                if gameState.board[j][i] is "R" or gameState.board[j][i] is "B":
                    next = deepcopy(gameState)
                    next.board[j][i] = " "
                    next.iterate(gameState.board)
                    move = "D:" + str(i) + "," + str(j)
                    parent.addChild(Node(next, move))
        
        # destroy 2 blue cells and birth 1
        # begin with destroy #1
        for j1 in range(0,len(gameState.board)):
            for i1 in range(0,len(gameState.board[j])):
                if gameState.board[j1][i1] is "B":
                    next1 = deepcopy(gameState)
                    next1.board[j1][i1] = " "
                    
                    # destroy #2
                    for j2 in range(0,len(gameState.board)):
                        for i2 in range(0,len(gameState.board[j])):
                            if next1.board[j2][i2] is "B":
                                next2 = deepcopy(next1)
                                next2.board[j2][i2] = " "
                                
                                # birth (can't be where a cell was sacrificed)
                                for j3 in range(0,len(gameState.board)):
                                    for i3 in range(0,len(gameState.board[j])):
                                        if (j3 is j1 and i3 is i1) or (j3 is j2 and i3 is i2):
                                            continue
                                        if next2.board[j3][i3] is " ":
                                            next3 = deepcopy(next2)
                                            next3.board[j3][i3] = "B"
                                            next3.iterate(gameState.board)
                                            move = "C:" + str(i3) + "," + str(j3) + "-" + str(i1) + "," + str(j1) + ";" + str(i2) + "," + str(j2)
                                            parent.addChild(Node(next3, move))


def depthFirstGameTree(initialGameState):
    # This will build a game tree using a depth first approach
    # This will go through all possible moves from the initialGameState and define the losing player on each node
    # Because GOLAD can have so many possible moves, this is only feasible for very small boards
    start = Node(deepcopy(initialGameState))
    
    # Add all possible moves recursively
    recursiveAddMoves(start)
    
    # Find who has the winning strategy
    recursiveSetLosing(start)
    
    return start

def recursiveAddMoves(node):
    # This function recursively adds all possible moves as children to each node (it continues until every leaf is a state where someone lost)
    node.addMoves()
    for child in node.children:
        recursiveAddMoves(child)

def recursiveSetLosing(node):
    # This function sets the losing player for each node in a tree populated with all possible moves
    if node.gameState.loser:
        # This means the game ended here
        node.losing = node.gameState.loser
    else:
        if not node.children:
            print("Error: Game ended without a loser")
        for child in node.children:
            recursiveSetLosing(child)
        # Based on the players turn, check if they have a move that makes the other player lose
        if node.gameState.turn is 0:
            # Red's turn
            for child in node.children:
                if child.losing is "Blue":
                    node.losing = "Blue"
                    break
            if not node.losing:
                # This means there was no move to make Blue lose and so Red will lose her
                node.losing = "Red"
        elif node.gameState.turn is 1:
            # Blue's turn
            for child in node.children:
                if child.losing is "Red":
                    node.losing = "Red"
                    break
            if not node.losing:
                # This means there was no move to make Red lose and so Blue will lose her
                node.losing = "Blue"


def breadthFirstGameTree(initialGameState):
    # This will build a game tree using a breadth first approach until the winning player is realized
    # This will be far more efficient than a depth first game tree, but will also not produce the full tree of all possible moves (by design)
    start = Node(deepcopy(initialGameState))
    
    # Each game state is in this array; the nth level of the tree will be in the list at nodes[n] (with n=0 corresponding to the initial state)
    nodes = [[start]]
    
    n = 0
    
    # Bad coding style - should only loop forever if the game never ends (which, technically, it always should... at some point)
    while(True):
        for node in nodes[n]:
            node.addMoves()
            checkLosing(node, nodes, n)
        if start.losing:
            break
        n += 1
    return start

def checkLosing(node, nodes, n):
    updated = False
    if node.gameState.turn is 0:
        # Red's turn: check if there is a move that causes blue to lose, or if all moves cause red to lose
        blueLose = False
        redLose = True
        for child in node.children:
            if child.gameState.loser is "Blue" or child.losing is "Blue":
                blueLose = True
                redLose = False
                break
            elif child.gameState.loser is not "Red" or child.losing is not "Red":
                redLose = False
        if blueLose:
            node.losing = "Blue"
            updated = True
        elif redLose:
            node.losing = "Red"
            updated = True
    else:
        # Blue's turn: check if there is a move that causes red to lose, or if all moves cause blue to lose
        redLose = False
        blueLose = True
        for child in node.children:
            if child.gameState.loser is "Red" or child.losing is "Red":
                redLose = True
                blueLose = False
                break
            elif child.gameState.loser is not "Blue" or child.losing is not "Blue":
                blueLose = False
        if redLose:
            node.losing = "Red"
            updated = True
        elif blueLose:
            node.losing = "Blue"
            updated = True
    if updated:
        if node.parent:
            checkLosing(node.parent, nodes, -1)
    else:
        # need to check children if there wasn't an update (n is -1 means children were already added)
        if n is -1:
            pass
        elif n + 1 >= len(nodes):
            nodes.append([child for child in node.children])
        else:
            nodes[n + 1] += [child for child in node.children]


def treeToJSON(root):
    return json.dumps(recursiveTreeToDict(root), indent = 4)

def recursiveTreeToDict(root):
    return {'board': root.gameState.board, 'turn': root.gameState.turn, 'move': root.move,
            'loser': root.gameState.loser, 'lossReason': root.gameState.lossReason, 'losing': root.losing,
            'children': [recursiveTreeToDict(node) for node in root.children]}

def saveJSON(root, filename):
    f = open(filename, "w")
    f.write(treeToJSON(root))

sampleGame_two_by_two = GameState([["R","R"],
["B","B"]])

sampleGame_three_by_three = GameState([[" ","R"," "],
["B"," ","B"],
[" ","R"," "]])

sampleGame_four_by_four = GameState([[" ","R"," ","R"],
[" "," ","B"," "],
[" ","R"," "," "],
["B"," ","B"," "]])

sampleGame_five_by_five = GameState([[" "," ","R"," ","R"],
["B"," ","B"," "," "],
[" ","R"," ","B"," "],
[" "," ","R"," ","R"],
["B"," ","B"," "," "]])

gameTree_two_by_two = depthFirstGameTree(sampleGame_two_by_two)

print("For 2x2...")
if gameTree_two_by_two.losing is "Blue":
    print("Red has the winning strategy")
elif gameTree_two_by_two.losing is "Red":
    print("Blue has the winning strategy")
else:
    print("Something went wrong: no winner?")
    
gameTree_three_by_three = depthFirstGameTree(sampleGame_three_by_three)

print("For 3x3...")
if gameTree_three_by_three.losing is "Blue":
    print("Red has the winning strategy")
elif gameTree_three_by_three.losing is "Red":
    print("Blue has the winning strategy")
else:
    print("Something went wrong: no winner?")

saveJSON(gameTree_three_by_three, "gameTree_three_by_three.json")

gameTree_four_by_four = breadthFirstGameTree(sampleGame_four_by_four)

print("For 4x4...")
if gameTree_four_by_four.losing is "Blue":
    print("Red has the winning strategy")
elif gameTree_four_by_four.losing is "Red":
    print("Blue has the winning strategy")
else:
    print("Something went wrong: no winner?")

saveJSON(gameTree_four_by_four, "gameTree_four_by_four.json")

# This takes a bit of time...
gameTree_five_by_five = breadthFirstGameTree(sampleGame_five_by_five)

print("For 5x5...")
if gameTree_five_by_five.losing is "Blue":
    print("Red has the winning strategy")
elif gameTree_five_by_five.losing is "Red":
    print("Blue has the winning strategy")
else:
    print("Something went wrong: no winner?")

saveJSON(gameTree_five_by_five, "gameTree_five_by_five.json")