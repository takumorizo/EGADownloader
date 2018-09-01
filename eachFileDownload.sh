#! /bin/sh
#$ -S /bin/sh
#$ -cwd

source ${CONFIG}
source ${UTIL}

fileListTemp=$1
user=$2
password=$3
encriptKey=$4
outputDir=$5
xmlMetaDataFolder=$6
statusDir=$7

sleep $((15*${SGE_TASK_ID}))
fileLine=$((${SGE_TASK_ID} + 1))

if [ -e ${statusDir}/${SGE_TASK_ID}.finish ]; then
    echo "${SGE_TASK_ID}th file already downloaded. Write detail below..."
    sed -n ${fileLine}p ${fileListTemp}
else
	sed -n ${fileLine}p ${fileListTemp} | cut -f 4,7 | while read fileName fileID; do
		encriptFileName=${outputDir}/${fileName}
	    echo "Start downloading ${fileName} ${fileID}"
	    echo "as ${encriptFileName}"
		echo "${PYTHON} ${DIR}/egaTools.py downloadFile \
		<user> <password> ${fileID} ${encriptKey} \
		${outputDir}/${fileName}"
		${PYTHON} ${DIR}/egaTools.py downloadFile \
		${user} ${password} ${fileID} ${encriptKey} \
		${outputDir}/${fileName}
		check_error $?

		echo "${JAVA} -Xms4g -Xmx4g -jar ${EGA} -p <user> <password> -dc ${encriptFileName} -dck ${encriptKey}"
		${JAVA} -Xms4g -Xmx4g -jar ${EGA} -p ${user} ${password} -dc ${encriptFileName} -dck ${encriptKey}
		check_error $?

		baseDir=$(dirname ${outputDir}/${fileName})
		fileNameBase=$(basename ${encriptFileName%.*})
		decriptFileName=${baseDir}/${fileNameBase}

		echo "${PYTHON} ${DIR}/egaTools.py listMetaData ${xmlMetaDataFolder} | \
		${PYTHON} ${DIR}/egaTools.py checkMD5 $(md5sum ${decriptFileName})"
		${PYTHON} ${DIR}/egaTools.py listMetaData ${xmlMetaDataFolder} | \
		${PYTHON} ${DIR}/egaTools.py checkMD5 $(md5sum ${decriptFileName})
		check_error $?

		echo "echo \"${fileName}	${fileID}	${decriptFileName}\" >  ${statusDir}/${SGE_TASK_ID}.finish"
		echo "${fileName}	${fileID}	${decriptFileName}" >  ${statusDir}/${SGE_TASK_ID}.finish
	done
fi

