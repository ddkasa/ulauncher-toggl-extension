# Usage Guide

## Default Extension Trigger

**tgl** - Adjust as needed in Ulauncher preferences.

## Arguments

| Argument      | Description                                                                                                                                                                                                                      |    Symbol    |         Examples          |
| :------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------: | :-----------------------: |
| Name          | Description/Name of a model enclosed in double quotes.<sup>1</sup>                                                                                                                                                               |  **"..."**   |      "Time Tracker"       |
| Project       | ID or name of a project. If the name contains spaces include quotes.                                                                                                                                                             |    **@**     |         @3512351          |
| Start         | Start time of a tracker, project or report.<sup>2</sup>                                                                                                                                                                          |    **>**     |          >10:10           |
| Stop          | End time of a tracker or project.<sup>2</sup>                                                                                                                                                                                    |    **<**     |          <10:20           |
| Duration      | Duration of the tracker. Supports hours, minutes, seconds, weeks, days.                                                                                                                                                          |  **>...<**   |  >1h<, >1m<, >1w<, >1d<   |
| Tags          | Comma separated list of tags starting with a pound sign. If specifically removing tags it must be prefixed with a minus **-** sign. Can also be prefixed with a plus **+**, but will default to adding tags anyway. <sup>1</sup> |   **#...**   |     #-tag1,tag2,tag3      |
| Color         | Hex code of color. If using non-premium only the supplied colors will work.                                                                                                                                                      |   **#...**   |          #ffffff          |
| Refresh       | While directly fetch from the Toggl API if this is enabled. Most of the commands support this.                                                                                                                                   | **refresh**  |          refresh          |
| Client        | ID or name of a client. . If the name contains spaces include quotes. <sup>1</sup>                                                                                                                                               |    **$**     |         $3521315          |
| Misc. Flags   | Inverted boolean flags, so if set the will return as False. Distinct will generally filter out duplicate tracker entries if turned on and is on by default in some tracker commands.                                             | **distinct** | private, active, distinct |
| Path          | File path to a folder for exporting reports start with a tilde. <sup>3</sup> <sup>4</sup>                                                                                                                                        |    **~**     |         ~/reports         |
| Report Format | File format to save a report in.                                                                                                                                                                                                 |    **.**     |       .csv or .pdf        |
| ID            | General identifier if targeting a specific model. Can be a name or the numerical id starting. If the name contains spaces include quotes. Also used in order to search with fuzzy matching.                                      |    **:**     |     :"Random Tracker"     |
| Sort Order    | Sorting direction for listing models. Default to descending. Most commands that list models support this argument.                                                                                                               |    **^-**    |            ^-             |

<sup>1</sup> _Autocomplete is supplied._

<sup>2</sup> Supported formats are: _YYYY-MM-DDTHH:MM:SS_, _HH:MM_, _HH:MM:SS_, _YYYY-MM-DD_ plus the 12 hour equivalents with AM/PM added e.g. **>10:10 PM**. If just using time the date will default to the current date.

<sup>3</sup> Filename will default to current date and scope of report._:MM:SS_, _YYYY-MM-DD_ plus the 12 hour equivalents with AM/PM added e.g. **>10:10 PM**. If just using time the date will default to the current date.

<sup>4</sup> _Folder structure will be created if not present._

## Commands

### **Continue**

- Description: Continue the last tracker or a tracker selected from the provided list.
- Usage: `tgl continue`
- Alt-Option: List alternative trackers to continue from cache.
- Aliases: continue, cnt, cont, c
- Optional Arguments: _Start_, _ID_, _Distinct_,

---

### **Start**

- Description: Start a new tracker. <sup>1</sup>
- Usage: `tgl start "Example Tracker" >11:42 #example-tag`
- Alt-Option: List trackers a pre-fill options to be edited before starting.
- Aliases: start, stt, begin
- Required Arguments: _Description_
- Optional Arguments: _Project_, _Start_, _Tags_, _Distinct_

---

### **Stop**

- Description: Stop the current tracker.
- Usage: `tgl stop`
- Aliases: stop, end, stp
- Optional Arguments: _Stop_

---

### **Edit**

- Description: Edit the current trackers attributes. <sup>1</sup>
- Usage: `tgl edit "Example Tracker Edit" >11:50 <15:00`
- Aliases: edit, change, amend, ed
- Optional Arguments: _Description_, _Project_, _Start_, _Tags_, _Stop_, _Distinct_,

---

### **Add**

- Description: Add a new tracker with given attributes. <sup>1</sup>
- Usage: `tgl add "Example Tracker" >11:42 <12:00`
- Alt-Option: Select a tracker from cache to be used as a pre-fill option.
- Aliases: add, a, insert
- Required Arguments: _Start_, _Stop_, _Description_
- Optional Arguments: _Duration_, _Project_, _Tags_, _Distinct_,

---

### **Delete**

- Description: Delete the selected tracker selected from a provided list.
- Usage: `tgl delete`
- Aliases: delete, remove, del
- Optional Arguments: _Distinct_, _ID_,

---

### **List**

- Description: Display a list of trackers. Use one of the listed trackers for more options and details.
- Usage: `tgl list refresh`
- Alt-Option: Refresh cache and fetch new trackers.
- Aliases: list, ls, lst
- Optional Arguments: _Distinct_, _ID_,

---

### **Current**

- Description: Display the current tracker.
- Usage: `tgl current`
- Aliases: current, now, running

---

