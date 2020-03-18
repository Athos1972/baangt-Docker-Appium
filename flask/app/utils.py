import os
from app import models, db, app
from datetime import datetime
import xlsxwriter, xlrd, json
from flask_login import current_user

#
# Default VALUES
#
CLASSNAME_TESTCASESEQUENCE = 'GC.CLASSES_TESTCASESEQUENCE'
CLASSNAME_TESTCASE = 'GC.CLASSES_TESTCASE'
CLASSNAME_TESTSTEP = 'GC.CLASSES_TESTSTEPMASTER'

BROWSER_TYPE = 'GC.BROWSER_FIREFOX'
TESTCASE_TYPE = 'Browser'

#
# item categories
#
def getItemCategories():
	categories = {}
	categories['main'] = [
		'testrun',
		'testcase_sequence',
		'testcase',
		'teststep_sequence',
		'teststep',
	]

	return categories

#
# get name of the item_type
#
def getItemType(item_type, plural=False):	
	# main items 
	if item_type == 'testrun':
		name = 'Testrun'
	elif item_type == 'testcase_sequence':
		name = 'Test Case Sequence'
	elif item_type == 'testcase':
		name = 'Test Case'
	elif item_type == 'teststep_sequence':
		name = 'Test Step Sequence'
	elif item_type == 'teststep':
		name = 'Test Step'
	else:
		# wrong item_type
		return ''

	# check for plurals
	if plural:
		name += 's'

	return name

#
# generate choices of items
#

def getTestCaseSequences():
	choices = []
	for item in models.TestCaseSequence.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getDataFiles():
	choices = []
	for item in models.DataFile.query.all():
		choices.append((f'{item.id}', item.filename))
	return choices

def getTestCases():
	choices = []
	for item in models.TestCase.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getTestStepSequences():
	choices = []
	for item in models.TestStepSequence.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getTestSteps():
	choices = []
	for item in models.TestStepExecution.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getClassNames():
	choices = []
	for item in models.ClassName.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getBrowserTypes():
	choices = []
	for item in models.BrowserType.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getTestCaseTypes():
	choices = []
	for item in models.TestCaseType.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getActivityTypes():
	choices = []
	for item in models.ActivityType.query.all():
		choices.append((f'{item.id}', item.name))
	return choices

def getLocatorTypes():
	choices = []
	for item in models.LocatorType.query.all():
		choices.append((f'{item.id}', item.name))
	return choices


#
# Comaprisions
#

COMPARISIONS = [
	'=',
	'>',
	'<',
	'>=',
	'<=',
	'<>',
]

def getComparisionChoices():
	return [('0', 'none')] + [(f'{i+1}', COMPARISIONS[i]) for i in range(len(COMPARISIONS))]

def getComparisionId(option):
	for i in range(len(COMPARISIONS)):
		if option == COMPARISIONS[i]:
			return f'{i+1}'
	return '0'

#
# Get Items By Name
#

def getOrCreateClassNameByName(name, description):
	# get ClassName from DB
	classname = models.ClassName.query.filter_by(name=name).first()
	if classname is None:
		# create ClassName if it doesn't exist
		classname = models.ClassName(
			name=name,
			description=description,
		)
		db.session.add(classname)
		db.session.commit()
		app.logger.info(f'Created ClassName ID #{classname.id} by {current_user}.')

	return classname 


def getBrowserTypeByName(name):
	# browser mapper
	bm = {
		'BROWSER_FIREFOX': "FF",
		'BROWSER_CHROME': "Chrome",
		'BROWSER_SAFARI': "Safari",
		'BROWSER_EDGE': "Edge",
	}
	return models.BrowserType.query.filter_by(name=bm[name.split('.')[-1]]).first()

def getTestCaseTypeByName(name):
	return models.TestCaseType.query.filter_by(name=name).first()

def getActivityTypeByName(name):
	return models.ActivityType.query.filter_by(name=name).first()

def getLocatorTypeByName(name):
	if name:
		return models.LocatorType.query.filter_by(name=name).first()
	else:
		return None

def getBooleanValue(value):
	if value:
		return True
	else:
		return False

#
# Cascade Delete
#

