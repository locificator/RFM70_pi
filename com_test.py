import rfm70_pi
import time

DEV_0_CE_PIN=25
DEV_0_IRQ_PIN=24   
DEV_0_BUS=0
DEV_0_PORT=0

DEV_1_CE_PIN=17		#CE ... look on the RFM70 >> goes to chip enable pin
DEV_1_IRQ_PIN=4 	#IRQ .. needed for triggering interrupt on incoming transmissions
DEV_1_BUS=0 		#standard on raspberry pi
DEV_1_PORT=1  		#CS ... chip select 1 (two possible: "0" on PIN24 CE0 or "1" or PIN26 CE1 )


dev0=rfm70_pi.device("module extern",DEV_0_BUS,DEV_0_PORT,DEV_0_CE_PIN,DEV_0_IRQ_PIN)
dev0.debug=False 						#default: False

dev1=rfm70_pi.device("module onboard",DEV_1_BUS,DEV_1_PORT,DEV_1_CE_PIN,DEV_1_IRQ_PIN)
dev1.debug=False 						#default: False

def DEV0_initRFM70_bank0():
	dev0.connect()						#init spi device
	dev0.attachInterrupt()				#for irq
	dev0.setPowerMode(1)					
	dev0.setCE(1, 0.2)					#set CE on high, delay after: 200ms
	#dev0.setCE(0, 0.2)					#device should be in stanby I now
	time.sleep(0.2)
	print dev0.fByte(dev0.readRegister(0, 0x00)[0])
	#dev0.sendCommand(0x00+32, [0x0F])
	dev0.setAutoAck([0,0,0,0,0,0])		#set auto ack pipe1, pipe2 .... pipe6
	dev0.enablePipes([1,1,1,1,1,1])		#enable pipes pipe1, pipe2 .... pipe6
	dev0.setRetransmitDelay(500)			#time for delay until a package will be sent again, min 250us, max 4000us in 250us steps
	dev0.setRetransmitAttempts(10)		#amount of retries until error will be set , 0 to 15
	dev0.setFrequency(2450) 				#default: 2402MHz, min 2400, max 2483
	dev0.writeRegister(0, 0x06, [0x3F])	#2Mbit (just the burst) 0011 1 111,full power (+5dBm) 0111 11 1,low noise amplifier is on 011111 0
	dev0.writeRegister(0, 0x07, [0x07])	#0x07 sets RX_FIFO to empty, for more details read the datasheet
	dev0.setListenTo([					#listening addresses for the pipes
		[0x01,0x00,0x00,0x00,0x01],			#pipe 1 
		[0x01,0x00,0x00,0x00,0x01],			#pipe 2 
		[0x02],								#pipe 3     first 4 bytes same as pipe1
		[0x03],								#pipe 4     ----
		[0x04], 							#pipe 5     ----
		[0x05],								#pipe 6		----
		])
	dev0.setTransmitAddress(				#set setListenTo pipe1 to the same address for an autoack
		[0x01,0x00,0x00,0x00,0x02],			
		)
	dev0.setPayloadSize([32,32,32,32,32,32])	#set payload sizes from pipe 1 to pipe 6 to 32bytes (max), min 1
	# register 17 FIFO status
	#----------------bank 0 done-------------------

def DEV0_initRFM70_bank1():
	dev0.initBank1()

def DEV0_init():
	DEV0_initRFM70_bank0()
	DEV0_initRFM70_bank1()
	dev0.activate()
	dev0.writeRegister(0, 0x1C, [0x00])
	dev0.writeRegister(0, 0x1D, [0x07])
	if dev0.readRegister(0, 0x1D)[0]==0x00:		#device was active before, ok then set it active now!
		print "register 0x1D was 0x00, reactivate and writing again"
		dev0.activate()
		dev0.writeRegister(0, 0x1C, [0x00])
		dev0.writeRegister(0, 0x1D, [0x07])

