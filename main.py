import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import logging
import sys


class TestSuite:
    def __init__(self, class_name, total_num, error_num, failure_num, skipped_num, test_cases):
        self.class_name = class_name
        self.total_num = total_num
        self.error_num = error_num
        self.failure_num = failure_num
        self.skipped_num = skipped_num
        self.test_cases = test_cases

    def get_summary(self):
        return "Total %s, Failures %s, Errors %s, Skipped %s" % (self.total_num, self.failure_num, self.error_num, self.skipped_num)


def extract_test_suite(test_suite: ET.Element):
    attr = test_suite.attrib
    return TestSuite(attr['name'], attr['tests'], attr['errors'], attr['failures'], attr['skipped'],
                     extract_test_cases(test_suite))


def extract_test_cases(test_suite: ET.Element):
    cases_dict = {}
    test_cases = test_suite.findall("testcase")
    for test_case in test_cases:
        cases_dict[test_case.attrib["name"]] = get_test_case_status(test_case)
    return cases_dict


def get_test_case_status(test_case: ET.Element):
    test_error = test_case.find("error")
    if test_error is not None:
        return "error"
    test_ignore = test_case.find("skipped")
    if test_ignore is not None:
        return "skipped"
    test_failure = test_case.find("failure")
    if test_failure is not None:
        return "failure"
    return "success"


def get_reports_dict(dir):
    xml_reports = list(Path(dir).glob("*.xml"))
    logging.debug("%d XML files found in %s" % (len(xml_reports), dir))
    test_suite_dict = {}
    for xml_report in xml_reports:
        test_suite_root = ET.parse(xml_report).getroot()
        test_suite_entity = extract_test_suite(test_suite_root)
        test_suite_dict[test_suite_entity.class_name] = test_suite_entity
    return test_suite_dict


def diff_dict(junit4_dict, junit5_dict, html):
    generate_html = html is not None

    pass_diff = True
    html_content = ""
    for test_suite_name in junit4_dict:
        junit4_test_suite = junit4_dict[test_suite_name]
        junit5_test_suite = junit5_dict.get(test_suite_name, None)
        if junit5_test_suite is not None:
            row_span = len(junit4_test_suite.test_cases) + 2

            html_content += "<tr><td rowspan=\"%d\">%s</td>" % (row_span, test_suite_name)
            first_case = True
            for test_case_name in junit4_test_suite.test_cases:
                junit4_test_case_status = junit4_test_suite.test_cases[test_case_name]
                junit5_test_case_status = junit5_test_suite.test_cases.get(test_case_name, None)
                if not first_case:
                    html_content += "<tr>"
                else:
                    first_case = False
                html_content += "<td>%s</td>" % test_case_name
                if junit5_test_case_status is not None:
                    if junit5_test_case_status == junit4_test_case_status:
                        logging.debug("%s matches." % test_case_name)
                        html_content += "<td style=\"color:green;\">O</td>"
                    else:
                        pass_diff = False
                        logging.debug("%s changes from %s to %s." % (test_case_name, junit4_test_case_status, junit5_test_case_status))
                        html_content += "<td style=\"background:#ff7575;\">X (Test status does not match.)</td>"
                    html_content += "<td>%s</td><td>%s</td>" % (junit4_test_case_status, junit5_test_case_status)
                else:
                    pass_diff = False
                    logging.debug("[%s] in [%s] Junit 4 test case lost." % (test_case_name, test_suite_name))
                    html_content += "<td colspan=\"3\" style=\"background:#ff7575;\">Junit 4 test case lost.</td>"
            logging.debug("Before: " + junit4_test_suite.get_summary())
            logging.debug("After: " + junit5_test_suite.get_summary())
            if not first_case:
                html_content += "</tr><tr>"
            summary_diff = get_summary_diff_html(junit4_test_suite, junit5_test_suite)
            html_content += summary_diff[1]
            if not summary_diff[0]:
                pass_diff = False
        else:
            pass_diff = False
            html_content += "<tr><td>%s</td><td colspan=\"4\" style=\"background:#ff7575;\">Junit 4 Test " \
                            "lost.</td></tr>" % test_suite_name
            logging.debug("[%s] Junit 4 Test lost." % test_suite_name)
    if pass_diff:
        logging.debug("Diff result : Pass")
    else:
        logging.debug("Diff result : Fail")
    if generate_html:
        html_file = open(html, "w")
        html_file.write("<!DOCTYPE html><html><head><title>Diff Result</title></head><body>"
                        "<p>%s</p><div><table border=\"1px solid\"><tr style=\"background:#c9c8c8;\"><th "
                        "rowspan=\"2\">Junit 4 Test Class</th><th rowspan=\"2\"> "
                        "Junit 4 Test Cases</th><th colspan=\"3\">Diff Result</th></tr>"
                        "<tr style=\"background:#c9c8c8;\"><th>result</th><th>Junit 4</th><th>Junit 5</th>"
                        "</tr>%s</table></div></body></html>" % (get_result_html(pass_diff), html_content))
        html_file.close()


def get_result_html(pass_diff):
    if pass_diff:
        return "Final Diff Result : <span style=\"color:green;\">PASS</span>"
    else:
        return "Final Diff Result : <span style=\"color:red;\">FAIL</span>"


def get_summary_diff_html(junit4_test_suite: TestSuite, junit5_test_suite: TestSuite):
    total_diff = get_num_diff_html(junit4_test_suite.total_num, junit5_test_suite.total_num)
    failure_diff = get_num_diff_html(junit4_test_suite.failure_num, junit5_test_suite.failure_num)
    error_diff = get_num_diff_html(junit4_test_suite.error_num, junit5_test_suite.error_num)
    skipped_diff = get_num_diff_html(junit4_test_suite.skipped_num, junit5_test_suite.skipped_num)
    pass_diff = total_diff[0] & failure_diff[0] & error_diff[0] & skipped_diff[0]
    if pass_diff:
        color = "#dddddd"
    else:
        color = "#ff7575"
    html_temp = "<td rowspan=\"2\" style=\"font-weight:900;background:%s;\">Summary</td><td colspan=\"3\">Junit " \
                "4: %s</td></tr>" % (color, junit4_test_suite.get_summary())
    html_temp += "<tr><td colspan=\"3\">Junit 5: Total %s, Failures %s, Errors %s, Skipped %s</td></tr>" % (total_diff[1], failure_diff[1], error_diff[1], skipped_diff[1])
    return pass_diff, html_temp


def get_num_diff_html(junit4_num, junit5_num):
    if junit4_num != junit5_num:
        return False, "<span style=\"color:red;\">%s</span>" % junit5_num
    else:
        return True, junit5_num


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Tiny script for comparing xml reports created by maven-surefire-plugin')
    parser.add_argument("--junit4-report-dir", "-j4r", dest="junit4Dir", help="Surefire test report dir for Junit4 (before change)")
    parser.add_argument("--junit5-report-dir", "-j5r", dest="junit5Dir", help="Surefire test report dir for Junit5 (after change)")
    parser.add_argument("--html-file", "-html", dest="htmlFile", help="The target html report location, e.g. /tmp/report.html")
    parser.add_argument("--verbose", "-v", action='store_true', help="Enable verbose mode")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    logging.debug("Junit4 report dir : %s" % args.junit4Dir)
    logging.debug("Junit5 report dir : %s" % args.junit5Dir)

    junit4_dict = get_reports_dict(args.junit4Dir)
    junit5_dict = get_reports_dict(args.junit5Dir)

    diff_dict(junit4_dict, junit5_dict, args.htmlFile)
    