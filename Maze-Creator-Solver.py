# Imports
import random
import pygame
from queue import PriorityQueue

# Variables
WIDTH = 800
WIN = pygame.display.set_mode((WIDTH, WIDTH+200))
pygame.init()
pygame.display.set_caption("Maze-Creator-Solver")

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 255, 0)
YELLOW = (255, 234, 0)
YELLOW2 = (225, 193, 110)
YELLOW3 = (194, 178, 128)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREY = (186, 186, 186)
TURQUOISE = (64, 224, 208)
DARKBLUE = (52, 73, 97)

FONT = pygame.font.Font('freesansbold.ttf', 25)

clock = pygame.time.Clock()


# Dropdown class
class DropDown:
    def __init__(self, color_menu, color_option, x, y, w, h, font, main, options):
        self.color_menu = color_menu
        self.color_option = color_option
        self.rect = pygame.Rect(x, y, w, h)
        self.font = font
        self.main = main
        self.options = options
        self.draw_menu = False
        self.menu_active = False
        self.active_option = -1

    def draw(self, surf):
        pygame.draw.rect(surf, self.color_menu[self.menu_active], self.rect, 0)
        msg = self.font.render(self.main, 1, (255, 255, 255))
        surf.blit(msg, msg.get_rect(center=self.rect.center))

        if self.draw_menu:
            for i, text in enumerate(self.options):
                rect = self.rect.copy()
                rect.y += (i + 1) * self.rect.height
                pygame.draw.rect(surf, self.color_option[1 if i == self.active_option else 0], rect, 0)
                msg = self.font.render(text, 1, (255, 255, 255))
                surf.blit(msg, msg.get_rect(center=rect.center))

    def update(self, event_list):
        mpos = pygame.mouse.get_pos()
        self.menu_active = self.rect.collidepoint(mpos)

        self.active_option = -1
        for i in range(len(self.options)):
            rect = self.rect.copy()
            rect.y += (i + 1) * self.rect.height
            if rect.collidepoint(mpos):
                self.active_option = i
                break

        if not self.menu_active and self.active_option == -1:
            self.draw_menu = False

        for event in event_list:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_active:
                    self.draw_menu = not self.draw_menu
                elif self.draw_menu and self.active_option >= 0:
                    self.draw_menu = False
                    return self.active_option
        return -1


# Variables for dropdown menus
COLOR_INACTIVE = (37, 54, 74)
COLOR_ACTIVE = (69, 102, 140)
COLOR_LIST_INACTIVE = (37, 54, 74)
COLOR_LIST_ACTIVE = (69, 102, 140)

mazes = DropDown(
    [COLOR_INACTIVE, COLOR_ACTIVE],
    [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
    50, 50, 200, 50,
    pygame.font.SysFont(None, 25),
    "Mazes", ["Prim's", "Recursive Backtracker", "Random"])

sizes = DropDown(
    [COLOR_INACTIVE, COLOR_ACTIVE],
    [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
    300, 50, 150, 50,
    pygame.font.SysFont(None, 25),
    "Size", ["6x6", "10x10", "20x20", "40x40", "80x80", "160x160", "200x200"])

speeds = DropDown(
    [COLOR_INACTIVE, COLOR_ACTIVE],
    [COLOR_LIST_INACTIVE, COLOR_LIST_ACTIVE],
    500, 50, 150, 50,
    pygame.font.SysFont(None, 25),
    "Speed", ["Slow", "Average", "Fast", "Ultra Fast"])


# Class for each spot of the grid
class Spot:
    def __init__(self, row, col, width, total_rows):
        self.row = row
        self.col = col
        self.x = row * width
        self.y = col * width + 200
        self.color = WHITE
        self.neighbors = []
        self.width = width
        self.total_rows = total_rows

    def get_pos(self):
        return self.row, self.col

    def is_closed(self):
        return self.color == RED

    def is_open(self):
        return self.color == GREEN

    def is_barrier(self):
        return self.color == BLACK

    def is_start(self):
        return self.color == ORANGE

    def is_room(self):
        return self.color == WHITE

    def is_end(self):
        return self.color == TURQUOISE

    def reset(self):
        self.color = WHITE

    def make_closed(self):
        self.color = RED

    def make_open(self):
        self.color = GREEN

    def make_barrier(self):
        self.color = BLACK

    def make_start(self):
        self.color = ORANGE

    def make_end(self):
        self.color = TURQUOISE

    def make_point(self, s):  # makes another point where the algorithm has to travel to
        if s == "1":
            self.color = YELLOW
        if s == "2":
            self.color = YELLOW2
        if s == "3":
            self.color = YELLOW3

    def make_path(self):  # draws the path
        self.color = PURPLE

    def draw(self, win):  # draws a square
        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.width))

    def update_neighbors(self, grid):
        self.neighbors = []
        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier():  # DOWN
            self.neighbors.append(grid[self.row + 1][self.col])

        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():  # UP
            self.neighbors.append(grid[self.row - 1][self.col])

        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier():  # RIGHT
            self.neighbors.append(grid[self.row][self.col + 1])

        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():  # LEFT
            self.neighbors.append(grid[self.row][self.col - 1])

    def __lt__(self, other):
        return False


