# Usage Guide

### Default Extension Trigger

**tgl** - Adjust as needed in Ulauncher preferences.

## Arguments

1. Description - Description/Name of the item enclosed in double quotes e.g. **"Time Tracker"**. <sup>1</sup>
2. Project - ID of the project to use starting with an **@** sign e.g. **@3512351**. <sup>1</sup>
3. Start Time - Start time of the tracker starting with a greater than sign e.g. **>10:10**. <sup>2</sup>
4. End Time - End time of the tracker starting with a lesser than sign e.g. **<10:20**. <sup>2</sup>
5. Duration - Duration of the tracker surrounded by a lesser than and greater than sign e.g. **>1h<**.
    - Supported formats are:
        1. Hours: *h*
        2. Minutes: *m*
        3. Seconds: *s*
        4. Milliseconds: *ms*
        5. Weeks: *w*
        6. Days: *d*
        7. Years: *y*
6. Tags - Comma separated list of tags starting with a pound sign e.g. **#tag1,tag2,tag3**. <sup>1</sup>
8. Color - Hex code of color e.g. **#ffffff**. If using non-premium only the supplied colors will work. <sup>1</sup>
7. Refresh - Whether to a refresh a list of values or not. Add **refresh** to the command to refresh cache. Most of the commands support this.
8. Client - ID of the client to use starting with an **$** sign e.g. **$3512351**. <sup>1</sup>
9. Private/Active/Distinct - Inverted boolean flags, so if set the will return as False e.g. **private**, **active**, **distinct**. 

<sup>1</sup> *Autocomplete is supplied.*

<sup>2</sup> Supported formats are: *YYYY-MM-DDTHH:MM:SS*, *HH:MM*, *HH:MM:SS*, *YYYY-MM-DD* plus the 12 hour equivalents with AM/PM added e.g. **>10:10 PM**. If just using time the date will default to the current date.



## Command Overview

1. **Continue**
- Description: Continue the last tracker or a tracker selected from the provided list.
- Alt-Option: List alternative trackers to continue from cache.
- Aliases: continue, cnt, cont, c
- Optional Arguments: *Start Time, Tracker ID*
2. **Start**
- Description: Start a new tracker. <sup>1</sup>
- Alt-Option: List trackers a pre-fill options to be edited before starting.
- Aliases: start, stt, begin
- Required Arguments: *Description*
- Optional Arguments: *Project, Start Time, Tags*
3. **Stop**
- Description: Stop the current tracker.
- Aliases: stop, end, stp
4. **Edit**
- Description: Edit the current trackers attributes. <sup>1</sup>
- Aliases: edit, change, amend, ed
- Optional Arguments: *Description, Project, Start Time, Tags* 
5. **Add**
- Description: Add a new tracker with given attributes. <sup>1</sup>
- Alt-Option: Select a tracker from cache to be used as a pre-fill option.
- Aliases: add, a, insert
- Required Arguments: *Start Time, Stop Time, Description*
6. **Delete**
- Description: Delete the selected tracker selected from a provided list.
- Aliases: delete, remove, del
7. **List**
- Description: Display a list of trackers. Use one of the listed trackers for more options and details.
- Alt-Option: Refresh cache and fetch new trackers.
- Aliases: list, ls, lst
8. **Current**
- Description: Display the current tracker.
- Aliases: current, now, running
9. **Projects**
- Description: Display a list of subcommands related to projects.
- Aliases: proj, p
- **Subcommands**:
    1. **List**
    - Description: Display a list of projects. Select a project for more options/details.
    - Alt-Option: Refresh cache and fetch new projects.
    - Aliases: list, ls, l
    2. **Add**
    - Description: Add a new project. <sup>2</sup>
    - Alt-Option: Use a list of projects as pre-fill options.
    - Aliases: add, a, create, insert
    - Required Arguments: *Description*
    - Optional Arguments: *Color*, *Client*, *active*, *private*
    3. **Edit**
    - Description: Edit an existing project. <sup>2</sup>
    - Aliases: edit, e, change, amend
    - Optional Arguments: *Description*, *Color*, *Client*, *active*, *private*
    4. **Delete**
    - Description: Delete a project. Provides a list of projects to select from. 
    - Aliases: delete, rm, d, del
10. **Clients**
- Description: Display a list of subcommands related to clients.
- Aliases: clients, c, cli
- **Subcommands**:
    1. **List**
    - Description: Display a list of clients. Select a client for more options/details.
    - Alt-Option: Refresh cache and fetch new clients.
    - Aliases: list, ls, l
    2. **Add**
    - Description: Add a new client. <sup>3</sup>
    - Alt-Option: Use a list of clients as pre-fill options.
    - Aliases: add, a, create, insert
    - Required Arguments: *Description*
    3. **Edit**
    - Description: Edit an existing client. <sup>3</sup>
    - Aliases: edit, e, change, amend
    - Optional Arguments: *Description*
    4. **Delete**
    - Description: Delete a client. Provides a list of clients to select from. 
    - Aliases: delete, rm, d, del, remove
11. **Tags**
- Description: Display a list of subcommands related to tags.
- Aliases: tag, t, tags
- **Subcommands**:
    1. **List**
    - Description: Display a list of tags. Select a tag for more options/details.
    - Alt-Option: Refresh cache and fetch new tags.
    - Aliases: list, ls, l
    2. **Add**
    - Description: Add a new tag. <sup>4</sup>
    - Alt-Option: Use a list of tags as pre-fill options.
    - Aliases: add, a, create
    - Required Arguments: *Description*
    3. **Edit**
    - Description: Edit an existing tag. <sup>4</sup>
    - Aliases: edit, e, amend
    - Optional Arguments: *Description*
    4. **Delete**
    - Description: Delete a tag. Provides a list of tags to select from. 
    - Aliases: delete, rm, d, del, remove
12. **Help**
- Description: Find out more about extensions commands.
- Usage: `tgl help <command>`
- Aliases: help, guide, hint, h

### Notes
<sup>1</sup> *Will provide a list of older trackers as pre fill options. These commands have a distinct flag available.*

<sup>2</sup> *Will provide a list of older projects as pre fill options.*

<sup>3</sup> *Will provide a list of older clients as pre fill options.*

<sup>4</sup> *Will provide a list of older tags as pre fill options.*
