#!/system/bin/python3

import datetime
from pathlib import Path
import re
import sys
from typing import List

import check_utils as cu

config_obj = cu.Config.make_config()

Path(config_obj['out_dir']).mkdir(parents=True, exist_ok=True)

case_pattern = r'^test ([0-9]+)'
p_pattern = r'^.*OK \([0-9]+\s+out of [0-9]+, remaining: [0-9:]+, took ([0-9\.]+)s, duration: [0-9:]+\)'
f_pattern = r'^.*[0-9]+: stderr FAILED:'
s_pattern = r'^.*SKIPPED:\s+(.*)$'

# Nothing better to report for suite name...
suite = 'test'
timestamp = datetime.datetime.now().isoformat()

passed_cases: List[cu.PassedCase] = []
failed_cases: List[cu.FailedCase] = []
skipped_cases: List[cu.SkippedCase] = []

case = None
with open(config_obj['out_dir'] + '/' + config_obj['package'] + '.txt', 'w') as out:
    for line in sys.stdin:
        if match := re.match(case_pattern, line):
            case = match.group(1).strip()

            if match := re.match(s_pattern, line):
                message = match.group(0)

                skipped_cases.append(cu.SkippedCase(case, '', [], [], message))

                case = None
        elif case is not None and (match := re.match(p_pattern, line)):
            time = match.group(1).strip()

            passed_cases.append(cu.PassedCase(case, '', time, ''))

            case = None
        elif case is not None and (match := re.match(f_pattern, line)):
            # It will be hard to parse the error message reliably.
            failed_cases.append(cu.FailedCase(case, '', '', '', '', ''))

            case = None

        out.write(line)

passed_suites = [cu.PassedSuite(suite, '', timestamp, passed_cases)]
failed_suites = [cu.FailedSuite(suite, '', timestamp, failed_cases)]
skipped_suites = [cu.SkippedSuite(suite, '', timestamp, skipped_cases)]

xml_report = cu.JUnitXML.make_from_passed(passed_suites)
xml_report += cu.JUnitXML.make_from_failed(failed_suites)
xml_report += cu.JUnitXML.make_from_skipped(skipped_suites)

xml_report.write(Path(config_obj['out_dir']).joinpath(config_obj['package'] + '.xml'))

if xml_report.is_success():
    exit(cu.CheckExit.EXIT_SUCCESS)

exit(cu.CheckExit.EXIT_FAILURE)
