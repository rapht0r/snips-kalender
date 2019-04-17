# snips-kalender
I've tested this skill using a Synology Diskstation. [This guide](https://www.synology.com/de-de/knowledgebase/DSM/tutorial/Collaboration/How_to_host_a_calendar_server_using_the_Synology_NAS) shows how to setup the CalDav server. The Synology [Calendar App](https://www.synology.com/de-de/dsm/feature/calendar) may also work, but wasn't tested by me.

## Features
This skill is able to read out appointments from a caldav server using a specified date. Examples:
*  Welche Termine habe ich am `18.08.2019`?
*  Was ist für `morgen` geplant?
*  Was ist `heute` los?

## Configuration

You have to configure the caldav server and the credentials to access it during installation or later by editing the config.ini file. The following parameters are relevant: 
* caldav_url: The url to the server, e.g. https://server.example.com:port/Kalender
* user: username to access the server
* password: the password of the user 
* ssl_verify: True, if the ssl connection should be verified. False, if the server is using self signed certificates.

The content of the `config.ini` file could look like this:

```
[secret]
caldav_url = https://diskstation:5009/share/Kalender
user = John
password = 5dr8ftc9vzu0biun
ssl_verify = True
```
