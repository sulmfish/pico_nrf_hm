"""
Micropython code to get live data from Hoymiles inverter (HM...) via NRF24L01+ module using nrf24l01.py driver.

HM1200, HM1500 not yet verified at all.
Setting power limit for HM600, HM700 and HM800 not yet verified.

"""

import time
import struct
import nrf24l01 as nrf


# type of inverter
hm_type_dict = {"1121" : 1, "1141" : 2, "1161" : 3} # 1: HM300, HM350, HM400; 2: HM600, HM700, HM800; 3: HM1200, HM1500
# power for tx
nrf_pa_levels_tuple = (0x00, 0x02, 0x04, 0x06)
dtu_ser = 99978563001 # The pico pretends to be a DTU with this serialnumber when communicating with the inverter
# channels for tx and rx
tx_channels_tuple = (3, 23, 40, 61, 75)
rx_channels_dict = {3 : (40, 61), 23 : (61, 75), 40 : (3, 75), 61 : (3, 23), 75 : (23, 40)}
# definitions for registers
packet_type_dict = {"TX_REQ_INFO" : 0x15, "TX_REQ_DEVCONTROL" : 0x51}
command_dict = {"ON" : 0, "OFF" : 1, "ACTIVE_POWER_LIMIT" : 11}
# miscellaneous
# leading number in packets in answer from inverter
packets_to_receive_dict = {1 : [0x01, 0x82], 2 : [0x01, 0x02, 0x83], 3 : [0x01, 0x02, 0x03, 0x04, 0x85]}
# location of data in packet
data_dict = {1 : ((2, 4), (4, 6), (6, 8), (8, 12), (12, 14), (14, 16), (16, 18), (18, 20), (20, 22), (22, 24), (24, 26), (26, 28), (28, 30)),
             2 : ((2, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 14), (14, 18), (18, 22), (22, 24), (24, 26), (26, 28), (28, 30), (30, 32),
                  (32, 34), (34, 36), (36, 38), (38, 40), (40, 42)),
             3 : ((2, 4), (4, 6), (6, 8), (8, 10), (10, 12), (12, 16), (16, 20), (20, 22), (22, 24), (24, 26), (26, 28), (28, 30), (30, 32),
                  (32, 34), (34, 38), (38, 42), (42, 44), (44, 46), (46, 48), (48, 50), (50, 52), (52, 54), (54, 56), (56, 58), (58, 60), (60, 62))}
evt_dict = {1: 12, 2: 17, 3: 25}
rx_packet_length_dict = {1 : 32, 2 : 44, 3 : 64}


