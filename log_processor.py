#!/bin/python3
from os.path import dirname
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence
import argparse
import logging
import sys
from sh import tail
import concurrent.futures
from lib.toolkit import remove_datetime
import configparser
config = configparser.ConfigParser()
config.read(f"{dirname(__file__)}/config.ini")
parser = argparse.ArgumentParser()
parser.add_argument("type", choices=['f5', 'palo', 'cisco'], help="Type of training logs. Can be: f5, palo, cisco")
args = parser.parse_args()
alarm_logfile = f"{config['files']['alarm_cache']}/alarm-{args.type}.log"
persistance_dir = config['persistance']['persistance_dir']
persistence = FilePersistence(f"{persistance_dir}/drain3_state_{args.type}.bin")
syslog_dir = config['syslog']['syslog_dir']
log_file = f"{syslog_dir}syslog-{args.type}"
drain3_config = TemplateMinerConfig()
drain3_config.load(f"{dirname(__file__)}/drain3.ini")
drain3_config.profiling_enabled = False
file = open(alarm_logfile, "a", encoding="utf-8")
template_miner = TemplateMiner(persistence, drain3_config)
def line_processor(line):
    """
    Function used by single thread
    input: line from syslog
    output: line in alarm file
    """
    cleared_line = remove_datetime(line)
    cluster = template_miner.match(cleared_line, "fallback")
    if cluster is None and line != '':
        file.write(line)
        file.flush()
def main():
    try:
        executor = concurrent.futures.ThreadPoolExecutor()
        #na mgt3 domyslny max_workers jest 20
        for line in tail("-f", "-n0", log_file, _iter=True):
            #print(f"line from tail: {line}")
            future = executor.submit(line_processor, line)
            if future is None:
                print("Pool of workers was exhausted.")
    except Exception as e:
        file.write(f"An error occurred: {e}")
 
if __name__ == "__main__":
    #logging.basicConfig(level=logging.INFO, filename=config['files']['lama_log'], filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('log_processor')
    logger.setLevel(logging.INFO)
    handlerf = logging.FileHandler(config['files']['lama_log'])
    #handlerc = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handlerf.setFormatter(formatter)
    #logger.addHandler(handlerc)
    logger.addHandler(handlerf)
    logging.info('Run Lama Log Processor.')
    main()
