# ghsprint

ghsprint is a Python library to simplify boring tasks of the sprint, like generating the report for sprint review. It fetches all stories from the given project board, detects which ones were pokered (they received labels with numbers in a certain time frame), detects which ones were repokered, detects what pull-requests relate to them, and detects pull-requests of that week. Finally it outputs an markdown-formatted text for copy-pasting. It takes around 20 seconds to generate a report.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install ghsprint.

```bash
pip install ghsprint
```

## Usage

```bash
python -m ghsprint --special-tags "on hold" --ignore-columns "Product Backlog" --login-name-mapper alxndrjhn:Alex,strenge:Robin --keep-columns "In Progress" ae71abf4f9a41cbb6af0005de932e265614f6a317c7 Storyboard company/some-service company/someLabel company/some_extraction
```

### Arguments
`access-token` is a [personal access-token from GitHub](https://github.com/settings/tokens), `ghsprint` requires only access to 'repo'

`project-name` is the project number, this will be fetched at stories are detected for the sprint. At the moment the number is only accessible through the [Github API Projects endpoint](https://developer.github.com/v3/projects/#list-repository-projects)

`repos` is space-separated list of owner/repository pairs, all pull-requests from this repositories will be considered for the sprint report. Example: `myownName/myRepo someOrganization/some_service`.

### Optional parameters
`--keep-columns`
list of columns names to have in the report when fetching stories from the project board, separated by commas. Example `--keep-columns "In Process"`

`--login-name-mapper TEXT`
list of mappings in the format `login_name:name_to_display,...`, to have better names in the report

`--special-tags TEXT`
list of special tags in the format `tag1,tag2,...`, this tags are mentioned if they are attached to a story or pull request. Example `--special-tags "on hold"`

`--ignore-columns`
list of columns names to ignore when fetching stories from the project board, separated by commas. Example `--ignore-columns "Product Backlog,Some other column"`

`-v` verbosity level, if not given, only the report and errors will be printed to stdout, with `-v` warnings will be printed as well, with `-vv` info messages and with `-vvv` debug messages

`-w` or `--week` is the calender week-number, if not given, the current week will be used. Example: `--week 6` will generate the report for the 6th week of the current year.

## Output
```
# title

19. June - 25. June 2019

Velocity: **X**

# Leftover stories from last week
- open  [**?(1)**] [**Service issue**](https://github.com/company/some-service/issues/123 ) Alex
   - PR open [some-service #1231 Update to `some_file.txt`](https://github.com/company/some-service/pull/1231 )
      - +1, -1, files changed: 1
      - Reviews: Richard > approved, Robin > approved

- open  [**?(5)**] [**Preview**](https://github.com/company/some-service/issues/1234 ) Alex, Some_Island
   - PR open [some-service #1210 Preview output functionality for customers](https://github.com/company/some-service/pull/1210 )
      - +1461, -153, files changed: 38
      - Reviews: Richard > changes requested, Dennis > changes requested, Emma > changes requested

- open  [**?(3)**] [**Item has two instead thingies instead of one**](https://github.com/company/some-service/issues/12 ) Emma
   - PR open [some-service #652 Less thingies](https://github.com/company/some-service/pull/652 )
      - +163, -4, files changed: 9
      - Reviews: Some_Island > changes requested, Alex > changes requested

- open  [**?(2)**] [**Get quantiles for numbers**](https://github.com/company/some-service/issues/51 ) Some_Island

# Unchanged stories
- open  [**?(None)**] [**Investigate Error**](https://github.com/company/some-service/issues/16 ) Dennis, Emma

- open  [**?(8)**] [**Create some Converter**](https://github.com/company/some-service/issues/73 ) Dennis, Richard
   - PR open [some-service #1208 some csv converter implemented](https://github.com/company/some-service/pull/484 )
      - +598, -0, files changed: 8
      - Reviews: Alex > changes requested

- open [**on hold**] [**?(None)**] [**Error message while doing something wrong**](https://github.com/company/some-service/issues/95 ) Alex, Dennis
   - PR open [someImg #167 Ignoring issues](https://github.com/company/someImg/pull/76 )
      - +8, -6, files changed: 1
      - Reviews: not reviewed

- open  [**?(3)**] [**Create Email**](https://github.com/company/some-service/issues/47 ) not assigned
   - PR open [some-service #1208 other converter](https://github.com/company/some-service/pull/214 )
      - +598, -0, files changed: 8
      - Reviews: Alex > changes requested

- open  [**?(None)**] [**Explore options**](https://github.com/company/some-service/issues/756 ) Richard, Some_Island

- open  [**?(13)**] [**Another crazy converter**](https://github.com/company/some-service/issues/4 ) Dennis, Richard
   - PR open [some-service #123 more converter](https://github.com/company/some-service/pull/123 )
      - +308, -0, files changed: 5
      - Reviews: not reviewed

- open [**on hold**] [**?(8)**] [**Tool crashing**](https://github.com/company/some-service/issues/1204 ) Alex, Dennis, Richard
```

### Format and meaning
- `[**?(2)**]` means that the story was pokered a 2 ([agile pokering](https://www.mountaingoatsoftware.com/agile/planning-poker)) and the `?`means that it was not repokered in the expected time frame.
- The names behind the stories are the usernames of the assignees of the story.
- The name behind the PR is the username of the creator of the PR

## Known issues
- Wrong settings (like access-token argument) will silently fail and give no feedback.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)
