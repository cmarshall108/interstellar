import random
import pygame
import time
from interstellar import node, resource, audio, controller, mechanism

class SpriteError(node.NodeError):
    """
    A sprite specific runtime error
    """

class Sprite(node.Node):
    """
    A controlled object within the game usually a player
    """

    def __init__(self, parent, image, controller):
        super(Sprite, self).__init__()

        self._parent = parent
        self.image = image
        self.controller = controller(self)
        self._attachment = None
        self.attachment_sound = audio.AudioSound('assets/audio/sfx/grabbed_attachment.wav')
        self.attachment_deny_sound = audio.AudioSound('assets/audio/sfx/grabbed_attachment_deny.wav')

        self.health = 0
        self.damage = 0
        self.can_damage = True

    @property
    def attachment(self):
        return self._attachment

    @attachment.setter
    def attachment(self, attachment):
        if self._attachment or attachment is self._attachment:
            if self.attachment_deny_sound.playing:
                self.attachment_deny_sound.stop()

            self.attachment_deny_sound.play()
            return

        self._attachment = attachment
        self.attachment.setup()

        if self.attachment_sound.playing:
            self.attachment_sound.stop()

        self.attachment_sound.play()

    def hurt(self, attacker):
        if not self.can_damage:
            return

        if self.health <= 0:
            return self.die(attacker)

        self.health -= attacker.damage

    def die(self, *args, **kwargs):
        pass

    def setup(self):
        self.controller.setup()

    def update(self):
        self.controller.update()

        if self._attachment:
            self._attachment.update()

    def explicit_update(self):
        self.controller.explicit_update()

    def destroy(self):
        super(Sprite, self).destroy()

        self.image.destroy()
        self.image = None

        self.controller.destroy()
        self.controller = None

        if self._attachment:
            self._attachment.destroy()

        self.attachment_sound.destroy()
        self.attachment_deny_sound.destroy()

class SpriteController(node.Node):
    """
    A controller, movement management for a specific sprite object
    """

    def __init__(self, sprite, bind_events=True):
        super(SpriteController, self).__init__()

        self.bind_events = bind_events

        self.sprite = sprite
        self.speed = 0

        self._parent = sprite._parent
        self.image = sprite.image

    def update(self):
        self.move()

    def explicit_update(self):
        pass

    def move(self):
        if self.sprite._attachment and hasattr(self.sprite._attachment, 'image') and self.sprite._attachment.image and self.image:
            self.sprite._attachment.image.position = (self.image.x, self.image.y)

    def bind(self, *args, **kwargs):
        if not self._parent or not self.bind_events:
            return None

        return self._parent.bind(*args, **kwargs)

    def unbind(self, *args, **kwargs):
        if not self._parent or not self.bind_events:
            return None

        return self._parent.unbind(*args, **kwargs)

    def send(self, *args, **kwargs):
        if not self._parent or not self.bind_events:
            return None

        return self._parent.send(*args, **kwargs)

    def destroy(self):
        super(SpriteController, self).destroy()

        self.sprite = None
        self.speed = 0