def h(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x1 - x2) + abs(y1 - y2)


def reconstruct_path(came_from, current, draw, path):
    while current in came_from:
        current = came_from[current]
        current.make_path()
        path.append(current)
        draw()


def algorithm(draw, grid, start, end, path, FPS):
    count = 0
    open_set = PriorityQueue()
    open_set.put((0, count, start))
    came_from = {}
    g_score = {spot: float("inf") for row in grid for spot in row}
    g_score[start] = 0
    f_score = {spot: float("inf") for row in grid for spot in row}
    f_score[start] = h(start.get_pos(), end.get_pos())

    open_set_hash = {start}

    while not open_set.empty():
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

        current = open_set.get()[2]
        open_set_hash.remove(current)

        if current == end:
            reconstruct_path(came_from, current, draw, path)
            end.make_end()
            return True

        for neighbor in current.neighbors:
            temp_g_score = g_score[current] + 1

            if temp_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = temp_g_score
                f_score[neighbor] = temp_g_score + h(neighbor.get_pos(), end.get_pos())
                if neighbor not in open_set_hash:
                    count += 1
                    open_set.put((f_score[neighbor], count, neighbor))
                    open_set_hash.add(neighbor)
                    neighbor.make_open()

        draw()

        if current != start:
            current.make_closed()

    return False


def make_drig(rows, width):  # makes a grid (rows*rows)
    grid = []
    gap = width // rows
    for i in range(rows):
        grid.append([])
        for j in range(rows):
            spot = Spot(i, j, gap, rows)
            grid[i].append(spot)
    return grid


def draw_lines(win, rows, width):  # draws lines -> makes it look like a grid
    gap = width // rows
    for i in range(rows):
        pygame.draw.line(win, GREY, (0, i * gap+200), (width, i * gap+200))

    for j in range(rows):
        pygame.draw.line(win, GREY, (j * gap, 0+200), (j * gap, width+200))


def draw(win, grid, rows, width, length):  # draws on the window
    win.fill(WHITE)
    win.fill(DARKBLUE, (0, 0, width, 200))

    name = FONT.render("Pathfinding Visualizer", 1, (255, 255, 255))
    length_text = FONT.render(f"length:{length}", 1, (255, 255, 255))
    win.blit(name, (15, 10))
    win.blit(length_text, (800 - (length_text.get_width()+15), 150))


    for row in grid:
        for spot in row:
            spot.draw(win)

    draw_lines(win, rows, width)
    pygame.display.update()


def get_clicked_pos(pos, rows, width):  # gets clicked position
    gap = width // rows
    y, x = pos
    x -= 200

    row = y // gap
    col = x // gap

    return row, col, x


def random_maze(grid, ROWS):  # generates a random maze (maybe not possible)
    for i in range(ROWS * 10):
        grid[random.randrange(0, ROWS)][random.randrange(0, ROWS)].make_barrier()


