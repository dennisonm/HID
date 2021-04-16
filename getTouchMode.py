# Test script for getting HID report/feature
# Author M R Dennison
# 19 Jan 2021
import usb.core     # Core USB features.
import usb.util     # USB utility functions.
import argparse     # Parser for command-line options, arguments and sub-commands.
import sys          # System-specific parameters and functions
import os           # Provides functions for interacting with the operating system
import traceback    # Provide information about the runtime error

sys.dont_write_bytecode = True  # Do not write .pyc or .pyo files on the import of source modules.

os.environ['PYUSB_DEBUG'] = 'debug'

import touchModes   # Supplier Touch Modes

# Convert the specified value into int 
def auto_int(x):
    return int(x, 0)

# Main
if __name__ == '__main__':
    # Initialise arg parser
    argparser = argparse.ArgumentParser(
        description="Set Touch Mode"
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

    # Interface Number
    bInterfaceNumber = dev[0].interfaces()[0].bInterfaceNumber

    if os.name != 'nt':
        # Determine if a kernel driver is active on an interface.
        # If a kernel driver is active, you cannot claim the interface, and the backend will be unable to perform I/O.
        if dev.is_kernel_driver_active(bInterfaceNumber):
            print("Kernel driver is active.")
            print("Detaching kernel driver...")
            dev.detach_kernel_driver(bInterfaceNumber)
    
    # The configuration parameter is the bConfigurationValue field of the configuration you want to set as active
    # If you call this method without parameter, it will use the first configuration found.
    try:
        if os.name != 'nt':
            print("Setting active configuration...")
            dev.set_configuration()
            print ("Configuration set.")
    except Exception as e:
        print ("Configuration not set.")
        traceback.print_exc()

    # Setup Packet (Setup Stage)
    # A control transfer starts with SETUP transaction which conveys 8 bytes that define the request from the host.
    bmRequestType = 0xA1    # Device-to-Host (IN)
                            # Class
                            # Interface
    bRequest = 0x01         # GET_REPORT Request
    if dev.manufacturer == "NanoTS":
        wValue = 0x03A3     # [Report Type: 1-Input 2-Output 3-Feature][Report ID]
        rid = 0xA3
        offset = 2          # Location of the touch mode byte
    elif dev.manufacturer == "Gamesman":
        wValue = 0x03A0     # [Report Type: 1-Input 2-Output 3-Feature][Report ID]
        rid = 0xA0
        offset = 3          # Location touch mode byte
    else:
        raise ValueError(dev.manufacturer + ' Device not registered!')
    wIndex = 0x0000         # Interface - Not relevant in setup packet since there is only one device descriptor
    wLength = 0x0008        # Number of bytes to be transferred should there be a data phase 

    # Data
    # The setup stage is followed by by zero or more control data transactions (data stage).

    # Do a control transfer on the endpoint 0
    # 
    # For host to device requests (OUT), data_or_wLength parameter is the data payload to send, 
    # and it must be a sequence type convertible to an array object. 
    # In this case, the return value is the number of bytes written in the data payload. 
    #
    # For device to host requests (IN), data_or_wLength is either the wLength parameter of the control request 
    # specifying the number of bytes to read in data payload, and the return value is an array object with data read, 
    # or an array object which the data will be read to, and the return value is the number of bytes read.
    try:
        print("Issuing control transfer to get the touch mode...")
        print("Sending " + '{:02X}'.format(bmRequestType)  + " " + '{:02X}'.format(bRequest) + " " + '{:04X}'.format(wValue) + " " + '{:04X}'.format(wIndex) + " " + '{:04X}'.format(wLength) + "...")
        ret = dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data_or_wLength=wLength)
        hex_ret = ['{:02X}'.format(x) for x in ret]
        print("Received: ", hex_ret)
        map(hex, ret)
        print("Current Touch Mode is " + touchModes.touchMode[dev.manufacturer][ret[offset]] + ".")
    except Exception as e:
        print("Something went wrong!")
        traceback.print_exc()        