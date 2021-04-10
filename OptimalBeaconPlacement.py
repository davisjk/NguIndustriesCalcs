#! /usr/bin/python3

import logging
import sys
from copy import deepcopy
from math import ceil

class NguIndustriesLayouts:
  # CAUTION, commented out debug messages create multiple GB of logs and drastically slow performance
  logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-5s %(message)s', level=logging.DEBUG)
  logger = logging.getLogger()
  files = ['TutorialIslandSmall.txt', 'TutorialIslandMain.txt']#, 'FleshWorld.txt']
  write_each_new_best = True
  empty = '0'
  bb = 'b'
  bb_bonus = 0.4
  bb_threshold = ceil(1 / bb_bonus)
  bk = 'B'
  bk_bonus = 0.35
  bk_threshold = ceil(1 / bk_bonus)
  pb = 'p'
  pb_bonus = 0.3
  pb_threshold = ceil(1 / pb_bonus)
  pk = 'K'
  pk_bonus = 0.35
  pk_threshold = ceil(1 / pk_bonus)

  def __init__(self):
    pass

  def print_beacon_layouts(self):
    self.logger.info(f'Empty = {self.empty}')
    self.logger.info(f'Blue Box = {self.bb}')
    self.logger.info(f'Pink Box = {self.pb}')
    self.logger.info(f'Blue Knight = {self.bk}')
    self.logger.info(f'Pink Knight = {self.pk}')
    for filename in self.files:
      self.logger.info(f'Finding best layouts for {filename}')
      self._read_file(filename)
      self.base_filename = filename
      self._create_layouts()

  def _read_file(self, filename):
    self.base_layout = []
    with open(filename, 'r') as f:
      for line in f.readlines():
        self.base_layout.append([space for space in line if space != '\n'])
    self._pad_layout(self.base_layout)
    self.base_value = self._layout_value(self.base_layout)

  def _pad_layout(cls, layout):
    max_length =  max([len(line) for line in layout])
    for line in layout:
      line += [''] * (max_length - len(line) + 2)
      line.insert(0, '')
      line.insert(0, '')
    layout += [[''] * (max_length + 4)] * 2
    layout.insert(0, [''] * (max_length + 4))
    layout.insert(0, [''] * (max_length + 4))

  def _create_layouts(self):
    # common setup
    self.x_max = len(self.base_layout[0])
    self.y_max = len(self.base_layout)
    # layout with speed
    # self.options = [self.empty, self.bb, self.bk, self.pb, self.pk]
    # self.current_filename = '{0}_best.{1}'.format(*self.base_filename.split('.', 1))
    # self._create_layout()
    # self.logger.info('Best possible layout ignoring speed caps and rounding errors:')
    # self.logger.info(f'Effective multiplier to base production with this layout is {self.best_value/self.base_value}')
    # self.logger.info('\n' + self._pretty_format_layout(self.best_layout))
    # layout without speed
    self.options = [self.empty, self.pb, self.pk]
    self.current_filename = '{0}_speedless.{1}'.format(*self.base_filename.split('.', 1))
    self._create_layout()
    self.logger.info('Best layout for buildings that have reached the speed cap (still ignoring rounding errors):')
    self.logger.info(f'Effective multiplier to base production with this layout is {self.best_value/self.base_value}')
    self.logger.info('\n' + self._pretty_format_layout(self.best_layout))

  def _create_layout(self):
    # reset and recurse
    self.permutations = 0
    self.best_layout = []
    self.best_value = 0
    self._recurse_layout(deepcopy(self.base_layout), 2, 2)
    self.logger.debug(f'Tried {self.permutations} permutations for {self.current_filename}')
    if not self.write_each_new_best:
      self._write_to_file(self.best_layout, self.current_filename)

  def _recurse_layout(self, layout, x, y):
    # without logic to eliminate permutations early, this will check about 10^158
    while layout[y][x] != self.empty and (x < self.x_max - 2 or y < self.y_max - 2):
      # self.logger.debug(f'Checking x: {x}, y: {y}')
      if x >= self.x_max - 2:
        x = 2
        y += 1
      else:
        x += 1
    # self.logger.debug(f'Checking x: {x}, y: {y}')
    if layout[y][x] == self.empty:
      must_be_empty = self._is_counterproductive(layout, x, y)
      # try all 4 beacons and no beacon
      for option in self.options:
        layout[y][x] = option
        if option == self.empty:
          # take advantage of empty spaces always being checked first
          empty_value = self._layout_value(layout)
          current_value = empty_value
        else:
          # check if any beacons affecting this space would lose their usefulness
          if must_be_empty:
            break
          # narrow down the tests a bit by checking if this beacon would be useless
          if (option == self.bb and self._box_touching_count(layout, x, y) < self.bb_threshold) or \
             (option == self.pb and self._box_touching_count(layout, x, y) < self.pb_threshold) or \
             (option == self.bk and self._knight_touching_count(layout, x, y) < self.bk_threshold) or \
             (option == self.pk and self._knight_touching_count(layout, x, y) < self.pk_threshold):
            continue
          current_value = self._layout_value(layout)
        # narrow down a bit more
        if current_value >= empty_value:
          # self.logger.debug(f'Trying x: {x}, y: {y}, beacon: {option}')
          self._recurse_layout(deepcopy(layout), x + 1, y)
    else:
      # last recursion
      # self.logger.debug(f'Checking layout number {self.permutations}')
      self.permutations += 1
      value = self._layout_value(layout)
      if value > self.best_value:
        self.best_layout = deepcopy(layout)
        self.best_value = value
        self.logger.debug(f'New value at permutation {self.permutations}: {value}')
        if self.write_each_new_best:
          self._write_to_file(self.best_layout, self.current_filename)

  def _is_counterproductive(cls, layout, x, y):
    for k in range(-2, 2):
      for j in range(-2, 2):
        if j == k == 0: continue
        elif abs(j) == abs(k) == 2: continue
        elif abs(j) == 2 or abs(k) == 2:
          if layout[y+k][x+j] == cls.bk and cls._knight_touching_count(layout, x + j, y + k) < cls.bk_threshold + 1: return True
          elif layout[y+k][x+j] == cls.pk and cls._knight_touching_count(layout, x + j, y + k) < cls.pk_threshold + 1: return True
        elif layout[y+k][x+j] == cls.bb and cls._box_touching_count(layout, x + j, y + k) < cls.bb_threshold + 1: return True
        elif layout[y+k][x+j] == cls.pb and cls._box_touching_count(layout, x + j, y + k) < cls.pb_threshold + 1: return True

  def _box_touching_count(cls, layout, x, y):
    return (1 if layout[y-1][x] == cls.empty else 0) + \
           (1 if layout[y-1][x-1] == cls.empty else 0) + \
           (1 if layout[y][x-1] == cls.empty else 0) + \
           (1 if layout[y+1][x-1] == cls.empty else 0) + \
           (1 if layout[y+1][x] == cls.empty else 0) + \
           (1 if layout[y+1][x+1] == cls.empty else 0) + \
           (1 if layout[y][x+1] == cls.empty else 0) + \
           (1 if layout[y-1][x+1] == cls.empty else 0)

  def _knight_touching_count(cls, layout, x, y):
    return (1 if layout[y-2][x-1] == cls.empty else 0) + \
           (1 if layout[y-1][x-2] == cls.empty else 0) + \
           (1 if layout[y+2][x-1] == cls.empty else 0) + \
           (1 if layout[y+1][x-2] == cls.empty else 0) + \
           (1 if layout[y-2][x+1] == cls.empty else 0) + \
           (1 if layout[y-1][x+2] == cls.empty else 0) + \
           (1 if layout[y+2][x+1] == cls.empty else 0) + \
           (1 if layout[y+1][x+2] == cls.empty else 0)

  def _layout_value(cls, layout):
    total_value = 0
    x_max = len(layout[0])
    y_max = len(layout)
    for y in range(2, y_max - 2):
      for x in range(2, x_max - 2):
        beacons = [0, 0, 0, 0] # [bb, bk, pb, pk]
        if layout[y][x] == cls.empty:
          # check 8 orthagonal and 8 "knight moves"
          # layouts are padded so none of these should be out of range
          # blue boxes
          if layout[y-1][x] == cls.bb: beacons[0] += 1
          if layout[y-1][x-1] == cls.bb: beacons[0] += 1
          if layout[y][x-1] == cls.bb: beacons[0] += 1
          if layout[y+1][x-1] == cls.bb: beacons[0] += 1
          if layout[y+1][x] == cls.bb: beacons[0] += 1
          if layout[y+1][x+1] == cls.bb: beacons[0] += 1
          if layout[y][x+1] == cls.bb: beacons[0] += 1
          if layout[y-1][x+1] == cls.bb: beacons[0] += 1
          # pink boxes
          if layout[y-1][x] == cls.pb: beacons[2] += 1
          if layout[y-1][x-1] == cls.pb: beacons[2] += 1
          if layout[y][x-1] == cls.pb: beacons[2] += 1
          if layout[y+1][x-1] == cls.pb: beacons[2] += 1
          if layout[y+1][x] == cls.pb: beacons[2] += 1
          if layout[y+1][x+1] == cls.pb: beacons[2] += 1
          if layout[y][x+1] == cls.pb: beacons[2] += 1
          if layout[y-1][x+1] == cls.pb: beacons[2] += 1
          # blue knights
          if layout[y-2][x-1] == cls.bk: beacons[1] += 1
          if layout[y-1][x-2] == cls.bk: beacons[1] += 1
          if layout[y+2][x-1] == cls.bk: beacons[1] += 1
          if layout[y+1][x-2] == cls.bk: beacons[1] += 1
          if layout[y-2][x+1] == cls.bk: beacons[1] += 1
          if layout[y-1][x+2] == cls.bk: beacons[1] += 1
          if layout[y+2][x+1] == cls.bk: beacons[1] += 1
          if layout[y+1][x+2] == cls.bk: beacons[1] += 1
          # pink knights
          if layout[y-2][x-1] == cls.pk: beacons[3] += 1
          if layout[y-1][x-2] == cls.pk: beacons[3] += 1
          if layout[y+2][x-1] == cls.pk: beacons[3] += 1
          if layout[y+1][x-2] == cls.pk: beacons[3] += 1
          if layout[y-2][x+1] == cls.pk: beacons[3] += 1
          if layout[y-1][x+2] == cls.pk: beacons[3] += 1
          if layout[y+2][x+1] == cls.pk: beacons[3] += 1
          if layout[y+1][x+2] == cls.pk: beacons[3] += 1
          value = cls._space_value(beacons)
          # cls.logger.debug(f'x: {x}, y: {y}, val: {value}')
          total_value += value
    # cls.logger.debug(f'Total: {total_value}')
    # cls.logger.debug('\n' + cls._pretty_format_layout(layout))
    return total_value

  def _space_value(cls, beacons):
    return (1 + (cls.bb_bonus * beacons[0]) + (cls.bk_bonus * beacons[2])) * (1 + (cls.pb_bonus * beacons[1]) + (cls.pk_bonus * beacons[3]))

  def _write_to_file(cls, layout, filename):
    with open(filename, 'w') as f:
      f.write(cls._pretty_format_layout(layout))

  def _pretty_format_layout(cls, layout):
    return '\n'.join([''.join(line) for line in layout if ''.join(line)])

if __name__ == '__main__':
  layouts = NguIndustriesLayouts()
  layouts.print_beacon_layouts()
  layouts.logger.info('Completed creating layouts')