def prims(grid, ROWS, win, width, FPS, length):  # Prim's algorithm for generating a maze
    walls = []
    path = []

    # Makes a walls and rooms
    for i in range(ROWS):
        if i % 2 == 0:
            for x in grid[i]:
                x.make_barrier()
            for x in range(ROWS):
                grid[x][i].make_barrier()

    x = 1
    y = 1

    path.append([x, y])

    for room in path:  # Checks for walls around x,y
        room_x = room[0]
        room_y = room[1]

        if room_x < ROWS - 1:
            if grid[room_x + 1][room_y].is_barrier() and grid[room_x + 2][room_y].is_room() and [room_x + 2, room_y] not in path and [room_x + 1, room_y, "R"] not in walls:  # Right
                walls.append([room_x + 1, room_y, "R"])

        if 1 < room_x:
            if grid[room_x - 1][room_y].is_barrier() and grid[room_x - 2][room_y].is_room() and [room_x - 2, room_y] not in path and [room_x - 1, room_y, "L"] not in walls:  # Left
                walls.append([room_x - 1, room_y, "L"])

        if room_y < ROWS - 1:
            if grid[room_x][room_y + 1].is_barrier() and grid[room_x][room_y + 2].is_room() and [room_x, room_y + 2] not in path and [room_x, room_y + 1, "D"] not in walls:  # Down
                walls.append([room_x, room_y + 1, "D"])

        if 1 < room_y:
            if grid[room_x][room_y - 1].is_barrier() and grid[room_x][room_y - 2].is_room() and [room_x, room_y - 2] not in path and [room_x, room_y - 1, "U"] not in walls:  # Up
                walls.append([room_x, room_y - 1, "U"])

    while walls:  # While loop for generating the maze
        clock.tick(FPS)
        wall = random.choice(walls)  # Picks random wall from walls list
        x2, y2, text = wall

        # Check for rooms around x,y

        if text == "R" and [x2 + 1, y2] not in path and grid[x2 + 1][y2].is_room():  # Right
            path.append([x2 + 1, y2])
            grid[x2][y2].reset()

        if text == "L" and [x2 - 1, y2] not in path and grid[x2 - 1][y2].is_room():  # Left
            path.append([x2 - 1, y2])
            grid[x2][y2].reset()

        if text == "D" and [x2, y2 + 1] not in path and grid[x2][y2 + 1].is_room():  # Down
            path.append([x2, y2 + 1])
            grid[x2][y2].reset()

        if text == "U" and [x2, y2 - 1] not in path and grid[x2][y2 - 1].is_room():  # Up
            path.append([x2, y2 - 1])
            grid[x2][y2].reset()

        for room in path:  # Checks for walls around x,y
            room_x = room[0]
            room_y = room[1]

            if room_x < ROWS - 2:
                if grid[room_x + 1][room_y].is_barrier() and grid[room_x + 2][room_y].is_room() and [room_x + 2, room_y] not in path and [room_x + 1, room_y, "R"] not in walls:  # Right
                    if grid[room_x + 2][room_y].is_room():
                        walls.append([room_x + 1, room_y, "R"])

            if 1 < room_x:
                if grid[room_x - 1][room_y].is_barrier() and grid[room_x - 2][room_y].is_room() and [room_x - 2, room_y] not in path and [room_x - 1, room_y, "L"] not in walls:  # Left
                    if grid[room_x - 2][room_y].is_room():
                        walls.append([room_x - 1, room_y, "L"])

            if room_y < ROWS - 2:
                if grid[room_x][room_y + 1].is_barrier() and grid[room_x][room_y + 2].is_room() and [room_x, room_y + 2] not in path and [room_x, room_y + 1, "D"] not in walls:  # Down
                    if grid[room_x][room_y + 2].is_room():
                        walls.append([room_x, room_y + 1, "D"])

            if 1 < room_y:
                if grid[room_x][room_y - 1].is_barrier() and grid[room_x][room_y - 2].is_room() and [room_x, room_y - 2] not in path and [room_x, room_y - 1, "U"] not in walls:  # Up
                    if grid[room_x][room_y - 2].is_room():
                        walls.append([room_x, room_y - 1, "U"])

        walls.remove(wall)
        draw(win, grid, ROWS, width, length)


