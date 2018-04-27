import json
import socket

class SimClient(object):
    
    def __init__(self, sim):
        
        data_defs = json.load(open('../react-groundstation-v2/config/packetDefinitions.json'))
        data_defs = data_defs['packetDefinitions']

        accel_data =  data_defs['Name']['FCU DAQ ACCEL 0 ACCEL']
        print(accel_data)
        velocity_data =  data_defs['Name']['FCU DAQ ACCEL 0 VELOCITY']
        displacement_data  = data_defs['Name']['FCU DAQ ACCEL 0 DISPLACEMENT']

    def data_input(self, data):

        for key in data:

            data['pda'] = accel_data
            data['pdv'] = velocity_data
            data['pdp'] = displacement_data

            generate_packet(data)

            return data

    def generate_packet(self, packet_name):

        payload = []

        for i in len(data_defs):
            if data_defs[i]['Name'] == packet_name:
                packet_def = data_defs[i]

                payload.append(tobytes(packet_def))

        send_packet(payload)

        return payload

    def send_packet(self, payload):
        UDP_IP = "192.168.0.255"
        UDP_PORT = 9531

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(payload, (UDP_IP, UDP_PORT))



        

        






