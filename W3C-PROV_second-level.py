#
#     Ophidia provenance
#     Copyright (C) 2022 CMCC Foundation
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re,glob,os,sys
import prov.model as prov
from prov.model import ProvDocument
from prov.identifier import Namespace
import argparse
from datetime import datetime, timedelta
import netCDF4 as nc
from prov.dot import prov_to_dot

def get_time_info(rows):

	startTime=None
	endTime=None
	for s in rows:
		if "Task string" in s:
			# Mon Feb 14 11:42:20 2022
			start=s.split("[",1)[1].split("]")[0]
		#Proc 0: Total execution:         Time 0,365209 sec
		if "Total execution" in s:
			duration=float(s.split(' ')[5].replace(",","."))

	year=int(start.split(" ")[4])
	month=int(datetime.strptime(start.split(" ")[1], "%b").month)
	day=int(start.split(" ")[2])
	hh=int(start.split(" ")[3].split(":")[0])
	mm=int(start.split(" ")[3].split(":")[1])
	ss=int(start.split(" ")[3].split(":")[2])
	startTime=datetime(year,month,day,hh,mm,ss)
	endTime=startTime+timedelta(seconds=duration)
	return startTime,endTime

basePath=""

# argparse settings
parser = argparse.ArgumentParser()
required = parser.add_argument_group('required arguments')
required.add_argument("-i", "--input",dest ="input_dir", required=True, help="Input directory containing logs file to be processed")
required.add_argument("-o", "--output",dest ="output_dir", required=True, help="Output directory to store PROV documents compliant to W3C prov standard")
args = parser.parse_args()

# Define logPath and outPath
if args.input_dir == ".":
	logPath=os.path.abspath(os.getcwd())
else:
	logPath = args.input_dir

if args.output_dir == ".":
	outPath = os.path.abspath(os.getcwd())
else:
	outPath = args.output_dir

print("The Ophidia logs in the ",logPath," directory will be processed")
print("\nThe PROV documents will be stored in ",outPath)

# Check input log files
files=glob.glob(logPath+'/*_*.txt')
if len(files)<1:
	print("\nNo log files available in ",logPath)
	sys.exit(1)
else:
	print("\nThe following log files will be processed: ",str(files))


############################################# Initialization of prov doc #############################################
# Create a new provenance document
d1 = ProvDocument()

# Declare namespaces for various prefixes used in the example
OPHIDIA = Namespace("ophidia",uri="http://ophidia.cmcc.it/")
PROV = Namespace("prov",uri="http://www.w3.org/ns/prov#")
OPERATOR = Namespace('operator', uri="https://ophidia.cmcc.it/documentation/users/operators/index.html")
FILE = Namespace('file',uri='https://www.wcrp-climate.org/wgcm-cmip')
DATACUBE = Namespace('datacube',uri='')

PROV_DATA = prov.PROV["Data"]
PROV_DATACUBE = OPHIDIA["Datacube"]
PROV_OPERATOR = OPHIDIA["Operator"]

d1.add_namespace(OPHIDIA)
d1.add_namespace(PROV)
d1.add_namespace(OPERATOR)
d1.add_namespace(FILE)
d1.add_namespace(DATACUBE)

######################################################################################################################

#Global dictionaries of operator names
dataOperators = ["oph_aggregate", "oph_aggregate2", "oph_apply", "oph_drilldown", "oph_duplicate","oph_merge", "oph_permute", "oph_reduce", "oph_reduce2", "oph_rollup", "oph_subset", "oph_subset2"]
specialOperators = ["oph_intercube", "oph_mergecubes", "oph_mergecubes2","oph_script", "oph_concatnc","oph_metadata","oph_delete"]
importOperators = ["oph_importnc", "oph_importnc2", "oph_importfits", "oph_randcube", "oph_randcube2"]
exportOperators = ["oph_exportnc", "oph_exportnc2", "oph_explorecube"]

taskList = []

