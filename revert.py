#!/bin/python3
import os
import shutil
import logging
import configparser
import json
import sys
from os.path import dirname
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence
import argparse
from lib.toolkit import remove_datetime
"""
This script searches for a specific string in all previously trained '.log' files and prompts the user to delete lines containing that string. The files are listed in a dedicated
file named list.txt. This list maintains the chronological order of the files. If a line is deleted, it is recorded to avoid prompting the user multiple times when deleting
the same line across different files. If a file becomes empty after deletions, it is removed. The first log file containing the searched string is also recorded.
Starting from this file, all more recent files are subject to training. Before starting the training process, the drain3 binary file corresponding to the first log file is copied
to the production directory. The purpose of these operations is to avoid training log files that are not affected by the deletion of the searched string.
 
Usage:
    Run the script and provide the directory to search and the string to search for when prompted.
Example:
    Enter the directory to search: /path/to/directory
    Enter the string to search for: target_string
"""
def train(in_log_file, template_miner):
    #logger.removeHandler(handlerf)
    with open(in_log_file, 'r', errors = "replace") as f:
        lines = f.readlines()
    for line in lines:
        line = line.rstrip()
        processed_line = remove_datetime(line)
        logger.info(f"Log line: {processed_line}")
        result = template_miner.add_log_message(processed_line)
        result_json = json.dumps(result)
        logger.info(result_json)
        template = result["template_mined"]
        params = template_miner.extract_parameters(template, processed_line)
        logger.info(f"Parameters: {str(params)}\n")
    logger.info("SUMMARY:")
    sorted_clusters = sorted(template_miner.drain.clusters, key=lambda it: it.size, reverse=True)
    for cluster in sorted_clusters:
        logger.info(cluster)
       
def main(search_string, type):
    logger.info(f"String to find: {search_string}")
   deleted_lines = set()
    first_occurrence_file = None
    directory = f"{trained_dir}{type}/"
    # Read the list of file names from list.txt
    list_file_path = os.path.join(directory, 'list.txt')
    with open(list_file_path, 'r') as list_file:
        file_names = list_file.read().splitlines()
    #for files in the list.txt
    for file in file_names:
        file_path = os.path.join(directory, f"{file}.log")
        with open(file_path, 'r') as f:
            lines = f.readlines()
        new_lines = []
        file_modified = False
        for line in lines:
            if search_string in line:
                if first_occurrence_file is None:
                    first_occurrence_file = file
                    logger.info(f"First occurrence found in: {first_occurrence_file}")
                #if line in deleted_lines:
                if any(search_string in deleted_line for deleted_line in deleted_lines):
                    file_modified = True
                    continue
                else:
                    logger.info(f"Found in {file_path}: {line.strip()}")
                    user_input = input("Delete this line? (YES/NO): ")
                    if user_input.strip().upper() == 'YES':
                        deleted_lines.add(line)
                        file_modified = True
                        continue
            new_lines.append(line)
 
        if file_modified:
            if new_lines:
                logging.info(f"Removing line with searched string from file {file_path}")
                with open(file_path, 'w') as f:
                    f.writelines(new_lines)
            else:
                os.remove(file_path)
                logging.info(f"Removing empty file: {file_path}")
                file_names.remove(file)
 
    if first_occurrence_file:
        #if given string has been found
        new_persistance_bin = f"{persistance_dir}drain3_state_{type}.bin"
        logging.info(f"The new drain3 bin file to start traing from is: {new_persistance_bin}")
        logging.info(f"Copying the new bin file to {persistance_dir}")
        shutil.copy2(F"{directory}{first_occurrence_file}.bin", new_persistance_bin)
        start_index = file_names.index(first_occurrence_file)
        persistence = FilePersistence(new_persistance_bin)
       drain3_config = TemplateMinerConfig()
        drain3_config.load(f"{dirname(__file__)}/drain3.ini")
        drain3_config.profiling_enabled = False
        template_miner = TemplateMiner(persistence, drain3_config)
        logging.info("Training log files from the first searched string occurrence onwards:")
        for file in file_names[start_index:]:
            file_path = os.path.join(directory, f"{file}.log")
            #tutaj robimy train
            logging.info(f"Training {file_path}:")
            train(file_path, template_miner)
            print(file)
    # Update list.txt
    with open(list_file_path, 'w') as list_file:
        list_file.write('\n'.join(file_names))
 
if __name__ == "__main__":
    #directory = '/opt/devel/lama/var/lama/trained/f5/'
    config = configparser.ConfigParser()
    config.read(f"{dirname(__file__)}/config.ini")
    logger = logging.getLogger('revert')
    logger.setLevel(logging.INFO)
    #handlerf = logging.FileHandler('/var/log/lama/lama.log')
    handlerf = logging.FileHandler(config['files']['lama_log'])
    handlerc = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handlerf.setFormatter(formatter)
    logger.addHandler(handlerc)
    logger.addHandler(handlerf)
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=['f5', 'palo', 'cisco'], help="Type of training logs. Can be: f5, palo, cisco")
    parser.add_argument("to_remove", help="Text to find in previously trained logs. The line with the text will be removed from the database of normal behaviour.")
    args = parser.parse_args()
    #logger.info(f"Start training process for {args.type}.")
    search_string = args.to_remove #'my33text44to_find'
    type = args.type
    config.read(f"{dirname(__file__)}/config.ini")
    trained_dir = config['persistance']['trained_dir']
    persistance_dir = config['persistance']['persistance_dir']
    main(search_string, type)
