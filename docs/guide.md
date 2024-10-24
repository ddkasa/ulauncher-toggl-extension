# Usage Guide

## Default Extension Trigger

**tgl** - Adjust as needed in Ulauncher preferences.

## Arguments

1. Description - Description/Name of the item enclosed in double quotes e.g. **"Time Tracker"**. <sup>1</sup>
2. Project - ID of the project to use starting with an **@** sign e.g. **@3512351**. <sup>1</sup>
3. Start Time - Start time of the tracker starting with a greater than sign e.g. **>10:10**. <sup>2</sup>
4. End Time - End time of the tracker starting with a lesser than sign e.g. **<10:20**. <sup>2</sup>
5. Duration - Duration of the tracker surrounded by a lesser than and greater than sign e.g. **>1h<**.
   - Supported formats are:
     1. Hours: _h_
     2. Minutes: _m_
     3. Seconds: _s_
     4. Milliseconds: _ms_
     5. Weeks: _w_
     6. Days: _d_
     7. Years: _y_
6. Tags - Comma separated list of tags starting with a pound sign e.g. **#tag1,tag2,tag3**. <sup>1</sup>
7. Color - Hex code of color e.g. **#ffffff**. If using non-premium only the supplied colors will work. <sup>1</sup>
8. Refresh - Whether to a refresh a list of values or not. Add **refresh** to the command to refresh cache. Most of the commands support this.
9. Client - ID of the client to use starting with an **$** sign e.g. **$3512351**. <sup>1</sup>
10. Private/Active/Distinct - Inverted boolean flags, so if set the will return as False e.g. **private**, **active**, **distinct**.
11. Path - File path to a folder for exporting reports start with a tilde **~** e.g. **~/reports**. <sup>3</sup><sup>4</sup>

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
- Optional Arguments: _Start Time, Tracker ID_

---

### **Start**

- Description: Start a new tracker. <sup>1</sup>
- Usage: `tgl start "Example Tracker" >11:42 #example-tag`
- Alt-Option: List trackers a pre-fill options to be edited before starting.
- Aliases: start, stt, begin
- Required Arguments: _Description_
- Optional Arguments: _Project, Start Time, Tags_

---

### **Stop**

- Description: Stop the current tracker.
- Usage: `tgl stop`
- Aliases: stop, end, stp
- Optional Arguments: _End Time_

---

### **Edit**

- Description: Edit the current trackers attributes. <sup>1</sup>
- Usage: `tgl edit "Example Tracker Edit" >11:50 <15:00`
- Aliases: edit, change, amend, ed
- Optional Arguments: _Description, Project, Start Time, Tags, End Time_

---

### **Add**

- Description: Add a new tracker with given attributes. <sup>1</sup>
- Usage: `tgl add "Example Tracker" >11:42 <12:00`
- Alt-Option: Select a tracker from cache to be used as a pre-fill option.
- Aliases: add, a, insert
- Required Arguments: _Start Time, End Time, Description_

---

### **Delete**

- Description: Delete the selected tracker selected from a provided list.
- Usage: `tgl delete`
- Aliases: delete, remove, del

---

### **List**

- Description: Display a list of trackers. Use one of the listed trackers for more options and details.
- Usage: `tgl list refresh`
- Alt-Option: Refresh cache and fetch new trackers.
- Aliases: list, ls, lst

---

### **Current**

- Description: Display the current tracker.
- Usage: `tgl current`
- Aliases: current, now, running

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

##### **Add**

- Description: Add a new project. <sup>2</sup>
- Usage: `tgl project add "Example Project" #0b83d9`
- Alt-Option: Use a list of projects as pre-fill options.
- Aliases: add, a, create, insert
- Required Arguments: _Description_
- Optional Arguments: _Color_, _Client_, _active_, _private_

##### **Edit**

- Description: Edit an existing project. <sup>2</sup>
- Usage: `tgl project edit "Example Project Edit"`
- Aliases: edit, e, change, amend
- Optional Arguments: _Description_, _Color_, _Client_, _active_, _private_

##### **Delete**

- Description: Delete a project. Provides a list of projects to select from.
- Usage: `tgl project delete`
- Aliases: delete, rm, d, del

---

### **Clients**

- Description: Display a list of subcommands related to clients.
- Usage: `tgl client`
- Aliases: client, c, cli

#### **Subcommands**:

##### **List**

- Description: Display a list of clients. Select a client for more options/details.
- Usage: `tgl client list`
- Alt-Option: Refresh cache and fetch new clients.
- Aliases: list, ls, l

##### **Add**

- Description: Add a new client. <sup>3</sup>
- Usage: `tgl client add "Example Client"`
- Alt-Option: Use a list of clients as pre-fill options.
- Aliases: add, a, create, insert
- Required Arguments: _Description_

##### **Edit**

- Description: Edit an existing client. <sup>3</sup>
- Usage: `tgl client add "Example Client Edit"`
- Aliases: edit, e, change, amend
- Optional Arguments: _Description_

##### **Delete**

- Description: Delete a client. Provides a list of clients to select from.
- Usage: `tgl client delete`
- Aliases: delete, rm, d, del, remove

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
- Aliases: list, ls, l

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
- Optional Arguments: _Description_

##### **Delete**

- Description: Delete a tag. Provides a list of tags to select from.
- Usage: `tgl tag delete`
- Aliases: delete, rm, d, del, remove

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
- Optional Arguments: _start, path_

##### **Week**

- Description: View weekly tracked stats and export a pdf or csv report.
- Usage: `tgl report week`
- Alt-Option: Directly export a weekly report.
- Aliases: week, weekly, w
- Optional Arguments: _start, path_

##### **Month**

- Description: View monthly tracked stats and export a pdf or csv report.
- Usage: `tgl report month`
- Alt-Option: Directly export a monthly report.
- Aliases: month, monthly, m
- Optional Arguments: _start, path_

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
