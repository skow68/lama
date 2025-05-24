## 1. Functionality

Lama is a tool designed to detect unusual events using machine learning methods. The data source consists of device logs, and the system's output is an alert in the form of an email sent to the administrator. The application is intended for environments generating a very large number of logs, which cannot be analyzed manually. The core of the system is the [Drain3] library, responsible for machine learning operations. It is recommended to consult its documentation.

> Term "False Positive" - in the context of this application, this term refers to alerts that do not indicate an actual failure. The application's goal is to filter out events that are truly significant.

## 2. Application Components

### 2.1. Log Source

Input data consists of current log files prepared by a Syslog server (e.g., Syslog-ng, Graylog). It is advisable to pre-filter logs, e.g., by severity level, so that only important logs are analyzed.

The application assumes the existence of separate log files for each device vendor. Each device type receives a unique tag, e.g., 'cisco', 'palo', 'f5'. These tags are used in the configuration and file naming. Log file names should follow the pattern: `syslog-<tag>.log`, e.g., `syslog-cisco.log`.

###### Why separate logs by vendor?

Each vendor uses a characteristic log formatting scheme. Processing them in separate threads facilitates the learning process and reduces the number of False Positives.
*Note*: Separation is not mandatory. In smaller environments, one file and one tag, e.g., 'all', can be used.

### 2.2. Analyzer

The current log file is the input for the analyzer, which runs as a systemd service. The executable file is the `lama_log_analizer.py` script, and its invocation parameter is the vendor tag. A separate systemd service should be created for each vendor.

Example systemd service configuration for Cisco logs:

```
[Unit]
Description=Lama Log Processor Service
After=network.target

[Service]
ExecStart=/opt/lama/log_processor.py cisco
WorkingDirectory=/opt/lama/
User=lamauser
Group=lamauser
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 2.3. Alerting

The `raport.py` script is responsible for notifying the administrator and is run cyclically from Crontab. The frequency of execution should be sufficiently high, e.g., once per minute. The script sends an email with logs classified as anomalies. Several mechanisms limit the number of emails sent to protect the mailbox:

* Line limit in the message (max\_lines)
* Emails are sent no more than once per minute
* Repeated logs are not sent again for an hour

As a result, not all logs are included in the emails. However, this is not the main purpose of these notifications. Their aim is to alert about unusual events. Detailed log analysis should be performed using specialized tools.

> Note: The mailbox will only be protected by the first two mechanisms if a device starts sending a large number of logs that:
> \-- contain a variable element such as a process ID that changes in every log
> \-- are classified as anomalies
> In such a case, emails will be sent continuously until the system is trained by marking these logs as normal.

### 2.4. Training

The system requires training the machine learning algorithm by providing logs representing normal operation. This is handled by the `train` script, which takes two arguments: a log file and a vendor tag.

Command sequence:

```
sudo systemctl <stop systemd_service_name>
./train <file_with_logs> <tag>
sudo systemctl start <systemd_service_name>
```

Where:

* *systemd\_service\_name* - name of the systemd service analyzing logs for a given vendor
* *file\_with\_logs* - file with logs deemed uninteresting
* *tag* - label assigned to the vendor

###### Initial training strategy

As mentioned, the application is intended for environments that generate a large volume of logs. The vast majority of these do not indicate failures. Therefore, the first batch of logs used to train the system will be relatively large. It is important that it does not contain logs indicating failures. One method to achieve this:

1. Archive logs from a workday
2. Wait one day to identify potential events that could be considered failures
3. If no issues are found, use the logs for initial training

Further training is performed on detected False Positives. Over time, their number decreases.

### 2.4. Reverting previously trained logs

The Drain3 library does not provide a function to undo training operations. Therefore, Lama stores the history of trained logs and model states, enabling the deletion of a specific log pattern from the trained model:

```
./revert.py <tag> "<text_to_find>"
```

Where:

* *tag* - label assigned to the device type
* *text\_to\_find* - log fragment whose pattern should be removed from the model. It should be long and specific enough to allow precise pattern identification.

### 2.5. Model Memory

Patterns learned by the model are stored in files named `drain3_state_<tag>.bin`. Their loss means the loss of all accumulated knowledge. The `lamarchive` script creates backups of these files in the directory specified in `config.ini`.

This script is usually run using Cron, e.g.:

```
0 2 * * 1-5 lamauser /opt/lama/lamarchive
```

## 3. System Configuration

#### 3.1. `config.ini` file

Contains paths to files and directories, as well as email and Syslog settings. It should be appropriately customized for the environment.

```
[persistance]
persistance_dir=/var/lama/
hash_dir=/var/lama/arch/hashes/
file_list=/var/lama/archlist
trained_dir=/var/lama/trained/
arch_dir=/var/lama/arch/
max_copies=30

[files]
alarm_cache=/var/log/lama/
day_alarm_cache=/var/log/lama/day_alarm_cache.log
lama_log=/var/log/lama/lama.log
shelf_file=/var/lama/hashes.shlv

[email]
sender=lama@example.com
receiver=someone@example.com
subject=Alarm
smtp_server=smtp.example.com
smtp_port=25
max_lines=100

[syslog]
syslog_dir=/var/log/
```

#### 3.2. `drain3.ini` file

Contains the configuration for the Drain3 library, including rules for masking variable parts of logs (e.g., IP addresses, serial numbers, session IDs). Masking is essential for reducing the number of false positives by generalizing log patterns. Masking is used for machine learning and classification purposes and not for the content of logs sent in alerts.

The file provided in the repository contains sample rules for F5, Cisco, and Palo Alto devices. Masking rules should be adjusted to suit the specifics of your environment and logs.

## 4. Quick Installation Guide

1. Group devices by vendor and assign appropriate tags (e.g., cisco, paloalto, f5).
2. Modify the `config.ini` file and create the specified directories with appropriate permissions.
3. Configure the Syslog server to save logs to files named `syslog-<tag>.log` in the directory defined in `config.ini` (`syslog_dir`).
4. Create systemd services for each defined tag (device vendor) using the example in section 2.2.
5. Add the `raport.py` script to scheduled tasks (Crontab).
6. Add the `lamarchive` script to scheduled tasks (Crontab).
7. Perform the initial training of the system using the `train` script for each tag.

## 5. System Architecture Diagram

![Alt Text](schema.jpg)

[//]: # "Library links"
[Drain3]: https://github.com/logpai/Drain3
