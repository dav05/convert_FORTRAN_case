# covert.py
# python3 script for case conversion of source code files written in fixed form fortran.
#
# python3 script for case conversion of source code files written in
# fixed form fortran. Ignores comments, strings, escape
# sequences within strings and some special words.
#
# For instructions type: python3 convert.py -h
#
# Copyright David Miranda 2021
# May 2021
#

# ---------------------------------------------------------------------
# LICENCE NOTICE
# ---------------------------------------------------------------------
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation License version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the
# GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/gpl-3.0.txt>.
# ---------------------------------------------------------------------


import os
import argparse


# tests whether a character can be used in a name identifier
def is_id_char(char):
    return char == '_' or 'A' <= char.upper() <= 'Z' or '1' <= char <= '9' or char == '0'


# same as find, but ensures that the name_id is and identifier (i.e. it's bounded by non name identifier characters)
def find_identifier(string, name_id, pos=0):
    found_pos = string.find(name_id, pos)
    found = False

    while found_pos != -1 and not found:
        # ensure that the name_id is isolated at the left (**** name_id), that is:
        # the word is either in at the start or has a non identifier character at the left
        if found_pos != 0:
            if is_id_char(string[found_pos - 1]):
                pos = found_pos + len(name_id)
                found_pos = string.find(name_id, pos)
                continue

        # ensure that the name_id is isolated ath the right (name_id ***), that is:
        # ensure that the name_id is right at the end or it is not followed by an identifier character
        temp_pos = found_pos + len(name_id)
        if temp_pos != len(string):
            if is_id_char(string[temp_pos]):
                pos = found_pos + len(name_id)
                found_pos = string.find(name_id, pos)
                continue
        found = True
    if found:
        return found_pos
    else:
        return -1


# data counters used only for statistics
class CStatistics:
    lines_changed = 0
    chars_changed = 0
    line_changed_flag = False

    # print statistics of the modifications
    def print(self):
        print(f'Lines changed: {self.lines_changed},   chars changed: {self.chars_changed}')


# data structure that defines the operator to apply to single characters
# also defines the modes of operation and contains statistics
class CCharOperator:
    upper = 1  # constant defining an operation mode : "make upper case"
    lower = 0  # constant defining operation mode : "make lower case"

    statistics = CStatistics()  # statistic data of the changes

    def __init__(self, mode_):
        self.mode = mode_

    # changes a single character according to mode_and_stat
    def change_case(self, char):
        if self.mode == CCharOperator.upper:
            c = char.upper()
        else:
            c = char.lower()
        if c != char:
            self.statistics.chars_changed += 1
            if not self.statistics.line_changed_flag:
                self.statistics.line_changed_flag = True
                self.statistics.lines_changed += 1
        return c


# data structure to handle protected words
# that is, words that should not be changed
# deals with finding protected words
# and helping to set the operation state of the algorithm that makes the changes (see parse_and_convert_line)
class CProtectedWords:
    def __init__(self, line):
        self.word_list = ['__LINE__', '__FILE__', '__DATE__']
        self.pos_next_word_start = 0
        self.pos_next_word_end = 0
        self.line = line  # copy of the working line of text, where the words are to be detected
        self.update_next_word(0)

    # finds the position of the next word, for word in self.word_list, starting from pos
    # -1 means not found or end of line reached, or has it has been reached before
    def update_next_word(self, pos):
        if self.pos_next_word_start == -1 or pos == -1:
            return

        new_position = len(self.line) + 1
        new_position_end = 0
        for word in self.word_list:
            this_word_position = find_identifier(self.line, word, pos)
            if -1 < this_word_position < new_position:  # make sure the word was found before
                # save the position of this word as being the next
                new_position = this_word_position
                new_position_end = new_position + len(word) - 1

        if new_position > len(self.line):
            self.pos_next_word_start = -1
            self.pos_next_word_end = 0
            return

        self.pos_next_word_start = new_position
        self.pos_next_word_end = new_position_end
        return

    # tests conditions for the protected word state to be active
    def test_whether_activate(self, pos):
        if self.pos_next_word_start == -1:
            return False
        # verify protected word state
        return self.pos_next_word_start <= pos <= self.pos_next_word_end


