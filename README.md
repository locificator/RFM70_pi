RFM70_pi
========

A python based module fpr the RFM70 in use with the raspberry pi.

Prerequisites:

- RPi.GPIO 0.5.2 or higher (for python2.7):
    - should allready be installed on newer images of raspbian
    - check with:

            sudo python2.7
            import RPi.GPIO as gp
            gp.VERSION
            exit(0)
    
-   SpiDev:

    source: https://github.com/doceme/py-spidev
    
    tutorial: http://tightdev.net/SpiDev_Doc.pdf


Status: not even alpha

- Interface with SPI on raspberry pi, done
- Configureable init, mostly done
- TX without AUTO_ACK available
- RX a bit weird, not working yet

