EGADownloader
======================
Downloading files from EGA(European Genome Phenome Archive) is a terrible task.
Many failure occurs due to EGA servers, and we should watch out and re-download each file.
This script is for Shirokane HGC users who want to download many files easily in parallel.

How to run
----------
### Configure ###
Set the following variables in config.sh
```sh
# Python path, we use python 2.7
PYTHON=/usr/local/package/python/current2.7/bin/python

# Log directory for each downloading job
LOGDIR=
# ex) LOGDIR=${HOME}/log/EGADownloader/

# Java path
JAVA=
# ex) /usr/local/package/java/current7/bin/java

# Ega demo client jar path
EGA=
# ex) EGA=${HOME}/tools/packages/EGA-2.2.2/EgaDemoClient.jar
```

### Run ###
Execute the following script in your shell:
```sh

bash /home/moriyama/sftp_scripts/160521_ohvarfinder/src/compRealData/downloadEGA/runEGATools.sh \
{EGA user email address} {password} \
{EGA data set id} {output Dir} \
{encryption key} {meta data run xml dir}

# example for the {meta data xml dir}.
# In this case we downloaded meta data of EGAD00001001859 in ~/download/
# ~/download/EGAD00001001859/xmls/runs
```
We extract md5 check sum from meta data xmls.

### Output ###
{output Dir}/data: files are downloaded here.
{output Dir}/status: Status files.
{output Dir}/fileList.txt: Information of files within {EGA data set id}.

Example of {output Dir}/status is as follows.
If we want to donwload 3 files. 3 downloading jobs are submit. If 1st job finish with valid md5 check sum, {output Dir}/status/1.finish appear. If 1st job does not finish with valid md5 check sum, then {output Dir}/status/1.finish does not appear.

### Re-run ###
Because of the server system of the EGA, usually we cannot donwload all the files.
Check the number of n.finish files, and compare the number of lines in {output Dir}/fileList.txt.
```sh
ls -1 {output Dir}/status | wc -l # same as the number of successfully downloaded files.
wc -l {output Dir}/fileList.txt   # same as 1 + number of files in {EGA data set id}.
```
If all the files are not donwloaded, just re-execute in the same way. Our job script tries to download only unsuccessful files, and avoid to download successful files by checking status files.
```sh

bash /home/moriyama/sftp_scripts/160521_ohvarfinder/src/compRealData/downloadEGA/runEGATools.sh \
{EGA user email address} {password} \
{EGA data set id} {output Dir} \
{encryption key} {meta data run xml dir}

# example for the {meta data xml dir}.
# In this case we downloaded meta data of EGAD00001001859 in ~/download/
# ~/download/EGAD00001001859/xmls/runs
```