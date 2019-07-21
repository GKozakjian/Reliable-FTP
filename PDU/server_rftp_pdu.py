from PDU.rftp_pdu import *


class server_rftp_pdu(rftp_pdu):
    answer_code = None
    length = None
    buffer = None

    def __init__(self, version_number, opcode, checksum, file_id, offset, answer_code, length, buffer):
        super().__init__(version_number, opcode, checksum, file_id, offset)
        self.answer_code = answer_code
        self.length = length
        self.buffer = buffer


