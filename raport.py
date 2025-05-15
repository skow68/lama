import json
import logging
import os
import sys
from os.path import dirname
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
from drain3.file_persistence import FilePersistence
import argparse
from lib.toolkit import remove_datetime
import configparser
import hashlib
import shutil
#Script for training ML based on log file that doesn't contain entries related to failures.
#Input file may or may not contain date time fields.
 
def hash_and_copy(log_file):
  """
  The content of the script is a part of 'train' script. For testing only.
  Calculates the MD5 hash of a log file. Originaly the file is parameter of 'train' script. Copies it to a new file named with the hash.
 Adds name of the copied file to the list maintained in the list.txt file. Copies also drain3 bin file named with the hash.
  Finally, directory 'trained' will contain training log file and current bin file (updated after training)
 
  Args:
    logfile (str): The path to the file to be processed.
 
  Returns:
   
  """
  try:
    # Calculate the MD5 hash of the file
    hasher = hashlib.md5()
    with open(log_file, 'rb') as file:
        while True:
            chunk = file.read(4096)  # Read in chunks to avoid loading large files into memory
            if not chunk:
                break
            hasher.update(chunk)
    md5_hash = hasher.hexdigest()
 
    #Create the new file path from the hash
   #file_name = os.path.basename(log_file)
    trained_dir_type = f"{trained_dir}/{args.type}"
    #file_extension = os.path.splitext(file_name)[1]
    if not os.path.exists(trained_dir_type):
        try:
            os.makedirs(trained_dir_type)
            logger.info(f"Directory '{trained_dir_type}' created.")
        except PermissionError:
            logger.error(f"Error: Permission denied. Run the script with elevated privileges (sudo).")
            return None
        except Exception as e:
            print(f"Error creating directory: {e}")
            return None
    filename_copy = f"{trained_dir_type}/{md5_hash}.log"
    #filename_copy = os.path.join(os.path.dirname(trained_dir_type), f"{md5_hash}.log")
    #new_filepath = os.path.join(os.path.dirname(log_file), filename_copy)
    #Copy the original file to the new file name
    try:
        shutil.copy2(log_file, filename_copy)
    except PermissionError:
        logger.error(f"Error: Permission denied while copying.")
        return
    except Exception as e:
        logger.error(f"Error copying file: {e}")
        return
    logger.info(f"File '{log_file}' hashed to '{md5_hash}' and copied to '{filename_copy}'")
    #Add log filename to the list of all file names.
    list_file_path = f"{trained_dir}{args.type}/list.txt"   
    with open(list_file_path, 'a', encoding="utf-8") as list_file:
        logger.info(f"Updating list of files {list_file}")
        list_file.write(f"{md5_hash}\n") 
  except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None
 
  try:
    # The same for the persisatnce bin file that has been created upon processing the above log file
    persistence_file = f"{persistance_dir}/drain3_state_{args.type}.bin"
    persistance_file_copy = f"{trained_dir_type}/{md5_hash}.bin"
    shutil.copy2(persistence_file, persistance_file_copy)
    logger.info(f"File '{persistence_file}' hashed to '{md5_hash}' and copied to '{persistance_file_copy}'")
    return md5_hash
  except FileNotFoundError:
    logger.info(f"Error: Persistance bin file not found at {persistence_file}")
    return None
  except Exception as e:
    logger.info(f"An error occurred: {e}")
    return None
 
def main():
    #logger.removeHandler(handlerf)
    if os.path.isfile(persistence_bin):
        try:
            shutil.copy2(persistence_bin, persistence_tmp)
        except PermissionError:
            logger.error(f"Error: Permission denied while creating temporary archive of {persistence_bin}.")
            return
        except Exception as e:
            logger.error(f"Error copying file: {e}")
            return
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
    """###to comment when creating test or temporary bin file
    result = hash_and_copy(in_log_file)
    if result == None:
        logger.info(f"Copy of log and bin files couldn't be done due to errors. So the drain3 state is inconsistent with the state archived in \
            {trained_dir} directory. Revert function (revert.py) may not work properly. Copy manualy {persistence_tmp} to {persistence_bin} \
                in order to go back to original state")
    else:
        if os.path.isfile(persistence_tmp):
            os.remove(persistence_tmp)
    ### comment end
    """
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(f"{dirname(__file__)}/config.ini")
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="File name with training logs")
    parser.add_argument("type", choices=['f5', 'palo', 'cisco'], help="Type of training logs. Can be: f5, palo, cisco")
    args = parser.parse_args()
    persistence_type = "FILE"
    in_log_file = args.file
    persistance_dir = config['persistance']['persistance_dir']
    trained_dir = config['persistance']['trained_dir']
    persistence_bin = f"{persistance_dir}/drain3_state_{args.type}.bin"
    persistence_tmp = f"{persistence_bin}.tmp"
    persistence = FilePersistence(persistence_bin)
    drain3_config = TemplateMinerConfig()
    drain3_config.load(f"{dirname(__file__)}/drain3.ini")
    drain3_config.profiling_enabled = False
    template_miner = TemplateMiner(persistence, drain3_config)
    logger = logging.getLogger('train')
    logger.setLevel(logging.INFO)
    #handlerf = logging.FileHandler('/var/log/lama/lama.log')
    handlerf = logging.FileHandler(config['files']['lama_log'])
    handlerc = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handlerf.setFormatter(formatter)
    logger.addHandler(handlerc)
    #do zakomentowania w przypadku obróbki bardzo dużych logów:
    logger.addHandler(handlerf)
    logger.info(f"Start training process for {args.type}. Using file {args.file}")
    logger.info(f"{len(drain3_config.masking_instructions)} masking instructions are in use")
    main()
