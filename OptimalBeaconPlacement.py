#! /bin/python3

import logging
import math
import sys
import time
from copy import deepcopy

class NguIndustriesLayouts:
  # CAUTION, commented out debug messages create multiple GB of logs and drastically slow performance
  logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-5s %(message)s', level=logging.DEBUG)
  logger = logging.getLogger()
  # default values
  files = ['TutorialIslandMain.txt', 'FleshWorld.txt']
  write_file = False
  write_each_new_best = True
  with_blue = False
  with_pink = True
  with_boxes = True
  with_knights = False
  with_arrows = False #TODO
  with_walls = False #TODO
  efficiency_buffer = 1.12
  empty = '0'
  bb = 'b'
  bb_bonus = 0.4
  bb_threshold = math.ceil(1 / bb_bonus)
  bk = 'B'
  bk_bonus = 0.35
  bk_threshold = math.ceil(1 / bk_bonus)
  pb = 'p'
  pb_bonus = 0.3
  pb_threshold = math.ceil(1 / pb_bonus)
  pk = 'K'
  pk_bonus = 0.35
  pk_threshold = math.ceil(1 / pk_bonus)

  def __init__(self):
    if len(sys.argv) > 1:
      self.files = sys.argv[1:]
    self.logger.info(f'Empty = {self.empty}')
    self._one_time_setup()

  def print_beacon_layouts(self):
    for filename in self.files:
      self.base_filename = filename
      self.logger.info(f'Finding best layout for {filename} with beacons: {self.beacons}')
      self._read_file(filename)
      self._repeated_setup()
      self._create_layout()
      self.logger.info(f'Approximate best calculated layout with beacons: {self.beacons}')
      self.logger.info(f'Effective bonus to base production with this layout is {round((100 * self.best_value/self.base_value) - 100, 2)}% with a total production of {self.best_value}')
      self.logger.info('\n' + self._pretty_format_layout(self.best_layout))

  def _read_file(self, filename):
    self.base_layout = []
    with open(filename, 'r') as f:
      for line in f.readlines():
        self.base_layout.append([space for space in line if space != '\n'])

  def _pad_layout(cls, layout):
    max_length =  max([len(line) for line in layout])
    for line in layout:
      line += [''] * (max_length - len(line) + 2)
      line.insert(0, '')
      line.insert(0, '')
    layout += [[''] * (max_length + 4)] * 2
    layout.insert(0, [''] * (max_length + 4))
    layout.insert(0, [''] * (max_length + 4))

  def _one_time_setup(self):
    self.never_bb = True
    self.never_pb = True
    self.never_bk = True
    self.never_pk = True
    self.beacons = [self.empty]
    self.filename_extras = ""
    if self.with_blue:
      if self.with_boxes:
        self.never_bb = False
        self.beacons.append(self.bb)
        self.filename_extras += "bb_"
        self.logger.info(f'Blue Box = {self.bb}')
      if self.with_knights:
        self.never_bk = False
        self.beacons.append(self.bk)
        self.filename_extras += "bk_"
        self.logger.info(f'Blue Knight = {self.bk}')
    if self.with_pink:
      if self.with_boxes:
        self.never_pb = False
        self.beacons.append(self.pb)
        self.filename_extras += "pb_"
        self.logger.info(f'Pink Box = {self.pb}')
      if self.with_knights:
        self.never_pk = False
        self.beacons.append(self.pk)
        self.filename_extras += "pk_"
        self.logger.info(f'Pink Knight = {self.pk}')
    self.filename_extras += str(math.floor(time.time()))
    self.logger.info(f'Efficiency buffer = {round((self.efficiency_buffer - 1) * 100, 2)}%')

  def _repeated_setup(self):
    self._pad_layout(self.base_layout)
    self.base_value = self._layout_value(self.base_layout)
    self.beacon_efficiency_ratio = 0.116927 * self.base_value * math.exp(-0.039872 * self.base_value)
    self.logger.info(f'Beacon efficiency ratio = {self.beacon_efficiency_ratio}')
    self.x_max = len(self.base_layout[0])
    self.y_max = len(self.base_layout)
    self.permutations = 0
    self.best_layout = self.base_layout
    self.best_value = self.base_value
    self.current_filename = '{0}_{2}.{1}'.format(*self.base_filename.split('.', 1), self.filename_extras)

  def _create_layout(self):
    self._recurse_layout(deepcopy(self.base_layout), 2, 2, self.base_value, 0)
    self.logger.debug(f'Tried {self.permutations} permutations for {self.current_filename}')
    if not self.write_each_new_best:
      self._write_to_file(self.best_layout, self.current_filename)

  def _recurse_layout(self, layout, x, y, value, beacons_used):
    # without logic to eliminate permutations early, this will check about 10^158
    while layout[y][x] != self.empty and (x < self.x_max - 2 or y < self.y_max - 2):
      # self.logger.debug(f'Checking x: {x-2}, y: {y-2}')
      if x >= self.x_max - 2:
        x = 2
        y += 1
      else:
        x += 1
    # self.logger.debug(f'Checking x: {x-2}, y: {y-2}')
    if layout[y][x] == self.empty:
      empty_value = value
      box_count = self._box_touching_count(layout, x, y)
      knight_count = self._knight_touching_count(layout, x, y)
      no_bb = self.never_bb or box_count < self.bb_threshold
      no_pb = self.never_pb or box_count < self.pb_threshold
      no_bk = self.never_bk or knight_count < self.bk_threshold
      no_pk = self.never_pk or knight_count < self.pk_threshold
      # self.logger.debug(f'no_bb: {no_bb}, no_pb: {no_pb}, no_bk: {no_bk}, no_pk: {no_pk}')
      # try all 4 beacons and no beacon
      for beacon in self.beacons:
        layout[y][x] = beacon
        if beacon != self.empty:
          beacons_used += 1
          # limit permutations by checking if any beacon would be useless
          if no_bb and no_pb and no_bk and no_pk: return
          # or counterproductive by also checking if any beacons affecting this space would lose their usefulness
          if self._is_counterproductive(layout, x, y): return
          # limit permutations by checking if this specific type of beacon would be useless
          if (beacon == self.bb and no_bb) or \
             (beacon == self.pb and no_pb) or \
             (beacon == self.bk and no_bk) or \
             (beacon == self.pk and no_pk):
            continue
          value = self._layout_value(layout)
        # limit permutations by abandoning paths that start by lowering productivity
        # or that lower the average beacon productivity below the expected curve
        if value >= empty_value and (beacon == self.empty or self.beacon_efficiency_ratio * beacons_used / (value - self.base_value) <= self.efficiency_buffer):
          # self.logger.debug(f'Trying x: {x-2}, y: {y-2}, beacon: {beacon}')
          self._recurse_layout(deepcopy(layout), x + 1, y, value, beacons_used)
    else:
      # last in the chain of recursions
      self.permutations += 1
      # self.logger.debug(f'Checking permutation {self.permutations} with value {value}')
      if value > self.best_value:
        self.best_layout = deepcopy(layout)
        self.best_value = value
        self.logger.debug(f'New best value at permutation {self.permutations}: {value}')
        if self.write_each_new_best:
          # self.logger.debug('\n' + self._pretty_format_layout(layout))
          self._write_to_file(self.best_layout, self.current_filename)

  def _is_counterproductive(cls, layout, x, y):
    for k in range(-2, 3):
      for j in range(-2, 3):
        if j == k == 0: continue
        elif abs(j) == abs(k) == 2: continue
        elif abs(j) == 2 or abs(k) == 2:
          if layout[y+k][x+j] == cls.bk and cls._knight_touching_count(layout, x + j, y + k) < cls.bk_threshold: return True
          elif layout[y+k][x+j] == cls.pk and cls._knight_touching_count(layout, x + j, y + k) < cls.pk_threshold: return True
        elif layout[y+k][x+j] == cls.bb and cls._box_touching_count(layout, x + j, y + k) < cls.bb_threshold: return True
        elif layout[y+k][x+j] == cls.pb and cls._box_touching_count(layout, x + j, y + k) < cls.pb_threshold: return True

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
          # cls.logger.debug(f'x: {x-2}, y: {y-2} affected by {beacons} with effective productivity: {value}')
          total_value += value
    # cls.logger.debug(f'Total: {total_value}')
    # cls.logger.debug('\n' + cls._pretty_format_layout(layout))
    return round(total_value, 2)

  def _space_value(cls, beacons):
    return (1 + (cls.bb_bonus * beacons[0]) + (cls.bk_bonus * beacons[1])) * (1 + (cls.pb_bonus * beacons[2]) + (cls.pk_bonus * beacons[3]))

  def _write_to_file(cls, layout, filename):
    if cls.write_file:
      with open(filename, 'w') as f:
        f.write(cls._pretty_format_layout(layout))

  def _pretty_format_layout(cls, layout):
    return '\n'.join([''.join(line) for line in layout if ''.join(line)])

if __name__ == '__main__':
  layouts = NguIndustriesLayouts()
  layouts.print_beacon_layouts()
  layouts.logger.info('Completed creating layouts')