# converts an entire file
def process_file(folder, file_in, file_out, char_operator):
    path_name_in = folder + '/' + file_in
    path_name_out = folder + '/' + file_out

    # print(f'Processing: {path_name_in}')
    # print(f'Processing: {path_name_out}')

    with open(path_name_in, 'r') as obj_file_in:
        lines = obj_file_in.readlines()

    with open(path_name_out, 'w') as obj_file_out:
        for line_in in lines:
            line_out = parse_and_convert_line(line_in, char_operator)
            obj_file_out.write(line_out)


# parses and converts a given line as defined in mode and stats
# (pattern: state machine)
def parse_and_convert_line(line_in, char_operator):
    if 'CcDd!#'.find(line_in[0]) > -1:  # check for line comments and compiler directives
        return line_in
    char_operator.statistics.line_changed_flag = False  # set the line as unchanged for the statistics

    # states used in this routine:
    # a - active change state
    # k - keyword skip state : skip n_skip characters (only can be activated from active state)
    # ' - string state 1
    # " - string state 2
    # ! - comment
    # / - escape character (only can be activated from one of the string states)

    k_state = CProtectedWords(line_in)  # initialize data for handling protected words
    line_out = ''
    # process all the other characters
    state = 'a'  # this is the default active state
    previous_state = 'a'
    pos = -1  # position being read on the file
    for char in line_in:
        pos += 1
        if state == 'a':  # default active state
            line_out += char_operator.change_case(char)  # change the case
            if char == "'" or char == '"' or char == '!':
                state = char  # enter in comment or string state
                continue
            if k_state.test_whether_activate(pos):  # test for the state k
                state = 'k'  # enter in keyword state
            continue

        elif state == "'" or state == '"':  # string state
            line_out += char  # do not change the case
            if char == state:
                # exit state to another
                if k_state.test_whether_activate(pos):  # test for the state k
                    state = 'k'  # enter in keyword state
                else:
                    state = 'a'  # enter in active state
                continue
            elif char == "\\":
                previous_state = state  # save previous state
                state = "\\"
            continue
        elif state == "!":  # comment state (no way out)
            line_out += char  # do not change the case
            continue
        elif state == "\\":
            line_out += char
            state = previous_state  # always restore to the previous state
            continue
        elif state == 'k':  # protected keyword state
            line_out += char  # do not change the case
            if not k_state.test_whether_activate(pos):
                state = 'a'
                k_state.update_next_word(pos+1)  # updates the next word coming
            continue
    return line_out


# parse the arguments passed to the script
def parse_script_arguments():
    folder = os.getcwd()  # current working directory

    parser = argparse.ArgumentParser(description='Converts a fixed form fortran file to upper or lower case.')
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
                        help='do not echo any output')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-u', '--upper', action='store_true', default=True,
                       help='convert to upper case (default)')
    group.add_argument('-l', '--lower', action='store_true', default=False,
                       help='convert to lower case')
    parser.add_argument('file', help='file name, including extension')
    options = parser.parse_args()

    file = options.file
    n_operation_mode = CCharOperator.upper
    if options.upper:
        n_operation_mode = CCharOperator.upper
    if options.lower:
        n_operation_mode = CCharOperator.lower
    return [n_operation_mode, folder, file, options.quiet]


# the main function
def main():
    [n_mode, folder_name, file_name, quiet] = parse_script_arguments()

    f_in = file_name
    f_out = file_name
    operator = CCharOperator(n_mode)
    process_file(folder_name, f_in, f_out, operator)
    if not quiet:
        operator.statistics.print()


# Main code
if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError:
        print('ERROR: File not found.\n')
    except IsADirectoryError:
        print('ERROR: The file is a directory.\n')
    except PermissionError:
        print('ERROR: Check file access permissions.\n')
    except ProcessLookupError:
        print('ERROR: File locked by another process.\n')
    except TimeoutError:
        print('ERROR: Time out.\n')
