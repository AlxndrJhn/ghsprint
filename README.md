# ghsprint

ghsprint is a Python library to simplify boring tasks of the sprint, like generating the report for sprint review. It fetches all stories from the given project board, detects which ones were pokered (they received labels with numbers in a certain time frame), detects which ones were repokered, detects what pull-requests relate to them, and dectects pull-requests of that week. Finally it outputs an markdown-formatted text for copy-pasting. It takes around 20 seconds to generate a report.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install ghsprint.

```bash
pip install ghsprint
```

## Usage

```bash
python -m ghsprint --ignore-columns "Product Backlog" <github access token> <project id> <owner>/<repo> <owner>/<repo>
```

### Arguments
`access-token` is a [personal access-token from GitHub](https://github.com/settings/tokens), `ghsprint` requires only access to 'repo'

`project-id` is the project number, this will be fetched at stories are detected for the sprint. At the moment the number is only accessible through the [Github API Projects endpoint](https://developer.github.com/v3/projects/#list-repository-projects)

`repos` is space-separated list of owner/repository pairs, all pull-requests from this repositories will be considered for the sprint report. Example: `myownName/myRepo someOrganization/some_service`.

### Optional parameters
`--ignore-columns`
list of columns names to ignore when fetching stories from the project board, separated by commas. Example `--ignore-columns "Product Backlog,Some other column"`

`-v` verbosity level, if not given, only the report and errors will be printed to stdout, with `-v` warnings will be printed as well, with `-vv` info messages and with `-vvv` debug messages

`-w` or `--week` is the calender week-number, if not given, the current week will be used. Example: `--week 6` will generate the report for the 6th week of the current year.


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
