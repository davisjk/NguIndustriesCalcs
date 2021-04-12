#! /bin/python3

import logging
import math
import sys
import time
from copy import deepcopy

class NguIBeacons:
  # CAUTION, commented out debug messages create multiple GB of logs and drastically slow performance
  logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-5s %(message)s', level=logging.DEBUG)
  logger = logging.getLogger()
  # default values
  files = ['TutorialIsland.txt', 'FleshWorld.txt']
  output_to_file = True
  check_all_combinations = True
  all_combinations = [(True, False, True, False),
                      (True, False, True, True),
                      (False, True, True, False),
                      (False, True, True, True),
                      (True, True, True, False),
                      (True, True, True, True)]
  with_blue = False
  with_pink = True
  with_boxes = True
  with_knights = False
  with_arrows = False #TODO
  with_walls = False #TODO
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

  def __init__(self, files):
    if len(files) > 0:
      self.files = files
    self._setup()

  def _setup(self):
    self.beacons = []
    self.logger.info(f'Empty = {self.empty}')
    self.filename_extras = ''
    if self.with_blue:
      if self.with_boxes:
        self.beacons += [self.bb]
        self.filename_extras += '_bb'
        self.logger.info(f'Blue Box = {self.bb}')
      if self.with_knights:
        self.beacons += [self.bk]
        self.filename_extras += '_bk'
        self.logger.info(f'Blue Knight = {self.bk}')
    if self.with_pink:
      if self.with_boxes:
        self.beacons += [self.pb]
        self.filename_extras += '_pb'
        self.logger.info(f'Pink Box = {self.pb}')
      if self.with_knights:
        self.beacons += [self.pk]
        self.filename_extras += '_pk'
        self.logger.info(f'Pink Knight = {self.pk}')
    # self.filename_extras += '_' + str(math.floor(time.time()))

  def print_beacon_layouts(self):
    for filename in self.files:
      if self.check_all_combinations:
        for combo in self.all_combinations:
          self.with_blue, self.with_pink, self.with_boxes, self.with_knights = combo
          self._setup()
          self._find_layouts(filename)
      else:
        self._setup()
        self._find_layouts(filename)

  def _find_layouts(self, filename):
    self.logger.info(f'Finding best layout for {filename} with beacons: {self.beacons}')
    base_layout = self._read_file(filename)
    base_value = self._layout_value(base_layout)
    self.best_value = base_value
    best_layout, best_value = self._find_best_layout(base_layout, self.beacons)
    percent_bonus = round((100 * best_value / base_value) - 100, 2)
    self.logger.info(f'Approximate best calculated layout with beacons: {self.beacons}')
    self.logger.info(f'Effective bonus to base production with this layout is {percent_bonus}% with a total production of {best_value}')
    self.logger.info('\n' + self._layout_to_string(best_layout))
    output_filename = '{0}{2}_fast.{1}'.format(*filename.split('.', 1), self.filename_extras)
    extra_contents = [f'Effective production: {best_value}', f'Effective bonus to production without beacons: {percent_bonus}%']
    if self.output_to_file:
      self._write_file(output_filename, best_layout, extra_contents)

  @staticmethod
  def _read_file(filename):
    with open(filename, 'r') as f:
      return [[space for space in line if space != '\n'] for line in f.readlines()]

  @staticmethod
  def _write_file(filename, layout, extra):
    with open(filename, 'w') as f:
      f.write(NguIBeacons._layout_to_string(layout))
      if extra:
        f.write('\n\n' + '\n'.join(extra))

  @staticmethod
  def _layout_to_string(layout):
    return '\n'.join([''.join(line) for line in layout if ''.join(line)])

  @classmethod
  def _find_best_layout(cls, base_layout, beacons):
    #TODO:
    # I don't think this way will always find the best layout even on a 3x3 so I'm not going to do it:
    # - loop through every empty space
    # - loop and try each beacon there
    # - find any beacons that are next to too many other beacons/voids
    # - find the best configuration of all of the suboptimal beacons (can this be done in smaller groups?)
    # - check if the total production decreased from the last time we checked this
    # - keep track of all of the beacons that have been tried in each space and skip those beacons in those spaces when looping through
    # Another way might be to:
    # - loop through every empty space
    # - find every space that affects this space
    #   - if only boxes or knights, only look at thos spaces, etc
    # - find the best configuration for those spaces with the rest of the layout remaining the same
    #   - anywhere from 1 to 17 spaces so shouldn't take too long by brute force with a bit of thought
    # - loop again until the new best value and the old best value are the same
    permutations = 0
    spaces = sum([row.count(cls.empty) for row in base_layout])
    base_value = cls._layout_value(base_layout)
    best_layout = base_layout
    best_value = base_value
    prev_layout = base_layout
    prev_value = base_value
    while permutations < spaces:
      permutations += 1
      # cls.logger.debug(f'Starting permutation {permutations}')
      start = 1
      layout = deepcopy(base_layout)
      prev_layout = base_layout
      prev_value = base_value
      for y in range(0, len(layout)):
        for x in range(0, len(layout[y])):
          if layout[y][x] == cls.empty:
            if start < permutations:
              start += 1
            else:
              for beacon in beacons:
                layout[y][x] = beacon
                value = cls._layout_value(layout)
                if value > prev_value:
                  prev_layout = deepcopy(layout)
                  prev_value = value
              layout = deepcopy(prev_layout)
      if prev_value > best_value:
        best_layout = prev_layout
        best_value = prev_value
        cls.logger.debug(f'New best value at permutation {permutations}: {best_value}')
        # cls.logger.debug('\n' + cls._layout_to_string(best_layout))
      # else:
        # cls.logger.debug(f'Checked permutation {permutations} with value: {prev_value}')
        # cls.logger.debug('\n' + cls._layout_to_string(prev_layout))
    cls.logger.debug(f'Checked a total of {permutations} permutations')
    return best_layout, best_value

  #TODO, delete this once it's no longer needed as a reference
  def _recurse_layout(self, layout, x, y, value):
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
        if value >= empty_value:
          # self.logger.debug(f'Trying x: {x-2}, y: {y-2}, beacon: {beacon}')
          self._recurse_layout(deepcopy(layout), x + 1, y, value)
    else:
      # last in the chain of recursions
      self.permutations += 1
      # self.logger.debug(f'Checking permutation {self.permutations} with value {value}')
      if value > self.best_value:
        self.best_layout = deepcopy(layout)
        self.best_value = value
        self.logger.debug(f'New best value at permutation {self.permutations}: {value}')
        if self.write_each_new_best:
          # self.logger.debug('\n' + self._layout_to_string(layout))
          self._write_to_file()

  @classmethod
  def _find_suboptimal_beacons(cls, layout):
    suboptimal = []
    #TODO
    return []

  @classmethod
  def _is_counterproductive(cls, layout, x, y):
    for k in range(-2, 3):
      for j in range(-2, 3):
        if j == k == 0 or \
           abs(j) == abs(k) == 2 or \
           (abs(j), k) == (2, 0) or \
           (j, abs(k)) == (0, 2):
          continue
        # knights
        elif abs(j) == 2 or abs(k) == 2:
          if layout[y+k][x+j] == cls.bk and cls._knight_touching_count(layout, x+j, y+k) < cls.bk_threshold:
            return True
          elif layout[y+k][x+j] == cls.pk and cls._knight_touching_count(layout, x+j, y+k) < cls.pk_threshold:
            return True
        # boxes
        else:
          if layout[y+k][x+j] == cls.bb and cls._box_touching_count(layout, x+j, y+k) < cls.bb_threshold:
            return True
          elif layout[y+k][x+j] == cls.pb and cls._box_touching_count(layout, x+j, y+k) < cls.pb_threshold:
            return True

  @classmethod
  def _box_touching_count(cls, layout, x, y):
    count = 0;
    for k in range(-1, 2):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-1, 2):
          if j == k == 0:
            continue
          elif x+j >= 0 and x+j < len(layout[y+k]):
            if layout[y+k][x+j] == cls.empty:
              count += 1
    return count

  @classmethod
  def _knight_touching_count(cls, layout, x, y):
    count = 0;
    for k in [-2, -1, 1, 2]:
      if y+k >= 0 and y+k < len(layout):
        for j in [-2, -1, 1, 2]:
          if abs(j) == abs(k):
            continue
          elif x+j >= 0 and x+j < len(layout[y+k]):
            if layout[y+k][x+j] == cls.empty:
              count += 1
    return count

  @classmethod
  def _layout_value(cls, layout):
    total = 0
    for y in range(0, len(layout)):
      for x in range(0, len(layout[y])):
        # [bb, bk, pb, pk]
        beacons = [0, 0, 0, 0]
        if layout[y][x] == cls.empty:
          for k in range(-2, 3):
            if y+k >= 0 and y+k < len(layout):
              for j in range(-2, 3):
                if j == k == 0 or \
                   abs(j) == abs(k) == 2 or \
                   (abs(j), k) == (2, 0) or \
                   (j, abs(k)) == (0, 2):
                  continue
                elif x+j >= 0 and x+j < len(layout[y+k]):
                  # knights
                  if abs(j) == 2 or abs(k) == 2:
                    if layout[y+k][x+j] == cls.bk:
                      beacons[1] += 1
                    elif layout[y+k][x+j] == cls.pk:
                      beacons[3] += 1
                  # boxes
                  else:
                    if layout[y+k][x+j] == cls.bb:
                      beacons[0] += 1
                    elif layout[y+k][x+j] == cls.pb:
                      beacons[2] += 1
          value = cls._space_value(beacons)
          # cls.logger.debug(f'x: {x-2}, y: {y-2} affected by {beacons} with effective productivity: {value}')
          total += value
    # cls.logger.debug(f'Total: {total}')
    # cls.logger.debug('\n' + cls._layout_to_string(layout))
    return round(total, 2)

  @classmethod
  def _space_value(cls, beacons):
    return (1 + (cls.bb_bonus * beacons[0]) + (cls.bk_bonus * beacons[1])) * (1 + (cls.pb_bonus * beacons[2]) + (cls.pk_bonus * beacons[3]))

