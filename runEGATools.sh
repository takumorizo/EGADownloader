#! /bin/sh
#$ -S /bin/sh
#$ -cwd
readonly DIR=`dirname ${0}`
CONFIG=${DIR}/config.sh
UTIL=${DIR}/utility.sh
source ${CONFIG}
source ${UTIL}

user=$1
password=$2
dataID=$3
outputDir=$4
encriptKey=$5
xmlMetaDataFolder=$6
parallel=${7:-25}
runTimeHours=${8:-24}

check_mkdir ${outputDir}/data
check_mkdir ${outputDir}/status

CURLOGDIR=${LOGDIR}
check_mkdir ${CURLOGDIR}
LOGSTR=-e\ ${CURLOGDIR}\ -o\ ${CURLOGDIR}
check_error $?

if [ -e ${xmlMetaDataFolder} ]; then
	echo "${PYTHON} ${DIR}/egaTools.py listFiles <user> <password> ${dataID} > ${outputDir}/fileList.txt"
	${PYTHON} ${DIR}/egaTools.py listFiles ${user} ${password} ${dataID} > ${outputDir}/fileList.txt
	check_error $?

	fileCount=$(cat ${outputDir}/fileList.txt | wc -l)
	fileCount=$(($fileCount - 1))
	echo ${fileCount}
	check_error $?

	echo "qsub -q mjobs.q,ljobs.q -pe def_slot 2 \
	-v DIR=${DIR} -v PARALLEL=${PARALLEL} -v CONFIG=${CONFIG} -v UTIL=${UTIL} -tc ${parallel} -t 1-${fileCount}:1 \
	-l s_vmem=5.6G,mem_req=5.6G -l h_rt=${runTimeHours}:00:00 ${LOGSTR} \
	${DIR}/eachFileDownload.sh ${outputDir}/fileList.txt <user> <password> ${encriptKey} ${outputDir}/data ${xmlMetaDataFolder} ${outputDir}/status"
	qsub -q mjobs.q,ljobs.q -pe def_slot 2 \
	-v DIR=${DIR} -v PARALLEL=${PARALLEL} -v CONFIG=${CONFIG} -v UTIL=${UTIL} -tc ${parallel} -t 1-${fileCount}:1 \
	-l s_vmem=5.6G,mem_req=5.6G -l h_rt=${runTimeHours}:00:00 ${LOGSTR} \
	${DIR}/eachFileDownload.sh ${outputDir}/fileList.txt ${user} ${password} ${encriptKey} ${outputDir}/data ${xmlMetaDataFolder} ${outputDir}/status
	check_error $?
else
	echo "Specify xmlMetaDataFolder!!"
	exit 1
fi

