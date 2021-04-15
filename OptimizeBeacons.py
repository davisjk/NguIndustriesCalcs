#! /bin/python3

import logging
import sys
from argparse import ArgumentParser
from copy import deepcopy
from math import ceil
from time import time

class NguiBeaconOptimizer:
  # constants
  all_combos = [(True, False, True, False),
                (False, True, True, False),
                (True, True, True, False),
                (False, True, True, True),
                (True, False, True, True),
                (True, True, True, True)]
  empty = '0'
  bx = 'b'
  bx_bonus = 0.4
  bx_threshold = ceil(1 / bx_bonus)
  bk = 'B'
  bk_bonus = 0.35
  bk_threshold = ceil(1 / bk_bonus)
  px = 'p'
  px_bonus = 0.3
  px_threshold = ceil(1 / px_bonus)
  pk = 'K'
  pk_bonus = 0.35
  pk_threshold = ceil(1 / pk_bonus)

  def __init__(self):
    self._parse_args()
    handlers=[logging.StreamHandler(sys.stdout)]
    if self.args.l:
      handlers.append(logging.FileHandler(f"{'_'.join(file.split('.', 1)[0] for file in self.args.files)}-{''.join([arg for arg in self.args if len(arg) == 1 and self.args[arg]])}_{round(time())}.log"))
    if self.args.verbosity > 0:
      level = logging.DEBUG
    else:
      level = logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)-5s %(message)s', handlers=handlers)
    self.logger = logging.getLogger()
    self.logger.debug(vars(self.args))
    self._setup()

  def _parse_args(self):
    parser = ArgumentParser()
    parser.add_argument('-a', help='all', action='store_true')
    parser.add_argument('-b', help='blue', action='store_true')
    parser.add_argument('-p', help='pink', action='store_true')
    parser.add_argument('-x', help='boxes', action='store_true')
    parser.add_argument('-k', help='knights', action='store_true')
    # parser.add_argument('-r', help='arrows', action='store_true')
    # parser.add_argument('-w', help='walls', action='store_true')
    parser.add_argument('-l', help='write to log file', action='store_true')
    parser.add_argument('-o', help='write to output file', action='store_true')
    parser.add_argument('-m', '--max', help='maximum permutations', type=int, default=0)
    parser.add_argument('-v', '--verbosity', help='0 to 5 where 0 is only INFO logging and higher than 1 can potentially create millions of logs and affect performance', action='count', default=0)
    parser.add_argument('files', nargs='*')
    self.args = parser.parse_args()

  def _setup(self):
    # beacons must be ordered and empty must be first
    self.beacons = [self.empty]
    self.logger.debug(f'Empty = {self.empty}')
    self.filename_id = ''
    if self.args.b:
      if self.args.x:
        self.beacons.append(self.bx)
        self.filename_id += '_bx'
        self.logger.debug(f'Blue Box = {self.bx}')
      if self.args.k:
        self.beacons.append(self.bk)
        self.filename_id += '_bk'
        self.logger.debug(f'Blue Knight = {self.bk}')
    if self.args.p:
      if self.args.x:
        self.beacons.append(self.px)
        self.filename_id += '_px'
        self.logger.debug(f'Pink Box = {self.px}')
      if self.args.k:
        self.beacons.append(self.pk)
        self.filename_id += '_pk'
        self.logger.debug(f'Pink Knight = {self.pk}')

  def print_beacon_layouts(self):
    for filename in self.args.files:
      if self.args.a:
        for combo in self.all_combos:
          self.args.b, self.args.p, self.args.x, self.args.k = combo
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
    layout = [[str(space) for space in line] for line in layout]
    return '\n'.join([''.join(line) for line in layout if ''.join(line)])

  def _find_best_layout(self, filename):
    self.logger.info(f'Finding best layout for {filename} with beacons: {self.beacons}')
    start_time = round(time(), 3)
    # get layout info that doesn't change per file
    output_filename = '{0}{2}.{1}'.format(*filename.split('.', 1), self.filename_id)
    base_layout = self._read_file(filename)
    base_value = self._layout_value(base_layout)
    spaces = sum([row.count(self.empty) for row in base_layout])
    subsets = []
    for y in range(0, len(base_layout)):
      for x in range(0, len(base_layout[y])):
        if base_layout[y][x] in self.beacons:
          subsets.append(self._find_space_subset(base_layout, x, y))
    # remove supersets of subsets to remove redundant calculations later
    # removing the subsets instead introduces a logic bug
    subsets_cp = subsets.copy()
    for subset in subsets:
      for other in subsets_cp:
        if subset < other:
          subsets_cp.remove(other)
          # subsets_cp.remove(subset)
          # break
    subsets = subsets_cp
    if self.args.verbosity >= 2:
      self.logger.debug(f'Starting layout value: {base_value}')
      self.logger.debug(f'Starting layout:\n{self._layout_to_string(base_layout)}')
      self.logger.debug(f'{len(subsets)} subsets: {subsets}')
    permutations = 0
    best_layout = base_layout
    best_value = base_value
    percent_bonus = 0
    # Intent:
    # - loop through every valid space
    # - find every space that affects this space
    #   - if only boxes or knights, only look at those spaces, etc
    # - find the best configuration for those spaces with the rest of the layout remaining the same
    #   - anywhere from 1 to 17 spaces so shouldn't take too long by brute force with a bit of logic for speedup
    # - loop again until the new best value and the old best value are the same
    while True:
      permutations += 1
      if self.args.verbosity >= 3:
        self.logger.debug(f'Starting permutation {permutations}')
      layout = deepcopy(best_layout)
      value = best_value
      for subset in subsets:
        layout, value = self._find_best_sublayout(layout, value, subset)
      if value > best_value:
        best_layout = deepcopy(layout)
        best_value = value
        if self.args.verbosity >= 2:
          self.logger.debug(f'New best layout at permutation {permutations}: {best_value}')
        if self.args.verbosity >= 3:
          self.logger.debug('\n' + self._layout_to_string(best_layout))
        percent_bonus = round((100 * best_value / spaces) - 100, 2)
        if self.args.o:
          extra_contents = [
            f'CAUTION: This may not be fully optimized, it is output after permutation {permutations}',
            f'Effective production: {best_value}',
            f'Effective bonus to production without beacons: {percent_bonus}%'
          ]
          self._write_file(output_filename, best_layout, extra_contents)
      elif value == best_value:
        if self.args.verbosity >= 1:
          self.logger.debug(f'Found best layout after {permutations} permutations')
        if self.args.o:
          extra_contents = [
            f'Effective production: {best_value}',
            f'Effective bonus to production without beacons: {percent_bonus}%'
          ]
          self._write_file(output_filename, best_layout, extra_contents)
        break
      else:
        self.logger.fatal(f'Reached an unexpected state after {permutation} permutations! Current layout value is less than best layout value.')
        self.logger.fatal(f'Best value: {best_value}')
        self.logger.fatal(f'Best layout:\n{self._layout_to_string(best_layout)}')
        self.logger.fatal(f'Current value: {value}')
        self.logger.fatal(f'Current layout:\n{self._layout_to_string(layout)}')
        sys.exit(1)
      if self.args.max > 0 and permutations >= self.args.max:
        self.logger.info(f'Stopped optimizing after {permutations} permutations upon reaching maximum number of permutations')
        break
    stop_time = round(time(), 3)
    self.logger.info(f'Optimized beacon placement of {filename} found in {round(stop_time - start_time, 3)} seconds with beacons: {self.beacons}')
    self.logger.info(f'Effective bonus to base production with this layout is {percent_bonus}% with a total production of {best_value}')
    self.logger.info('\n' + self._layout_to_string(best_layout))

  def _find_best_sublayout(self, layout, value, subset):
    if self.args.verbosity >= 3:
      self.logger.debug(f'Finding best sublayout for {subset} with starting value: {value}')
    best_layout, best_value, subpermutations = self._recurse_sublayout(layout, subset.copy(), deepcopy(layout), value, 0)
    if self.args.verbosity >= 2:
      self.logger.debug(f'Found best sublayout after {subpermutations} subpermutations: {best_value}')
    return best_layout, best_value

  def _recurse_sublayout(self, layout, subset, best_layout, best_value, subpermutations):
    if subset:
      space = subset.pop()
      counterproductive = self._counterproductive_beacon(layout, *space)
      for beacon in self.beacons:
        if self.args.verbosity >= 3:
          self.logger.debug(f'Checking {beacon} in {space}')
        if beacon == self.empty or not counterproductive:
          if (beacon == self.bx and self._box_touching_count(layout, *space) < self.bx_threshold) or \
             (beacon == self.px and self._box_touching_count(layout, *space) < self.px_threshold) or \
             (beacon == self.bk and self._knight_touching_count(layout, *space) < self.bk_threshold) or \
             (beacon == self.pk and self._knight_touching_count(layout, *space) < self.pk_threshold):
            continue
          layout[space[1]][space[0]] = beacon
          if self.args.verbosity >= 3:
            self.logger.debug(f'Current value: {self._layout_value(layout)}')
            self.logger.debug(f'Current layout:\n{self._layout_to_string(layout)}')
          best_layout, best_value, subpermutations = self._recurse_sublayout(deepcopy(layout), deepcopy(subset), best_layout, best_value, subpermutations)
    value = self._layout_value(layout)
    if value > best_value:
      best_layout = deepcopy(layout)
      best_value = value
      if self.args.verbosity >= 3:
        self.logger.debug(f'New best sublayout at subpermutation {subpermutations}: {value}')
        self.logger.debug('\n' + self._layout_to_string(best_layout))
    return best_layout, best_value, subpermutations + 1

  def _counterproductive_beacon(self, layout, x, y):
    adjustment = 1 if layout[y][x] == self.empty else 0
    for k in range(-2, 3):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-2, 3):
          if x+j >= 0 and x+j < len(layout[y+k]):
            if j == k == 0 or \
               abs(j) == abs(k) == 2 or \
               (abs(j), k) == (2, 0) or \
               (j, abs(k)) == (0, 2):
              continue
            # knights
            elif abs(j) == 2 or abs(k) == 2:
              if layout[y+k][x+j] == self.bk and self._knight_touching_count(layout, x+j, y+k) - adjustment < self.bk_threshold:
                return True
              elif layout[y+k][x+j] == self.pk and self._knight_touching_count(layout, x+j, y+k) - adjustment < self.pk_threshold:
                return True
            # boxes
            else:
              if layout[y+k][x+j] == self.bx and self._box_touching_count(layout, x+j, y+k) - adjustment < self.bx_threshold:
                return True
              elif layout[y+k][x+j] == self.px and self._box_touching_count(layout, x+j, y+k) - adjustment < self.px_threshold:
                return True
    return False

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

  def _find_space_subset(self, layout, x, y):
    subset = set()
    for k in range(-2, 3):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-2, 3):
          if x+j >= 0 and x+j < len(layout[y+k]):
            if (not self.args.k and (abs(j) == 2 or abs(k) == 2)) or \
               (not self.args.x and (j, k) != (0, 0) and abs(j) < 2 and abs(k) < 2) or \
               abs(j) == abs(k) == 2 or \
               (abs(j), k) == (2, 0) or \
               (j, abs(k)) == (0, 2):
              continue
            else:
              if layout[y+k][x+j] in self.beacons:
                subset.add((x+j, y+k))
    return subset

  def _layout_value(self, layout):
    total = 0
    for y in range(0, len(layout)):
      for x in range(0, len(layout[y])):
        # [bx, bk, px, pk]
        beacon_counts = [0, 0, 0, 0]
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
                      beacon_counts[1] += 1
                    elif layout[y+k][x+j] == self.pk:
                      beacon_counts[3] += 1
                  # boxes
                  else:
                    if layout[y+k][x+j] == self.bx:
                      beacon_counts[0] += 1
                    elif layout[y+k][x+j] == self.px:
                      beacon_counts[2] += 1
          value = self._space_value(beacon_counts)
          if self.args.verbosity >= 5:
            self.logger.debug(f'x: {x-2}, y: {y-2} affected by {beacon_counts} with effective productivity: {value}')
          total += value
    if self.args.verbosity >= 4:
      self.logger.debug(f'Total: {total}')
      self.logger.debug('\n' + self._layout_to_string(layout))
    return round(total, 2)

  def _space_value(self, beacon_counts):
    return (1 + (self.bx_bonus * beacon_counts[0]) + (self.bk_bonus * beacon_counts[1])) * (1 + (self.px_bonus * beacon_counts[2]) + (self.pk_bonus * beacon_counts[3]))

if __name__ == '__main__':
  mapper = NguiBeaconOptimizer()
  mapper.print_beacon_layouts()
  mapper.logger.info('Completed optimizing beacon layout(s)')