#Parse logs and build task list
for filename in os.listdir(logPath):
	if filename.endswith(".txt"):
		with open(os.path.join(logPath, filename), 'r') as file:
			stringTxt = file.read()
			stringRows = stringTxt.splitlines()

			#Define keys to get from submission string
			operName = ""
			operType = ""
			jobID = ""
			sessionID = ""
			inputFile = ""
			inputCube = ""
			inputCube2 = ""
			outputPath = ""
			outputName = ""
			cdd = ""
			outputCube = ""
			execTime = ""
			scriptArgs = ""

			#Search for keywords
			for s in stringRows:

				#Extract keys from operator string
				if "operator=" in s:
					operatorKeys = s.split(";")

					for k in operatorKeys:
						val = k.split("=")
						#Get type of operator
						if val[0] == "operator":
							if val[1] in exportOperators:
								operType = "export"
							elif val[1] in dataOperators:
								operType = "datacube"
							elif val[1] in importOperators:
								operType = "import"
							elif val[1] in specialOperators:
								operType = "special"
							operName = val[1]
						#Extract jobid
						if val[0] == "jobid":
							jobID = val[1]
						#Extract sessionid
						if val[0] == "sessionid":
							sessionID = val[1]
						#Extract input file
						if val[0] == "src_path":
							inputFile = val[1]
						#Extract output file components
						if val[0] == "output_path":
							outputPath = val[1]
						if val[0] == "output_name":
							outputName = val[1]
						if val[0] == "cdd":
							cdd = val[1]
						if val[0] == "args":
							scriptArgs = val[1]
						#Extract input cube (various cases)
						if val[0] == "cube" or val[0] == "cubes":
							inputCube = val[1]
						if val[0] == "cube2":
							inputCube2 = val[1]

				if "PID of output datacube is" in s:
					outputCube = s.split("PID of output datacube is: ",1)[1]

				if "Total execution:" in s:
					execTime = re.search('Time (.*) sec', s)

			#Check if keywords and operator type are matching
			if operType == "export":
				if outputPath[0] != "/" and cdd:
					outputPath = os.path.join(cdd, outputPath)
				if outputName and outputPath:
					outputFile = os.path.join(outputPath, outputName) + ".nc"
				else:#TODO Check default when no file name is used
					outputFile = outputPath

				if outputFile == "" or inputCube == "" or operName == "" or jobID == "":
					print("Unable to get export operator keywords")
					continue
				else:
					#Store data
					taskList.append([{"operType": operType, "outputFile": outputFile, "inputCube": inputCube, "operName": operName, "jobID": jobID}])
					print("\n"+inputCube + " " + outputFile + " " + operName + " " + jobID)
					# Add to prov doc
					ei= d1.entity(DATACUBE[inputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL: "Ophidia Datacube PID"})
					startTime,endTime=get_time_info(stringRows)
					a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR})
					eo = d1.entity(FILE[outputFile], {prov.PROV_TYPE: PROV_DATA, prov.PROV_LABEL: "Output NetCDF filename"})
					d1.wasDerivedFrom(eo, ei)
					d1.wasGeneratedBy(eo, a)
					d1.used(a,ei)

			elif operType == "datacube":
				if outputCube == "" or inputCube == "" or operName == "" or jobID == "":
					print("Unable to get data operator keywords")
					continue
				else:
					#Store data
					taskList.append([{"operType": operType, "outputCube": outputCube, "inputCube": inputCube, "operName": operName, "jobID": jobID}])
					print("\n"+inputCube + " " + outputCube + " " + operName + " " + jobID)
					# Add to prov doc
					ei = d1.entity(DATACUBE[inputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL: "Ophidia Datacube PID"})
					startTime,endTime=get_time_info(stringRows)
					a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR})
					eo = d1.entity(DATACUBE[outputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL: "Ophidia Datacube PID"})
					d1.wasDerivedFrom(eo, ei)
					d1.wasGeneratedBy(eo, a)
					d1.used(a,ei)

			elif operType == "import":
				if "randcube" in operName:
					if outputCube == "" or operName == "" or jobID == "":
						print("Unable to get import operator keywords")
						continue
					else:
						#Store data
						taskList.append([{"operType": operType, "outputCube": outputCube, "operName": operName, "jobID": jobID}])
						print("\n"+outputCube + " " + operName + " " + jobID)
						# Add to prov doc
						e = d1.entity(DATACUBE[outputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL: "Ophidia Datacube PID"})
						startTime,endTime=get_time_info(stringRows)
						a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR})
						d1.wasGeneratedBy(e, a)

				else:
					if outputCube == "" or inputFile == "" or operName == "" or jobID == "":
						print("Unable to get import operator keywords")
						continue
					else:
						#Store data
						taskList.append([{"operType": operType, "outputCube": outputCube, "inputFile": inputFile, "operName": operName, "jobID": jobID}])
						print("\n"+inputFile + " " + outputCube + " " + operName + " " + jobID)
						# Add to prov doc
						check = d1.get_record(FILE[inputFile])
						eo = d1.entity(DATACUBE[outputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
						startTime,endTime=get_time_info(stringRows)
						a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR})
						try:
							ds = nc.Dataset(basePath+inputFile)
							pidf = ds.getncattr('tracking_id')
							label = "Input tracking id"
						except:
							pidf = inputFile
							label= "Input filename"
						if not check:
							ei = d1.entity(FILE[pidf], { prov.PROV_TYPE: PROV_DATA, prov.PROV_LABEL:label, prov.PROV_VALUE: inputFile})
						else:
							ei=check[0]
						d1.wasDerivedFrom(eo, ei)
						d1.wasGeneratedBy(eo, a)
						d1.used(a,ei)

			#Handle special cases
			elif operType == "special":
				if "intercube" in operName:
					if inputCube and inputCube2:
						inputCube = [inputCube, inputCube2]
					else:
						inputCube = ""

					if outputCube == "" or inputCube == "" or operName == "" or jobID == "":
						print("Unable to get data operator keywords")
						continue
					else:
						#Store data
						taskList.append([{"operType": operType, "outputCube": outputCube, "inputCube": '|'.join(inputCube), "operName": operName, "jobID": jobID}])
						print("\n"+'-'.join(inputCube) + " " + outputCube + " " + operName + " " + jobID)
						# Add to prov doc
						ei1 = d1.entity(DATACUBE[inputCube[0]], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
						ei2 = d1.entity(DATACUBE[inputCube[1]], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
						eo = d1.entity(DATACUBE[outputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
						startTime,endTime=get_time_info(stringRows)
						a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR} )
						d1.used(a,ei1)
						d1.used(a,ei2)
						d1.wasGeneratedBy(eo, a)
						d1.wasDerivedFrom(eo, ei1)
						d1.wasDerivedFrom(eo, ei2)

				elif "mergecubes" in operName:
					if inputCube:
						inputCube = inputCube.split("|")

					if outputCube == "" or inputCube == "" or operName == "" or jobID == "":
						print("Unable to get data operator keywords")
						continue
					else:
						#Store data
						taskList.append([{"operType": operType, "outputCube": outputCube, "inputCube": '|'.join(inputCube), "operName": operName, "jobID": jobID}])
						print("\n"+'-'.join(inputCube) + " " + outputCube + " " + operName + " " + jobID)
						# Add to prov doc
						startTime,endTime=get_time_info(stringRows)
						a = d1.activity(OPERATOR[operName+str(jobID)], startTime, endTime, { prov.PROV_TYPE: PROV_OPERATOR})
						eo = d1.entity(DATACUBE[outputCube], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
						d1.wasGeneratedBy(eo, a)

						for i in range(0,len(inputCube)):
							# Add to prov doc
							ei = d1.entity(DATACUBE[inputCube[i]], { prov.PROV_TYPE: PROV_DATACUBE, prov.PROV_LABEL:"Ophidia Datacube PID"})
							d1.used(a,ei)
							d1.wasDerivedFrom(eo, ei)

				#TODO Handle also updates in metadata and files in scripts
				elif "oph_script" in operName:
					continue
	else:
		continue

#Export to W3C PROV docs
dot = prov_to_dot(d1)
dot.write_png(outPath+'/W3C-PROV_second-level.png')
d1.serialize(outPath+'/W3C-PROV_second-level.json')
d1.serialize(outPath+'/W3C-PROV_second-level.xml', format='xml')
d1.serialize(outPath+'/W3C-PROV_second-level.ttl', format='rdf', rdf_format='ttl')
