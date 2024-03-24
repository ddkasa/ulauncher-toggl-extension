# Usage Guide

### Default Extension Trigger

**tgl** - Adjust as needed in Ulauncher preferences.

## Arguments

1. Description - Description of an item enclosed in double quotes e.g. **"Time Tracker"**.
2. Project - ID or name of the project to use starting with an **@** sign e.g. **@3512351**.
3. Start Time - Start time of the tracker starting with a greater than sign e.g. **>10:10**.
4. End Time - End time of the tracker starting with a lesser than sign e.g. **<10:20**.
5. Duration - Duration of the tracker surrounded by a lesser than and greater than sign e.g. **>1h10m<**.
6. Tags - Comma separated list of tags starting with a pound sign e.g. **#tag1,tag2,tag3**.
7. Refresh - Whether to a refresh a list of values or not. Add refresh to the command to refresh.

## Command Overview

1. **Continue**
- Description: Continue the last tracker or a tracker selected from the provided list.
- Aliases: continue
- Optional Arguments: *Start Time, Tracker ID*
2. **Start**
- Description: Start a new tracker.
- Aliases: start
- Required Arguments: *Description*
- Optional Arguments: *Project, Start Time, Tags*
3. **Stop**
- Description: Stop the current tracker.
- Aliases: *stop, end*
4. **Edit**
- Description: Edit the current trackers attributes.
- Aliases: edit, now
- Optional Arguments: *Description, Project, Start Time, Tags* 
5. **Add**
- Description: Add a new tracker with given attributes.
- Aliases: add
- Required Arguments: *Start Time, Stop Time, Description*
6. **Delete**
- Description: Delete the selected tracker selected from a provided list.
- Aliases: delete, remove
7. **Report**
- Description: Generates a total report of all trackers within the last days.
- Aliases: report, sum
8. **List**
- Description: Display a list of trackers.
- Aliases: list
- Optional Arguments: *refresh*
9. **Projects**
- Description: Display a list of projects.
- Aliases: projects
- Optional Arguments: *refresh*
10. **Help**
- Description: Display a list of hints on how to use the extension.
- Aliases: help

