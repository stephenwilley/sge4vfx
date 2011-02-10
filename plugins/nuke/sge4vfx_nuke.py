#  sge4vfx_nuke.py
#  sge4vfx_nuke
#
#  Created by Stephen Willey on 04/02/2011

import os, nuke, nukescripts, time, shutil
from datetime import datetime
from subprocess import Popen,PIPE

# TODO
# Allow user to choose
# - Which write nodes to render
# -- Turn off write notes that had the read file flag set
# - Allow relative paths in the Nuke files (won't work currently because
#   we're copying the nuke script into the SGE directories)
# - Batch size (this is part of a bigger work-out-how-to-do-it chunking project)


def Submit(fullSize, startFrame, endFrame,
	batchSize, slotsPerFrame, whichQueue):
	# Specify where gridsub is
	gridsub = "gridsub" # assumes it's in the path, otherwise put full path

	# Get all the job bits
	script_name=nuke.Root().name()
	job_path=os.path.basename(script_name)
	(job_title, extension)=os.path.splitext(job_path)
	dirPath = nukescripts.script_directory();
	
	# Build a date string to save off the SGE submission stuff
	dt = datetime.today()
	tt = dt.timetuple()
	dateStr = (str(tt[0]) + str(tt[1]).zfill(2) + str(tt[2]).zfill(2) +
		"-" + str(tt[3]).zfill(2) + str(tt[4]).zfill(2) +
		str(tt[5]).zfill(2))
	
	# Create the SGE folder next to the Nuke script if it doesn't exist
	# This also creates the log folder for the stdout and stderr
	sgePath = dirPath + "/theQ/" + dateStr
	prepCmd1 = ("if [ ! -d " + sgePath + " ]; then mkdir -p "
		+ sgePath + "/logs; fi")
	os.system(prepCmd1)

	# Check whether to force full size
	if fullSize:
		fullSizeBit = "-f "
	else:
		fullSizeBit = ""

	nukeCmd = ("nuke -x " + fullSizeBit + "-F ${SGE_TASK_ID} "
		+ sgePath + "/" + job_path)

	nf = open(sgePath + "/nukeCommand.sh", "w")
	nf.write("#!/bin/bash\n\n")
	nf.write("#$ -o " + sgePath + "/logs/o_$TASK_ID\n")
	nf.write("#$ -e " + sgePath + "/logs/e_$TASK_ID\n\n")
	nf.write(nukeCmd + "\n")
	nf.write("\n# Write return code for epilog script\n")
	nf.write("echo $? > /tmp/${JOB_ID}-${SGE_TASK_ID}-return\n")
	nf.close()
	os.chmod(sgePath + "/nukeCommand.sh", 0755)

	# Now the actual gridsub execution thingy
	sgeCmd = (gridsub
		+ " -N " + job_title
		+ " -V -S /bin/bash "
		+ " -pe pe1 " + slotsPerFrame
		+ " -q " + whichQueue
		+ " -t " + startFrame + "-" + endFrame + " "
		+ sgePath
		+ "/nukeCommand.sh")
	sf = open(sgePath + "/sgeNuke.sh", "w")
	sf.write("#!/bin/bash\n\n")
	sf.write(sgeCmd + "\n")
	sf.close()
	os.chmod(sgePath + "/sgeNuke.sh", 0755)

	# Take a snapshot of the Nuke file (useful for resubmission)
	shutil.copyfile(script_name, sgePath + "/" + job_path)

	# Run the SGE submission command
	p1 = Popen(sgePath + "/sgeNuke.sh", stdout=PIPE)
	theJobID = p1.communicate()[0]
	
	# Tell the user the SGE ID
	sgeID = theJobID.partition(".")[0]
	nuke.message("Render job submitted\nID is " + sgeID)


# Creates the UI panel that the user sees
# When they click OK, it runs the submit function
def RenderPanel():
	# Set defaults
	startFrame = str(nuke.root().firstFrame())
	endFrame = str(nuke.root().lastFrame())
	batchSize = str(1)
	slotsRequired = str(4)
	renderFullSize = not(nuke.root().proxy())
	whichQueue = "farm.q"

	# Create the panel and put the bits on it
	p = nuke.Panel("Render on theQ")
	p.addBooleanCheckBox("Ensure render full size:", renderFullSize)
	p.addSingleLineInput("Start Frame:", startFrame)
	p.addSingleLineInput("End Frame:", endFrame)
	p.addSingleLineInput("Slots per frame:", slotsRequired)
	p.addSingleLineInput("Queue:", whichQueue)
	#p.addSingleLineInput("Batch Size:", batchSize)
	p.addButton("Cancel")
	p.addButton("OK")

	# Show the panel and wait for a button
	result = p.show()

	# Now get all the values and submit if the user clicked OK
	if result == 1:
		renderFullSize = str(p.value("Ensure render full size:"))
		startFrame = p.value("Start Frame:")
		endFrame = p.value("End Frame:")
		slotsPerFrame = p.value("Slots per frame:")
		queue = p.value("Queue:")
		#batchSize = p.value("Batch Size:")

		Submit(renderFullSize,
			startFrame,
			endFrame,
			batchSize,
			slotsPerFrame,
			whichQueue)