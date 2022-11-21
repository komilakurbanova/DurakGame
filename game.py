import card
import player
import field


class Game(object):
    def __init__(self, p1: player.Player, p2: player.Player):
        self.field: Field = Field(p1, p2)
        # self.players:
        self.active_player: player.puid() = None
        self.defence_player: player.puid() = None


    def move(p: player.Player):
        message = ''
        if p.puid == Game.active_player:
            message = "Place your card!"
        elif p.puid == Game.defence_player:
            message = "The opponent is making a move"
        return message


    def is_defending(self, id: player.puid):
        return self.defendce_player == id


    def is_active(self, id: player.puid):
        return self.active_player == id
