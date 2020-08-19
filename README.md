# Twilio audio download

With this script, whenever you use SurveyCTO Desktop to export CSV data, it will also download all calls recorded using the [twilio-call](https://github.com/surveycto/twilio-call/blob/master/README.md) field plug-in.

This script is currently in beta, and it has the following limitations:
1. It will not work when the twilio-call field plug-in is used in a nested repeated group (i.e. a repeat group within a repeat group).
1. It will only run automatically on Windows. However, the script will still work with Mac. See *Running on Mac* below.

If you run into issues while using this script, see *Troubleshooting* below. If you believe you have found an error with the script, email max@surveycto.com; be sure to send the "recording_log.log" file when you do so.

## Setup

### Using Python

This script uses Python 3. To make sure the file will run properly, you will have to make sure the correct application is being used to run it.

To check your default Python application, open the [*check-python.py* file]() (in this respository under "extras/other-files/"). When you open that file, one of the following situations will occur:  
**A popup appears stating the Python 3 or above is installed**: Click *OK*, and you are all set. (Python 3.8, 3.7.4, and other versions of Python 3 will work well.)  
**A popup appears stating a version of Python 2 is installed**:
1. Click *OK*.
1. Right-click the *check-python.py* file again, hover over *Open with*, and click *Choose another app*.
1. Click Python 3 (Python 3.8, 3.7.4, and other versions of Python 3 will work well), checkmark *Always use this app to open .py files*, and click *OK*. If Python 3 is not listed as an option, install Python 3 (see *Installing Python 3* below), then go back to step 2.  
**You are prompted about which application to use**: Select Python 3 (Python 3.8, 3.7.4, and other versions of Python 3 will work well). If Python 3 is not listed as an option, install Python 3 (see *Installing Python 3* below), then open the Python file again.

#### Installing Python 3

Follow these steps if Python 3 needs to be installed.
1. Open Python 3 in the Windows Store at https://microsoft.com/p/python-38/9mssztt1n39l.
1. On the right, click *Get*. Confirm you would like to open the link in the Windows Store if prompted.
1. Install Python 3.

### Setting up SurveyCTO Destkop

SurveyCTO Desktop should be properly setup by default, but you can follow these steps to be sure:
1. Open SurveyCTO Desktop.
1. On the bottom-left, open *Desktop settings*.
1. On the top, go to *EXPORT OPTIONS*.
1. Checkmark *Auto-run other processors after export.*

To learn more, check our documentation on [automatically executing outside processes](https://docs.surveycto.com/05-exporting-and-publishing-data/02-exporting-data-with-surveycto-desktop/10.outside-processes.html).

### Setting up the files

There are two files that need to be setup: A Python file called "twilio-audio-download.py", and a file called "twilio_settings.ini.template" (the second file will be renamed). Download both of these files from the "source" folder, then follow these steps:

#### Python file

This file does not have to be changed, just put into the correct location.

1. Navigate to the folder where you will be exporting your CSV data to.
1. Create a new folder called "thenrun".
1. Move the "twilio-audio-download.py" file to that folder.

#### twilio_settings.ini file

1. Navigate to the folder where you will be exporting your CSV data to (the same folder containing the "thenrun" folder).
1. Move the "twilio_settings.ini.template" file to that folder.
1. Rename that file to "twilio_settings.ini.template". At the popup, click *OK* to confirm you would like to change the file extension.
1. Open the file in a text editor, such as Notepad (double-clicking the file will usually open it in a text editor by default).
1. Make the needed changes to the "twilio_settings.ini" file (see below).
1. Save and close the file.

Below are details about the twilio_settings.ini file. Enter the needed information into the file (as mentioned in step 5) so it can run well.

##### key
**path**: Full path to the private key on your computer used to decrypt your files. This usually ends in *.pem*. If your call recordings are not encrypted, you can leave this blank.

##### file
This is information about the CSV data file that will be used to retrieve the paths to the audio files.
**form_title**: The title of the form. Make sure you are using the form title, not the form ID, since the form title is used in the CSV file name.
**rg_name**: Short for "repeat group name". If the Twilio call field is a repeated field, enter the name of the repeated field. If it is in a nested repeat group, enter the name of the top-level repeat group only.
**format**: Whether the data is being exported in `long` or `wide` format. If left blank, it will assume the data is being exported in long format.
**add_group_name**: Whether the group name is going to be added to the field name. To check this, in SurveyCTO Desktop, go to *Desktop settings* on the bottom-left, then *EXPORT OPTIONS*, and check *Treatment of enclosing groups in exports*. If *Add groups to exported field names* is selected, make this property `True`. Otherwise, it can be left blank.
**field**: The name of the field that uses the Twilio field plug-in

##### twilio
This is information about your Twilio account. Be careful about this data, since these are the credentials used to access call recordings

##### recording
**location**: Where the recordings will be exported to. If this is left blank, a folder will be created in the export folder called "Call recordings", and the files will be exported there. If the specified folder does not exist, it will be created.
**format**: Format of the downloaded recordings. This can be either `wav` or `mp3`. Note: Encrypted recordings can only be downloaded in .wav format; if `mp3` is specified, unencrypted recordings will be downloaded in .mp3 format, but encrypted recordings will be downloaded in .wav format.

## Running on Mac

Currently the script is setup to only run automatically on Windows. However, it will still work on MacOS devices. First, setup the twilio-audio-download.py and twilio_settings.ini files, and put them in the correct locations. Then, follow these steps:
1. Copy the path name of the "twilio-audio-download.py" file. To do so, navigate to it in a Finder window, right-click it, hold the *Option* key on your keyboard, then click *Copy "twilio-audio-download.py" as Pathname*.
1. Open a Terminal window (you can open a Mac search with `Cmd + space`, then search for and open "terminal").
1. In the Terminal window that appears, type `python3`, then a space, then a single quote (don't press *Return* yet).
1. Paste in the path name you had copied, and then enter a closing single quote. It will look something like this:
    python3 '/Users/username/Documents/Data exports/Twilio/files/twilio-audio-download.py'
1. Press *Return* on your keyboard. The script will run. When it is complete, you can close the Terminal window.

## Troubleshooting
If the recordings are not being created, go to the folder where the data is being exported to, and open the "recording_log.log" file. This will give you details about what happened, and what went wrong (time stamps are given in UTC, not local time).

If that file has not been created, check to make sure "thenrun" is turned on in SurveyCTO Desktop, and that Python files are set to be opened using Python 3. If you are still having trouble, paid users can [create a ticket](https://support.surveycto.com/hc/en-us/requests) with SurveyCTO support. All users can also post to the [community forums](https://support.surveycto.com/hc/en-us/community/topics/200604277-Advice-hacks-and-questions-about-using-SurveyCTO).