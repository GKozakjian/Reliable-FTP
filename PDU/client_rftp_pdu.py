from PDU.rftp_pdu import *


class client_rftp_pdu(rftp_pdu):
    file_name = None

    def __init__(self, version_number, opcode, checksum, file_id, offset, file_name):
        super().__init__(version_number, opcode, checksum, file_id, offset)
        self.file_name = file_name


