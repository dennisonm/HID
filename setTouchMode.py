import usb.core     # Core USB features.
import usb.util     # USB utility functions.
import argparse     # Parser for command-line options, arguments and sub-commands.
import sys          # System-specific parameters and functions

sys.dont_write_bytecode = True  # Do not write .pyc or .pyo files on the import of source modules.

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
    argparser.add_argument('--rid', help="Report ID", type=auto_int)
    argparser.add_argument('--did', help="Device ID", type=auto_int)
    argparser.add_argument('--mode', help="Touch Mode", type=auto_int)

    # Parse the arguments
    args = argparser.parse_args()

    
    # Parse the arguments
    args = argparser.parse_args()

    # Find device
    dev = usb.core.find(idVendor=args.vid, idProduct=args.pid)

    # Was it found?
    if dev is None:
        raise ValueError('Device not found')
    print("Found " + dev.manufacturer + " for " + dev.product + ".")

    # Interface Number
    bInterfaceNumber = dev[0].interfaces()[0].bInterfaceNumber

    # Determine if a kernel driver is active on an interface.
    # If a kernel driver is active, you cannot claim the interface, and the backend will be unable to perform I/O.
    if dev.is_kernel_driver_active(bInterfaceNumber):
        print("Kernel driver is active.")
        print("Detaching kernel driver...")
        dev.detach_kernel_driver(bInterfaceNumber)
    # The configuration parameter is the bConfigurationValue field of the configuration you want to set as active
    # If you call this method without parameter, it will use the first configuration found.
    print("Setting active configuration...")
    dev.set_configuration()

    # Setup Packet (Setup Stage)
    # A control transfer starts with SETUP transaction which conveys 8 bytes that define the request from the host.
    bmRequestType = 0x21    # Host-to-Device (OUT)
                            # Class
                            # Interface
    bRequest = 0x09         # SET_CONFIGURATION Request
    wValue = 0x03A0         # [Report Type: 1-Input 2-Output 3-Feature][Report ID]
    wIndex = 0x0000         # Interface - Not relevant in setup packet since there is only one device descriptor
    wLength = 0x0008        # Number of bytes to be transferred should there be a data phase 

    # Data
    # The setup stage is followed by by zero or more control data transactions (data stage).
    payload = [args.rid, args.did, args.mode, 0x00, 0x00, 0x00, 0x00, 0x00]

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
        print("Issuing control transfer to set the touch mode...")
        ret = dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data_or_wLength=payload, timeout=1000 )
        #print ret
        print("Touch Mode successfully set to " + touchModes.touchMode[dev.manufacturer][args.mode] + ".")
    except Exception as e:
        print("Something went wrong!")
        print(e)

    # Reset the device
    dev.reset()