def deleteCascade(item_type, item_id, ):
	#
	# implementation of cascade delete of items
	#

	# delete Testrun and its children
	if item_type == 'testrun':
		item = models.Testrun.query.get(item_id)
		# delete children TestCaseSequences
		for child in item.testcase_sequences:
			deleteCascade('testcase_sequence', child.id)
		# delete Testrun
		db.session.delete(item)
		db.session.commit()
		app.logger.info(f'Deleted {item_type} id {item_id} by {current_user}.')

	# delete TestCaseSequence and its children
	elif item_type == 'testcase_sequence':
		item = models.TestCaseSequence.query.get(item_id)
		# check if item has not more then one parent
		if len(item.testrun) <= 1:
			# delete children TestCases
			for child in item.testcases:
				deleteCascade('testcase', child.id)
			# delete TestCaseSequence
			db.session.delete(item)
			db.session.commit()
			app.logger.info(f'Deleted {item_type} id {item_id} by {current_user}.')

	# delete TestCase and its children
	elif item_type == 'testcase':
		item = models.TestCase.query.get(item_id)
		# check if item has not more then one parent
		if len(item.testcase_sequence) <= 1:
			# delete children TestCaseSequences
			for child in item.teststep_sequences:
				deleteCascade('teststep_sequence', child.id)
			# delete TestCase
			db.session.delete(item)
			db.session.commit()
			app.logger.info(f'Deleted {item_type} id {item_id} by {current_user}.')

	# delete TestCaseSequence and its children
	elif item_type == 'teststep_sequence':
		item = models.TestStepSequence.query.get(item_id)
		# check if item has not more then one parent
		if len(item.testcase) <= 1:
			# delete children TestStepExecutions
			for child in item.teststeps:
				deleteCascade('teststep', child.id)
			# delete TestCaseSequence
			db.session.delete(item)
			db.session.commit()
			app.logger.info(f'Deleted {item_type} id {item_id} by {current_user}.')

	# delete TestStepExecution
	elif item_type == 'teststep':
		item = models.TestStepExecution.query.get(item_id)
		db.session.delete(item)
		db.session.commit()
		app.logger.info(f'Deleted {item_type} id {item_id} by {current_user}.')

	# invalid type
	else:
		raise Exception(f'Item type {item_type} does not exists.')


#
# Testrun export/import
#

