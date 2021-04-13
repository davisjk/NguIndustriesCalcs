#! /bin/python3

import argparse
import logging
import math
import sys
import time
from copy import deepcopy

class NguIMapper:
  # CAUTION, commented out debug messages create multiple GB of logs and drastically slow performance
  logging.basicConfig(stream=sys.stdout, format='%(asctime)s %(levelname)-5s %(message)s', level=logging.DEBUG)
  logger = logging.getLogger()
  # constants
  all_combos = [(True, False, True, False),
                (True, False, True, True),
                (False, True, True, False),
                (False, True, True, True),
                (True, True, True, False),
                (True, True, True, True)]
  empty = '0'
  bx = 'b'
  bx_bonus = 0.4
  bx_threshold = math.ceil(1 / bx_bonus)
  bk = 'B'
  bk_bonus = 0.35
  bk_threshold = math.ceil(1 / bk_bonus)
  px = 'p'
  px_bonus = 0.3
  px_threshold = math.ceil(1 / px_bonus)
  pk = 'K'
  pk_bonus = 0.35
  pk_threshold = math.ceil(1 / pk_bonus)

  def __init__(self):
    self._parse_args()
    self._setup()

  def _parse_args(self):
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--all', action='store_true')
    parser.add_argument('-b', '--blue', action='store_true')
    parser.add_argument('-p', '--pink', action='store_true')
    parser.add_argument('-x', '--boxes', action='store_true')
    parser.add_argument('-k', '--knights', action='store_true')
    # parser.add_argument('-r', '--arrows', action='store_true')
    # parser.add_argument('-w', '--walls', action='store_true')
    parser.add_argument('-o', '--output', action='store_true')
    parser.add_argument('files', nargs='*')
    self.args = vars(parser.parse_args())

  def _setup(self):
    self.beacons = [self.empty]
    self.logger.info(f'Empty = {self.empty}')
    self.filename_id = ''
    if self.args['blue']:
      if self.args['boxes']:
        self.beacons += [self.bx]
        self.filename_id += '_bx'
        self.logger.info(f'Blue Box = {self.bx}')
      if self.args['knights']:
        self.beacons += [self.bk]
        self.filename_id += '_bk'
        self.logger.info(f'Blue Knight = {self.bk}')
    if self.args['pink']:
      if self.args['boxes']:
        self.beacons += [self.px]
        self.filename_id += '_px'
        self.logger.info(f'Pink Box = {self.px}')
      if self.args['knights']:
        self.beacons += [self.pk]
        self.filename_id += '_pk'
        self.logger.info(f'Pink Knight = {self.pk}')
    # self.filename_id += '_' + str(math.floor(time.time()))
    self.filename_id += '_fast'

  def print_beacon_layouts(self):
    for filename in self.args['files']:
      if self.args['all']:
        for combo in self.all_combos:
          self.args['blue'], self.args['pink'], self.args['boxes'], self.args['knights'] = combo
          self._setup()
          self._find_best_layout(filename)
      else:
        self._find_best_layout(filename)

  def _read_file(self, filename):
    with open(filename, 'r') as f:
      return [[space for space in line if space != '\n'] for line in f.readlines()]

  def _write_file(self, filename, layout, extra):
    with open(filename, 'w') as f:
      f.write(self._layout_to_string(layout))
      if extra:
        f.write('\n\n' + '\n'.join(extra))

  def _layout_to_string(self, layout):
    return '\n'.join([''.join(line) for line in layout if ''.join(line)])

  def _find_best_layout(self, filename):
    self.logger.info(f'Finding best layout for {filename} with beacons: {self.beacons}')
    permutations = 0
    base_layout = self._read_file(filename)
    base_value = self._layout_value(base_layout)
    self.logger.info(f'Starting layout value: {base_value}')
    best_layout = base_layout
    best_value = base_value
    # Another way might be to:
    # - loop through every empty space
    # - find every space that affects this space
    #   - if only boxes or knights, only look at thos spaces, etc
    # - find the best configuration for those spaces with the rest of the layout remaining the same
    #   - anywhere from 1 to 17 spaces so shouldn't take too long by brute force with a bit of thought
    # - loop again until the new best value and the old best value are the same
    while True:
      permutations += 1
      # self.logger.debug(f'Starting permutation {permutations}')
      layout = deepcopy(base_layout)
      value = base_value
      for y in range(0, len(layout)):
        for x in range(0, len(layout[y])):
          if layout[y][x] in self.beacons:
            layout, value = self._find_best_sublayout(layout, x, y)
      if value > best_value:
        best_layout = deepcopy(layout)
        best_value = value
        self.logger.debug(f'New best layout at permutation {permutations}: {best_value}')
        # self.logger.debug('\n' + self._layout_to_string(best_layout))
      elif value == best_value:
        #TODO, permutations is always 2 which seems wrong
        self.logger.debug(f'Found best layout after {permutations} permutations')
        break
      else:
        self.logger.error(f'Reached an unexpected state after {permutation} permutations! Current layout value is less than best layout value.')
        self.logger.error(f'Best value: {best_value}')
        self.logger.error(f'Best layout: {best_layout}')
        self.logger.error(f'Current value: {value}')
        self.logger.error(f'Current layout: {layout}')
        sys.exit(1)
    percent_bonus = round((100 * best_value / base_value) - 100, 2)
    self.logger.info(f'Approximate best calculated layout with beacons: {self.beacons}')
    self.logger.info(f'Effective bonus to base production with this layout is {percent_bonus}% with a total production of {best_value}')
    self.logger.info('\n' + self._layout_to_string(best_layout))
    output_filename = '{0}{2}.{1}'.format(*filename.split('.', 1), self.filename_id)
    extra_contents = [f'Effective production: {best_value}', f'Effective bonus to production without beacons: {percent_bonus}%']
    if self.args['output']:
      self._write_file(output_filename, best_layout, extra_contents)

  def _find_best_sublayout(self, layout, x, y):
    spaces = self._find_space_subset(layout, x, y)
    value = self._layout_value(layout)
    # self.logger.debug(f'Finding best sublayout for {spaces} with starting value: {value}')
    best_layout, best_value, permutations = self._recurse_sublayout(layout, spaces.copy(), deepcopy(layout), value, 0)
    # self.logger.debug(f'Found best sublayout after {permutations} permutations: {best_value}')
    return best_layout, best_value

  def _recurse_sublayout(self, layout, spaces, best_layout, best_value, permutations):
    #TODO, use 2x5 to debug this
    if spaces:
      space = spaces.pop()
      for beacon in self.beacons:
        # self.logger.debug(f'Checking {beacon} in {space}')
        #TODO, use logic in _recurse_layout to skip some beacons
        layout[space[1]][space[0]] = beacon
        best_layout, best_value, permutations = self._recurse_sublayout(deepcopy(layout), spaces, best_layout, best_value, permutations)
    value = self._layout_value(layout)
    if value > best_value:
      best_layout = deepcopy(layout)
      best_value = value
      # self.logger.debug(f'New best sublayout at permutation {permutations}: {value}')
      # self.logger.debug('\n' + self._layout_to_string(best_layout))
    return best_layout, best_value, permutations + 1

  def _find_space_subset(self, layout, x, y):
    spaces = []
    for k in range(-2, 3):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-2, 3):
          if (not self.args['knights'] and (abs(j) == 2 or abs(k) == 2)) or \
             (not self.args['boxes'] and (j, k) != (0, 0) and abs(j) < 2 and abs(k) < 2) or \
             abs(j) == abs(k) == 2 or \
             (abs(j), k) == (2, 0) or \
             (j, abs(k)) == (0, 2):
            continue
          elif x+j >= 0 and x+j < len(layout[y+k]):
            if layout[y+k][x+j] in [self.empty] + self.beacons:
              spaces.append((x+j, y+k))
    return spaces

  def _find_fast_layout(self):
    # I don't think this way will ever find the best layout even on a 3x3 so I'm not going to do it:
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
    # This is deprecated, but still fast and not terrible at boxes only
    self.logger.info(f'Finding best layout for {filename} with beacons: {self.beacons}')
    permutations = 0
    base_layout = self._read_file(filename)
    base_value = self._layout_value(base_layout)
    spaces = sum([row.count(self.empty) for row in base_layout])
    best_layout = base_layout
    best_value = base_value
    prev_layout = base_layout
    prev_value = base_value
    while permutations < spaces:
      permutations += 1
      # self.logger.debug(f'Starting permutation {permutations}')
      start = 1
      layout = deepcopy(base_layout)
      prev_layout = base_layout
      prev_value = base_value
      for y in range(0, len(layout)):
        for x in range(0, len(layout[y])):
          if layout[y][x] == self.empty:
            if start < permutations:
              start += 1
            else:
              for beacon in beacons:
                layout[y][x] = beacon
                value = self._layout_value(layout)
                if value > prev_value:
                  prev_layout = deepcopy(layout)
                  prev_value = value
              layout = deepcopy(prev_layout)
      if prev_value > best_value:
        best_layout = prev_layout
        best_value = prev_value
        self.logger.debug(f'New best value at permutation {permutations}: {best_value}')
        # self.logger.debug('\n' + self._layout_to_string(best_layout))
      # else:
        # self.logger.debug(f'Checked permutation {permutations} with value: {prev_value}')
        # self.logger.debug('\n' + self._layout_to_string(prev_layout))
    percent_bonus = round((100 * best_value / base_value) - 100, 2)
    self.logger.debug(f'Checked a total of {permutations} permutations')
    self.logger.info(f'Approximate best calculated layout with beacons: {self.beacons}')
    self.logger.info(f'Effective bonus to base production with this layout is {percent_bonus}% with a total production of {best_value}')
    self.logger.info('\n' + self._layout_to_string(best_layout))
    output_filename = '{0}{2}.{1}'.format(*filename.split('.', 1), self.filename_id)
    extra_contents = [f'Effective production: {best_value}', f'Effective bonus to production without beacons: {percent_bonus}%']
    if self.output_to_file:
      self._write_file(output_filename, best_layout, extra_contents)

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
      no_bx = self.never_bx or box_count < self.bx_threshold
      no_px = self.never_px or box_count < self.px_threshold
      no_bk = self.never_bk or knight_count < self.bk_threshold
      no_pk = self.never_pk or knight_count < self.pk_threshold
      # self.logger.debug(f'no_bx: {no_bx}, no_px: {no_px}, no_bk: {no_bk}, no_pk: {no_pk}')
      # try all 4 beacons and no beacon
      for beacon in self.beacons:
        layout[y][x] = beacon
        if beacon != self.empty:
          # limit permutations by checking if any beacon would be useless
          if no_bx and no_px and no_bk and no_pk: return
          # or counterproductive by also checking if any beacons affecting this space would lose their usefulness
          if self._is_counterproductive(layout, x, y): return
          # limit permutations by checking if this specific type of beacon would be useless
          if (beacon == self.bx and no_bx) or \
             (beacon == self.px and no_px) or \
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

  def _is_counterproductive(self, layout, x, y):
    for k in range(-2, 3):
      for j in range(-2, 3):
        if j == k == 0 or \
           abs(j) == abs(k) == 2 or \
           (abs(j), k) == (2, 0) or \
           (j, abs(k)) == (0, 2):
          continue
        # knights
        elif abs(j) == 2 or abs(k) == 2:
          if layout[y+k][x+j] == self.bk and self._knight_touching_count(layout, x+j, y+k) < self.bk_threshold:
            return True
          elif layout[y+k][x+j] == self.pk and self._knight_touching_count(layout, x+j, y+k) < self.pk_threshold:
            return True
        # boxes
        else:
          if layout[y+k][x+j] == self.bx and self._box_touching_count(layout, x+j, y+k) < self.bx_threshold:
            return True
          elif layout[y+k][x+j] == self.px and self._box_touching_count(layout, x+j, y+k) < self.px_threshold:
            return True

  def _box_touching_count(self, layout, x, y):
    count = 0;
    for k in range(-1, 2):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-1, 2):
          if j == k == 0:
            continue
          elif x+j >= 0 and x+j < len(layout[y+k]):
            if layout[y+k][x+j] == self.empty:
              count += 1
    return count

  def _knight_touching_count(self, layout, x, y):
    count = 0;
    for k in [-2, -1, 1, 2]:
      if y+k >= 0 and y+k < len(layout):
        for j in [-2, -1, 1, 2]:
          if abs(j) == abs(k):
            continue
          elif x+j >= 0 and x+j < len(layout[y+k]):
            if layout[y+k][x+j] == self.empty:
              count += 1
    return count

  def _layout_value(self, layout):
    total = 0
    for y in range(0, len(layout)):
      for x in range(0, len(layout[y])):
        # [bx, bk, px, pk]
        beacons = [0, 0, 0, 0]
        if layout[y][x] == self.empty:
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
                    if layout[y+k][x+j] == self.bk:
                      beacons[1] += 1
                    elif layout[y+k][x+j] == self.pk:
                      beacons[3] += 1
                  # boxes
                  else:
                    if layout[y+k][x+j] == self.bx:
                      beacons[0] += 1
                    elif layout[y+k][x+j] == self.px:
                      beacons[2] += 1
          value = self._space_value(beacons)
          # self.logger.debug(f'x: {x-2}, y: {y-2} affected by {beacons} with effective productivity: {value}')
          total += value
    # self.logger.debug(f'Total: {total}')
    # self.logger.debug('\n' + self._layout_to_string(layout))
    return round(total, 2)

  def _space_value(self, beacons):
    return (1 + (self.bx_bonus * beacons[0]) + (self.bk_bonus * beacons[1])) * (1 + (self.px_bonus * beacons[2]) + (self.pk_bonus * beacons[3]))

if __name__ == '__main__':
  # sys.argv += ['-px', '3x3.txt']
  mapper = NguIMapper()
  mapper.print_beacon_layouts()
  mapper.logger.info('Completed finding best layout(s)')
