# Reliable-FTP

## Introduction
The file transfer protocol is an application layer potocol that runs over TCP or UDP, and facilitates the transmission of data between 
a client and a server, in form of a single file, multiple files or even data chunks or blocks of some file. It is today one of the most 
important standards widely used, and built on the well-known `client-server` architecture model, which in its primitive form, is composed of
two different pieces of software that run on different nodes, and have different functionalities and features. 


Most implementations of FTP run over TCP to make it reliable, but it can also run over UDP to make the data transmission smoother and
faster, but it comes with a tradeoff for channels that suffer from high bit error rates. however, FTP with UDP can be augmented with 
`error control` code, to make it reliable and efficient. If done right, it might work better than TCP in environments which 
suffer from high `jitters` and `round trip times`. From our previous assignment, we have seen that error control is mainly composed of 
`error detection`, and `error correction`. Hence, to make FTP over UDP reliable, we need to support error detection and correctiom. s

In this implementation, error detection will be supported using `checksums` attached to datagram headers, and error correction will be 
handed using `ARQ` which is sending a repeat request to the remote party.


## Implementation& Code
This implementation tries to simulate the Reliable-FTP protocol with re-transmission requests for corrupt data chunks, or transmissions 
with timeouts. Error detection for data chunks is carried out using MD5 hashes as checksums; when the server wants to send some requested
data chunk back to the client, it calculates a new MD5 checksum for data, and adds it to the header of the server_rftp_pdu, which allow 
the client to evaluate the hash, and detect transmission errors. this simple Reliable-FTP implementation also uses threads and UDP
sockets to carry out the conversation between the server and client nodes. 

The Code is written in Python, and includes a good documentation to build on, or translate to other programming languages.


## Read More about it
Please read more in the "Report" directory.


## Developers 
George Kozakjian