def DEV1_initRFM70_bank0():
	dev1.connect()						#init spi device
	dev1.attachInterrupt()				#for irq
	dev1.setPowerMode(1)					
	dev1.setCE(1, 0.2)					#set CE on high, delay after: 200ms
	#dev1.setCE(0, 0.2)					#device should be in stanby I now
	time.sleep(0.2)
	#dev1.sendCommand(0x00+32, [0x0F])
	print dev1.fByte(dev1.readRegister(0, 0x00)[0])
	dev1.setAutoAck([0,0,0,0,0,0])		#set auto ack pipe1, pipe2 .... pipe6
	dev1.enablePipes([1,1,1,1,1,1])		#enable pipes pipe1, pipe2 .... pipe6
	dev1.setRetransmitDelay(500)			#time for delay until a package will be sent again, min 250us, max 4000us in 250us steps
	dev1.setRetransmitAttempts(10)		#amount of retries until error will be set , 0 to 15
	dev1.setFrequency(2450) 				#default: 2402MHz, min 2400, max 2483
	dev1.writeRegister(0, 0x06, [0x3F])	#2Mbit (just the burst) 0011 1 111,full power (+5dBm) 0111 11 1,low noise amplifier is on 011111 0
	dev1.writeRegister(0, 0x07, [0x07])	#0x07 sets RX_FIFO to empty, for more details read the datasheet
	dev1.setListenTo([					#listening addresses for the pipes
		[0x01,0x00,0x00,0x00,0x02],			#pipe 1 
		[0x01,0x00,0x00,0x00,0x01],			#pipe 2 
		[0x02],								#pipe 3     first 4 bytes same as pipe1
		[0x03],								#pipe 4     ----
		[0x04], 							#pipe 5     ----
		[0x05],								#pipe 6		----
		])
	dev1.setTransmitAddress(				#set setListenTo pipe1 to the same address for an autoack
		[0x01,0x00,0x00,0x00,0x01],			
		)
	dev1.setPayloadSize([32,32,32,32,32,32])	#set payload sizes from pipe 1 to pipe 6 to 32bytes (max), min 1
	# register 17 FIFO status
	#----------------bank 0 done-------------------

def DEV1_initRFM70_bank1():
	dev1.initBank1()

def DEV1_init():
	DEV1_initRFM70_bank0()
	DEV1_initRFM70_bank1()
	dev1.activate()
	dev1.writeRegister(0, 0x1C, [0x00])
	dev1.writeRegister(0, 0x1D, [0x07])
	if dev1.readRegister(0, 0x1D)[0]==0x00:		#device was active before, ok then set it active now!
		print "register 0x1D was 0x00, reactivate and writing again"
		dev1.activate()
		dev1.writeRegister(0, 0x1C, [0x00])
		dev1.writeRegister(0, 0x1D, [0x07])

DEV0_init()
DEV1_init()


#dev1.activate()
#dev0.activate()
print "both devices online"
dev0.activate()
dev1.activate()

dev0.setComMode(1)
dev0.setPowerMode(1)
dev0.setCE(1, 0.2)
#dev0.setListening()
dev0.activate()
dev1.activate()

dev0.writeRegister(0, 0x1D, [0x03])
dev1.writeRegister(0, 0x1D, [0x03])

print dev0.readRegister(0, 0x1D)
print dev1.readRegister(0, 0x1D)

dev0.setListening()

#print dev1.convertPayload(32,"hello world")
#dev0.setComMode(0)
#dev1.setComMode(1)


for i in range(3):
	dev1.send(dev1.readRegister(0, 0x0A), dev1.convertPayload(32,"hello world"))
	#time.sleep(0.2)
	print "dev1: %s || %s" % (dev1.fByte(dev1.readRegister(0, 0x07)[0]),dev1.fByte(dev1.readRegister(0, 0x00)[0]))
	print "dev0: %s || %s" % (dev0.fByte(dev0.readRegister(0, 0x07)[0]),dev0.fByte(dev0.readRegister(0, 0x00)[0]))
	#dev0.send(dev0.readRegister(0, 0x0A), dev0.convertPayload(32,"hello world"))
	#time.sleep(0.2)
	print "dev1: %s || %s" % (dev1.fByte(dev1.readRegister(0, 0x07)[0]),dev1.fByte(dev1.readRegister(0, 0x00)[0]))
	print "dev0: %s || %s" % (dev0.fByte(dev0.readRegister(0, 0x07)[0]),dev0.fByte(dev0.readRegister(0, 0x00)[0]))
	
