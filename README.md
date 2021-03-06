__NOTE: This project is no longer under active development and uses a deprecated version of the API.__

__Use guyzmo's fork at https://github.com/guyzmo/pyoctopart moving forward.__

A simple Python client frontend to the Octopart public REST API.

For detailed API documentation, refer to the Octopart API documentation:
http://octopart.com/api/documentation

A note on API method/argument syntax:

There are a number of arguments in the Octopart API documentation which contain periods in their names.
When passing these arguments from Python, substitute an underscore for any periods.

Similarly, substitute underscores for backslashes in method names.

For example:
>>> o = Octopart()
>>> o.parts_get(1881614252472, optimize.hide_datasheets=True)
SyntaxError: keyword can't be an expression

Instead, pass the argument as:
>>> o.parts_get(1881614252472, optimize_hide_datasheets=True)

The library will perform the translation internally.

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
