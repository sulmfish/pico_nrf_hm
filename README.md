# pico_nrf_hm
Basic communication with one Hoymiles inverter HM... (HM300 and HM800 tested).

Code is micropython. You may want to use Thonny for editing.

Hardware:
- Raspberry Pi Pico (tested) or maybe any other microcontroller suitable for micropython and
- NRF24L01+ module ("+" is important; NRF24L01 does not work!) and probably
- capacitor: I supplied the NRF from the 3V3 supply of the Pico but had to solder a 100uF capacitor to GND and Vcc of the NRF module (maybe 10uF is enough).

Software:
- nrf24l01.py must be on your Pico. You can download the file from
https://github.com/micropython/micropython-lib/tree/master/micropython/drivers/radio/nrf24l01.
(You can then open the file with Thonny and save it to the connected Pico as nrf24l01.py)
- In the file pico_nrf_hm.py is the code for communicating with the inverter via a NRF24L01+ module. (You can open the file with Thonny and save it to the connected Pico as pico_nrf_hm.py)

The file main.py is just an example for the communication with the inverter.
You can run the file main.py with Thonny or save it from Thonny to the Pico as main.py, so that it starts automatically when powering the Pico.
Modify the file main.py according to your needs: Receive data from the inverter; send commands to the inverter; add code for a display module, ....

Meaning of the received data depends on the inverter (see main.py).

Sometimes a request for new data will not be successfull (see variable "data_info")!

Variable data_info is binary:
- 0b1xxxx = ON/OFF not accomplished;
- 0bx1xxx = timeout;
- 0bxx1xx = crc_m error;
- 0bxxx1x = crc_8 error ;
- 0bxxxx1 = new valid data.

So if data_info & 0b1 == True, the new data is valid.

### Important!!!!!!!
You must provide the serialnumber of YOUR inverter (my_inverter_ser in main.py)!

## This software comes without any warranty! Use it at your own risk!

### Special thanks to

https://github.com/lumapu/ahoy,

https://github.com/tbnobody/OpenDTU,

https://github.com/Knedox/hoymiles_control,

and https://www.mikrocontroller.net/topic/525778.