def exportXLSX(testrun_id):
	#
	# Exports Testrun to XLSX
	#

	# get testrun
	testrun = models.Testrun.query.get(testrun_id)
	testrun_json = testrun.to_json()

	# create workbook
	headers = {
		'TestRun': [
			'Attribute',
			'Value',
		],

		'TestCaseSequence': [
			'Number',
			'SequenceClass',
			'TestDataFileName',
		],
		
		'TestCase': [
			'TestCaseSequenceNumber',
			'TestCaseNumber',
			'TestCaseClass'
			'TestCaseType',
			'Browser',
		],
		
		'TestStep': [
			'TestCaseSequenceNumber',
			'TestCaseNumber',
			'TestStepNumber',
			'TestStepClass',
		],
		
		'TestStepExecution': [
			'TestCaseSequenceNumber',
			'TestCaseNumber',
			'TestStepNumber',
			'TestStepExecutionNumber',
			'Activity',
			'LocatorType',
			'Locator',
			'Value',
			'Comparison',
			'Value2',
			'Timeout',
			'Optional',
			'Release',
		],
	}

	xlsx_file = f'Testrun_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx'
	workbook = xlsxwriter.Workbook(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/files', xlsx_file))
	worksheets = {}
	for sheet in headers:
		worksheets[sheet] = workbook.add_worksheet(sheet)

	# write headers
	for key, items in headers.items():
		for col in range(len(items)):
			worksheets[key].write(0, col, items[col])

	# write data
	# to TestRun
	worksheets['TestRun'].write(1, 0, 'Export Format')
	worksheets['TestRun'].write(1, 1, 'XLSX')

	# to TestCaseSequence
	i = 1 # i for TestCaseSequence Number
	for testcase_sequence in testrun.testcase_sequences: 
		worksheets['TestCaseSequence'].write(i, 0, i)
		worksheets['TestCaseSequence'].write(i, 1, testcase_sequence.classname.name)
		worksheets['TestCaseSequence'].write(i, 2, testcase_sequence.datafiles[0].filename)

		# to TestCase
		j = 1 # j for TestCase 
		for testcase in testcase_sequence.testcases:
			worksheets['TestCase'].write(j, 0, i)
			worksheets['TestCase'].write(j, 1, j)
			worksheets['TestCase'].write(j, 2, testcase.classname.name)
			worksheets['TestCase'].write(j, 3, testcase.testcase_type.name)
			worksheets['TestCase'].write(j, 4, testcase.browser_type.name)

			# to TestStep
			k = 1 # k for TestStep
			for teststep_sequence in testcase.teststep_sequences:
				worksheets['TestStep'].write(k, 0, i)
				worksheets['TestStep'].write(k, 1, j)
				worksheets['TestStep'].write(k, 2, k)
				worksheets['TestStep'].write(k, 3, teststep_sequence.classname.name)

				# to TestStepExecution
				m = 1 # m for TestStepExecution
				for teststep in teststep_sequence.teststeps:
					worksheets['TestStepExecution'].write(m, 0, i)
					worksheets['TestStepExecution'].write(m, 1, j)
					worksheets['TestStepExecution'].write(m, 2, k)
					worksheets['TestStepExecution'].write(m, 3, m)
					worksheets['TestStepExecution'].write(m, 4, teststep.activity_type.name)
					worksheets['TestStepExecution'].write(m, 5, teststep.locator_type.name)
					worksheets['TestStepExecution'].write(m, 6, teststep.locator)
					worksheets['TestStepExecution'].write(m, 7, teststep.value)
					worksheets['TestStepExecution'].write(m, 8, teststep.comparision)
					worksheets['TestStepExecution'].write(m, 9, teststep.value2)
					worksheets['TestStepExecution'].write(m, 10, teststep.timeout)
					worksheets['TestStepExecution'].write(m, 11, teststep.optional)
					worksheets['TestStepExecution'].write(m, 12, teststep.release)

					m += 1
				k += 1
			j += 1
		i += 1

	workbook.close()
	return xlsx_file


def importXLSX(xlsx_file, item_id=None):
	#
	# imports testrun from xlsx file
	#

	if item_id is None:
		app.logger.info(f'Importing a Testrun from {xlsx_file.filename} by {current_user}.')
	else:
		# get item
		testrun = models.Testrun.query.get(item_id)
		if testrun is None: # item does not exist
			raise Exception(f'Testrun ID #{item_id} does not exists.')
		app.logger.info(f'Updating Testrun ID #{item_id} from {xlsx_file.filename} by {current_user}.')
	
	# open xlsx
	try:
		xl = xlrd.open_workbook(file_contents=xlsx_file.read())
	except xlrd.XLRDError:
		raise Exception(f'File "{xlsx_file.filename}" could not be imporeted.')
	# get file name
	file_name = os.path.basename(xlsx_file.filename)

	# Testrun object
	if item_id is None:
		# create Testrun
		testrun  = models.Testrun(
			name=file_name,
			description=f'Imported from "{file_name}".',
			creator=current_user,
		)
		db.session.add(testrun)
		db.session.commit()
		app.logger.info(f'Created Testrun ID #{testrun.id} by {current_user}.')
	else:
		# update Testrun
		testrun.description = f'Updated from "{file_name}".'
		testrun.editor = current_user
		testrun.edited = datetime.utcnow()
		db.session.commit()
		app.logger.info(f'Updated Testrun ID #{item_id} by {current_user}.')

	# TestCaseSequence objects
	if item_id is None:
		testcase_sequences = {}
	else:
		testcase_sequences = {i+1: testrun.testcase_sequences[i] for i in range(len(testrun.testcase_sequences))}
	if 'TestCaseSequence' in xl.sheet_names():
		# get sheet
		testcase_sequence_sheet = xl.sheet_by_name('TestCaseSequence')
		# get headers as dict
		headers = {h[1]: h[0] for h in enumerate(testcase_sequence_sheet.row_values(0))}
		# get TestCaseSequences
		for row in range(1, testcase_sequence_sheet.nrows):
			if headers.get('Number') is None:
				# default number is 1
				n = 1
			else:
				# get the number from sheet
				n = int(testcase_sequence_sheet.cell(row, headers['Number']).value)
			
			# ClassName
			if headers.get('SequenceClass') is None:
				# default ClassName name
				name = CLASSNAME_TESTCASESEQUENCE
			else:
				# get ClassName name from sheet
				name = testcase_sequence_sheet.cell(row, headers['SequenceClass']).value
			# get ClassName from DB or create if it doesn't exist
			classname = getOrCreateClassNameByName(name, f'Imported from "{file_name}".')
						
			# DataFile
			if headers.get('TestDataFileName') is None:
				# default DataFile name
				name = file_name
			else:
				# get DataFile name from sheet
				name = testcase_sequence_sheet.cell(row, headers['TestDataFileName']).value
			# get DataFile from DB
			datafile = models.DataFile.query.filter_by(filename=name).first()
			if datafile is None:
				# create DataFile if it doesn't exist
				datafile  = models.DataFile(
					filename=name,
					creator=current_user,
				)
				db.session.add(datafile)
				db.session.commit()
				app.logger.info(f'Created DataFile ID #{datafile.id} by {current_user}.')
			
			# TestCaseSequence
			if n in testcase_sequences:
				# update item
				testcase_sequences[n].description = f'Updated from "{file_name}".'
				testcase_sequences[n].editor = current_user
				testcase_sequences[n].edited = datetime.utcnow()
				testcase_sequences[n].classname = classname
				testcase_sequences[n].datafiles = [datafile]
				db.session.commit()
				app.logger.info(f'Updated TestCaseSequence ID #{testcase_sequences[n].id} by {current_user}.')
			else:
				# create item
				testcase_sequences[n] = models.TestCaseSequence(
					name=f'{file_name}_{row}',
					description=f'Imported from "{file_name}"',
					creator=current_user,
					classname=classname,
					datafiles=[datafile],
					testrun=[testrun],
				)
				db.session.add(testcase_sequences[n])
				db.session.commit()
				app.logger.info(f'Created TestCaseSequence ID #{testcase_sequences[n].id} by {current_user}.')
			
	else:
		# create default TestCaseSequence
		
		# ClassName
		# get ClassName from DB or create if it doesn't exist
		classname = getOrCreateClassNameByName(CLASSNAME_TESTCASESEQUENCE, 'Default for TestCaseSequence.')
		
		# DataFile
		# get DataFile from DB
		datafile = models.DataFile.query.filter_by(filename=file_name).first()
		if datafile is None:
			# create DataFile if it doesn't exist
			datafile  = models.DataFile(
				filename=file_name,
				creator=current_user,
			)
			db.session.add(datafile)
			db.session.commit()
			app.logger.info(f'Created DataFile ID #{datafile.id} by {current_user}.')

		# TestCaseSequence
		if 1 in testcase_sequences:
			# update item
			testcase_sequences[1].description = f'Updated to default.'
			testcase_sequences[1].editor = current_user
			testcase_sequences[1].edited = datetime.utcnow()
			testcase_sequences[1].classname = classname
			testcase_sequences[1].datafiles = [datafile]
			db.session.commit()
			app.logger.info(f'Updated TestCaseSequence ID #{testcase_sequences[1].id} by {current_user}.')
		else:
			# create item
			testcase_sequences[1] = models.TestCaseSequence(
				name=f'{file_name}',
				description=f'Default for "{file_name}"',
				creator=current_user,
				classname=classname,
				datafiles=[datafile],
				testrun=[testrun],
			)
			db.session.add(testcase_sequences[1])
			db.session.commit()
			app.logger.info(f'Created TestCaseSequence ID #{testcase_sequences[1].id} by {current_user}.')

	# TestCase objects
	if item_id is None:
		testcases = {i+1: {} for i in range(len(testcase_sequences))}
	else:
		testcases = {index: {j+1: item.testcases[j] for j in range(len(item.testcases))} for index, item in testcase_sequences.items()}

	if 'TestCase' in xl.sheet_names():
		# get sheet
		testcase_sheet = xl.sheet_by_name('TestCase')
		# get headers as dict
		headers = {h[1]: h[0] for h in enumerate(testcase_sheet.row_values(0))}
		# get TestCases
		for row in range(1, testcase_sheet.nrows):
			# get TestCaseSequenceNumber
			if headers.get('TestCaseSequenceNumber') is None:
				# default number is 1
				i = 1
			else:
				# get the number from sheet
				i = int(testcase_sheet.cell(row, headers['TestCaseSequenceNumber']).value)

			# get TestCaseNumber
			if headers.get('TestCaseNumber') is None:
				# default number is 1
				n = 1
			else:
				# get the number from sheet
				n = int(testcase_sheet.cell(row, headers['TestCaseNumber']).value)
			
			# ClassName
			if headers.get('TestCaseClass') is None:
				# default ClassName name
				name = CLASSNAME_TESTCASE
			else:
				# get ClassName name from sheet
				name = testcase_sheet.cell(row, headers['TestCaseClass']).value
			# get ClassName from DB or create if it doesn't exist
			classname = getOrCreateClassNameByName(name, f'Imported from "{file_name}".')

			# TestCase
			# Browser Type
			if headers.get('Browser') is None:
				raise Exception('Sheet "TestCase" does not contain "Browser" column.')
			else:
				name = testcase_sheet.cell(row, headers['Browser']).value
				browser_type = getBrowserTypeByName(name)
				if browser_type is None:
					raise Exception(f'Unknown browser type "{name}": sheet "TestCase", row {row+1}.')
			# TestCase Type
			if headers.get('TestCaseType') is None:
				raise Exception('Sheet "TestCase" does not contain "TestCaseType" column.')
			else:
				name = testcase_sheet.cell(row, headers['TestCaseType']).value
				testcase_type=getTestCaseTypeByName(name)
				if testcase_type is None:
					raise Exception(f'Unknown testcase type "{name}": sheet "TestCase" row {row+1}.')

			if n in testcases[i]:
				# update item
				testcases[i][n].description = f'Updated from "{file_name}".'
				testcases[i][n].editor = current_user
				testcases[i][n].edited = datetime.utcnow()
				testcases[i][n].classname = classname
				testcases[i][n].browser_type = browser_type
				testcases[i][n].testcase_type = testcase_type
				db.session.commit()
				app.logger.info(f'Updated TestCase ID #{testcases[n].id} by {current_user}.')
			else:
				# create item
				testcases[i][n]  = models.TestCase(
					name=f'{file_name}_{row}',
					description=f'Imported from "{file_name}".',
					creator=current_user,
					classname=classname,
					browser_type=browser_type,
					testcase_type=testcase_type,
					testcase_sequence=[testcase_sequences[i]],
				)
				db.session.add(testcases[i][n])
				db.session.commit()
				app.logger.info(f'Created TestCase ID #{testcases[i][n].id} by {current_user}.')
	else:
		# create default TestCase

		# ClassName
		# get ClassName from DB or create if it doesn't exist
		classname = getOrCreateClassNameByName(CLASSNAME_TESTCASE, 'Default for TestCase.')

		# TestCase
		if 1 in testcases[1]:
			# update item
			testcases[1][1].description = f'Updated to default.'
			testcases[1][1].editor = current_user
			testcases[1][1].edited = datetime.utcnow()
			testcases[1][1].classname = classname
			testcases[1][1].browser_type = getBrowserTypeByName(BROWSER_TYPE)
			testcases[1][1].testcase_type = getTestCaseTypeByName(TESTCASE_TYPE)
			db.session.commit()
			app.logger.info(f'Updated TestCase ID #{testcases[1][1].id} by {current_user}.')
		else:
			# create item
			testcases[1][1]  = models.TestCase(
				name=f'{file_name}',
				description=f'Default for "{file_name}".',
				creator=current_user,
				classname=classname,
				browser_type=getBrowserTypeByName(BROWSER_TYPE),
				testcase_type=getTestCaseTypeByName(TESTCASE_TYPE),
				testcase_sequence=[testcase_sequences[1]],
			)
			db.session.add(testcases[1][1])
			db.session.commit()
			app.logger.info(f'Created TestCase ID #{testcases[1][1].id} by {current_user}.')


	# create TestSteps
	teststeps = {}
	if 'TestStep' in xl.sheet_names():
		# get sheet
		teststep_sheet = xl.sheet_by_name('TestStep')
		# get headers as dict
		headers = {h[1]: h[0] for h in enumerate(teststep_sheet.row_values(0))}
		# get TestSteps
		for row in range(1, teststep_sheet.nrows):
			# get TestStepNumber
			if headers.get('TestStepNumber') is None:
				# default number is 1
				n = 1
			else:
				# get the number from sheet
				n = int(teststep_sheet.cell(row, headers['TestStepNumber']).value)

			# get TestCaseNumber
			if headers.get('TestCaseNumber') is None:
				# default number is 1
				j = 1
			else:
				# get the number from sheet
				j = int(teststep_sheet.cell(row, headers['TestCaseNumber']).value)

			# get TestCaseSequenceNumber
			if headers.get('TestCaseSequenceNumber') is None:
				# default number is 1
				i = 1
			else:
				# get the number from sheet
				i = int(teststep_sheet.cell(row, headers['TestCaseSequenceNumber']).value)

			# ClassName
			if headers.get('TestStepClass') is None:
				# default ClassName name
				name = CLASSNAME_TESTSTEP
			else:
				# get ClassName name from sheet
				name = teststep_sheet.cell(row, headers['TestStepClass']).value
			# get ClassName from DB or create if it doesn't exist
			classname = getOrCreateClassNameByName(name, f'Imported from "{file_name}".')
			
			# TestCase
			# ---------------------------------------------------------------> continue with update
			teststeps[n]  = models.TestStepSequence(
				name=f'{file_name}_{row}',
				description=f'Imported from "{file_name}"',
				creator=current_user,
				classname=classname,
				testcase=[testcases[i][j]],
			)
			db.session.add(teststeps[n])
			db.session.commit()
			app.logger.info(f'Created TestStepSequence id {teststeps[n].id} by {current_user}.')
	else:
		# create default TestStep
		# ClassName
		# get ClassName from DB or create if it doesn't exist
		classname = getOrCreateClassNameByName(CLASSNAME_TESTSTEP, 'Default for TestStep')
		
		# TestStep
		teststeps[1]  = models.TestStepSequence(
			name=f'{file_name}_1',
			description=f'Default for "{file_name}"',
			creator=current_user,
			classname=classname,
			testcase=[testcases[1][1]]
		)
		db.session.add(teststeps[1])
		db.session.commit()
		app.logger.info(f'Created TestStepSequence id {teststeps[1].id} by {current_user}.')

	# create TestStepsExecutions
	if 'TestStepExecution' in xl.sheet_names():
		# get sheet
		teststep_execution_sheet = xl.sheet_by_name('TestStepExecution')
		# get headers as dict
		headers = {h[1]: h[0] for h in enumerate(teststep_execution_sheet.row_values(0))}
		# get TestStepExecutions
		for row in range(1, teststep_execution_sheet.nrows):
			# get TestStepExecutionNumber
			if headers.get('TestStepExecutionNumber') is None:
				# default number is 1
				n = row
			else:
				# get the number from sheet
				n = int(teststep_execution_sheet.cell(row, headers['TestStepExecutionNumber']).value)
			# get TestStepNumber
			if headers.get('TestStepNumber') is None:
				# default number is 1
				teststep_n = 1
			else:
				# get the number from sheet
				teststep_n = int(teststep_execution_sheet.cell(row, headers['TestStepNumber']).value)
			# Activity Type
			if headers.get('Activity') is None:
				raise Exception('Sheet "TestStepExecution" does not contain "Activity" column.')
			else:
				name = teststep_execution_sheet.cell(row, headers['Activity']).value
				activity_type = getActivityTypeByName(name.upper())
				if activity_type is None:
					raise Exception(f'Unknown activity type "{name}": sheet "TestStepExecution", row {row+1}')
			# Locator Type
			if headers.get('LocatorType') is None:
				raise Exception('Sheet "TestStepExecution" does not contain "LocatorType" column.')
			else:
				locator_type = getLocatorTypeByName(teststep_execution_sheet.cell(row, headers['LocatorType']).value)
			# get Locator
			if headers.get('Locator') is None:
				locator = None
			else:
				locator = teststep_execution_sheet.cell(row, headers['Locator']).value or None
			# get Value
			if headers.get('Value') is None:
				value = None
			else:
				value = teststep_execution_sheet.cell(row, headers['Value']).value or None
			# get Value 2
			if headers.get('Value2') is None:
				value2 = None
			else:
				value2 = teststep_execution_sheet.cell(row, headers['Value2']).value or None
			# get Comparison
			if headers.get('Comparison') is None:
				comparision = None
			else:
				comparision = teststep_execution_sheet.cell(row, headers['Comparison']).value or None
			# get Timeout
			if headers.get('Timeout') is None:
				timeout = None
			else:
				timeout = teststep_execution_sheet.cell(row, headers['Timeout']).value or None
			# get Optional
			if headers.get('Optional') is None:
				optional = False
			else:
				optional = getBooleanValue(teststep_execution_sheet.cell(row, headers['Optional']).value)
			# get Release
			if headers.get('Release') is None:
				release = None
			else:
				release = teststep_execution_sheet.cell(row, headers['Release']).value or None

			# TestStepExecution
			teststepex  = models.TestStepExecution(
				name=f'{file_name}_{row}',
				description=f'Imported from "{file_name}"',
				creator=current_user,
				teststep_sequence=teststeps[teststep_n],
				activity_type=activity_type,
				locator_type=locator_type,
				locator=locator,
				value=value,
				comparision=comparision,
				value2=value2,
				timeout=timeout,
				optional=optional,
				release=release,
			)
			db.session.add(teststepex)
			db.session.commit()
			app.logger.info(f'Created TestStepExecution id {teststepex.id} by {current_user}.')

	return 1












