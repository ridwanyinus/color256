#!/usr/bin/env python3

import sys
import os
import random
import time
import termios
import tty
import select
import signal

PIPE_SET = "████▀▀███▀█▀▀██▀"
FRAME_RATE = 75
HUE_UPDATE_INTERVAL = 5
FADE_START_FRAMES = 100
BASE_FADE_DURATION = 1000
HUE_SPEED = 0.5
MIN_STRAIGHT_LENGTH = 2
MAX_STRAIGHT_LENGTH = 10

resize_flag = False

def handle_resize(*_):
    global resize_flag
    resize_flag = True

class Pipe:
    def __init__(self, w, h):
        self.x = w // 2
        self.y = h // 2
        self.dir = 0
        self.hue = random.random() * 360
        self.straight_length = random.randint(
            MIN_STRAIGHT_LENGTH, MAX_STRAIGHT_LENGTH)

def hsv_to_rgb(h, s, v):
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255)
    )


def rgb_to_color_index(r, g, b):
    r = max(0, min(5, round(r * 5 / 255)))
    g = max(0, min(5, round(g * 5 / 255)))
    b = max(0, min(5, round(b * 5 / 255)))
    return 16 + 36 * r + 6 * g + b


def color_index_to_rgb(idx):
    idx = idx - 16
    r = ((idx // 36) % 6) * 255 // 5
    g = ((idx // 6) % 6) * 255 // 5
    b = (idx % 6) * 255 // 5
    return r, g, b


def fade_color(color_idx, fade_amount):
    r, g, b = color_index_to_rgb(color_idx)
    r = int(r * (1 - fade_amount))
    g = int(g * (1 - fade_amount))
    b = int(b * (1 - fade_amount))
    return rgb_to_color_index(r, g, b)


def find_empty_square(grid, w, h, pipe_x, pipe_y, grid_size=4):
    closest = None
    closest_dist = float('inf')
    
    for grid_y in range(0, h, grid_size):
        for grid_x in range(0, w, grid_size * 2):
            if grid_y + grid_size > h or grid_x + grid_size > w:
                continue
            
            empty = True
            for dy in range(grid_size):
                for dx in range(grid_size):
                    if grid[grid_y + dy][grid_x + dx] is not None:
                        empty = False
                        break
                if not empty:
                    break
            
            if empty:
                center_x = grid_x + grid_size // 2
                center_y = grid_y + grid_size // 2
                
                dist = abs(center_x - pipe_x) + abs(center_y - pipe_y)
                
                if dist < closest_dist:
                    closest_dist = dist
                    closest = (center_x, center_y)
    
    return closest


def get_turn_direction(pipe, target_x, target_y):
    if pipe.dir % 2 == 1:
        if target_y < pipe.y:
            return 0
        elif target_y > pipe.y:
            return 2
        else:
            return random.choice([(pipe.dir + 3) % 4, (pipe.dir + 1) % 4])
    else:
        if target_x < pipe.x:
            return 3
        elif target_x > pipe.x:
            return 1
        else:
            return random.choice([(pipe.dir + 3) % 4, (pipe.dir + 1) % 4])


def calculate_fade_duration(w, h):
    screen_area = w * h
    base_area = 80 * 24
    scale_factor = screen_area / base_area
    return int(BASE_FADE_DURATION * scale_factor)


def get_terminal_size():
    rows, cols = os.popen('stty size', 'r').read().split()
    return int(cols), int(rows)


def main():
    global resize_flag
    
    signal.signal(signal.SIGWINCH, handle_resize)
    
    w, h = get_terminal_size()
    fade_duration = calculate_fade_duration(w, h)
    
    grid = [[None for _ in range(w)] for _ in range(h)]
    
    tty.setcbreak(sys.stdin.fileno())
    
    print("\033[?1049h", end="")
    print("\033[?25l", end="")
    print("\033[2J", end="")
    sys.stdout.flush()
    
    pipe = Pipe(w, h)
    frame = 0
    
    while True:
            if resize_flag:
                resize_flag = False
                w, h = get_terminal_size()
                fade_duration = calculate_fade_duration(w, h)
                grid = [[None for _ in range(w)] for _ in range(h)]
                pipe = Pipe(w, h)
                frame = 0
                print("\033[2J", end="")
                sys.stdout.flush()
                continue
            
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key in ['q', '\x1b']:
                    break
            
            pipe.hue = (pipe.hue + HUE_SPEED) % 360
            
            if pipe.dir % 2 == 0 and frame % 2 == 1:
                pass
            else:
                next_dir = pipe.dir
                
                pipe.straight_length -= 1
                if pipe.straight_length <= 0:
                    target = find_empty_square(grid, w, h, pipe.x, pipe.y)
                    
                    if target is not None:
                        target_x, target_y = target
                        next_dir = get_turn_direction(pipe, target_x, target_y)
                    else:
                        next_dir = random.choice([(pipe.dir + 3) % 4, (pipe.dir + 1) % 4])
                    
                    pipe.straight_length = random.randint(
                        MIN_STRAIGHT_LENGTH, MAX_STRAIGHT_LENGTH)
                
                r, g, b = hsv_to_rgb(pipe.hue, 1.0, 1.0)
                color_idx = rgb_to_color_index(r, g, b)
                
                char = PIPE_SET[pipe.dir * 4 + next_dir]
                
                existing = grid[pipe.y][pipe.x]
                
                bg_color = None
                bg_frame = None
                fg_frame = frame
                
                if existing is not None:
                    existing_char, existing_fg, existing_bg, existing_fg_frame, existing_bg_frame = existing
                    
                    if existing_char == '█' and char == '▀':
                        bg_color = existing_fg
                        bg_frame = existing_fg_frame
                    elif existing_char == '▀' and char == '▀':
                        bg_color = existing_bg
                        bg_frame = existing_bg_frame
                
                esc = f"\033[{pipe.y + 1};{pipe.x + 1}H\033[1m\033[38;5;{color_idx}m"
                if bg_color is not None:
                    esc += f"\033[48;5;{bg_color}m"
                esc += f"{char}\033[0m"
                
                print(esc, end="")
                
                grid[pipe.y][pipe.x] = (char, color_idx, bg_color, fg_frame, bg_frame)
                
                pipe.dir = next_dir
                
                if pipe.dir % 2 == 1:
                    pipe.x += -pipe.dir + 2
                else:
                    pipe.y += pipe.dir - 1
                
                pipe.x = pipe.x % w
                pipe.y = pipe.y % h
            
            for y in range(h):
                for x in range(w):
                    cell = grid[y][x]
                    if cell is None:
                        continue
                    
                    char, fg_color, bg_color, fg_frame_born, bg_frame_born = cell
                    
                    fg_age = frame - fg_frame_born
                    bg_age = frame - bg_frame_born if bg_frame_born is not None else 0
                    
                    if fg_age < FADE_START_FRAMES and (bg_color is None or bg_age < FADE_START_FRAMES):
                        continue
                    
                    fg_fade = min(1.0, (fg_age - FADE_START_FRAMES) / fade_duration) if fg_age >= FADE_START_FRAMES else 0.0
                    bg_fade = min(1.0, (bg_age - FADE_START_FRAMES) / fade_duration) if bg_color and bg_age >= FADE_START_FRAMES else 0.0
                    
                    if fg_fade >= 1.0 and (bg_color is None or bg_fade >= 1.0):
                        print(f"\033[{y + 1};{x + 1}H \033[0m", end="")
                        grid[y][x] = None
                        continue
                    
                    faded_fg = fade_color(fg_color, fg_fade)
                    esc = f"\033[{y + 1};{x + 1}H\033[1m\033[38;5;{faded_fg}m"
                    
                    if bg_color is not None:
                        faded_bg = fade_color(bg_color, bg_fade)
                        esc += f"\033[48;5;{faded_bg}m"
                    
                    esc += f"{char}\033[0m"
                    print(esc, end="")
            
            sys.stdout.flush()
            frame += 1
            time.sleep(1.0 / FRAME_RATE)


if __name__ == "__main__":
    old_settings = None
    try:
        old_settings = termios.tcgetattr(sys.stdin)
        main()
    except KeyboardInterrupt:
        pass
    finally:
        if old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("\033[?25h", end="")
        print("\033[?1049l", end="")
        print("\033[0m", end="")
        sys.stdout.flush()
