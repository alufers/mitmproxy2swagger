# -*- coding: utf-8 -*-
import sys

ANSI_RGB = "\033[38;2;{};{};{}m"
ANSI_RGB_BG = "\033[48;2;{};{};{}m"
ANSI_RED = "\033[31m"
ANSI_RESET = "\033[0m"

RAINBOW_COLORS = [
    (255, 0, 0),
    (255, 127, 0),
    (255, 255, 0),
    (127, 255, 0),
    (0, 255, 0),
    (0, 255, 127),
    (0, 255, 255),
    (0, 127, 255),
    (0, 0, 255),
    (127, 0, 255),
    (255, 0, 255),
    (255, 0, 127),
]


def rgb_interpolate(start, end, progress):
    return tuple(int(start[i] + (end[i] - start[i]) * progress) for i in range(3))


# take a value from 0 to 1 and return an interpolated color from the rainbow
def rainbow_at_position(progress):
    idx_a = int(progress * float(len(RAINBOW_COLORS) - 1))
    idx_b = idx_a + 1
    return rgb_interpolate(
        RAINBOW_COLORS[idx_a],
        RAINBOW_COLORS[idx_b],
        progress * float(len(RAINBOW_COLORS) - 1) - idx_a,
    )


def print_progress_bar(progress=0.0):
    sys.stdout.write("\r")
    progress_bar_contents = ""
    PROGRESS_LENGTH = 30
    blocks = ["▉", "▊", "▋", "▌", "▍", "▎", "▏"]

    for i in range(PROGRESS_LENGTH):
        interpolated = rainbow_at_position(i / PROGRESS_LENGTH)
        # check if should print a full block
        if i < int(progress * PROGRESS_LENGTH):
            interpolated_2nd_half = rainbow_at_position((i + 0.5) / PROGRESS_LENGTH)
            progress_bar_contents += ANSI_RGB.format(*interpolated)
            progress_bar_contents += ANSI_RGB_BG.format(*interpolated_2nd_half)
            progress_bar_contents += "▌"
        # check if should print a non-full block
        elif i < int((progress * PROGRESS_LENGTH) + 0.5):
            progress_bar_contents += ANSI_RESET
            progress_bar_contents += ANSI_RGB.format(*interpolated)
            progress_bar_contents += blocks[
                int((progress * PROGRESS_LENGTH) + 0.5) - i - 1
            ]
        # otherwise, print a space
        else:
            progress_bar_contents += ANSI_RESET
            progress_bar_contents += " "

    progress_bar_contents += ANSI_RESET
    sys.stdout.write("[{}] {:.1f}%".format(progress_bar_contents, progress * 100))
    sys.stdout.flush()
