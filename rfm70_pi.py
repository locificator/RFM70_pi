import time
import spidev
import RPi.GPIO as gp

class device:
  def __init__(self,name,bus,port,ce,irq):
		self.bus=bus
		self.port=port
		self.name=name
		self.ce=ce
		self.irq=irq
		self.debug=False
		self.channel=2

	def registerLength(self,bank,register):	# the registers have individual lengths
		if bank==0:
			if register==0x0A or register==0x0B or register==0x10:
				return 5
			else:
				return 1
		elif bank==1:
			if register==0x0E:
				return 11
			else:
				return 4 				#ok not the truth....

	def reverseBytes(self,bytes):
		bytes[::-1]
		return bytes

	def setBit(self,byte, offset):
		mask = 1 << offset
		return(byte | mask)

	def toggleBit(self,byte, offset):
		mask = 1 << offset
		return(byte ^ mask)

	def clearBit(self,byte, offset):
		mask = ~(1 << offset)
		return(byte & mask)

	def fByte(self,byte):	# simple formatting tool sample: 0x03 >> 0b11 >> 00000011
		byte=str(bin(byte))
		byte=byte[2:]
		byte=(8-len(byte))*"0"+byte
		return byte

	def getBit(self,byte,pos):	#credit goes to Michael Aaron Safyan
		return ((byte&(1<<pos))!=0)

	def reverseBits(self,byte):	#credit goes to Thomas Baumann
		byte = ((byte & 0xF0) >> 4) | ((byte & 0x0F) << 4)
		byte = ((byte & 0xCC) >> 2) | ((byte & 0x33) << 2)
		byte = ((byte & 0xAA) >> 1) | ((byte & 0x55) << 1)
		return byte

	def connect(self):
		try:
			gp.setmode(gp.BCM)
			gp.setwarnings(False)

			gp.setup(self.ce,gp.OUT)
			gp.setup(self.irq,gp.IN, pull_up_down=gp.PUD_UP)
		except:
			print "failed connecting to gpio"
		try:
			self.spi=spidev.SpiDev()
			self.spi.open(self.bus, self.port)
			self.spi.max_speed_hz=500000
		except:
			print "failed loading spi"

	def close(self):
		try:
			self.spi.close()
			gp.cleanup()
		except:
			print "master failure"

	def readStatus(self):
		status=self.spi.xfer2([0xFF])
		return status[0]

	def sendCommand(self,command,data):	#command as INT, data as array of INT's
		#gp.output(self.ce,1)
		block=[]
		block.append(command)
		for element in data:
			block.append(element)
		answer=self.spi.xfer2(block)
		#gp.output(self.ce,0)
		return answer

	def selectBank(self,bank):	#just for toggling between the two banks (0/1) bank0 for use, bank1 mostly for init
		if self.getBit(self.readStatus(),7)!=bank:  #bit 7 represents the current bank
			status=self.sendCommand(0x50,[0x53])  #toggle bank

	def readRegister(self,bank,register):
		self.selectBank(bank)
		data=[]
		for byte in range(self.registerLength(bank,register)):
			data.append(0x00)
		answer=self.sendCommand(register,data)
		answer.pop(0) #remove the status register

		if self.debug:
			i=0			
			temp=""
			for byte in answer:
				temp+=self.fByte(byte)+" "
			print "readed register %s (%s) from bank %s : (%s) %s " % (str(register),str(hex(register)),str(bank),[hex(byte) for byte in answer],temp)
		return answer

	def Interrupt(self,channel):
		current=self.readRegister(0,0x07)[0]
		if self.getBit(current,6):
			pos=(int(("0b"+str(self.getBit(current,3))+str(self.getBit(current,2))+str(self.getBit(current,1))),2))
			if pos==7:
				print 10*"#"+"%s FIFO empty" % self.name
			else:
				print 10*"#"+"RX_DR data ready to read @ pipe %s on %s" % (str(pos),self.name)
				blank=[0 for x in range(32)]
				print "%s got: %s" % (self.name,self.sendCommand(0x61, blank))
			print 10*"#"+"clearing now"
			self.writeRegister(0,0x07,[self.setBit(current, 6)]) #for clearing write "1"
		elif self.getBit(current,5):
			print 10*"#"+"TX_DS data has been sent, clearing now TX-FIFO on %s" % self.name
			self.writeRegister(0,0x07,[self.setBit(current, 5)])
		elif self.getBit(current,4):
			print 10*"#"+"MAX_RT reached, clearing now on %s" % self.name
			self.writeRegister(0,0x07,[self.setBit(current, 4)])
		elif self.getBit(current,0):
			print 10*"#"+"TX_FIFO full on %s" % self.name
		else:
			print 10*"#"+"Interrupt triggered wtf?? %s || 0x00:  %s  0x07: %s" % (self.name,self.fByte(self.readRegister(0, 0x00)[0]),self.fByte(self.readRegister(0, 0x07)[0]))
		


	def attachInterrupt(self):
		gp.add_event_detect(self.irq,gp.FALLING,callback=self.Interrupt)

	def convertPayload(self,size,data):
		temp=""
		payload=[]
		for char in data:
			payload.append(ord(char))

		for i in range(len(data),size):
			payload.append(0x00)

		#print len(payload)
		return payload


	def getPowerMode(self):						# returns true if PWR_UP
		current=self.readRegister(0,0x00)[0]
		awake=0
		if self.getBit(current, 1):			
			awake=1
		return awake

	def setPowerMode(self,value):				#1 awake, 0 sleep
		self.selectBank(0)
		current=self.readRegister(0,0x00)[0]
		gp.output(self.ce,0)					#just to be sure
		if value:
			self.sendCommand(0x20, [self.setBit(current, 1)])
		else:
			self.sendCommand(0x20, [self.clearBit(current, 1)])

	def writeRegister(self,bank,register,value):				#single write, for changing config during runtime
		self.selectBank(bank)
		self.sendCommand((register+32),value)		#pretty easy
		if self.debug:
			print "writed to register %s (%s) from bank %s : %s (%s) " % (str(register),str(hex(register)),str(bank),[hex(byte) for byte in value],[self.fByte(byte) for byte in value])

	def setAutoAck(self,pipes):						#bank 01
		byte=0x00
		for i in range(0,6):
			if pipes[i]:
				byte=self.setBit(byte,i)
			else:
				byte=self.clearBit(byte,i)
		if self.debug:
			print "reg1 byte: %s" % self.fByte(byte)
		self.writeRegister(0, 0x01, [byte])

	def enablePipes(self,pipes):
		byte=0x00
		for i in range(0,6):
			if pipes[i]:
				byte=self.setBit(byte,i)
			else:
				byte=self.clearBit(byte,i)
		if self.debug:
			print "reg2 byte: %s" % self.fByte(byte)
		self.writeRegister(0, 0x02, [byte])

	def setRetransmitDelay(self,delay):
		value=(delay/250-1)
		current=self.readRegister(0, 0x04)[0]
		for i in range(4,8):
			if self.getBit(value, i-4):
				current=self.setBit(current, i)
			else:
				current=self.clearBit(current, i)
		if self.debug:
			print "delay current %s :" % self.fByte(current)
		self.writeRegister(0,0x04,[current])

	def setRetransmitAttempts(self,attempts):
		current=self.readRegister(0, 0x04)[0]
		for i in range(0,4):
			if self.getBit(attempts, i):
				current=self.setBit(current, i)
			else:
				current=self.clearBit(current, i)
		if self.debug:
			print "retransmit attempts now %s :" % self.fByte(current)
		self.writeRegister(0,0x04,[current])


	def setFrequency(self,frequency): #frequency as INT from 2400 to 2483
		self.writeRegister(0, 0x05, [frequency-2400])
		if self.debug:
			print "setted frequency to %s MHz" % str(self.readRegister(0, 0x05)[0]+2400)

	def setComMode(self,mode):	#1 RX, 0 TX
		current=self.readRegister(0, 0x00)
		if mode:
			self.writeRegister(0,0x00,[self.setBit(current[0], 0)])
		else:
			self.writeRegister(0,0x00,[self.clearBit(current[0],0)])

	def setListenTo(self,adlist):
		i=0x0A
		for adress in adlist:
			self.writeRegister(0, i, adress)
			i+=1

	def setTransmitAddress(self,address):
		self.writeRegister(0,0x10,address)

	def setPayloadSize(self,payloads):
		i=0x11
		for payload in payloads:
			self.writeRegister(0, i, [payload])
			i+=1

	def setCE(self,value,delay):
		gp.output(self.ce,value)
		time.sleep(delay)

	def activate(self):
		self.sendCommand(0x50, [0x73])

	def initBank1(self):
		part1_reversed=[
		[0xE2,0x01,0x4B,0x40],
		[0x00,0x00,0x4B,0xC0],
		[0x02,0x8C,0xFC,0xD0],
		[0x41,0x39,0x00,0x99],
		[0x0B,0x86,0x9E,0xF9], 
		[0xA6,0x7F,0x06,0x24],]

		i=0
		for reg in range(0x00,0x06):
			self.writeRegister(1, reg, part1_reversed[i])
			i+=1

		
		self.writeRegister(1,0x0C,[0x00,0x12,0x73,0x00])
		self.writeRegister(1,0x0D,[0x36,0xB4,0x80,0x00])
		
		self.sendCommand(0x0E+32, [0x41, 0x20, 0x08, 0x04, 0x81, 0x20, 0xCF, 0xF7, 0xFE, 0xFF, 0xFF])


		#gp.output(self.ce,0)
		time.sleep(0.1)

	def send(self,address,data):
		self.setFrequency(2450)				#to reset some strange counter
		self.sendCommand(0xE1, [])			#flush tx fifo
		self.setPowerMode(1)
		self.setComMode(0)
		self.setCE(0, 0.1)
		#self.setTransmitAddress(address) 	#change target address
		#self.sendCommand(0x0A,data)			#write data in fifo tx buffer with autoack
		self.sendCommand(0xB0,data)			#write data in fifo tx buffer
		self.setCE(1, 0.2)					#CE pulse for sending
		self.setCE(0, 0.1)
		self.setComMode(1)					#back to RX mode

	def setListening(self):
		self.setCE(0, 0.2)
		self.setComMode(1)
		self.setPowerMode(1)
		self.setCE(1, 0.2)
		




		


