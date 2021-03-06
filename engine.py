import pygame, math, os, json, pymunk
pygame.font.init()

class SceneMap:
    def __init__(self, map_json_file, tiles_directory):
        self.json_map = json.load(open(map_json_file))
        layers = {}

        _grass_tiles = os.listdir(tiles_directory)
        self.tiles = []
        for i in _grass_tiles:
            self.tiles.append(pygame.image.load(f"{tiles_directory}/{i}"))

        self.bodies = []
        self.game_map = []
        self.rects = []

        for layer in self.json_map["layers"]:
            _x, _y, i = 0, 0, 0
            for e in layer["data"]:
                if e != 0:
                    self.game_map.append([_x, _y, self.tiles[e - 1]])
                    pos, size = [(_x+16, _y+16), (32, 32)]
                    body = pymunk.Body(body_type=pymunk.Body.STATIC)
                    body.position = pos
                    self.bodies.append(body)
                    self.rects.append(pygame.Rect(pos, size))
                _x += 32
                i += 1
                if i > layer["width"] - 1:
                    i = 0
                    _x = 0
                    _y += 32

        self.width = self.json_map["width"] * self.json_map["tilewidth"]
        self.height = self.json_map["height"] * self.json_map["tileheight"]


class Scene:
    def __init__(
        self,
        screen,
        _game_map: SceneMap,
        clock: pygame.time.Clock,
        background_image=None,
        background_color=(20, 206, 215),
    ):
        self.screen = screen
        self.background = (
            pygame.image.load(background_image).convert_alpha()
            if background_image
            else None
        )
        self.background_color = background_color
        self.offset = [0, 0]
        self.entities = []
        self.game_map = _game_map
        self.space = pymunk.Space()
        self.space.gravity = (0, 981)
        for body in self.game_map.bodies:
            shape = pymunk.Poly.create_box(body, (32, 32))
            self.space.add(body, shape)
        self.DEBUG = False
        self.clock = clock

    def add_entity(self, ID, entity):
        self.entities.append({ID: entity})

    def scroll(self, player):
        x, y = player.x, player.y
        if x < self.screen.get_width() / 2:
            self.offset[0] = 0
        elif x > self.game_map.width - self.screen.get_width() / 2:
            self.offset[0] = self.game_map.width - self.screen.get_width()
        elif x > self.screen.get_width() / 2:
            self.offset[0] = x - self.screen.get_width() / 2

        if y > 0 and y < self.screen.get_height() / 2:
            self.offset[1] = 0
        elif y > self.game_map.height - self.screen.get_height() / 2:
            self.offset[1] = self.game_map.height - self.screen.get_height()
        elif y > self.screen.get_height() / 2:
            self.offset[1] = y - self.screen.get_height() / 2

    def draw(self):
        self.space.step(1 / 60)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_p]:
            self.DEBUG = not self.DEBUG

        self.screen.fill(self.background_color)
        if self.background:
            self.screen.blit(self.background, self.offset)

        index = 0
        for i in self.game_map.game_map:
            x, y, tile = i
            self.screen.blit(tile, (x - self.offset[0], y - self.offset[1], 32, 32))
            pos = (x - self.offset[0], y - self.offset[1])
            self.game_map.bodies[index].position = pos
            self.game_map.rects[index].topleft = pos
            index += 1


        for entity in self.entities:
            entity = list(entity.values())[0]
            if entity.body not in self.space.bodies:
                self.space.add(entity.body, entity.shape)
            entity.draw(self.screen, self.offset)
            if self.DEBUG:
                entity.debug(self.screen)
        
        if self.DEBUG:
            fps = round(self.clock.get_fps())
            self.screen.blit(
                pygame.font.SysFont("Arial", 20).render(f"FPS: {fps}", True, (255, 255, 255)),
                (0, 0),
            )
            for body in self.game_map.bodies:
                x, y = body.position
                pygame.draw.rect(self.screen, (255, 0, 0), (int(x), int(y), 32, 32), 1)



class Sprite:
    def __init__(self, x, y, width, height, angle):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.angle = angle
        self.animations = {}
        self.current_animation = None
        self.current_frame = 0
        self.origin = (0, 0)
        self.flipped = False
        self.mirrored = False
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.body = pymunk.Body(3, 100, body_type=pymunk.Body.DYNAMIC)
        self.body.position = (self.x, self.y)
        self.shape = pymunk.Poly.create_box(self.body, (self.width, self.height))

    def load(self, image):
        self.render = pygame.transform.flip(image, self.flipped, self.mirrored)
        self.render = pygame.transform.scale(self.render, (self.width, self.height))
        self.render = pygame.transform.rotate(self.render, self.angle)

    def add_animation(self, name, frames, speed=6):
        final_frames = []
        for frame in frames:
            for i in range(speed):
                final_frames.append(pygame.image.load(frame).convert_alpha())
        self.animations[name] = final_frames
        self.current_animation = name
        self.current_frame = 0
        self.load(self.animations[self.current_animation][self.current_frame])

    def draw(self, screen, offset):
        if self.current_animation:
            if self.current_frame >= len(self.animations[self.current_animation]):
                self.current_frame = 0
            self.load(self.animations[self.current_animation][self.current_frame])
            self.current_frame += 1
        self.x = int(self.body.position.x)
        self.y = int(self.body.position.y)
        self.rect = pygame.Rect(
            self.x - offset[0] - self.origin[0],
            self.y - offset[1] - self.origin[1],
            self.width,
            self.height,
        )

    def debug(self, screen):
        text = f"""X: {self.x} Y: {self.y} Angle: {self.angle} Velocity: {self.body.velocity[0]} {round(self.body.velocity[1], 5)}"""
        screen.blit(
            pygame.font.SysFont("Arial", 20).render(text, True, (255, 255, 255)),
            (self.rect.x, self.rect.y-50),
        )
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)