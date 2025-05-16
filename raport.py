#!/bin/python3
import sys
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os.path import dirname
import hashlib
import shelve
import datetime
from lib.toolkit import remove_datetime
import configparser
import re
import glob
"""Script should be executed by a cron. It sends alarming mail.
Following methods are implemented to protect mail boxes from ovelloading:
- At most 40 lines of text are sent.
- Each line of text is remembered between script executions and it is sent no more frequently than 1 our after its first apperance. Shelve structure is used as the memory (as disk file).
  Hash of line is stored rather the text itsef. The hash is connected with the time of its apperance in the form of dictionary.
"""
def send_email(subject, body, sender, receiver):
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = subject 
    message.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        text = message.as_string()
        receiver_list = receiver.split(", ")
        server.sendmail(sender, receiver_list, text)
        server.quit()
        logger.info('Email sent successfully.')
    except Exception as e:
        logger.error(f'Failed to send email: {e}')
def get_md5_hash(text):
    """Generate an MD5 hash for a given text."""
    hasher = hashlib.md5()
    hasher.update(text.encode('utf-8'))  # Encode the text to bytes
    return hasher.hexdigest()
def clean_old_entries(shelf, expiration_delta=datetime.timedelta(hours=1)):
    """Remove entries older than the specified time delta directly from an open shelf.
    input: Object pointing to the shelve file. Expiration time for entries in shelve structure.
    output: no output
    """
    keys_to_delete = []
    for key, timestamp in shelf.items():
        if datetime.datetime.now() - timestamp > expiration_delta:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del shelf[key]
    logger.info(f"Cleaned {len(keys_to_delete)} old entries.")
def remove_variable(text):
    """Remove parts of log content that vary in each log. A method against duplicating email messages with similar logs.
    Useful when:
    - important logs appear in large quantities and they are almost the same (apart from numeric parts)
    - not important logs appear in large quantities and they are almost the same and they haven't yet been put into learning procedure.
    Used only when hash of log is created. Don't mistake this funcionality for what drain3 does.
    """
    #Rather risky assumption that parts of 4 or more digits are not important for log meaning, but they may change frequently making each log unique.
    #In consequence, this may cause email flood.
    patterns = [
        r'\d{4,}' #matches 4 digits or more
    ]
    # Compile all patterns into a single regex
    combined_pattern = re.compile('|'.join(patterns)) 
    # Substitute occurrences of the date/time patterns with an empty string
    cleaned_text = re.sub(combined_pattern, '', text)
    return cleaned_text
def update_shelf(text, shelf):
    """Update the shelf with new text hash if not already present.
    input: Alarming log line without date and time fields. Shelve object containing dictionary 'log_line_hash'->'time_of_hash_creation'
    output:
    """
    #variables for information purposes only; used by logger:
    global hash_already_exists
    global new_hash_detected
    #remove numeric frequently changing parts of log content (i.e. pid); protection against email flood:
    text = remove_variable(text)
    text_hash = get_md5_hash(text)
    current_time = datetime.datetime.now()
    if text_hash in shelf:
        hash_already_exists += 1
        return False
    else:
        new_hash_detected += 1
        shelf[text_hash] = current_time
        return True
def prepare_content(text_file):
    """
    input: A path to the file contaning alarming logs.
    output: A string no longer than 40 lines and stripped of any date and time fields.
    """
    #Returns content of a text file or a part of it if it is longer than max_lines
    file_content = []
    try:
        with open(text_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logger.info(f"Error accessing file {text_file}: {e}")
        exit()
    line_count = 0
    # Add to list up to a maximum of fragment_size of lines
    for line in lines:
        line = remove_datetime(line)
        file_content.append(line)
        #print(line.strip())
        line_count += 1
        if line_count == fragment_size:
            break
    return file_content
def main():
    """
    Sends a mail. Empties file with alarming logs.
    """
    alarm_file_pattern = f"{alarm_dir}/alarm-*.log"
    alarm_files = glob.glob(alarm_file_pattern)
    mail_content = ''
    for alarm_file in alarm_files:
        content = prepare_content(alarm_file)
        with shelve.open(shelf_file, writeback=True) as shelf:
            clean_old_entries(shelf)
            for line in content:
                if update_shelf(line, shelf):
                    mail_content = mail_content + line
                #(file_content.encode("utf-8"))
        logger.info(f"New hashes detected: {new_hash_detected}. Hashes already existed: {hash_already_exists}")
        #empties the file:
        try:
            with open(alarm_file, 'w'):
                pass
        except Exception as e:
            logger.error(f"Failed to clear alarm file: {alarm_file}")
            exit()
        try:
            day_alarm_cache = open(day_alarm_logfile, "a", encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to open day alarm cache: {e}")
        day_alarm_cache.write(mail_content)
        if mail_content:
            send_email(email_subject, mail_content, email_sender, email_receiver)
        else:
            logger.info("Nothing to send this time.")
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(f"{dirname(__file__)}/config.ini")
    alarm_dir = config['files']['alarm_cache']
    day_alarm_logfile = config['files']['day_alarm_cache']
    shelf_file = config['files']['shelf_file']
    #alarm_logfile = ['alarm_cache.log', 'alarm_cache_palo.log','alarm_cache_f5.log','alarm_cache_cisco.log']
    #md5_current_file = "/usr/local/bin/lama/mail_content.md5"
    email_sender = config['email']['sender']
    email_receiver = config['email']['receiver']
    email_subject = config['email']['subject']
    smtp_server = config['email']['smtp_server']
    smtp_port = config['email']['smtp_port']
    fragment_size = config['email']['max_lines']  # max log lines in one mail message
    #md5 = hashlib.md5()
    hash_already_exists = 0
    new_hash_detected = 0
    logger = logging.getLogger('raport')
    logger.setLevel(logging.INFO)
    #handlerf = logging.FileHandler('/var/log/lama/lama.log')
    handlerf = logging.FileHandler(config['files']['lama_log'])
    handlerc = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handlerf.setFormatter(formatter)
    #uncomment to see logs on console
    #logger.addHandler(handlerc)
    logger.addHandler(handlerf)
    logger.info(f"Start sending alarms by email.")
    main()
