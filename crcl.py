#!/usr/bin/python3


########################################
############### Settings ###############
########################################

# Form URL
url = "//localhost/"

# Limits on when to use adjusted body weight, e.g. 1.2 = >120% of IBW
ABWlimit = 1.2

# Cutoff to use ideal body weight for low weight, e.g. 1.0 = <100% of IBW
lowWtCutoff = 1.0

# Limits when to round SCr up, due to frail/elderly = lowSCr
frailAgeLimit = 65	# Age cutoff for elderly. Set to 0 if N/A
frailSCrLimit = 0.8	# SCr lowest limit allowed in calculation for frail.

# Use actual body weight instead of ideal when weight is considered 'ideal,' but not underweight
# WHHS uses IBW when weight is normal, and rounds scr to 0.8 for all patients
whhsProtocols = "yes"	# This flag should be yes if at Washington Hospital

########################################
########################################
########################################


# Define classes and objects
class patient:
	def __init__(self, age, gender, weight, height, scr):
		self.age = age
		self.gender = gender
		self.weight = weight
		self.height = height
		self.scr = scr
		
	# Converts lbs to kg
	def getKg(self):
		weight = (self.weight/2.20462)
		return(round(weight,2))

	# Converts cm to inches
	def getIn(self):
		height = (self.height/2.54)
		return(round(height,2))

	# Determines ideal body weight
	def IBW(self):
		# If less than 60 inches, use Hume equation
		if (height < 60):
			IBWShort = ((0.3281*weight) + (0.33939*(height*2.54)) - 29.5336)
			if (gender == "f"):
				IBWShort = ((0.29569*weight) + (0.41813*(height*2.54)) - 43.2933)
			print("[ ! ]  Patient is shorter than 60 inches. Using Hume Equation for IBW calculations.<br>")
			return(IBWShort)
		else:
			baseweight = 50
			if (gender == "f"):
				baseweight = float(45.5)
			heightdiff = height-60
			weightdiffadj = 2.3*heightdiff
			return(float(baseweight+weightdiffadj))

	# Determines Scr, especially if should be rounded up if frail weight
	def SCr(self):
		scr = float(self.scr)
		scrInput = scr
		if whhsProtocols == "yes":
			if (scrInput < frailSCrLimit):
				scr = float(frailSCrLimit)
				print("[ ! ]   Rounded SCr of {} to {} per WHHS protocols (reduced geriatric muscle mass adjustment).<br>".format(scrInput, frailSCrLimit))
				return(scr)
			else:
				return(scr)
		else:
			if (scrInput < frailSCrLimit and age >= frailAgeLimit):
				scr = float(frailSCrLimit)
				print("[ ! ]   Rounded SCr of {} to {} because patient age >{} years old with SCr of <{} (reduced geriatric muscle mass adjustment).<br>".format(scrInput, frailSCrLimit, frailAgeLimit, frailSCrLimit))
				return(scr)
			else:
				return(scr)

	# Determines actual, ideal, or adjusted BW to use
	def formulaBW(self):
		wtratio = weight/IBW
		if (wtratio >= ABWlimit):
			TotalMinusIdealBW = weight-IBW
			ABW = (IBW + (0.4*TotalMinusIdealBW))
			print("[ ! ]   Patient is overweight. (Actual/Ideal) = {}, which is >{}.<br>".format(round(wtratio,2), ABWlimit))
			return(ABW)
		elif (wtratio < 1.0):
			print("[ ! ]   Patient is underweight. Actual ({} kg) < Ideal ({} kg).<br>".format(weight, round(IBW,2)))
			return(weight)
		else:
#			print("Within ideal limits")
			if whhsProtocols == "yes":
				return(weight)
			else:
				return(IBW)

	# Get CrCl
	def CrCl(self):
		CrCl = (((140-self.age)*formulaWt)/(72*scr))
		if self.gender == "f":
			CrCl = round((CrCl*0.85),2)
			return(CrCl)
		else:
			return(CrCl)

	def weightType(self):
		wtratio = weight/IBW
		if (wtratio >= ABWlimit):
			return("over")
		elif (wtratio < 1.0):
			return("under")
		else:
			return("at ideal")

import sys
import cgi, cgitb
import re


form = cgi.FieldStorage()
returnMsg = "<br>Return <a href='{}'>back</a>".format(url)

print("Content-type: text/html")
print("")	
print("<!DOCTYPE html>")
print("<style>body { font-family: 'Trebuchet MS' }</style>")
print("</head>")

# Obtain user input
# Note that if no value is supplied, variable obtains a value "None" (NoneType, not a String Type)
scr = form.getvalue("scr")
age = form.getvalue("age")
gender = form.getvalue("gender")
height = form.getvalue("height")
hUnit = form.getvalue("hUnit")
weight = form.getvalue("weight")
wUnit = form.getvalue("wUnit")

# Make sure there are no missing variables
if None in ({scr, age, gender, height, hUnit, weight, wUnit}):
	print("<title>Error</title>One or more parameters have not been set. Please recheck the form to make sure all fields have been entered.")
	print(returnMsg)
	sys.exit()
