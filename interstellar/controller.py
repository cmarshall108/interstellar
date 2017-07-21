import pygame

JOYAXISMOTION = pygame.JOYAXISMOTION
JOYBALLMOTION = pygame.JOYBALLMOTION
JOYBUTTONDOWN = pygame.JOYBUTTONDOWN
JOYBUTTONUP = pygame.JOYBUTTONUP
JOYHATMOTION = pygame.JOYHATMOTION

JOYBUTTON_Y = 0x00
JOYBUTTON_B = 0x01
JOYBUTTON_A = 0x02
JOYBUTTON_X = 0x03
JOYBUTTON_LB = 0x04
JOYBUTTON_RB = 0x05
JOYBUTTON_LT = 0x06
JOYBUTTON_RT = 0x07

class Controller(object):
    """
    A class that processes, handles controller input
    """

    def __init__(self, root):
        self.root = root

    def setup(self):
        pass

    def update(self):
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                self.button_down(event.button)
            elif event.type == JOYBUTTONUP:
                self.button_up(event.button)
            elif event.type == JOYAXISMOTION:
                self.axis_motion(event)

    def button_down(self, button):
        pass

    def button_up(self, button):
        pass

    def axis_motion(self, event):
        pass

    def destroy(self):
        pass

class GameController(Controller):
    """
    A game controller specifically for the player sprite
    """

    def button_down(self, button):
        if button == JOYBUTTON_LT or button == JOYBUTTON_RT:
            self.root.send('<space>')

    def button_up(self, button):
        if button == JOYBUTTON_LT or button == JOYBUTTON_RT:
            self.root.send('<KeyRelease-space>')

    def axis_motion(self, event):
        x, y = round(joystick.get_axis(0)), round(joystick.get_axis(1))

        if x == 1.0:
            self.root.send('<Right>')
        elif x == -1.0:
            self.root.send('<Left>')
        else:
            if self.root.moving_right:
                self.root.send('<KeyRelease-Right>')
            elif self.root.moving_left:
                self.root.send('<KeyRelease-Left>')

        if y == -1.0:
            self.root.send('<Up>')
        elif y == 1.0:
            self.root.send('<Down>')
        else:
            if self.root.moving_forward:
                self.root.send('<KeyRelease-Up>')
            elif self.root.moving_backward:
                self.root.send('<KeyRelease-Down>')