class my_nrf():
    def __init__(self, inv_ser, mynrf_spi, mynrf_cs, mynrf_ce, nrf_pa_level_no = 0, tx_channel_no = 0, timeout_ms = 2000):
        self.inv_ser = inv_ser
        self.hm_type = hm_type_dict[str(self.inv_ser)[:4]]
        self.NRF = nrf.NRF24L01(mynrf_spi, mynrf_cs, mynrf_ce)
        self.set_nrf_power(nrf_pa_level_no)
        self.set_tx_channel(tx_channel_no)
        self.rx_channel = rx_channels_dict[self.tx_channel][0]
        self.set_timeout_ms(timeout_ms)
        # only needed for additional functions for nrf:
        self._in = bytearray(97)  # MISO buffer for full RX FIFO reads + STATUS byte
        self._out = bytearray(97)  # MOSI buffer length must equal MISO buffer length
        self.my_buf = bytearray(1) # for rx data
    
    def set_nrf_power(self, nrf_pa_level_no):
        self.NRF.set_power_speed(nrf_pa_levels_tuple[nrf_pa_level_no % 4], nrf.SPEED_250K)
    
    def set_tx_channel(self, tx_channel_no):
        self.tx_channel = tx_channels_tuple[tx_channel_no % 5]
        
    def set_timeout_ms(self, timeout_ms):
        self.timeout_ms = timeout_ms
        
    def get_data(self):
        self.data_info = 0
        self.packets_to_receive_list = packets_to_receive_dict[self.hm_type][:]
        self.packets_received = []
        payload = self._payload_time()
        packet = self._packet_to_send(packet_type_dict["TX_REQ_INFO"], payload)
        starttime_ms = time.ticks_ms()
        timeout = False
        while not timeout:
            while self.packets_to_receive_list != []:
                # stop if timeout
                if time.ticks_diff(time.ticks_ms(), starttime_ms) > self.timeout_ms:
                    self.data_info |= 0b1000
                    timeout = True
                    break
                self._transmit_package(packet)
                for r in [0, 1]:
                    self.rx_channel = rx_channels_dict[self.tx_channel][r]
                    self._receive_loop(packet)
            if not timeout:
                full_package = bytearray()
                for i in packets_to_receive_dict[self.hm_type]:
                    for j in self.packets_received:
                        if j[0] == i:
                            full_package += j[1]
                            break
                full_package = full_package[:rx_packet_length_dict[self.hm_type]]
                # drop on crc_m error
                if not self._f_crc_m_hm(full_package[:-2]) == struct.unpack('>H', full_package[-2:])[0]:
                    self.data_info |= 0b100
                    self.packets_to_receive_list = packets_to_receive_dict[self.hm_type][:]
                    self.packets_received = []
                else:
                    self.data_info |= 0b1
                    break
            else:
                full_package = bytearray(66)
        return self._parse_packet(full_package)
    
    def send_output_onoff(self, cmd_str, data = None, mod = 0):
        payload = self._payload_command(cmd_str, data, mod)
        packet = self._packet_to_send(packet_type_dict["TX_REQ_DEVCONTROL"], payload)
        evt_old = self._get_evt()
        evt_new = evt_old
        cntr = 0
        self.data_info &= 0b1111
        while evt_new == evt_old:
            for self.tx_channel in tx_channels_tuple:
                self._transmit_package(packet)
            evt_new = self._get_evt()
            cntr += 1
            if cntr == 9:
                self.data_info |= 0b10000
                break
        return self.data_info
    
    def set_output_power_limit(self, limit, relative = False, persist = False):
        mod = persist * 0x100 # 0x100 -> persistent
        mod += relative * 0x1 # 0x1 -> relative (%)
        payload = self._payload_command("ACTIVE_POWER_LIMIT", limit, mod)
        packet = self._packet_to_send(packet_type_dict["TX_REQ_DEVCONTROL"], payload)
        self._transmit_package(packet)
    
    def _get_evt(self):
        while True:
            data, data_info = self.get_data()
            evt = data[evt_dict[self.hm_type]]
            if not (data_info & 0b1000): # no timeout
                break
        return evt
    
    def _payload_time(self):
        payload = bytearray(13)
        payload[0] = 0x0B
        payload[2:5] = struct.pack('>L', time.time())
        payload[9] = 0x05
        return payload
    
    def _payload_command(self, cmd_str, data, mod):
        payload = bytearray(2)
        payload[0] = command_dict[cmd_str]
        if data is not None:
            payload+= data.to_bytes(2, 'big')
            payload+= mod.to_bytes(2, 'big')
        return payload
    
    def _packet_to_send(self, p_type, payload, frame_id = 0):
        packet = bytes([p_type])
        packet += bytearray.fromhex(str(self.inv_ser)[-8:])
        packet += bytearray.fromhex(str(dtu_ser)[-8:])
        packet += int(0x80 + frame_id).to_bytes(1, 'big')
        packet += payload
        if len(payload) > 0:
            packet += struct.pack('>H', self._f_crc_m_hm(payload)) 
        packet += struct.pack('B', self._f_crc8_hm(packet))
        return packet
    
    def _transmit_package(self, package):
        self.inv_esb_addr = b'\01' + package[1:5]
        self.dtu_esb_addr = b'\01' + package[5:9]
        self.NRF.flush_tx()
        self.NRF.set_channel(self.tx_channel)
        self.NRF.stop_listening()
        self.NRF.open_tx_pipe(self.inv_esb_addr)
        self.NRF.open_rx_pipe(0b1, self.dtu_esb_addr)
        self._auto_ack(True, 0b10)
        self.NRF.send(package)
    
    def _receive_loop(self, package):
        self._enable_dynamic_payloads()
        self.NRF.set_channel(self.rx_channel)
        self.NRF.start_listening()
        strtt = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), strtt) < 7: # 5 was too low
            if self.packets_to_receive_list == []:
                break
            self.data_received = False
            if self.NRF.any():
                self.data_received = True
                buffer = self._my_recv()
                buffer27 = buffer[:27]
                received_packet = buffer[9]
                # drop on crc8 error
                if not self._f_crc8_hm(buffer27[:-1]) == buffer27[-1:][0]:
                    self.data_info |= 0b10
                    break
                self.packets_received.append([received_packet, buffer27[10:-1]])
                if received_packet in self.packets_to_receive_list:
                    self.packets_to_receive_list.remove(received_packet)
                    if self.packets_to_receive_list == []:
                        break
    
    def _parse_packet(self, packet):
        self.and_data = 0xffff
        if self.data_info & 0b1000 == True:
            self.and_data = 0
        return [int(str(packet[i:j].hex()), 16) & self.and_data for i, j in data_dict[self.hm_type]], self.data_info
    
    # crc16 modbus: poly = 0x8005; reversed = True; init-value = 0xFFFF; XOR-out = 0x0000; Check = 0x4B37
    def _f_crc_m_hm(self, data_bytes):
        crc = 0xffff
        for b in data_bytes:
            crc ^= b
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xa001
                else:
                    crc >>= 1
        return crc
    
    # crc8_hm: poly = 0x101; reversed = False; init-value = 0x00; XOR-out = 0x00; Check = 0x31
    def _f_crc8_hm(self, data_bytes):
        crc = 0
        for b in data_bytes:
            crc ^= b
            for _ in range(8):
                crc <<= 1
                if crc & 0x0100:
                    crc ^= 0x01
                crc &= 0xFF
        return crc
    
    
    # additional functions for nrf
    
    def _enable_dynamic_payloads(self):
        self.NRF.reg_write(0x1D, 0b100) # EN_DPL: address (0x1D); Bit 2; enables dynamic payload length
        self.NRF.reg_write(0x1C, 0b11) # 0b10) # DYNDP: address (0x1C); DPL_P0: Bit 0; enables dynamic payload length 0b10; requires EN_DPL and ENAA_P1
    
    def _auto_ack(self, aa_bool, aa_0b10 = 0b10):
        if aa_bool: # auto_ack = True
            self.NRF.reg_write(0x01, aa_0b10) # ENAA_Px: address (0x01); Enable auto acknowledgement naa_data_pipe
        else: # auto_ack = False
            aa_0b10_inv = (~ aa_0b10) & 0b111111 # invert 0b10
            self.NRF.reg_write(0x01, aa_0b10_inv) # ENAA_Px: address (0x01); Disable auto acknowledgement naa_data_pipe
    
    def _write_readinto(self, _out, _in):
        self.cs(0)
        time.sleep(0.00001)
        self.spi.write_readinto(_out, _in)
        self.cs(1)
    
    def _reg_read_bytes(self, reg, buf_len = 5):
        self._out[0] = reg
        buf_len += 1
        self._write_readinto(self._out, self._in)
        return self._in[1:buf_len]
    
    def _clear_status_flags(self, data_recv = True, data_sent = True, data_fail = True):
        """This clears the interrupt flags in the status register."""
        config = bool(data_recv) << 6 | bool(data_sent) << 5
        self.NRF.reg_write(7, config | bool(data_fail) << 4)
    
    # for rx; because of different payload size(!?)
    def _my_recv(self):
        self.NRF.cs(0)
        self.NRF.spi.readinto(self.my_buf, nrf.R_RX_PAYLOAD)
        buf = self.NRF.spi.read(32)
        self.NRF.cs(1)
        self.NRF.reg_write(nrf.STATUS, nrf.RX_DR)
        return buf