def tests():
  empty_5x5 = [['0','0','0','0','0'],
               ['0','0','0','0','0'],
               ['0','0','0','0','0'],
               ['0','0','0','0','0'],
               ['0','0','0','0','0']]
  pb_5x5 = [['0','0','0','0','0'],
            ['0','p','0','p','0'],
            ['0','p','0','p','0'],
            ['0','p','0','p','0'],
            ['0','0','0','0','0']]
  pk_5x5 = [['0','0','0','0','0'],
            ['0','0','K','0','0'],
            ['0','K','K','K','0'],
            ['0','0','K','0','0'],
            ['0','0','0','0','0']]
  crowded_5x5 = [['0','0','0','0','0'],
                 ['0','p','p','p','0'],
                 ['0','p','0','p','0'],
                 ['0','p','p','p','0'],
                 ['0','0','0','0','0']]
  blobland = [['0','0','0'],
              ['0',' ','0','0','0'],
              ['0','0'],
              ['0','0',' ',' ','0']]
  if NguIBeacons._box_touching_count(empty_5x5, 0, 0) != 3: return False
  if NguIBeacons._box_touching_count(empty_5x5, 1, 1) != 8: return False
  if NguIBeacons._box_touching_count(pk_5x5, 0, 0) != 3: return False
  if NguIBeacons._box_touching_count(pk_5x5, 1, 1) != 5: return False
  if NguIBeacons._box_touching_count(blobland, 1, 1) != 7: return False
  if NguIBeacons._box_touching_count(blobland, 1, 2) != 5: return False
  if NguIBeacons._knight_touching_count(empty_5x5, 0, 0) != 2: return False
  if NguIBeacons._knight_touching_count(empty_5x5, 1, 1) != 4: return False
  if NguIBeacons._knight_touching_count(empty_5x5, 2, 2) != 8: return False
  if NguIBeacons._knight_touching_count(empty_5x5, 4, 4) != 2: return False
  if NguIBeacons._knight_touching_count(pk_5x5, 0, 0) != 0: return False
  if NguIBeacons._knight_touching_count(pk_5x5, 1, 1) != 2: return False
  if NguIBeacons._knight_touching_count(pk_5x5, 2, 2) != 8: return False
  if NguIBeacons._knight_touching_count(pk_5x5, 4, 4) != 0: return False
  if NguIBeacons._knight_touching_count(blobland, 1, 1) != 1: return False
  if NguIBeacons._layout_value(empty_5x5) != 25: return False
  if NguIBeacons._layout_value(pb_5x5) != 31: return False
  if NguIBeacons._layout_value(pk_5x5) != 31.2: return False
  # sys.exit(0)
  return True

if __name__ == '__main__':
  # if not tests():
    # print('Tests found ERROR')
    # sys.exit(1)
  layouts = NguIBeacons(sys.argv[1:])
  layouts.print_beacon_layouts()
  layouts.logger.info('Completed creating layouts')
