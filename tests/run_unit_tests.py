# run_unit_tests.py
# unit tests
#
# how to run the tests:
# 1-keep, the directory structure as given in the original repo
# 2-change the working directory to the directory of this script
# 3- run python3 run_unit_tests.py
#
# how to create new tests:
# 1-create a directory inside ./tests
# 2-name the folder so that it ends with U for uppercase or L for lower case operation
# 3-create two files inside the folder
# 3.1-input.for for the original reference file
# 3.2-expected.for the expected file after changes
#
#
# Copyright David Miranda 2021
# May 2021


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
from pathlib import Path


# compares two files
def compare_files(path_name_1, path_name_2):
    with open(path_name_1, 'r') as obj_file_1:
        data1 = obj_file_1.read()
    with open(path_name_2, 'r') as obj_file_2:
        data2 = obj_file_2.read()

    # the files have different length
    if len(data1) != len(data2):
        return 1  # different length
    for pos in range(len(data1)):
        if data1[pos] != data2[pos]:
            return 2  # different characters
    return 0


# run a system command (and verbose if active)
def run_command(sys_command):
    debug_verbose = 0  # switch to one if you want to see what commands are running
    if debug_verbose:
        print('running command:')
        print(sys_command)
    os.system(sys_command)


# run the tests. i.e. runs the tool with a system command on the test files
def run_test(folder, folder_test, mode=''):
    # define the default names
    file_result = 'result.for'
    file_input = 'input.for'
    file_expected = 'expected.for'
    folder_test_full = os.path.join(folder, folder_test)  # full path of the test folder

    sys_command = 'cp ' + os.path.join(folder_test_full, file_input) + ' ' + os.path.join(folder, file_result)
    run_command(sys_command)

    sys_command = 'python3 ' + os.path.join(folder.parent, 'convert.py ')
    sys_command += mode + ' ' + os.path.join(folder, file_result)
    run_command(sys_command)

    result = compare_files(os.path.join(folder, file_result), os.path.join(folder_test_full, file_expected))
    if result == 0:
        result_message = "passed"
    else:
        result_message = "++++ FAILED ++++."

    print('TEST {0} {1}.'.format(folder_test, result_message))

    if result == 0:
        return 0
    else:
        return 1


def run_test_with_error_handling(folder, folder_test, mode=''):
    try:
        result = run_test(folder, folder_test, mode)
    except FileNotFoundError:
        print('ERROR: File not found.\n')
        result = 1
    except IsADirectoryError:
        print('ERROR: The file is a directory.\n')
        result = 1
    except PermissionError:
        print('ERROR: Check file access permissions.\n')
        result = 1
    except ProcessLookupError:
        print('ERROR: File locked by another process.\n')
        result = 1
    except TimeoutError:
        print('ERROR: Time out.\n')
        result = 1

    return result


# main function, runs all the tests
def main():
    n_fail = 0
    folder_name = Path(os.getcwd())  # get current working directory
    files_list = os.listdir(folder_name)
    files_list.sort()
    n_tested = 0
    for test_folder in files_list:
        if os.path.isdir(os.path.join(folder_name, test_folder)):
            if test_folder[-1] == 'u' or test_folder[-1] == 'U':
                n_fail += run_test_with_error_handling(folder_name, test_folder, mode='-q -u')
                n_tested += 1
            elif test_folder[-1] == 'l' or test_folder[-1] == 'L':
                n_fail += run_test_with_error_handling(folder_name, test_folder, mode='-q -l')
                n_tested += 1

    print("------------------------------------------")
    if n_fail > 0:
        print("({0} out of {1} testes ++++ failed +++)".format(n_fail, n_tested))
    else:
        print("{0} tests run, all passed.".format(n_tested))


# Main script (exception handling here)
if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError:
        print('ERROR: File(s) not found.\n')
    except IsADirectoryError:
        print('ERROR: The file is a directory.\n')
    except PermissionError:
        print('ERROR: Check file access permissions.\n')
    except ProcessLookupError:
        print('ERROR: File locked by another process.\n')
    except TimeoutError:
        print('ERROR: Time out.\n')