def recursive_backtracker(grid, ROWS, win, width, FPS, length):  # Recursive Backtracking algorithm for generating a maze
    walls = []
    path = []
    visited = []

    # Creating a walls and rooms
    for i in range(ROWS):
        if i % 2 == 0:
            for x in grid[i]:
                x.make_barrier()
            for x in range(ROWS):
                grid[x][i].make_barrier()

    x = 1
    y = 1

    path.append([x, y])
    visited.append([x, y])

    # Checks for walls around x,y

    if x < ROWS - 1:
        if grid[x + 1][y].is_barrier() and grid[x + 2][y].is_room() and [x + 2, y] not in visited and [x + 1, y, "R"] not in walls:  # Right
            walls.append([x + 1, y, "R"])

    if 1 < x:
        if grid[x - 1][y].is_barrier() and grid[x - 2][y].is_room() and [x - 2, y] not in visited and [x - 1, y, "L"] not in walls:  # Left
            walls.append([x - 1, y, "L"])

    if y < ROWS - 1:
        if grid[x][y + 1].is_barrier() and grid[x][y + 2].is_room() and [x, y + 2] not in visited and [x, y + 1, "D"] not in walls:  # Down
            walls.append([x, y + 1, "D"])

    if 1 < y:
        if grid[x][y - 1].is_barrier() and grid[x][y - 2].is_room() and [x, y - 2] not in visited and [x, y - 1, "U"] not in walls:  # Up
            walls.append([x, y - 1, "U"])

    wall = random.choice(walls)  # Picks random wall from walls list

    x2, y2, text = wall

    if text == "R" and [x2 + 1, y2] not in visited and grid[x2 + 1][y2].is_room():  # Right
        path.append([x2 + 1, y2])
        visited.append(([x2 + 1, y2]))
        grid[x2][y2].reset()

    if text == "L" and [x2 - 1, y2] not in visited and grid[x2 - 1][y2].is_room():  # Left
        path.append([x2 - 1, y2])
        visited.append(([x2 - 1, y2]))
        grid[x2][y2].reset()

    if text == "D" and [x2, y2 + 1] not in visited and grid[x2][y2 + 1].is_room():  # Down
        path.append([x2, y2 + 1])
        visited.append(([x2, y2 + 1]))
        grid[x2][y2].reset()

    if text == "U" and [x2, y2 - 1] not in visited and grid[x2][y2 - 1].is_room():  # Up
        path.append([x2, y2 - 1])
        visited.append(([x2, y2 - 1]))
        grid[x2][y2].reset()

    while path:
        walls = []
        x, y = path[-1]  # Picks latest room from path list

        if x < ROWS - 2:
            if grid[x + 1][y].is_barrier() and grid[x + 2][y].is_room() and [x + 2, y] not in visited and [x + 1, y, "R"] not in walls:  # Right
                walls.append([x + 1, y, "R"])

        if 1 < x:
            if grid[x - 1][y].is_barrier() and grid[x - 2][y].is_room() and [x - 2, y] not in visited and [ x - 1, y, "L"] not in walls:  # Left
                walls.append([x - 1, y, "L"])

        if y < ROWS - 2:
            if grid[x][y + 1].is_barrier() and grid[x][y + 2].is_room() and [x, y + 2] not in visited and [x, y + 1, "D"] not in walls:  # Down
                walls.append([x, y + 1, "D"])

        if 1 < y:
            if grid[x][y - 1].is_barrier() and grid[x][y - 2].is_room() and [x,y - 2] not in visited and [x, y - 1, "U"] not in walls:  # Up
                walls.append([x, y - 1, "U"])

        if walls == []:
            path.remove(path[-1])
            continue

        wall = random.choice(walls)  # Picks a random wall that is next to the room

        x2, y2, text = wall

        no_rooms = True

        if text == "R" and [x2 + 1, y2] not in visited and grid[x2 + 1][y2].is_room():  # Right
            path.append([x2 + 1, y2])
            visited.append(([x2 + 1, y2]))
            grid[x2][y2].reset()
            no_rooms = False

        if text == "L" and [x2 - 1, y2] not in visited and grid[x2 - 1][y2].is_room():  # Left
            path.append([x2 - 1, y2])
            visited.append(([x2 - 1, y2]))
            grid[x2][y2].reset()
            no_rooms = False

        if text == "D" and [x2, y2 + 1] not in visited and grid[x2][y2 + 1].is_room():  # Down
            path.append([x2, y2 + 1])
            visited.append(([x2, y2 + 1]))
            grid[x2][y2].reset()
            no_rooms = False

        if text == "U" and [x2, y2 - 1] not in visited and grid[x2][y2 - 1].is_room():  # Up
            path.append([x2, y2 - 1])
            visited.append(([x2, y2 - 1]))
            grid[x2][y2].reset()
            no_rooms = False

        if no_rooms:
            path.remove(path[-1])
            continue

        clock.tick(FPS)
        draw(win, grid, ROWS, width, length)


