# Surefire Report Diff Script

This python script aims to diff two versions of test reports generated by the surefire plugin, 
when we migrate from Junit 4 to Junit 5. 
And it will generate a html diff report in the given location.

Show optional arguments: `python main.py -h`
```
  -h, --help            show this help message and exit
  --junit4-report-dir JUNIT4DIR, -j4r JUNIT4DIR
                        Surefire test report dir for Junit4 (before change)
  --junit5-report-dir JUNIT5DIR, -j5r JUNIT5DIR
                        Surefire test report dir for Junit5 (after change)
  --html-file HTMLFILE, -html HTMLFILE
                        The target html report location, e.g. report.html, /tmp/report.html
  --verbose, -v         Enable verbose mode
```

## Quick start

run as following, you will get the diff report (report.html).
```
python main.py -j4r junit4-surefire-reports -j5r junit5-surefire-reports -v -html report.html
```

## How to get the surefire reports

When using the surefire plugin in maven, we could use `mvn test` to generate reports.
The reports lies in the `target/surefire-reports` directory.

## Note

- The script uses the test case name to compare, so we need to keep the same test case name
 when we migrate from Junit 4 to Junit 5.
- The script compare the Junit 4 reports to Jßunit 5 reports, and it will not identify the new 
 test cases from Junit 5 reports. In other words, it will only identify whether the Junit 5 tests
 contain all the Junit 4 test cases and ignore the new tests.