else:
	# Validates input
	ageRE = re.compile(r"^[0-9]{1,3}$")
	digitRE = re.compile(r"^[0-9]{1,3}\.?[0-9]{0,3}$")
	strRE = re.compile(r"^[A-Za-z]{1,6}$")
	if (not digitRE.match(scr)) or (not ageRE.match(age)) or (not digitRE.match(weight)) or (not digitRE.match(height)):
		print("<Title>Error</title>Please verify the corrent input of the parameters:")
		if not digitRE.match(scr):
			print(" scr ")
		if not ageRE.match(age):
			print(" age ")
		if not digitRE.match(weight):
			print(" weight ")
		if not digitRE.match(height):
			print(" height ")
		print(returnMsg)
		sys.exit()
        # Makes sure age is in appropriate range, 0-140 and warns if less than 18 years
        elif int(age) > int(140):
                print("<title>Error</title>Age cannot be greater than 140.")
                print(returnMsg)
                sys.exit()
        elif int(age) < (int(18)) and int(age) > (int(0)):
                print("[ ! ]  This is a pediatric patient. Use caution with assessment.<br>")
        elif int(age) < int(1):
                print("<title>Error</title>Age cannot be less than 1.")
                print(returnMsg)
                sys.exit()
	# Throws an error if form is bypassed via GET request
	elif (not strRE.match(gender)) or (not strRE.match(hUnit)) or (not strRE.match(wUnit)):
		print("<title>Error</title>Please use the web form to submit data.")
		print(returnMsg)
		sys.exit()

# If not, turn the variables into floats/integers/strings.
scr = float(form.getvalue("scr"))
age = int(form.getvalue("age"))
gender = str(form.getvalue("gender"))
height = float(form.getvalue("height"))
hUnit = str(form.getvalue("hUnit"))
weight = float(form.getvalue("weight"))
wUnit = str(form.getvalue("wUnit"))

####################################################	
## Input for development purposes only	##

#print("Enter SCr: ")
#scr = float(input())
#print("Enter age: ")
#age = int(input())
#print("Enter sex: ")
#gender = str(input())
#print("Enter height: ")
#height = float(input())
#print("Enter height Unit: ")
#hUnit = str(input())
#print("Enter weight: ")
#weight = float(input())
#print("Enter weight Unit: ")
#wUnit = str(input())
####################################################


#Script
p = patient(age, gender, weight, height, scr)

print("<title>{} yo{} result</title>".format(age, gender))
print("<body style='font-family: Trebuchet MS; width: 700px;'>")


if hUnit == "cm":
	height = p.getIn()

if wUnit == "lbs":
	weight = p.getKg()

IBW = p.IBW()
formulaWt = p.formulaBW()
scr = p.SCr()
crclInt = round(p.CrCl(),0)

####################################################	
## Input for development purposes only	##

#print("The height is {} inches".format(height))
#print("The Kg weight is {} kg".format(weight))
#print("The patient's ideal body weight is {} kg.".format(p.IBW()))
#print("SCr = {} mg/dL".format(p.SCr()))
#print("Body weight used in the formula {} kg".format(p.formulaBW()))

####################################################	

# Script output
print("<br><div style='border: solid blue 2px; padding: 10px; width: 550px;'>")
print("The estimated creatinine clearance for this patient is ")
# Colors answer by ranges
if crclInt > 60:
        print("<span style='background: #baebae;'><b>")
elif 30 < crclInt <= 60:
        print("<span style='background: #fff200;'><b>")
elif crclInt <= 30:
        print("<span style='background: #c25400; color: white;'><b>")
print("{} mL/min</b></span>.".format(round(p.CrCl(),2)))
print("<br><span style='font-size:x-small;'><i>Calculate <a href='{}'>another</a> patient.</i></span>".format(url))

print("</div>")if whhsProtocols == "yes":
	print("<span style='font-size:x-small; color: #999;'>This result complies with WHHS renal dosing protocols.</span>")
print("<br><br>")
print("<br><br>")

print("Calculations: <br>")
print("((140 - age)* wt) / (72 * SCr) --> if female, multiply 0.85<br><br>".format(age, formulaWt, scr))
print("<div style='font-size: x-small;'>")
print("<span style='color: #999;'>")
print("The patient's ideal body weight is {} kg.<br>".format(round(IBW,2)))
print("Patient's weight is {} weight.<br>".format(p.weightType()))
print("Body weight used in the formula {} kg.<br>".format(round(formulaWt,2)))
print("SCr = {} mg/dL.<br>".format(scr))
print("<br><br>")

print("[((140 - {})* {}) / (72 * {})]   ".format(age, formulaWt, scr))
if (gender == "f"):
	print('* 0.85  ')
print('=  ')
print("<b>{} mL/min</b>".format(round(p.CrCl(),2)))
print("</span>")
print("</div>")
print("</body>")