### **Refresh** <sup>5</sup>

- Description: Refresh a single tracker.
- Usage: `tgl refresh`
- Aliases: refresh, re, update
- Optional Arguments: _Distinct_, _ID_

---

### **Projects**

- Description: Display a list of subcommands related to projects.
- Usage: `tgl project`
- Aliases: projects, proj, p

#### **Subcommands**:

##### **List**

- Description: Display a list of projects. Select a project for more options/details.
- Usage: `tgl project list`
- Alt-Option: Refresh cache and fetch new projects.
- Aliases: list, ls, l
- Optional Arguments: _Active_, _ID_

##### **Add**

- Description: Add a new project. <sup>2</sup>
- Usage: `tgl project add "Example Project" #0b83d9`
- Alt-Option: Use a list of projects as pre-fill options.
- Aliases: add, a, create, insert
- Required Arguments: _Description_
- Optional Arguments: _Color_, _Client_, _Active_, _Private_

##### **Edit**

- Description: Edit an existing project. <sup>2</sup>
- Usage: `tgl project edit "Example Project Edit"`
- Aliases: edit, e, change, amend
- Optional Arguments: _Description_, _Color_, _Client_, _Active_, _Private_

##### **Delete**

- Description: Delete a project. Provides a list of projects to select from.
- Usage: `tgl project delete`
- Aliases: delete, rm, d, del
- Optional Arguments: _ID_

##### **Refresh** <sup>5</sup>

- Description: Refresh a single project model.
- Usage: `tgl project refresh`
- Aliases: refresh, re, update
- Optional Arguments: _ID_

---

### **Clients**

- Description: Display a list of subcommands related to clients.
- Usage: `tgl client`
- Aliases: client, cli

#### **Subcommands**:

##### **List**

- Description: Display a list of clients. Select a client for more options/details.
- Usage: `tgl client list`
- Alt-Option: Refresh cache and fetch new clients.
- Aliases: list, ls, lst
- Optional Arguments: _ID_

##### **Add**

- Description: Add a new client. <sup>3</sup>
- Usage: `tgl client add "Example Client"`
- Alt-Option: Use a list of clients as pre-fill options.
- Aliases: add, a, create, insert
- Required Arguments: _Description_

##### **Edit**

- Description: Edit an existing client. <sup>3</sup>
- Usage: `tgl client edit "Example Client Edit"`
- Aliases: edit, e, change, amend
- Optional Arguments: _Description_, _ID_

##### **Delete**

- Description: Delete a client. Provides a list of clients to select from.
- Usage: `tgl client delete`
- Aliases: delete, rm, d, del, remove
- Optional Arguments: _ID_

##### **Refresh** <sup>5</sup>

- Description: Refresh a single client model.
- Usage: `tgl client refresh`
- Aliases: refresh, re, update
- Optional Arguments: _ID_

---

### **Tags**

- Description: Display a list of subcommands related to tags.
- Usage: `tgl tag`
- Aliases: tag, t, tags

#### **Subcommands**:

##### **List**

- Description: Display a list of tags. Select a tag for more options/details.
- Usage: `tgl tag list`
- Alt-Option: Refresh cache and fetch new tags.
- Aliases: list, ls, lst
- Optional Arguments: _ID_

##### **Add**

- Description: Add a new tag. <sup>4</sup>
- Usage: `tgl tag add "New Tag"`
- Alt-Option: Use a list of tags as pre-fill options.
- Aliases: add, a, create
- Required Arguments: _Description_

##### **Edit**

- Description: Edit an existing tag. <sup>4</sup>
- Usage: `tgl tag edit "Edited Tag"`
- Aliases: edit, e, amend
- Optional Arguments: _Description_, _ID_

##### **Delete**

- Description: Delete a tag. Provides a list of tags to select from.
- Usage: `tgl tag delete`
- Aliases: delete, rm, d, del, remove
- Optional Arguments: _ID_

---

### **Reports**

- Description: Export & view reports on a daily, weekly or monthly basis.
- Usage: `tgl report`
- Aliases: report, stats, rep

#### **Subcommands**:

##### **Day**

- Description: View daily tracked stats and export a pdf or csv report.
- Usage: `tgl report day`
- Alt-Option: Directly export a daily report.
- Aliases: day, daily, d
- Optional Arguments: _Start_, _Path_, _Report Format_

##### **Week**

- Description: View weekly tracked stats and export a pdf or csv report.
- Usage: `tgl report week`
- Alt-Option: Directly export a weekly report.
- Aliases: week, weekly, w
- Optional Arguments: _Start_, _Path_, _Report Format_

##### **Month**

- Description: View monthly tracked stats and export a pdf or csv report.
- Usage: `tgl report month`
- Alt-Option: Directly export a monthly report.
- Aliases: month, monthly, m
- Optional Arguments: _Start_, _Path_, _Report Format_

---

### **Help**

- Description: Find out more about extensions commands.
- Usage: `tgl help <command>`
- Aliases: help, guide, hint, h

---

### Notes

- _Alt-Option_ refers to hovering a command and triggering it with `alt + enter`

<sup>1</sup> _Will provide a list of older trackers as pre fill options. These commands have a distinct flag available._

<sup>2</sup> _Will provide a list of older projects as pre fill options._

<sup>3</sup> _Will provide a list of older clients as pre fill options._

<sup>4</sup> _Will provide a list of older tags as pre fill options._

<sup>5</sup> _Will not appear unless a direct match._
