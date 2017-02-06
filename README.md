# wifi-evaluator
## Information
Wireless Networks &amp; Mobile Communitcation  
Athens University of Economics and Business (AUEB)  

Philip Maurer &amp; Elias Zervudakis  
Licence: MIT License
Platform: macOS

## Description
This application was developed for the course "Wireless Networks &amp; Mobile Communitcation" at the Athens University of Economics and Business (AUEB).  

It utilizes „airport“ tool included with macOS for capturing traffic in „managed mode". Alternatively, on windows and linux/unix one could use „tcpdump“ instead for capturing traffic in „managed mode". We have not implemented this options.

In a second step, the Wireshark command line tool "thsark“ is for reading pcap files and exporting the needed information to a csv-file.


In a last step, our custom analyzing part processes the csv-file.

## Usage info
First create a symlink from `/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport` to `/usr/local/bin/`:

```
# ln -s /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport /usr/local/bin/airport
```
Second install tshark:
```
brew install wireshark
```
Now the tool can be used:
```
usage: run.sh [[-h] | [-d] | [-c] | [-r][-a]]
-h: Display this usage info
-d: Do all: capture, read and analyze
-c: Only capture
-r <capture_id>: Read existing capture
-a <capture_id>: Analyze existing read
```