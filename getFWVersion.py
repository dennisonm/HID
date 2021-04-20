# Test script for parsing the FW version number from bInterfaceNumber 1
# Author M R Dennison
# 20 Apr 2021

import usb.core     # Core USB features.
import usb.util     # USB utility functions.
import argparse     # Parser for command-line options, arguments and sub-commands.
import sys          # System-specific parameters and functions
import os           # Provides functions for interacting with the operating system
import binascii
import time
import itertools
import traceback    # Provide information about the runtime error

sys.dont_write_bytecode = True  # Do not write .pyc or .pyo files on the import of source modules.

# Convert the specified value into int 
def auto_int(x):
    return int(x, 0)

# Main
if __name__ == '__main__':
    # Avoiding UnicodeDecodeError
    if sys.version_info[0] < 3 and sys.getdefaultencoding() != 'utf-8':
        stdin, stdout, stderr = sys.stdin, sys.stdout, sys.stderr                                 
        # The magic trick that enables us to call setdefaultencoding()
        reload(sys)
        sys.stdin, sys.stdout, sys.stderr = stdin, stdout, stderr                                
        sys.setdefaultencoding(os.environ.get('PYTHONIOENCODING', 'utf-8'))

    # Initialise arg parser
    argparser = argparse.ArgumentParser(
        description="Get FW version number."
    )

    # Positional/Optional parameters
    argparser.add_argument('--vid', help="Vendor ID", type=auto_int)
    argparser.add_argument('--pid', help="Product ID", type=auto_int)

    # Handle no arguments call
    if len(sys.argv) < 2:
        argparser.print_usage()
        sys.exit(1)    # Parse the arguments
    
    args = argparser.parse_args()
    
    # Find device
    dev = usb.core.find(idVendor=args.vid, idProduct=args.pid)

    # Was it found?
    if dev is None:
        raise ValueError('Device not found')
    
    print("Found " + dev.product +  " from " + dev.manufacturer + ".")

    # Target Interface 
    bIntNum = 1;

    if os.name != 'nt':
        # Determine if a kernel driver is active on an interface.
        # If a kernel driver is active, you cannot claim the interface, and the backend will be unable to perform I/O.
        if dev.is_kernel_driver_active(bIntNum):
            print("Kernel driver is active.")
            print("Detaching kernel driver of " + str(bIntNum) + "...")
            dev.detach_kernel_driver(bIntNum)
    
    # The configuration parameter is the bConfigurationValue field of the configuration you want to set as active
    # If you call this method without parameter, it will use the first configuration found.
    try:
        if os.name == 'nt':
            print("Setting active configuration...")
            dev.set_configuration()
            print ("Configuration set.")
    except Exception as e:
        print ("Configuration not set.")
        traceback.print_exc()
    
    # Get the current active configuration of the device
    cfg = dev.get_active_configuration()
    
    # Print all the interfaces in the current active configuration
    print("Printing all the interfaces of the current active configuration")
    for interface in cfg:
        print(str(interface))
    print("-------------------------------------------")

    # Set the correct Interface (Interface #1)
    interface = cfg[(1, 0)]

    # Explicitly claim an interface
    # Users normally do not have to worry about interface claiming,
    # as the library takes care of it automatically. But there are situations
    # where you need deterministic interface claiming. For these uncommon
    # cases, you can use claim_interface.
    # If the interface is already claimed, either through a previously call
    # to claim_interface or internally by the device object, nothing happens.    
    print("Trying to claim device...")
    try:
        usb.util.claim_interface(dev, interface)
        print("Claimed device.")
    except usb.core.USBError as e:
        print("Error occurred claiming ")
        traceback.print_exc()

    # Get the OUT descriptor
    outPoint = usb.util.find_descriptor(
        interface,
        # match our first out endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)

    # get the IN descriptor
    inPoint = usb.util.find_descriptor(
        interface,
        # match our first in endpoint
        custom_match= \
            lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

    assert inPoint, outPoint is not None

    # Data
    dataPacket = [0x76, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    # Write data to the endpoint.
    # This method is used to send data to the device. 
    # The endpoint parameter corresponds to the bEndpointAddress member whose endpoint you want to communicate with.
    # The timeout is specified in miliseconds.
    # The method returns the number of bytes written.
    try:
        print("Sending data packet to bEndpointAddress " + hex(outPoint.bEndpointAddress) + "...")
        hex_dataPacket = ['{:02X}'.format(x) for x in dataPacket]
        print(str(hex_dataPacket))
        ret = outPoint.write(dataPacket)
    except Exception as e:
        print(cRed, "Something went wrong during write!") 
        print(e, cEnd)
        traceback.print_exc()
    
    # Read data from the endpoint.
    # This method is used to receive data from the device. 
    # The endpoint parameter corresponds to the bEndpointAddress member whose endpoint you want to communicate with. 
    # The size_or_buffer parameter either tells how many bytes you want to read 
    # or supplies the buffer to receive the data (it must be an object of the type array).
    # The timeout is specified in miliseconds.
    # If the size_or_buffer parameter is the number of bytes to read, the method returns an array object with the data read. 
    # If the size_or_buffer parameter is an array object, it returns the number of bytes actually read.
    
    try: 
        ret = inPoint.read(inPoint.wMaxPacketSize)       
        hex_ret = ['{:02X}'.format(x) for x in ret]
        print("Received " + str(inPoint.wMaxPacketSize) + " from bEndpointAddress " + hex(inPoint.bEndpointAddress) + "...")
        print(str(hex_ret))
        map(hex, ret)
        print("FW Version:  v" + str(ret[8]) + "." + str(ret[10]))  
    except Exception as e:
        print("Something went wrong during read!")
        traceback.print_exc()

    # release the device
    usb.util.release_interface(dev, interface)