def main(win, width):  # Main function
    ROWS = 40

    FPS = 60

    grid = make_drig(ROWS, width)

    start = None
    end = None
    point1 = None
    point2 = None
    point3 = None

    length = 0

    Six = True
    Ten = True
    Twenty = True
    Fourty = True
    Eightty = True
    OnehundredSixty = True
    TwoHundred = True

    Slow = True
    Average = True
    Fast = True
    UltraFast = True

    run = True
    while run:  # main while loop
        clock.tick(30)

        event_list = pygame.event.get()

        selected_option = mazes.update(event_list)
        if selected_option >= 0:
            mazes.main = mazes.options[selected_option]

        selected_option2 = sizes.update(event_list)
        if selected_option2 >= 0:
            sizes.main = sizes.options[selected_option2]

        selected_option3 = speeds.update(event_list)
        if selected_option3 >= 0:
            speeds.main = speeds.options[selected_option3]

        # Draws window
        draw(win, grid, ROWS, width, length)
        mazes.draw(WIN)
        sizes.draw(WIN)
        speeds.draw(WIN)
        pygame.display.flip()

        for event in event_list:
            if event.type == pygame.QUIT:
                run = False

            if pygame.mouse.get_pressed()[1]: #
                pos = pygame.mouse.get_pos()
                row, col, x = get_clicked_pos(pos, ROWS, width)
                if x >= 0:
                    spot = grid[row][col]
                    if not start and spot != end:
                        start = spot
                        start.make_start()

                    elif not end and spot != start:
                        end = spot
                        end.make_end()

                    elif spot != end and spot != start:
                        spot.make_barrier()

            elif pygame.mouse.get_pressed()[2]:
                pos = pygame.mouse.get_pos()
                row, col, x = get_clicked_pos(pos, ROWS, width)
                if x >= 0:
                    spot = grid[row][col]
                    spot.reset()
                    if spot == start:
                        start = None
                    elif spot == end:
                        end = None
                    elif spot == point1:
                        point1 = None
                    elif spot == point2:
                        point2 = None
                    elif spot == point3:
                        point3 = None


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and start and end:
                    length = 0
                    path = []
                    for row in grid:
                        for spot in row:
                            spot.update_neighbors(grid)

                    length = 0
                    if point1:
                        algorithm(lambda: draw(win, grid, ROWS, width, length), grid, start, point1, path, FPS)
                        point1.make_point("1")

                        if point2:
                            algorithm(lambda: draw(win, grid, ROWS, width, length), grid, point1, point2, path, FPS)
                            point2.make_point("2")

                            if point3:
                                algorithm(lambda: draw(win, grid, ROWS, width, length), grid, point2, point3, path, FPS)
                                algorithm(lambda: draw(win, grid, ROWS, width, length), grid, point3, end, path, FPS)
                                point3.make_point("3")

                            else:
                                algorithm(lambda: draw(win, grid, ROWS, width, length), grid, point2, end, path, FPS)

                        else:
                            algorithm(lambda: draw(win, grid, ROWS, width, length), grid, point1, end, path, FPS)

                    else:
                        algorithm(lambda: draw(win, grid, ROWS, width, length), grid, start, end, path, FPS)

                    for x in path:
                        x.make_path()
                        length += 1
                    end.make_end()
                    start.make_start()

                    if point1:
                        point1.make_point("1")
                    if point2:
                        point2.make_point("2")
                    if point3:
                        point3.make_point("3")

                if event.key == pygame.K_c:  # Clears the grid
                    start = None
                    end = None
                    point1 = None
                    point2 = None
                    point3 = None
                    length = 0
                    grid = make_drig(ROWS, width)

                if event.key == pygame.K_g:  # Starts generating a maze
                    if mazes.main == "Prim's":
                        prims(grid, ROWS, win, width, FPS, length)
                    if mazes.main == "Recursive Backtracker":
                        recursive_backtracker(grid, ROWS, win, width, FPS, length)
                    if mazes.main == "Random":
                        random_maze(grid, ROWS)

                if event.key == pygame.K_p:  # makes a point to which algorithm must go to, for example (start>point1>end)
                    pos = pygame.mouse.get_pos()
                    row, col, x = get_clicked_pos(pos, ROWS, width)
                    if x >= 0:
                        spot = grid[row][col]
                        if start and end:
                            if not point1 and spot != end and spot != start:
                                point1 = spot
                                point1.make_point("1")

                            if point1:
                                if not point2 and spot != end and spot != start and spot != point1:
                                    point2 = spot
                                    point2.make_point("2")

                                if point2:
                                    if not point3 and spot != end and spot != start and spot != point1 and spot != point2:
                                        point3 = spot
                                        point3.make_point("3")


            # If statements for the lists
            if sizes.main == "6x6" and Six:
                ROWS = 5
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                Six = False
                Ten = True
                Twenty = True
                Fourty = True
                Eightty = True
                OnehundredSixty = True
                TwoHundred = True

            if sizes.main == "10x10" and Ten:
                ROWS = 10
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                Ten = False
                Six = True
                Twenty = True
                Fourty = True
                Eightty = True
                OnehundredSixty = True
                TwoHundred = True

            if sizes.main == "20x20" and Twenty:
                ROWS = 20
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                Twenty = False
                Six = True
                Ten = True
                Fourty = True
                Eightty = True
                OnehundredSixty = True
                TwoHundred = True

            if sizes.main == "40x40" and Fourty:
                ROWS = 40
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                Fourty = False
                Six = True
                Ten = True
                Twenty = True
                Eightty = True
                OnehundredSixty = True
                TwoHundred = True

            if sizes.main == "80x80" and Eightty:
                ROWS = 80
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                Eightty = False
                Six = True
                Ten = True
                Twenty = True
                Fourty = True
                OnehundredSixty = True
                TwoHundred = True

            if sizes.main == "160x160" and OnehundredSixty:
                ROWS = 160
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                OnehundredSixty = False
                Six = True
                Ten = True
                Twenty = True
                Fourty = True
                Eightty = True
                TwoHundred = True

            if sizes.main == "200x200" and TwoHundred:
                ROWS = 200
                start = None
                end = None
                point1 = None
                point2 = None
                point3 = None
                grid = make_drig(ROWS, width)
                TwoHundred = False
                Six = True
                Ten = True
                Twenty = True
                Fourty = True
                Eightty = True
                OnehundredSixty = True

            if speeds.main == "Slow" and Slow:
                FPS = 1
                Slow = False
                Average = True
                Fast = True
                UltraFast = True

            if speeds.main == "Average" and Average:
                FPS = 15
                Slow = True
                Average = False
                Fast = True
                UltraFast = True

            if speeds.main == "Fast" and Fast:
                FPS = 60
                Slow = True
                Average = True
                Fast = False
                UltraFast = True

            if speeds.main == "Ultra Fast" and UltraFast:
                FPS = 0
                Slow = False
                Average = True
                Fast = True
                UltraFast = False

    pygame.quit()


main(WIN, WIDTH)