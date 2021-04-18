#! /bin/python3

import logging
import os
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
    arg_dict = vars(self.args)
    handlers=[logging.StreamHandler(sys.stdout)]
    if self.args.l:
      log_name_files = '_'.join(os.path.splitext(os.path.split(file)[1])[0] for file in self.args.files)
      log_name_opts = ''.join([arg for arg in arg_dict if len(arg) == 1 and arg_dict[arg]])
      log_name_time = round(time())
      log_name = os.path.join('logs', f'{log_name_files}-{log_name_opts}_{log_name_time}.log')
      handlers.append(logging.FileHandler(log_name))
    if self.args.verbosity > 0:
      level = logging.DEBUG
    else:
      level = logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)-5s %(message)s', handlers=handlers)
    self.logger = logging.getLogger()
    self.logger.debug(arg_dict)
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
    subsetslist = []
    # the whole layout in 1 set
    all_in_one = [set([(x, y) for y in range(0, len(base_layout)) for x in range(0, len(base_layout[y])) if base_layout[y][x] in self.beacons])]
    # rows, columns, and diagonals
    num_rows = len(base_layout)
    rows = [set([(x, y) for x in range (0, len(base_layout[y])) if base_layout[y][x] in self.beacons]) for y in range(0, num_rows)]
    num_columns = max([len(row) for row in rows])
    columns = [set([(x, y) for y in range(0, num_rows) if x < len(base_layout[y]) and base_layout[y][x] in self.beacons]) for x in range (0, num_columns)]
    num_diagonals = max(num_columns, num_rows)
    tlbr = [set([(x, y) for i in range(0, num_diagonals) if 0 <= (y := i) < num_rows and 0 <= (x := i + j) < len(base_layout[y]) and base_layout[y][x] in self.beacons]) for j in range(1 - num_diagonals, num_diagonals)]
    tlbr = [i for i in tlbr if i]
    bltr = [set([(x, y) for i in range(0, num_diagonals) if 0 <= (y := i) < num_rows and 0 <= (x := 2 * num_diagonals - 2 - i - j) < len(base_layout[y]) and base_layout[y][x] in self.beacons]) for j in range(0, 2 * num_diagonals - 1)]
    bltr = [i for i in bltr if i]
    # subsets by affected space groups, order might matter, not sure how to sort
    self.center = ((num_columns - 1) / 2, (num_rows - 1) / 2)
    all_space_subsets = [self._find_space_subset(base_layout, x, y) for y in range(0, len(base_layout)) for x in range(0, len(base_layout[y])) if base_layout[y][x] in self.beacons]
    all_space_subsets.sort(key=self._sort_subsets)
    all_space_subsets = [set(subset) for subset in all_space_subsets]
    space_subsets = all_space_subsets.copy()
    for s in all_space_subsets:
      while space_subsets.count(s) > 1:
        self.logger.debug(f'Removing duplicate {s}')
        space_subsets.remove(s)
    # pick the subsets we're testing with
    subsets = space_subsets
    # if self.args.x and not self.args.k:
      # subsetslist = [
        # rows + columns + tlbr + bltr,
        # rows + columns + bltr + tlbr,
        # rows + tlbr + columns + bltr,
        # rows + bltr + columns + tlbr,
        # rows + tlbr + bltr + columns,
        # rows + bltr + tlbr + columns,
        # columns + rows + tlbr + bltr,
        # columns + rows + bltr + tlbr,
        # columns + tlbr + rows + bltr,
        # columns + bltr + rows + tlbr,
        # columns + tlbr + bltr + rows,
        # columns + bltr + tlbr + rows,
        # tlbr + bltr + rows + columns,
        # tlbr + bltr + columns + rows,
        # tlbr + rows + bltr + columns,
        # tlbr + columns + bltr + rows,
        # tlbr + rows + columns + bltr,
        # tlbr + columns + rows + bltr,
        # bltr + tlbr + rows + columns,
        # bltr + tlbr + columns + rows,
        # bltr + rows + tlbr + columns,
        # bltr + columns + tlbr + rows,
        # bltr + rows + columns + tlbr,
        # bltr + columns + rows + tlbr
      # ]
    if self.args.verbosity >= 2:
      self.logger.debug(f'Starting layout value: {base_value}')
      self.logger.debug(f'Starting layout:\n{self._layout_to_string(base_layout)}')
      self.logger.debug(f'{len(all_in_one)} all_in_one: {all_in_one}')
      self.logger.debug(f'{len(space_subsets)} space_subsets: {space_subsets}')
      self.logger.debug(f'{len(reduced_space_subsets)} reduced_space_subsets: {reduced_space_subsets}')
      self.logger.debug(f'{len(rows)} rows: {rows}')
      self.logger.debug(f'{len(columns)} columns: {columns}')
      self.logger.debug(f'{len(tlbr)} tlbr: {tlbr}')
      self.logger.debug(f'{len(bltr)} bltr: {bltr}')
      self.logger.debug(f'{len(subsets)} subsets: {subsets}')
      self.logger.debug(f'{len(subsetslist)} subsetslist: {subsetslist}')
    permutations = 0
    best_layout = base_layout
    best_value = base_value
    percent_bonus = 0
    current_best_layout = base_layout
    current_best_value = base_value
    while True:
      if not subsetslist:
        subsetslist = [subsets]
      if self.args.verbosity >= 3:
        self.logger.debug(f'Starting permutation {permutations}')
      layout = deepcopy(best_layout)
      value = best_value
      for subsets in subsetslist:
        permutations += 1
        for subset in subsets:
          layout, value = self._find_best_sublayout(layout, value, subset)
        if value > current_best_value:
          current_best_layout = deepcopy(layout)
          current_best_value = value
          if self.args.verbosity >= 2:
            self.logger.debug(f'New current best layout at permutation {permutations}: {current_best_value}')
          if self.args.verbosity >= 3:
            self.logger.debug('\n' + self._layout_to_string(current_best_layout))
      if current_best_value > best_value:
        best_layout = deepcopy(current_best_layout)
        best_value = current_best_value
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
      elif current_best_value == best_value:
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
    if self.args.verbosity >= 3:
      self.logger.debug('\n' + self._layout_to_string(best_layout))
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
    subset = [(x, y)]
    for k in range(-2, 3):
      if y+k >= 0 and y+k < len(layout):
        for j in range(-2, 3):
          if x+j >= 0 and x+j < len(layout[y+k]):
            if j == k == 0 or \
               (not self.args.k and (abs(j) == 2 or abs(k) == 2)) or \
               (not self.args.x and (j, k) != (0, 0) and abs(j) < 2 and abs(k) < 2) or \
               abs(j) == abs(k) == 2 or \
               (abs(j), k) == (2, 0) or \
               (j, abs(k)) == (0, 2):
              continue
            else:
              if layout[y+k][x+j] in self.beacons:
                subset.append((x+j, y+k))
    return subset

  def _sort_subsets(self, subset):
    x, y = self.center
    j, k = subset[0]
    return max(abs(x-j), abs(y-k))

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