class ShipController(SpriteController):

    def __init__(self, sprite):
        super(ShipController, self).__init__(sprite)

        self.music_array = resource.ResourceAudioArray(self._parent.root, [
            'assets/audio/sfx/laser_fire_0.wav',
            'assets/audio/sfx/laser_fire_1.wav',
            'assets/audio/sfx/laser_fire_2.wav',
            'assets/audio/sfx/laser_fire_3.wav',
        ])

        self.fire_sound = None

        self.speed = 15
        self.health = 100
        self.projectile_speed = 20

        self.moving_forward = False
        self.moving_backward = False
        self.moving_right = False
        self.moving_left = False
        self.firing = False

        self.projectiles = []
        self.maximum_projectiles = 15

        self.controller = controller.GameController(self)
        self.current_distance = 0

    def setup(self):
        super(ShipController, self).setup()

        self.bind('Up', self.move_forward)
        self.bind('KeyRelease-Up', lambda event: self.move_forward(event, True))
        self.bind('Down', self.move_backward)
        self.bind('KeyRelease-Down', lambda event: self.move_backward(event, True))
        self.bind('Right', self.move_right)
        self.bind('KeyRelease-Right', lambda event: self.move_right(event, True))
        self.bind('Left', self.move_left)
        self.bind('KeyRelease-Left', lambda event: self.move_left(event, True))
        self.bind('space', self.fire)
        self.bind('KeyRelease-space', lambda event: self.fire(event, True))

        self.controller.setup()

    def move_forward(self, event, release=False):
        if not release:
            self.moving_forward = True
        else:
            self.moving_forward = False

    def move_backward(self, event, release=False):
        if not release:
            self.moving_backward = True
        else:
            self.moving_backward = False

    def move_right(self, event, release=False):
        if not release:
            self.moving_right = True
        else:
            self.moving_right = False

    def move_left(self, event, release=False):
        if not release:
            self.moving_left = True
        else:
            self.moving_left = False

    def fire(self, event, release=False):
        if not release:
            self.firing = True
        else:
            self.firing = False

    def explicit_update(self):
        self.controller.update()

    def move(self):
        super(ShipController, self).move()

        self.current_distance += self.speed

        if self.moving_forward and not self.image.y - self.image.height / 2 <= 0:
            self.image.y -= self.speed
        elif self.moving_backward and not self.image.y + self.image.height / 2 >= self._parent.root.display.height:
            self.image.y += self.speed / 2
            self.current_distance -= self.speed / 2

        if self.moving_right and not self.image.x + self.image.width / 2 >= self._parent.root.display.width:
            self.image.x += self.speed
        elif self.moving_left and not self.image.x - self.image.width / 2 <= 0:
            self.image.x -= self.speed

        if self.firing and len(self.projectiles) < self.maximum_projectiles:
            self.fire_projectile()

        self.update_projectiles()
        self.check_player_collisions()

    def update_projectiles(self):
        for projectile in self.projectiles:

            if projectile.y <= 0:
                self.destroy_projectile(projectile)
                continue

            if self.check_projectile_collisions(projectile):
                self.destroy_projectile(projectile)
                continue

            projectile.y -= random.random() * self.projectile_speed * 2

    def check_projectile_collisions(self, projectile):
        for asteroid in self._parent.asteroids:

            if projectile.collide_point(asteroid.image):
                asteroid.hurt(self.sprite)
                return True

        return False

    def check_player_collisions(self):
        for asteroid in self._parent.asteroids:

            if asteroid.image.collide_point(self.sprite.image):
                return self.sprite.hurt(asteroid)

    def fire_projectile(self):
        if self.fire_sound:
            self.music_array.deselect(use_pygame=True)
            self.fire_sound = None

        self.fire_sound = self.music_array.select(False, use_pygame=True)
        self.fire_sound.play()

        bullet0 = resource.ResourceImage(self._parent.root, 'assets/bullet.png')
        bullet0.position = (self.image.x - self.image.width / 2, self.image.y)

        bullet1 = resource.ResourceImage(self._parent.root, 'assets/bullet.png')
        bullet1.position = (self.image.x + self.image.width / 2, self.image.y)

        bullet0.render(self._parent.canvas)
        bullet1.render(self._parent.canvas)

        self.projectiles.append(bullet0)
        self.projectiles.append(bullet1)

    def destroy_projectile(self, projectile):
        projectile.destroy()
        self.projectiles.remove(projectile)

    def destroy_projectiles(self):
        for projectile in self.projectiles:
            self.destroy_projectile(projectile)

    def destroy(self):
        self.music_array.destroy()
        self.fire_sound = None

        self._parent.unbind('Up')
        self._parent.unbind('KeyRelease-Up')
        self._parent.unbind('Down')
        self._parent.unbind('KeyRelease-Down')
        self._parent.unbind('Right')
        self._parent.unbind('KeyRelease-Right')
        self._parent.unbind('Left')
        self._parent.unbind('KeyRelease-Left')
        self._parent.unbind('space')
        self._parent.unbind('KeyRelease-space')

        self.controller.destroy()
        self.destroy_projectiles()
        super(ShipController, self).destroy()

class Ship(Sprite):

    def __init__(self, parent, controller):
        image = resource.ResourceImage(parent.root, 'assets/player.png')
        image.position = (parent.master.root.winfo_width() / 2, parent.master.root.winfo_height() - image.height)
        image.render(parent.canvas)

        super(Ship, self).__init__(parent, image, controller)

        self.health = 100
        self.damage = 5

    def die(self, killer):
        self._parent.explode(self.image.x, self.image.y)
        self._parent.end()

class AsteroidController(SpriteController):

    def __init__(self, sprite):
        super(AsteroidController, self).__init__(sprite)

        self.speed = 25
        self.speed = random.random() * self.speed

    def move(self):
        if self.image.y >= self._parent.root.display.height:
            self._parent.remove_asteroid(self.sprite)
            return

        self.image.y += self.speed

class Asteroid(Sprite):
    PROBABILITY = 100

    def __init__(self, parent, controller, image=None, is_mechanism=False):
        if not image:
            images = [
                'assets/asteroids/asteroid-small.png',
                'assets/asteroids/asteroid-big.png'
            ]

            image = resource.ResourceImage(parent.root, random.choice(images))
            image.position = (random.randrange(0, parent.root.display.width), 0)
            image.render(parent.canvas)

        super(Asteroid, self).__init__(parent, image, controller)

        self.is_mechanism = is_mechanism
        self.health = 10
        self.damage = 1

    def die(self, killer):
        self._parent.explode(self.image.x, self.image.y)
        self._parent.remove_asteroid(self, True)

class MechanismAsteroid(Asteroid):
    ICON = ''
    ATTACHMENT = None

    def __init__(self, parent, controller):
        image = resource.ResourceImage(parent.root, self.ICON)
        image.position = (random.randrange(0, parent.root.display.width), 0)
        image.render(parent.canvas)

        super(MechanismAsteroid, self).__init__(parent, controller, image, True)

        self.health = 0
        self.damage = 0

    def die(self, killer):
        killer.attachment = self.ATTACHMENT(killer)
        self._parent.remove_asteroid(self, False)

class ShieldMechanismAsteroid(MechanismAsteroid):
    PROBABILITY = 0.5
    ICON = 'assets/icons/shield_icon.png'
    ATTACHMENT = mechanism.ShieldMechanism

class InstantKillMechanismAsteroid(MechanismAsteroid):
    PROBABILITY = 0.1
    ICON = 'assets/icons/instant_kill_icon.png'
    ATTACHMENT = mechanism.InstantKillMechanism

class FullHealthMechanismAsteroid(MechanismAsteroid):
    PROBABILITY = 0.3
    ICON = 'assets/icons/full_health_icon.png'
    ATTACHMENT = mechanism.FullHealthMechanism

class DoubleHealthMechanismAsteroid(MechanismAsteroid):
    PROBABILITY = 0.5
    ICON = 'assets/icons/double_health_icon.png'
    ATTACHMENT = mechanism.DoubleHealthMechanism
