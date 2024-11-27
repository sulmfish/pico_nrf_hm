
import time
from machine import SPI, Pin
import pico_nrf_hm


# SETTINGS:
# Inverter type 1: HM300, HM350, HM400
my_inverter_ser = 112183212262
# Inverter type 2: HM600, HM700, HM800
# my_inverter_ser = 1141........
# Inverter type 3: HM1200, HM1500
# my_inverter_ser = 1161........
# transmission power of NRF24L01+_module:
# 0 = -18 dBm (= min); 1 = -12 dBm; 2 = -6 dBm; 3 = 0 dBm (= max)
nrf_pa_level_no = 0
# channel number for transmission; 0 ... 4
tx_channel_no = 0
# Settings for pins and spi-bus for NRF24L01+_module:
nrf_spi = SPI(1, sck=Pin(14), mosi=Pin(15), miso=Pin(12))
nrf_csn = Pin(13, Pin.OUT, value = 1)
nrf_ce = Pin(11, Pin.OUT, value = 0)

#Setting up interface to NRF:
p_n_h = pico_nrf_hm.my_nrf(my_inverter_ser, nrf_spi, nrf_csn, nrf_ce, nrf_pa_level_no, tx_channel_no)


cycletime = 10 # request for data every x seconds


while True:
    data, data_info = p_n_h.get_data()
    if data_info & 0b1 == 0b1: # if data is valid
        # hm-type 1:
        print("U_DC =", data[0]/10, "V  -  I_DC =", data[1]/100, "A  -  P_DC =", data[2]/10, "W  -  Y_DC_tot =", data[3]/1000,
              "kWh  -  Y_DC_day =", data[4], "Wh  -  U_AC =", data[5]/10, "V")
        print("f =", data[6]/100, "Hz  -  P_AC =", data[7]/10, "W  -  Q =", data[8]/10, "  -  I_AC =", data[9]/100, "A  -  PF =",
              data[10]/1000, "  -  T =", data[11]/10, "°C  -  EVT =", data[12])
        # hm-type 2:
        """
        print("U1_DC =", data[0]/10, "V  -  I1_DC =", data[1]/100, "A  -  P1_DC =", data[2]/10, "W  -  U2_DC =", data[3]/10, "V  -  I2_DC =",
              data[4]/100, "A  -  P2_DC =", data[5]/10, "W  -  Y1_DC_tot =", data[6]/1000, "kWh")
        print("Y2_DC_tot =", data[7]/1000, "kWh  -  Y1_DC_day =", data[8], "Wh  -  Y2_DC_day =", data[9], "Wh  -  U_AC =", data[10]/10, "V  -  f =",
              data[11]/100, "Hz  -  P_AC =", data[12]/10, "W  -  Q =", data[13]/10)
        print("I_AC =", data[14]/100, "A  -  PF =", data[15]/1000, "  -  T =", data[16]/10, "°C  -  EVT =", data[17])
        """
        # hm-type 3:
        """
        print("U1_DC =", data[0]/10, "V  -  I1_DC =", data[1]/100, "A  -  I2_DC =", data[2]/100, "A  -  P1_DC =", data[3]/10, "W  -  P2_DC =", data[4]/10, "W")
        print("Y1_DC_day =", data[5], "kWh  -  Y2_DC_day =", data[6], "Wh  -  Y1_DC_tot =", data[7]/1000, "Wh  -  Y2_DC_tot =", data[8]/1000, "Wh")
        print("U3_DC =", data[9]/10, "V  -  I3_DC =", data[10]/100, "A  -  I4_DC =", data[11]/100, "A  -  P3_DC =", data[12]/10, "W  -  P4_DC =", data[13]/10, "W")
        print("Y3_DC_day =", data[14], "kWh  -  Y4_DC_day =", data[15], "Wh  -  Y3_DC_tot =", data[16]/1000, "Wh  -  Y4_DC_tot =", data[17]/1000, "Wh")
        print("U_AC =", data[18]/10, "V  -  f =", data[19]/100 "Hz  -  P_AC =", data[20]/10, "W  -  Q =", data[21]/10)
        print("I_AC =", data[22]/100, "A  -  PF =", data[23]/1000, "  -  T =", data[24]/10, "°C  -  EVT =", data[25])
        """
    time.sleep(cycletime)


# At your own risk:
#data_info = p_n_h.send_output_onoff("OFF")
#data_info = p_n_h.send_output_onoff("ON")
#p_n_h.set_output_power_limit(1000, True, False) # limit(int), relative(bool), persist(bool)
