
class rftp_pdu():
    version_number = None
    opcode = None
    checksum = None
    file_id = None
    offset = 0

    def __init__(self, version_number, opcode, checksum, file_id, offset):
        self.version_number = version_number
        self.opcode = opcode
        self.checksum = checksum
        self.file_id = file_id
        self.offset = offset
